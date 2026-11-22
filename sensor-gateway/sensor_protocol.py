from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Iterable, Literal

import websockets
from websockets.server import WebSocketServerProtocol

Signal = Literal["eeg", "ppg", "gsr"]


@dataclass(frozen=True)
class SensorBatch:
    signal: Signal
    sample_rate_hz: int
    first_seq: int
    channel_names: list[str]
    samples: list[list[float | None]]
    started_at_ms: int
    raw_channel_names: list[str] | None = None
    raw_samples: list[list[float | None]] | None = None
    status: int | None = None

    def to_message(self, include_raw: bool = False) -> str:
        batch = {
            "signal": self.signal,
            "sampleRateHz": self.sample_rate_hz,
            "firstSeq": self.first_seq,
            "startedAtMs": self.started_at_ms,
            "channelNames": self.channel_names,
            "samples": self.samples,
        }
        if include_raw and self.raw_channel_names is not None:
            batch["rawChannelNames"] = self.raw_channel_names
        if include_raw and self.raw_samples is not None:
            batch["rawSamples"] = self.raw_samples
        if self.status is not None:
            batch["status"] = self.status

        return json.dumps(
            {"type": "sensor_batch", "batch": batch},
            separators=(",", ":"),
            allow_nan=False,
        )


class SensorBroadcaster:
    def __init__(self, include_raw: bool = False) -> None:
        self._clients: set[WebSocketServerProtocol] = set()
        self._last_messages: dict[Signal, str] = {}
        self._has_clients = asyncio.Event()
        self._include_raw = include_raw

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def handle_client(self, websocket: WebSocketServerProtocol) -> None:
        self._clients.add(websocket)
        self._has_clients.set()
        try:
            for message in self._last_messages.values():
                await websocket.send(message)
            await websocket.wait_closed()
        finally:
            self._clients.discard(websocket)
            if not self._clients:
                self._has_clients.clear()

    async def wait_for_client(self) -> None:
        await self._has_clients.wait()

    async def publish(self, batch: SensorBatch) -> None:
        message = batch.to_message(self._include_raw)
        self._last_messages[batch.signal] = message
        if not self._clients:
            return
        disconnected = []
        for client in list(self._clients):
            try:
                await client.send(message)
            except websockets.ConnectionClosed:
                disconnected.append(client)
        for client in disconnected:
            self._clients.discard(client)


def now_ms() -> int:
    return int(time.time() * 1000)


async def run_gateway(
    broadcaster: SensorBroadcaster,
    producers: Iterable[asyncio.Task[None]],
    host: str,
    port: int,
    path: str,
) -> None:
    async def handler(websocket: WebSocketServerProtocol, request_path: str) -> None:
      if request_path.split("?", 1)[0] != path:
          await websocket.close(code=1008, reason="Unsupported path")
          return
      await broadcaster.handle_client(websocket)

    async with websockets.serve(handler, host, port, ping_interval=20, ping_timeout=20):
        print(f"sensor gateway listening on ws://{host}:{port}{path}")
        await asyncio.gather(*producers)


def finite_or_none(value: float) -> float | None:
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value
