"""Simple in-memory rate limiting and connection tracking."""

import time
from collections import defaultdict


class RateLimiter:
    """Token-bucket-style rate limiter keyed by arbitrary string (e.g. IP)."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self.window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= self.max_requests:
            return False
        self._requests[key].append(now)
        return True


class FailedLoginLimiter:
    """Tracks failed login attempts and locks out a key (e.g., email) if it exceeds max_failures within the window."""

    def __init__(self, max_failures: int, lockout_window_seconds: int):
        self.max_failures = max_failures
        self.window = lockout_window_seconds
        self._failures: dict[str, list[float]] = defaultdict(list)

    def is_locked(self, key: str) -> bool:
        """Check if the key is currently locked out."""
        now = time.time()
        cutoff = now - self.window
        # Clean up old failures outside the window
        self._failures[key] = [t for t in self._failures[key] if t > cutoff]
        return len(self._failures[key]) >= self.max_failures

    def add_failure(self, key: str):
        """Record a failed login attempt."""
        self._failures[key].append(time.time())

    def clear(self, key: str):
        """Clear all failures for a key (e.g., on successful login)."""
        if key in self._failures:
            del self._failures[key]


# --- WebSocket connection tracking ---

_active_connections: dict[str, int] = defaultdict(int)


def track_ws_connection(ip: str, max_per_ip: int) -> bool:
    """Try to register a new WS connection for ip. Returns False if limit exceeded."""
    if _active_connections[ip] >= max_per_ip:
        return False
    _active_connections[ip] += 1
    return True


def release_ws_connection(ip: str):
    """Release a WS connection slot for ip."""
    _active_connections[ip] = max(0, _active_connections[ip] - 1)
