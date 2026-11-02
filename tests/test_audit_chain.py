import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit_chain


class AuditChainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.chain = Path(self.temp.name) / "test_chain.jsonl"
        self.patch = patch.object(audit_chain, "CHAIN", str(self.chain))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_new_event_creates_valid_chain(self):
        audit_chain.append_event({"action": "safe_demo"})
        audit_chain.append_event({"action": "second_demo"})

        with patch("builtins.print"):
            self.assertTrue(audit_chain.verify())

        records = [
            json.loads(line)
            for line in self.chain.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(records), 2)
        self.assertEqual(records[1]["previous_hash"], records[0]["hash"])

    def test_modified_record_is_detected(self):
        audit_chain.append_event({"action": "safe_demo"})
        record = json.loads(self.chain.read_text(encoding="utf-8"))
        record["event"]["action"] = "tampered_action"
        self.chain.write_text(json.dumps(record) + "\n", encoding="utf-8")

        with patch("builtins.print"):
            self.assertFalse(audit_chain.verify())

    def test_corrupted_chain_rejects_new_event(self):
        audit_chain.append_event({"action": "safe_demo"})
        record = json.loads(self.chain.read_text(encoding="utf-8"))
        record["hash"] = "f" * 64
        self.chain.write_text(json.dumps(record) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(
            RuntimeError, "Audit chain verification failed"
        ):
            audit_chain.append_event({"action": "second_demo"})

        self.assertEqual(len(self.chain.read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
