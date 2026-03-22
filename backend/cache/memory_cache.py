import hashlib
import time
from typing import Any, Optional
from loguru import logger


class ScheduleCache:
    """In-memory cache with TTL support."""

    def __init__(self, ttl: int = 3600):
        self._store: dict[str, dict] = {}
        self._ttl = ttl

    def _make_key(self, *parts) -> str:
        return ":".join(str(p) for p in parts)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + self._ttl,
        }
        logger.debug(f"Cache SET: {key}")

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() > entry["expires_at"]:
            del self._store[key]
            logger.debug(f"Cache EXPIRED: {key}")
            return None
        logger.debug(f"Cache HIT: {key}")
        return entry["value"]

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
        logger.info("Cache cleared")

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def stats(self) -> dict:
        now = time.time()
        alive = sum(1 for v in self._store.values() if v["expires_at"] > now)
        return {"total_keys": len(self._store), "alive_keys": alive}


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_str(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


# Global singleton
cache = ScheduleCache()
