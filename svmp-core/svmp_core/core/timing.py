"""Latency-tracing helpers for end-to-end workflow visibility."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Any


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def _to_isoformat(value: datetime) -> str:
    """Serialize a datetime in a stable ISO-8601 format."""

    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class LatencyTrace:
    """Collect absolute timestamps and durations for a workflow run."""

    def __init__(self, name: str, *, started_at: datetime | None = None) -> None:
        self._name = name
        self._started_at = started_at or _utcnow()
        self._perf_started_at = perf_counter()
        self._steps: list[dict[str, Any]] = []

    def _timestamp_for_elapsed(self, elapsed_seconds: float) -> datetime:
        """Translate a perf-counter offset into an absolute timestamp."""

        return self._started_at + timedelta(seconds=elapsed_seconds)

    @contextmanager
    def step(self, name: str, **fields: Any) -> Iterator[dict[str, Any]]:
        """Record a timed step and allow callers to attach extra fields."""

        perf_started_at = perf_counter()
        started_at = self._timestamp_for_elapsed(perf_started_at - self._perf_started_at)
        step: dict[str, Any] = {
            "name": name,
            "startedAt": _to_isoformat(started_at),
            **fields,
        }

        try:
            yield step
        finally:
            perf_finished_at = perf_counter()
            finished_at = self._timestamp_for_elapsed(perf_finished_at - self._perf_started_at)
            step["finishedAt"] = _to_isoformat(finished_at)
            step["durationMs"] = max(0, int(round((perf_finished_at - perf_started_at) * 1000)))
            self._steps.append(step)

    def snapshot(self, **fields: Any) -> dict[str, Any]:
        """Return the current trace snapshot in JSON-safe form."""

        perf_finished_at = perf_counter()
        finished_at = self._timestamp_for_elapsed(perf_finished_at - self._perf_started_at)
        return {
            "trace": self._name,
            "startedAt": _to_isoformat(self._started_at),
            "finishedAt": _to_isoformat(finished_at),
            "durationMs": max(0, int(round((perf_finished_at - self._perf_started_at) * 1000))),
            "steps": [dict(step) for step in self._steps],
            **fields,
        }
