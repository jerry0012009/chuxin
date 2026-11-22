from __future__ import annotations

import argparse
import asyncio
import math
from collections import deque
from dataclasses import dataclass

from bleak import BleakClient, BleakScanner

from signal_processing import EegDisplayProcessor
from sensor_protocol import SensorBatch, SensorBroadcaster, finite_or_none, now_ms, run_gateway

EEG_DEVICE_NAME = "EEG_8CH"
EEG_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
EEG_TX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
EEG_RX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

PPG_DEVICE_NAME = "PPG_GSR"
PPG_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
PPG_RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
PPG_TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

EEG_CHANNELS = [f"CH{i}_processed_uV" for i in range(1, 9)]
EEG_RAW_CHANNELS = [f"CH{i}_counts" for i in range(1, 9)] + [f"CH{i}_raw_uV" for i in range(1, 9)]
PPG_CHANNELS = ["HR_bpm", "SpO2_pct", "SpO2_RatioR"]
PPG_RAW_CHANNELS = ["RED_raw", "IR_raw"]
GSR_CHANNELS = ["GSR_display_mV", "GSR_display_V", "GSR_physical_mV", "GSR_physical_V"]
GSR_RAW_CHANNELS = ["GSR_raw"]


@dataclass
class EegState:
    buffer: bytearray
    include_raw: bool = False
    first_seq: int | None = None
    last_seq: int | None = None
    seq_count: int = 0
    processor: EegDisplayProcessor | None = None
    pending_first_seq: int | None = None
    pending_raw_uv: list[list[float]] | None = None
    pending_samples: list[list[float]] | None = None
    pending_raw_samples: list[list[float | int]] | None = None


@dataclass
class PpgState:
    buffer: bytearray
    include_raw: bool = False
    first_seq: int | None = None
    last_block: int | None = None
    sample_count: int = 0


def eeg_counts_to_uv(counts: int) -> float:
    return counts * 4.5 / 6 / 8388607 * 1_000_000


async def find_device(name: str) -> str:
    devices = await BleakScanner.discover(timeout=10.0)
    for device in devices:
        if device.name == name:
            return device.address
    raise RuntimeError(f"device not found: {name}")


def parse_int24_signed(raw: bytes) -> int:
    value = int.from_bytes(raw, byteorder="big", signed=False)
    if value >= 1 << 23:
        value -= 1 << 24
    return value


def parse_eeg_packet(pkt: bytes) -> tuple[int, list[int], list[float]]:
    if len(pkt) != 33 or pkt[0] != 0xAA or pkt[1] != 0x83 or pkt[-1] != 0x55:
        raise ValueError("invalid eeg packet")
    checksum = 0
    for value in pkt[:31]:
        checksum ^= value
    if checksum != pkt[31]:
        raise ValueError("bad eeg checksum")

    seq = pkt[2] + pkt[3] * 256
    frame = pkt[4:31]
    samples = []
    counts_samples = []
    for channel in range(8):
        offset = 3 + channel * 3
        counts = parse_int24_signed(frame[offset:offset + 3])
        counts_samples.append(counts)
        samples.append(eeg_counts_to_uv(counts))
    return seq, counts_samples, samples


def parse_ppg_packet(pkt: bytes) -> tuple[int, int, int, list[tuple[int, int]], int]:
    if len(pkt) != 71 or pkt[0] != 0xAA or pkt[1] != 0xD0 or pkt[-1] != 0x55:
        raise ValueError("invalid ppg packet")
    checksum = 0
    for value in pkt[:69]:
        checksum ^= value
    if checksum != pkt[69]:
        raise ValueError("bad ppg checksum")

    block = pkt[2] * 256 + pkt[3]
    first_seq = pkt[4] * 256 + pkt[5]
    status = pkt[6]

    samples = []
    pos = 7
    for _ in range(10):
        red = int.from_bytes(pkt[pos:pos + 3], "big") & 0x03FFFF
        ir = int.from_bytes(pkt[pos + 3:pos + 6], "big") & 0x03FFFF
        samples.append((red, ir))
        pos += 6

    gsr_raw = int.from_bytes(pkt[pos:pos + 2], "big", signed=False)
    if gsr_raw >= 32768:
        gsr_raw -= 65536
    return block, first_seq, status, samples, gsr_raw


