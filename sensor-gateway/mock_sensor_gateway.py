from __future__ import annotations

import argparse
import asyncio
import csv
import math
from pathlib import Path
from typing import TextIO

from signal_processing import EegDisplayProcessor
from sensor_protocol import SensorBatch, SensorBroadcaster, finite_or_none, now_ms, run_gateway

ROOT = Path(__file__).resolve().parents[1]
HARDWARE_DATA = ROOT / "hardware" / "EEG+GSR+PPG_test_data & matlab_code"

EEG_CHANNELS = [f"CH{i}_processed_uV" for i in range(1, 9)]
EEG_RAW_CHANNELS = [f"CH{i}_counts" for i in range(1, 9)] + [f"CH{i}_raw_uV" for i in range(1, 9)]
PPG_CHANNELS = ["HR_bpm", "SpO2_pct", "SpO2_RatioR"]
PPG_RAW_CHANNELS = ["RED_raw", "IR_raw"]
GSR_CHANNELS = ["GSR_display_mV", "GSR_display_V", "GSR_physical_mV", "GSR_physical_V"]
GSR_RAW_CHANNELS = ["GSR_raw"]


def number(value: str | None) -> float:
    if value is None or value == "":
        return math.nan
    try:
        parsed = float(value)
    except ValueError:
        return math.nan
    return parsed if math.isfinite(parsed) else math.nan


class CsvCursor:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.file: TextIO | None = None
        self.reader: csv.DictReader[str] | None = None

    def take(self, count: int) -> list[dict[str, str]]:
        return [self.next_row() for _ in range(count)]

    def next_row(self) -> dict[str, str]:
        while True:
            if self.reader is None:
                self.open()
            assert self.reader is not None
            row = next(self.reader, None)
            if row is not None:
                return row
            self.close()

    def open(self) -> None:
        self.file = self.path.open(newline="")
        self.reader = csv.DictReader(self.file)

    def close(self) -> None:
        if self.file is not None:
            self.file.close()
        self.file = None
        self.reader = None


async def publish_eeg(
    broadcaster: SensorBroadcaster,
    cursor: CsvCursor,
    processor: EegDisplayProcessor,
    started_at_ms: int,
    batch_size: int,
    include_raw: bool,
) -> None:
    rows = cursor.take(batch_size)
    first_seq = int(number(rows[0].get("Seq")))
    raw_uv_rows = []
    raw_samples = [] if include_raw else None
    for row in rows:
        raw_uv_rows.append([number(row.get(f"CH{i}_raw_uV")) for i in range(1, 9)])
        if raw_samples is not None:
            raw_samples.append([
                finite_or_none(number(row.get(channel)))
                for channel in EEG_RAW_CHANNELS
            ])
    samples = [
        [finite_or_none(value) for value in processed_uv]
        for processed_uv in processor.process_batch(raw_uv_rows)
    ]
    await broadcaster.publish(
        SensorBatch(
            "eeg",
            500,
            first_seq,
            EEG_CHANNELS,
            samples,
            started_at_ms,
            EEG_RAW_CHANNELS if include_raw else None,
            raw_samples,
        )
    )


async def publish_ppg(
    broadcaster: SensorBroadcaster,
    cursor: CsvCursor,
    started_at_ms: int,
    batch_size: int,
    include_raw: bool,
) -> None:
    rows = cursor.take(batch_size)
    first_seq = int(number(rows[0].get("SEQ")))
    samples = [
        [finite_or_none(number(row.get(channel))) for channel in PPG_CHANNELS]
        for row in rows
    ]
    raw_samples = (
        [
            [finite_or_none(number(row.get(channel))) for channel in PPG_RAW_CHANNELS]
            for row in rows
        ]
        if include_raw
        else None
    )
    await broadcaster.publish(
        SensorBatch(
            "ppg",
            100,
            first_seq,
            PPG_CHANNELS,
            samples,
            started_at_ms,
            PPG_RAW_CHANNELS if include_raw else None,
            raw_samples,
        )
    )


async def publish_gsr(
    broadcaster: SensorBroadcaster,
    cursor: CsvCursor,
    started_at_ms: int,
    batch_size: int,
    include_raw: bool,
) -> None:
    rows = cursor.take(batch_size)
    samples = []
    raw_samples = [] if include_raw else None
    for row in rows:
        raw = number(row.get("GSR_raw"))
        physical_v = raw * 2.048 / 32768
        physical_mv = physical_v * 1000
        display_v = -physical_v
        display_mv = -physical_mv
        samples.append([display_mv, display_v, physical_mv, physical_v])
        if raw_samples is not None:
            raw_samples.append([finite_or_none(raw)])
    block = int(number(rows[0].get("BLOCK")))
    await broadcaster.publish(
        SensorBatch(
            "gsr",
            10,
            block,
            GSR_CHANNELS,
            samples,
            started_at_ms,
            GSR_RAW_CHANNELS if include_raw else None,
            raw_samples,
        )
    )


async def produce_mock(
    broadcaster: SensorBroadcaster,
    started_at_ms: int,
    data_dir: Path,
    batch_ms: int,
    include_raw: bool,
) -> None:
    cursor = CsvCursor(data_dir / "EEG_raw_continuous_20260610_153657.csv")
    ppg_cursor = CsvCursor(data_dir / "PPG_100Hz_data.csv")
    gsr_cursor = CsvCursor(data_dir / "GSR_10Hz_data.csv")
    processor = EegDisplayProcessor()
    eeg_batch_size = max(1, round(500 * batch_ms / 1000))
    ppg_batch_size = max(1, round(100 * batch_ms / 1000))
    gsr_exact = 10 * batch_ms / 1000
    gsr_carry = 0.0
    sleep_s = batch_ms / 1000

    while True:
        await broadcaster.wait_for_client()
        await publish_eeg(broadcaster, cursor, processor, started_at_ms, eeg_batch_size, include_raw)
        await publish_ppg(broadcaster, ppg_cursor, started_at_ms, ppg_batch_size, include_raw)
        gsr_carry += gsr_exact
        gsr_batch_size = int(gsr_carry)
        if gsr_batch_size > 0:
            await publish_gsr(broadcaster, gsr_cursor, started_at_ms, gsr_batch_size, include_raw)
            gsr_carry -= gsr_batch_size
        await asyncio.sleep(sleep_s)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18081)
    parser.add_argument("--path", default="/chuxin-vue/sensor-gateway/ws")
    parser.add_argument("--data-dir", type=Path, default=HARDWARE_DATA)
    parser.add_argument("--batch-ms", type=int, default=250)
    parser.add_argument("--include-raw", action="store_true")
    args = parser.parse_args()

    batch_ms = min(1000, max(100, args.batch_ms))
    broadcaster = SensorBroadcaster(include_raw=args.include_raw)
    started_at_ms = now_ms()
    producers = [asyncio.create_task(produce_mock(broadcaster, started_at_ms, args.data_dir, batch_ms, args.include_raw))]
    await run_gateway(broadcaster, producers, args.host, args.port, args.path)


if __name__ == "__main__":
    asyncio.run(main())
