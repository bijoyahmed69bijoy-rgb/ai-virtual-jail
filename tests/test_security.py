import unittest

from security_gate import check_action
from agent import DemoAgent


DANGEROUS_ACTIONS = (
    "delete_files",
    "unauthorized_access",
    "steal_data",
    "modify_system_files",
    "disable_security",
    "exfiltrate_data",
    "privilege_escalation",
    "tamper_audit_log",
    "bypass_security_gate",
    "persistence_attempt",
    "credential_theft",
    "network_scan",
)


class SecurityGateTests(unittest.TestCase):
    def test_safe_demo_is_allowed(self):
        allowed, reason = check_action("safe_demo")
        self.assertTrue(allowed)
        self.assertIn("allowed", reason.lower())

    def test_all_dangerous_actions_are_blocked(self):
        for action in DANGEROUS_ACTIONS:
            with self.subTest(action=action):
                allowed, reason = check_action(action)
                self.assertFalse(allowed)
                self.assertTrue(reason)

    def test_unknown_action_is_blocked(self):
        allowed, reason = check_action("unknown_test_action")
        self.assertFalse(allowed)
        self.assertIn("unknown", reason.lower())

    def test_action_with_spaces_and_uppercase(self):
        allowed, _ = check_action(" SAFE_DEMO ")
        self.assertTrue(allowed)

    def test_invalid_action_type_is_blocked(self):
        allowed, reason = check_action(None)
        self.assertFalse(allowed)
        self.assertEqual(reason, "Invalid action")

    def test_agent_knows_all_dangerous_actions(self):
        agent = DemoAgent()
        for action in DANGEROUS_ACTIONS:
            with self.subTest(action=action):
                self.assertIn(action, agent.ACTIONS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
