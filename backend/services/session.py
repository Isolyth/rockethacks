from dataclasses import dataclass


@dataclass
class Session:
    session_id: str
    language: str = "en"
    user_response: dict | None = None
    active: bool = True
    user_id: str | None = None
    encryption_key: bytes | None = None


sessions: dict[str, Session] = {}
