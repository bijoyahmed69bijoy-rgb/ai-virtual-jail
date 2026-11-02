import os
import json
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
MEMORY = os.path.join(DATA, "memory.json")

os.makedirs(DATA, exist_ok=True)

_LOCK = threading.RLock()

def load_memory():
    """Load blocked-attempt records for display and compatibility only."""
    with _LOCK:
        try:
            with open(MEMORY, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError, TypeError):
            return {}

def learn(action, reason):
    """Record a blocked attempt; this does not create an enforcement rule."""
    if not isinstance(action, str) or not action.strip():
        return None

    with _LOCK:
        records = load_memory()
        records[action.strip()] = {
            "reason": str(reason or "Blocked by Security Gate"),
            "record_type": "blocked_attempt"
        }

        temp = MEMORY + ".tmp"
        try:
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            os.replace(temp, MEMORY)
        except OSError:
            try:
                if os.path.exists(temp):
                    os.remove(temp)
            except OSError:
                pass
            return None

    return None

def learned(action):
    """Stored records never influence future security decisions."""
    return False
