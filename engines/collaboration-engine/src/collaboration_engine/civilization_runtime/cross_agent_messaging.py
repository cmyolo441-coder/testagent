"""Cross-Agent Messaging — Inboxes, point-to-point send, and room broadcasts."""
from dataclasses import dataclass, field
from typing import Any, Optional
import time
import uuid


@dataclass
class Message:
    id: str = field(default_factory=lambda: f"MSG-{uuid.uuid4().hex[:8]}")
    from_id: str = ""
    to_id: str = ""  # empty when broadcast
    room: Optional[str] = None
    msg_type: str = "info"
    payload: Any = None
    ts: float = field(default_factory=time.time)


class CrossAgentMessenger:
    """Inbox-per-agent messaging with room broadcasts."""

    def __init__(self):
        self.inboxes: dict[str, list[Message]] = {}
        self.rooms: dict[str, set[str]] = {}
        self.sent: list[Message] = []

    def _inbox(self, agent_id: str) -> list[Message]:
        return self.inboxes.setdefault(agent_id, [])

    def join_room(self, agent_id: str, room: str) -> None:
        self.rooms.setdefault(room, set()).add(agent_id)
        self._inbox(agent_id)  # ensure inbox exists

    def leave_room(self, agent_id: str, room: str) -> None:
        if room in self.rooms:
            self.rooms[room].discard(agent_id)

    def send(self, from_id: str, to_id: str, msg_type: str, payload: Any) -> Message:
        msg = Message(from_id=from_id, to_id=to_id, msg_type=msg_type, payload=payload)
        self._inbox(to_id).append(msg)
        self.sent.append(msg)
        return msg

    def broadcast(self, room: str, payload: Any, from_id: str = "system",
                  msg_type: str = "broadcast") -> list[Message]:
        members = self.rooms.get(room, set())
        delivered: list[Message] = []
        for member_id in members:
            if member_id == from_id:
                continue
            msg = Message(from_id=from_id, to_id=member_id, room=room,
                          msg_type=msg_type, payload=payload)
            self._inbox(member_id).append(msg)
            self.sent.append(msg)
            delivered.append(msg)
        return delivered

    def receive(self, agent_id: str, since_ts: float = 0.0) -> list[Message]:
        return [m for m in self._inbox(agent_id) if m.ts >= since_ts]

    def clear_inbox(self, agent_id: str) -> int:
        n = len(self._inbox(agent_id))
        self.inboxes[agent_id] = []
        return n

    def stats(self) -> dict:
        return {
            "agents": len(self.inboxes),
            "rooms": len(self.rooms),
            "messages_sent": len(self.sent),
            "inbox_sizes": {a: len(b) for a, b in self.inboxes.items()},
        }
