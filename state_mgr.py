import json
from pathlib import Path
from threading import Lock

_STATE_FILE = Path("state.json")
_LOCK = Lock()

if _STATE_FILE.exists():
    _state = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
else:
    _state = {}

def _save():
    with _LOCK:
        _STATE_FILE.write_text(json.dumps(_state), encoding="utf-8")

def get_state(user_id: int) -> dict:
    return _state.setdefault(str(user_id), {})

def set_state(user_id: int, data: dict) -> None:
    _state[str(user_id)] = data
    _save()

def clear_state(user_id: int) -> None:
    if str(user_id) in _state:
        del _state[str(user_id)]
        _save()