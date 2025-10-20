import asyncio

_locks: dict[str, asyncio.Lock] = {}

def get_lock(key: str) -> asyncio.Lock:
    """Возвращает глобальный asyncio.Lock по ключу, создавая при необходимости."""
    lock = _locks.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _locks[key] = lock
    return lock