async def eeg_loop(client: BleakClient, broadcaster: SensorBroadcaster, include_raw: bool) -> None:
    state = EegState(buffer=bytearray(), include_raw=include_raw, processor=EegDisplayProcessor())

    async def handle(_: int, data: bytearray) -> None:
        state.buffer.extend(data)
        while len(state.buffer) >= 33:
            idx = state.buffer.find(b"\xAA")
            if idx < 0:
                state.buffer.clear()
                return
            if idx > 0:
                del state.buffer[:idx]
            if len(state.buffer) < 33:
                return
            pkt = bytes(state.buffer[:33])
            try:
                seq, counts, raw_uv = parse_eeg_packet(pkt)
            except ValueError:
                del state.buffer[:1]
                continue
            del state.buffer[:33]
            if state.first_seq is None:
                state.first_seq = seq
            state.seq_count += 1
            if state.pending_first_seq is None:
                state.pending_first_seq = seq
                state.pending_raw_uv = []
                state.pending_samples = []
                state.pending_raw_samples = [] if state.include_raw else None
            state.pending_raw_uv.append(raw_uv)
            if state.pending_raw_samples is not None:
                state.pending_raw_samples.append([*counts, *raw_uv])
            if len(state.pending_raw_uv) >= 50:
                state.pending_samples = (
                    state.processor.process_batch(state.pending_raw_uv)
                    if state.processor
                    else state.pending_raw_uv
                )
                await broadcaster.publish(
                    SensorBatch(
                        "eeg",
                        500,
                        state.pending_first_seq,
                        EEG_CHANNELS,
                        state.pending_samples,
                        now_ms(),
                        EEG_RAW_CHANNELS if state.include_raw else None,
                        state.pending_raw_samples,
                    )
                )
                state.pending_first_seq = None
                state.pending_raw_uv = []
                state.pending_samples = []
                state.pending_raw_samples = []

    await client.start_notify(EEG_RX_UUID, handle)
    await client.write_gatt_char(EEG_TX_UUID, bytes([0xAA, 0x31, 0x55]), response=False)
    try:
        while client.is_connected:
            await asyncio.sleep(1.0)
    finally:
        if client.is_connected:
            await client.write_gatt_char(EEG_TX_UUID, bytes([0xAA, 0x32, 0x55]), response=False)


