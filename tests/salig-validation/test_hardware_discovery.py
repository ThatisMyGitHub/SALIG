"""Regression tests for the repository-only QNAP discovery package."""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "deploy" / "qnap" / "hardware-discovery"
COLLECTOR = PACKAGE / "collect-qnap-hardware.sh"
VERIFIER = PACKAGE / "verify-qnap-hardware-evidence.sh"
README = PACKAGE / "README.md"


class QnapHardwareDiscoveryTests(unittest.TestCase):
    def test_shell_scripts_parse(self) -> None:
        for script in (COLLECTOR, VERIFIER):
            subprocess.run(["sh", "-n", str(script)], check=True)

    def test_collector_help_is_side_effect_free(self) -> None:
        result = subprocess.run(
            ["sh", str(COLLECTOR), "--help"],
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("--output-dir", result.stdout)
        self.assertIn("read-only", result.stdout.lower())

    def test_collector_requires_absolute_external_output(self) -> None:
        result = subprocess.run(
            ["sh", str(COLLECTOR), "--output-dir", "relative/path"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("absolute", result.stderr)

        result = subprocess.run(
            ["sh", str(COLLECTOR), "--output-dir", str(ROOT / "private-evidence")],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("outside the Git repository", result.stderr)

    def test_collector_avoids_prohibited_mutation_and_secret_dumping(self) -> None:
        content = COLLECTOR.read_text(encoding="utf-8")
        prohibited = (
            r"docker\s+(?:run|start|stop|restart|kill|rm|rmi|pull|push|exec)\b",
            r"docker\s+compose\s+(?:up|down|start|stop|restart|pull)\b",
            r"docker\s+(?:container|image|network|volume)\s+(?:create|rm|prune)\b",
            r"\bdocker\s+inspect\b",
            r"\b(?:printenv|set)\b.*(?:docker|container|host)?\s*environment",
            r"/proc/[0-9*]+/environ",
            r"\bsystemctl\s+(?:start|stop|restart|enable|disable)\b",
            r"\bservice\s+\S+\s+(?:start|stop|restart)\b",
            r"\b(?:apt|apt-get|apk|dnf|yum|pacman)\s+(?:install|remove|upgrade)\b",
        )
        for pattern in prohibited:
            self.assertIsNone(re.search(pattern, content, flags=re.IGNORECASE), pattern)

    def test_documentation_contains_complete_future_host_command(self) -> None:
        content = README.read_text(encoding="utf-8")
        required = (
            "SALIG_REPO=/share/data/dockerapps/SALIG",
            "git fetch origin",
            "git checkout salig/integration",
            "git pull --ff-only origin salig/integration",
            "collect-qnap-hardware.sh",
            "--output-dir",
            "verify-qnap-hardware-evidence.sh",
        )
        for value in required:
            self.assertIn(value, content)

    def test_verifier_rejects_incomplete_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "incomplete.txt"
            evidence.write_text("FORMAT_VERSION=1\n", encoding="utf-8")
            result = subprocess.run(
                ["sh", str(VERIFIER), str(evidence)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 3)
            self.assertIn("missing evidence marker", result.stderr)


if __name__ == "__main__":
    unittest.main()
