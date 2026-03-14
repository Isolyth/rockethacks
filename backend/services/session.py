from dataclasses import dataclass


@dataclass
class Session:
    session_id: str
    user_response: dict | None = None
    active: bool = True


sessions: dict[str, Session] = {}