async def ppg_loop(client: BleakClient, broadcaster: SensorBroadcaster, include_raw: bool) -> None:
    state = PpgState(buffer=bytearray(), include_raw=include_raw)
    metrics = PpgMetrics()

    async def handle(_: int, data: bytearray) -> None:
        state.buffer.extend(data)
        while len(state.buffer) >= 71:
            idx = state.buffer.find(b"\xAA")
            if idx < 0:
                state.buffer.clear()
                return
            if idx > 0:
                del state.buffer[:idx]
            if len(state.buffer) < 71:
                return
            pkt = bytes(state.buffer[:71])
            try:
                block, first_seq, status, samples, gsr_raw = parse_ppg_packet(pkt)
            except ValueError:
                del state.buffer[:1]
                continue
            del state.buffer[:71]
            if state.first_seq is None:
                state.first_seq = first_seq

            if status & 0x02:
                samples = [(math.nan, math.nan) for _ in samples]
            for red, ir in samples:
                state.sample_count += 1
                if not (math.isnan(red) or math.isnan(ir)):
                    metrics.append(state.sample_count / 100, int(red), int(ir))
            hr_bpm, spo2_pct, ratio_r = metrics.current()
            if status & 0x01:
                gsr_raw_value = math.nan
            else:
                gsr_raw_value = gsr_raw
            display_v = -gsr_raw_value * 2.048 / 32768
            display_mv = display_v * 1000
            physical_v = -display_v
            physical_mv = -display_mv
            ppg_rows = [
                [finite_or_none(hr_bpm), finite_or_none(spo2_pct), finite_or_none(ratio_r)]
                for _ in samples
            ]

            await broadcaster.publish(
                SensorBatch(
                    "ppg",
                    100,
                    first_seq,
                    PPG_CHANNELS,
                    ppg_rows,
                    now_ms(),
                    PPG_RAW_CHANNELS if state.include_raw else None,
                    [
                        [finite_or_none(float(red)), finite_or_none(float(ir))]
                        for red, ir in samples
                    ] if state.include_raw else None,
                    status,
                )
            )
            await broadcaster.publish(
                SensorBatch(
                    "gsr",
                    10,
                    block,
                    GSR_CHANNELS,
                    [[display_mv, display_v, physical_mv, physical_v]],
                    now_ms(),
                    GSR_RAW_CHANNELS if state.include_raw else None,
                    [[finite_or_none(gsr_raw_value)]] if state.include_raw else None,
                    status,
                )
            )

    await client.start_notify(PPG_TX_UUID, handle)
    await client.write_gatt_char(PPG_RX_UUID, bytes([0xAA, 0x30, 0x55]), response=False)
    try:
        while client.is_connected:
            await asyncio.sleep(1.0)
    finally:
        if client.is_connected:
            await client.write_gatt_char(PPG_RX_UUID, bytes([0xAA, 0x31, 0x55]), response=False)


class PpgMetrics:
    def __init__(self) -> None:
        self._window: deque[tuple[float, int, int]] = deque()
        self._last_hr_update_s = 0.0
        self._last_spo2_update_s = 0.0
        self._hr_bpm = math.nan
        self._spo2_pct = math.nan
        self._ratio_r = math.nan

    def append(self, time_s: float, red: int, ir: int) -> None:
        self._window.append((time_s, red, ir))
        while self._window and time_s - self._window[0][0] > 10:
            self._window.popleft()

        if len(self._window) > 30 and time_s - self._last_hr_update_s >= 1.0:
            self._last_hr_update_s = time_s
            self._hr_bpm = estimate_hr_from_ir(list(self._window))

        if len(self._window) > 500 and time_s - self._last_spo2_update_s >= 1.0:
            self._last_spo2_update_s = time_s
            self._spo2_pct, self._ratio_r = estimate_spo2_from_red_ir(list(self._window))

    def current(self) -> tuple[float, float, float]:
        return self._hr_bpm, self._spo2_pct, self._ratio_r


def estimate_spo2_from_red_ir(window: list[tuple[float, int, int]]) -> tuple[float, float]:
    if len(window) < 100 or window[-1][0] - window[0][0] < 5:
        return math.nan, math.nan

    red = [float(item[1]) for item in window]
    ir = [float(item[2]) for item in window]
    fs = (len(window) - 1) / max(window[-1][0] - window[0][0], 1e-9)
    if fs < 5:
        return math.nan, math.nan

    red_dc = mean(red)
    ir_dc = mean(ir)
    if red_dc <= 1000 or ir_dc <= 1000:
        return math.nan, math.nan

    base_win = max(5, round(fs * 1.5))
    red_ac_signal = subtract(red, moving_mean(red, base_win))
    ir_ac_signal = subtract(ir, moving_mean(ir, base_win))
    red_ac = rms(red_ac_signal)
    ir_ac = rms(ir_ac_signal)
    if red_ac <= 1 or ir_ac <= 1:
        return math.nan, math.nan

    ratio_r = (red_ac / red_dc) / (ir_ac / ir_dc)
    if ratio_r < 0.2 or ratio_r > 2.0:
        return math.nan, ratio_r

    spo2 = 104 - 17 * ratio_r
    if 70 <= spo2 <= 105:
        return min(100, max(70, spo2)), ratio_r
    return math.nan, ratio_r


