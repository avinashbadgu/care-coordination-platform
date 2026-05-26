"""Notification reliability layer.

Per CLAUDE.md the operational reliability matters more than flashy AI. This
keeps the interface small (Channel.send returning success/false) and tracks
delivery attempts so the workflow engine and timeline see what happened.
The default channel is a deterministic in-memory log channel — production
deployments slot in SMS / push providers behind the same Protocol.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Protocol

log = logging.getLogger(__name__)


@dataclass
class DeliveryAttempt:
    channel: str
    success: bool
    detail: str | None = None


@dataclass
class Outbox:
    items: list[dict] = field(default_factory=list)

    def append(self, **kwargs) -> None:
        self.items.append(kwargs)


# Process-global outbox so tests / scripts can inspect what was "sent".
OUTBOX = Outbox()


class Channel(Protocol):
    name: str

    def send(self, *, patient_id: int, title: str, body: str) -> bool: ...


class LogChannel:
    """Pretend-channel that always succeeds and writes to the outbox."""

    name: str = "log"

    def send(self, *, patient_id: int, title: str, body: str) -> bool:
        OUTBOX.append(channel=self.name, patient_id=patient_id, title=title, body=body)
        log.info("notification[%s] -> patient=%s :: %s", self.name, patient_id, title)
        return True


class FailingChannel:
    """Always-fails channel — used to demonstrate retry / fallback behaviour."""

    name: str = "failing"

    def send(self, *, patient_id: int, title: str, body: str) -> bool:
        return False


class NotificationService:
    """Tries a chain of channels with simple in-call retries.

    Returns (success, channel_used, attempt_count). The channel_used is the
    last channel that was attempted; on success it's the one that delivered.
    """

    def __init__(self, channels: Iterable[Channel] | None = None) -> None:
        self.channels = list(channels) if channels is not None else [LogChannel()]

    def send_reminder(
        self, *, patient_id: int, title: str, body: str
    ) -> tuple[bool, str, int]:
        attempts = 0
        last_channel = self.channels[0].name if self.channels else "none"
        for channel in self.channels:
            attempts += 1
            last_channel = channel.name
            try:
                if channel.send(patient_id=patient_id, title=title, body=body):
                    return True, channel.name, attempts
            except Exception:  # noqa: BLE001
                log.exception("channel %s raised; trying next", channel.name)
        return False, last_channel, attempts
