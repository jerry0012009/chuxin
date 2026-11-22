from __future__ import annotations

import math


class EegDisplayProcessor:
    def __init__(self, fs: int = 500) -> None:
        self._fs = fs
        self._states: list[EegChannelState] = []

    def process(self, raw_uv: list[float]) -> list[float]:
        return self.process_batch([raw_uv])[-1]

    def process_batch(self, raw_rows: list[list[float]]) -> list[list[float]]:
        if not raw_rows:
            return []

        self._ensure_states(len(raw_rows[0]))
        return [
            [
                state.process(value)
                for state, value in zip(self._states, row)
            ]
            for row in raw_rows
        ]

    def _ensure_states(self, channel_count: int) -> None:
        while len(self._states) < channel_count:
            self._states.append(EegChannelState(self._fs))


class EegChannelState:
    def __init__(self, fs: int) -> None:
        dt = 1 / fs
        high_pass_tau_s = 1.0
        self._hp_alpha = high_pass_tau_s / (high_pass_tau_s + dt)
        self._prev_x: float | None = None
        self._prev_hp_y = 0.0

        notch_freq = 50
        r = 0.95
        theta = 2 * math.pi * notch_freq / fs
        self._b0 = 1.0
        self._b1 = -2 * math.cos(theta)
        self._b2 = 1.0
        self._a1 = -2 * r * math.cos(theta)
        self._a2 = r * r
        self._x1 = self._x2 = 0.0
        self._y1 = self._y2 = 0.0

    def process(self, value: float) -> float:
        if not math.isfinite(value):
            return math.nan
        if self._prev_x is None:
            self._prev_x = value
            return 0.0

        high_passed = self._hp_alpha * (self._prev_hp_y + value - self._prev_x)
        self._prev_x = value
        self._prev_hp_y = high_passed
        return self._notch(high_passed)

    def _notch(self, value: float) -> float:
        y = self._b0 * value + self._b1 * self._x1 + self._b2 * self._x2 - self._a1 * self._y1 - self._a2 * self._y2
        self._x2 = self._x1
        self._x1 = value
        self._y2 = self._y1
        self._y1 = y
        return y
