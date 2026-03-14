import asyncio
from dataclasses import dataclass, field


@dataclass
class Session:
    session_id: str
    event: asyncio.Event = field(default_factory=asyncio.Event)
    document_request: dict | None = None
    user_response: dict | None = None
    active: bool = True


sessions: dict[str, Session] = {}
