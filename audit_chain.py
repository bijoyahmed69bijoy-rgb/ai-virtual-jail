import hashlib
import json
import os
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
CHAIN = os.path.join(BASE, "data", "audit_chain.jsonl")
GENESIS = "0" * 64
LOCK = threading.RLock()


def digest(record):
    raw = json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _append_event_unlocked(event):
    previous = GENESIS
    if os.path.exists(CHAIN):
        with open(CHAIN, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if lines:
            last = json.loads(lines[-1])
            if not verify():
                raise RuntimeError("Audit chain verification failed")
            previous = last["hash"]

    record = {"previous_hash": previous, "event": event}
    record["hash"] = digest(record)

    with open(CHAIN, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_event(event):
    with LOCK:
        return _append_event_unlocked(event)

def _verify_unlocked():
    previous = GENESIS
    if not os.path.exists(CHAIN) or os.path.getsize(CHAIN) == 0:
        print("OK: audit chain is empty; no chained events yet")
        return True
    try:
        with open(CHAIN, "r", encoding="utf-8") as f:
            for number, line in enumerate(f, 1):
                record = json.loads(line)
                stored_hash = record.pop("hash")
                if record.get("previous_hash") != previous:
                    print(f"FAIL: chain link at line {number}")
                    return False
                if digest(record) != stored_hash:
                    print(f"FAIL: content changed at line {number}")
                    return False
                previous = stored_hash
    except (OSError, ValueError, KeyError, TypeError):
        print("FAIL: unreadable or invalid audit chain")
        return False

    print("OK: audit chain is intact")
    return True


def verify():
    with LOCK:
        return _verify_unlocked()


if __name__ == "__main__":
    raise SystemExit(0 if verify() else 1)