def estimate_hr_from_ir(window: list[tuple[float, int, int]]) -> float:
    if len(window) < 30 or window[-1][0] - window[0][0] < 5:
        return math.nan

    times = [item[0] for item in window]
    ir = [float(item[2]) for item in window]
    fs = (len(window) - 1) / max(times[-1] - times[0], 1e-9)
    if fs < 5:
        return math.nan

    base_win = max(5, round(fs * 1.5))
    smooth_win = max(3, round(fs * 0.12))
    centered = subtract(ir, moving_mean(ir, base_win))
    smoothed = moving_mean(centered, smooth_win)

    hr1, score1 = find_ppg_peaks(times, smoothed)
    hr2, score2 = find_ppg_peaks(times, [-value for value in smoothed])
    return hr1 if score1 >= score2 else hr2


def find_ppg_peaks(times: list[float], values: list[float]) -> tuple[float, float]:
    if len(values) < 10 or stdev(values) <= 1e-12:
        return math.nan, 0.0

    min_hr = 45
    max_hr = 180
    min_interval = 60 / max_hr
    max_interval = 60 / min_hr
    threshold = median(values) + 0.35 * stdev(values)
    candidates = [
        index
        for index in range(1, len(values) - 1)
        if values[index] > values[index - 1]
        and values[index] >= values[index + 1]
        and values[index] > threshold
    ]
    if not candidates:
        return math.nan, 0.0

    selected: list[int] = []
    for candidate in candidates:
        if not selected:
            selected.append(candidate)
            continue
        last = selected[-1]
        if times[candidate] - times[last] >= min_interval:
            selected.append(candidate)
        elif values[candidate] > values[last]:
            selected[-1] = candidate

    if len(selected) < 3:
        return math.nan, 0.0

    intervals = [
        times[selected[index]] - times[selected[index - 1]]
        for index in range(1, len(selected))
    ]
    intervals = [value for value in intervals if min_interval <= value <= max_interval]
    if len(intervals) < 2:
        return math.nan, 0.0

    hr_bpm = 60 / median(intervals)
    if hr_bpm < min_hr or hr_bpm > max_hr:
        return math.nan, 0.0

    score = len(intervals) * stdev([values[index] for index in selected])
    return hr_bpm, score


def moving_mean(values: list[float], window: int) -> list[float]:
    if window <= 1:
        return values[:]
    half_left = (window - 1) // 2
    half_right = window // 2
    prefix = [0.0]
    for value in values:
        prefix.append(prefix[-1] + value)
    output = []
    for index in range(len(values)):
        start = max(0, index - half_left)
        end = min(len(values), index + half_right + 1)
        output.append((prefix[end] - prefix[start]) / (end - start))
    return output


def subtract(left: list[float], right: list[float]) -> list[float]:
    return [left[index] - right[index] for index in range(len(left))]


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def median(values: list[float]) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def rms(values: list[float]) -> float:
    if not values:
        return math.nan
    return math.sqrt(sum(value * value for value in values) / len(values))


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eeg-address")
    parser.add_argument("--ppg-address")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18081)
    parser.add_argument("--path", default="/chuxin-vue/sensor-gateway/ws")
    parser.add_argument("--include-raw", action="store_true")
    args = parser.parse_args()

    eeg_address = args.eeg_address or await find_device(EEG_DEVICE_NAME)
    ppg_address = args.ppg_address or await find_device(PPG_DEVICE_NAME)
    broadcaster = SensorBroadcaster(include_raw=args.include_raw)

    async with BleakClient(eeg_address) as eeg_client, BleakClient(ppg_address) as ppg_client:
        producers = [
            asyncio.create_task(eeg_loop(eeg_client, broadcaster, args.include_raw)),
            asyncio.create_task(ppg_loop(ppg_client, broadcaster, args.include_raw)),
        ]
        await run_gateway(broadcaster, producers, args.host, args.port, args.path)


if __name__ == "__main__":
    asyncio.run(main())
