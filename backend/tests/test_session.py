"""Tests for services/session.py — Session management."""

from services.session import Session, sessions


class TestSession:
    def test_create_session(self):
        s = Session(session_id="abc123")
        assert s.session_id == "abc123"
        assert s.language == "en"
        assert s.user_response is None
        assert s.active is True

    def test_custom_language(self):
        s = Session(session_id="test", language="es")
        assert s.language == "es"

    def test_set_user_response(self):
        s = Session(session_id="test")
        s.user_response = {"action": "upload", "document_text": "some text"}
        assert s.user_response["action"] == "upload"

    def test_clear_user_response(self):
        s = Session(session_id="test")
        s.user_response = {"answer": "Option A"}
        s.user_response = None
        assert s.user_response is None

    def test_deactivate(self):
        s = Session(session_id="test")
        assert s.active is True
        s.active = False
        assert s.active is False

    def test_sessions_dict_add_remove(self):
        sid = "test-session-001"
        s = Session(session_id=sid)
        sessions[sid] = s
        assert sid in sessions
        assert sessions[sid].session_id == sid

        sessions.pop(sid, None)
        assert sid not in sessions

    def test_multiple_sessions(self):
        s1 = Session(session_id="s1", language="en")
        s2 = Session(session_id="s2", language="fr")
        sessions["s1"] = s1
        sessions["s2"] = s2

        assert sessions["s1"].language == "en"
        assert sessions["s2"].language == "fr"

        # Cleanup
        sessions.pop("s1", None)
        sessions.pop("s2", None)

    def test_session_equality_by_identity(self):
        s1 = Session(session_id="same")
        s2 = Session(session_id="same")
        # Dataclasses support equality by value
        assert s1 == s2

    def test_session_different_state(self):
        s1 = Session(session_id="same")
        s2 = Session(session_id="same", active=False)
        assert s1 != s2
