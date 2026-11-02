import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class JailIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.logs = self.root / "logs"
        self.data.mkdir()
        self.logs.mkdir()

        self.state = self.data / "state.json"
        self.memory = self.data / "memory.json"
        self.audit = self.logs / "audit.jsonl"

        self.state.write_text(
            json.dumps({"quarantined": False}), encoding="utf-8"
        )
        self.memory.write_text("{}", encoding="utf-8")
        self.audit.write_text("", encoding="utf-8")

        self.patches = [
            patch.object(main, "STATE", str(self.state)),
            patch.object(main, "AUDIT", str(self.audit)),
            patch("behavior.MEMORY", str(self.memory)),
            patch("audit_chain.CHAIN", str(self.root / "audit_chain.jsonl")),
        ]

        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def tearDown(self):
        self.temp.cleanup()

    def test_dangerous_action_quarantines_agent(self):
        main.run_test("delete_files")

        state = json.loads(self.state.read_text(encoding="utf-8"))
        memory = json.loads(self.memory.read_text(encoding="utf-8"))
        events = [
            json.loads(line)
            for line in self.audit.read_text(encoding="utf-8").splitlines()
        ]

        self.assertTrue(state["quarantined"])
        self.assertIn("delete_files", memory)
        self.assertEqual(events[-1]["result"], "blocked_and_quarantined")

    def test_quarantined_agent_cannot_run_action(self):
        self.state.write_text(
            json.dumps({"quarantined": True}), encoding="utf-8"
        )

        main.run_test("safe_demo")

        self.assertEqual(self.audit.read_text(encoding="utf-8"), "")
        self.assertTrue(
            json.loads(self.state.read_text(encoding="utf-8"))["quarantined"]
        )

    def test_safe_action_is_logged(self):
        main.run_test("safe_demo")

        events = [
            json.loads(line)
            for line in self.audit.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(events[-1]["action"], "safe_demo")
        self.assertEqual(events[-1]["result"], "allowed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
