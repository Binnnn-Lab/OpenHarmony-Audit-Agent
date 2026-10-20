import os
import unittest
from pathlib import Path
from unittest.mock import patch

from openharmony_audit.workflow.generic_contracts import RuntimeConfig, ConfigError
from openharmony_audit.workflow.generic_runner import runtime_command, _runtime_environment


class CodexWorkflowTests(unittest.TestCase):
    def test_codex_stdin_json_and_sandbox(self):
        runtime = {"adapter": "codex", "command": "codex", "model": "example-model"}
        self.assertEqual(RuntimeConfig.from_dict(runtime).command, "codex")
        command = runtime_command(runtime)
        self.assertEqual(command[-1], "-")
        self.assertIn("--json", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "workspace-write")
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)

    def test_codex_uses_existing_auth_directory_without_inheriting_secrets(self):
        runtime = {"adapter": "codex", "command": "codex", "model": "example-model"}
        with patch.dict(os.environ, {"HOME": "/user", "CODEX_HOME": "/auth",
                                    "USERPROFILE": "C:/user", "UNRELATED_SECRET": "private"}, clear=True):
            env = _runtime_environment(runtime, Path("/worker"))
        self.assertEqual(env["HOME"], "/user")
        self.assertEqual(env["CODEX_HOME"], "/auth")
        self.assertEqual(env["USERPROFILE"], "C:/user")
        self.assertNotIn("UNRELATED_SECRET", env)
        self.assertNotIn("ANTHROPIC_MODEL", env)

    def test_claude_command_compatibility_and_unknown_adapter(self):
        self.assertEqual(runtime_command({"command": "claude", "model": "example"})[:3],
                         ["claude", "-p", "--model"])
        with self.assertRaises(ConfigError):
            runtime_command({"adapter": "unknown"})


if __name__ == "__main__":
    unittest.main()
