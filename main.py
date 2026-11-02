import tempfile
import json
import os
from datetime import datetime, timezone

from agent import DemoAgent
from behavior import learn, learned
from security_gate import check_action

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(DATA, "state.json")
AUDIT = os.path.join(LOGS, "audit.jsonl")

os.makedirs(DATA, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def load_state():
    if not os.path.exists(STATE):
        return {"quarantined": False}
    try:
        with open(STATE, "r", encoding="utf-8") as f:
            state = json.load(f)
        if not isinstance(state, dict) or not isinstance(
            state.get("quarantined"), bool
        ):
            raise ValueError("Invalid state")
        return state
    except (OSError, json.JSONDecodeError, ValueError):
        return {"quarantined": True}


def save_state(state):
    fd, temp = tempfile.mkstemp(
        prefix="state_", suffix=".tmp", dir=DATA
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, STATE)
    except Exception:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def log_event(event):
    from audit_chain import append_event
    event["time"] = now()
    with open(AUDIT, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
    append_event(event)


def status():
    state = load_state()
    print("\nQuarantine:", "ON" if state["quarantined"] else "OFF")
    print("Learned rules:", len(__import__("behavior").load_memory()))


def run_test(action):
    state = load_state()

    if state["quarantined"]:
        print("BLOCKED: Agent is quarantined. Release it from the menu first.")
        return

    agent = DemoAgent()
    decision = agent.decide(action)

    if decision == "AVOID":
        print("AVOID: Stored safety rule says not to repeat this action.")
        log_event({"action": action, "result": "avoided"})
        return

    allowed, reason = check_action(action)

    if not allowed:
        print("BLOCKED:", reason)
        learn(action, reason)
        save_state({"quarantined": True})
        log_event({
            "action": action,
            "result": "blocked_and_quarantined",
            "reason": reason,
        })
        print("Agent quarantined; safety rule saved.")
        return

    print("ALLOWED:", reason)
    log_event({"action": action, "result": "allowed", "reason": reason})

def run_ai_proposal():
    state = load_state()

    if state["quarantined"]:
        print("BLOCKED: Agent is quarantined. Release it from the menu first.")
        return

    agent = DemoAgent()
    action, message = agent.propose_action()

    print("AI status:", message)

    if action is None:
        print("No valid proposal. Nothing was executed.")
        return

    print("AI proposed:", action)
    print("Passing proposal to the existing security gate...")
    run_test(action)

def release_agent():
    state = load_state()
    if not state["quarantined"]:
        print("Agent is not quarantined.")
        return
    confirmation = input("Type RELEASE to confirm: ").strip()
    if confirmation != "RELEASE":
        print("Release cancelled.")
        return
    save_state({"quarantined": False})
    log_event({"result": "manual_release"})
    print("Quarantine released. Stored safety rules remain active.")


def main():
    actions = {
        "1": ("safe_demo", "Safe demo action"),
        "2": ("delete_files", "Simulate file deletion"),
        "3": ("unauthorized_access", "Simulate unauthorized access"),
        "4": ("steal_data", "Simulate data theft"),
        "8": ("modify_system_files", "Simulate system file modification"),
        "9": ("disable_security", "Simulate disabling security"),
        "10": ("exfiltrate_data", "Simulate unauthorized data transfer"),
        "11": ("privilege_escalation", "Simulate privilege escalation"),
        "12": ("tamper_audit_log", "Simulate audit log tampering"),
        "13": ("bypass_security_gate", "Simulate security gate bypass"),
        "14": ("persistence_attempt", "Simulate unauthorized persistence"),
        "15": ("credential_theft", "Simulate credential theft"),
        "16": ("network_scan", "Simulate unauthorized network scan"),
        "17": ("validate_config", "Simulate configuration validation"),
        "18": ("check_agent_status", "Simulate agent status check"),
        "19": ("verify_audit_chain", "Simulate audit chain verification"),
        "20": ("generate_test_report", "Simulate test report generation"),
    }

    while True:
        print("""
=== AI Virtual Jail (SAFE SIMULATION) ===
1. Safe demo action
2. Simulate file deletion
3. Simulate unauthorized access
4. Simulate data theft
5. Show status
6. Release quarantine
7. Request AI action proposal
8. Simulate system file modification
9. Simulate disabling security
10. Simulate unauthorized data transfer
11. Simulate privilege escalation
12. Simulate audit log tampering
13. Simulate security gate bypass
14. Simulate unauthorized persistence
15. Simulate credential theft
16. Simulate unauthorized network scan
17. Simulate configuration validation
18. Simulate agent status check
19. Simulate audit chain verification
20. Simulate test report generation
0. Exit
""")
        choice = input("Choose: ").strip()

        if choice == "0":
            break
        elif choice == "5":
            status()
        elif choice == "6":
            release_agent()
        elif choice == "7":
            run_ai_proposal()
        elif choice in actions:
            action, label = actions[choice]
            print("\nAction:", label)
            run_test(action)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as exc:
        print("Safety stop: operation failed:", exc)
