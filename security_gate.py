"""Conservative local decision gate for virtual intent labels."""

def check_intent(intent):
    if not isinstance(intent, str):
        return False, "Invalid intent. Request blocked."
    intent = intent.strip().upper()
    if intent == "SAFE":
        return True, "ALLOW: The request was classified as a benign task."
    if intent == "HARMFUL":
        return False, "BLOCKED: Harmful or unauthorized intent detected."
    if intent == "UNCLEAR":
        return False, "BLOCKED: The request is ambiguous and requires clarification."
    if intent == "CHAT":
        return None, "CHAT: Ordinary conversation; no action requested."
    return False, "BLOCKED: Unrecognized intent was denied by default."


def check_action(action):
    allowed = {"safe_demo", "validate_config", "check_agent_status",
               "verify_audit_chain", "generate_test_report"}
    blocked = {
        "delete_files": "Destructive action blocked",
        "unauthorized_access": "Unauthorized access blocked",
        "steal_data": "Data theft blocked",
        "modify_system_files": "System modification blocked",
        "disable_security": "Security disable attempt blocked",
        "exfiltrate_data": "Unauthorized data transfer blocked",
        "privilege_escalation": "Privilege escalation blocked",
        "tamper_audit_log": "Audit tampering blocked",
        "bypass_security_gate": "Security bypass attempt blocked",
        "persistence_attempt": "Unauthorized persistence blocked",
        "credential_theft": "Credential theft blocked",
        "network_scan": "Unauthorized scanning blocked"
    }
    if not isinstance(action, str):
        return False, "Invalid action"
    action = action.strip().lower()
    if action in blocked:
        return False, blocked[action]
    if action in allowed:
        return True, "Safe demo action allowed"
    return False, "Unknown action blocked"
