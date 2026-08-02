from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import salig_validate as validator  # noqa: E402


class SaligValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compose = yaml.safe_load((ROOT / "deploy/qnap/compose.yaml").read_text(encoding="utf-8"))
        cls.allowlist = yaml.safe_load((ROOT / "salig/model-allowlist.yaml").read_text(encoding="utf-8"))
        cls.schema = json.loads((ROOT / "salig/model-allowlist.schema.json").read_text(encoding="utf-8"))

    def errors_for_compose(self, compose):
        errors = validator.ValidationErrors()
        validator.validate_compose_data(compose, errors)
        return errors.items

    def errors_for_allowlist(self, allowlist, profile="baseline"):
        errors = validator.ValidationErrors()
        validator.validate_allowlist_data(allowlist, self.schema, errors, profile)
        return errors.items

    def test_repository_baseline_profile_passes(self):
        errors = validator.run_validation(ROOT, profile="baseline")
        self.assertEqual([], errors, "\n".join(errors))

    def test_host_ports_are_rejected(self):
        compose = copy.deepcopy(self.compose)
        compose["services"]["localai"]["ports"] = ["8080:8080"]
        self.assertTrue(any("host ports" in item for item in self.errors_for_compose(compose)))

    def test_agents_and_mcp_must_remain_disabled(self):
        compose = copy.deepcopy(self.compose)
        compose["services"]["localai"]["environment"]["LOCALAI_DISABLE_AGENTS"] = "false"
        compose["services"]["localai"]["environment"]["LOCALAI_DISABLE_MCP"] = "false"
        errors = self.errors_for_compose(compose)
        self.assertTrue(any("agents" in item for item in errors))
        self.assertTrue(any("MCP" in item for item in errors))

    def test_docker_socket_mount_is_rejected(self):
        compose = copy.deepcopy(self.compose)
        compose["services"]["localai"]["volumes"].append("/var/run/docker.sock:/var/run/docker.sock")
        self.assertTrue(any("socket" in item for item in self.errors_for_compose(compose)))

    def test_model_mount_must_be_read_only(self):
        compose = copy.deepcopy(self.compose)
        compose["services"]["localai"]["volumes"][0] = "${SALIG_DATA_ROOT}/models:/models:rw"
        self.assertTrue(any("/models mount" in item for item in self.errors_for_compose(compose)))

    def test_expected_internal_network_is_required(self):
        compose = copy.deepcopy(self.compose)
        compose["services"]["localai"]["networks"].pop("salutapp-internal")
        self.assertTrue(any("SalutApp internal network" in item for item in self.errors_for_compose(compose)))

    def test_duplicate_model_aliases_are_rejected_case_insensitively(self):
        allowlist = copy.deepcopy(self.allowlist)
        model = self.approved_model("salig-text-small")
        duplicate = self.approved_model("SALIG-TEXT-SMALL")
        allowlist["models"] = [model, duplicate]
        self.assertTrue(any("duplicate model alias" in item for item in self.errors_for_allowlist(allowlist)))

    def test_missing_model_hash_is_rejected(self):
        allowlist = copy.deepcopy(self.allowlist)
        model = self.approved_model("salig-text-small")
        model.pop("sha256")
        allowlist["models"] = [model]
        self.assertTrue(any("sha256" in item.lower() for item in self.errors_for_allowlist(allowlist)))

    def test_unapproved_model_is_rejected_for_accepted_deployment(self):
        allowlist = copy.deepcopy(self.allowlist)
        model = self.approved_model("salig-text-small")
        model["status"] = "review"
        model.pop("approved_at")
        model.pop("approved_by")
        allowlist["models"] = [model]
        self.assertTrue(any("not approved" in item for item in self.errors_for_allowlist(allowlist, "accepted-deployment")))

    def test_floating_deployment_image_is_rejected(self):
        values = {
            "SALIG_LOCALAI_IMAGE": "registry.invalid/salig/localai:latest",
            "SALIG_API_KEY": "synthetic-validation-key-000000000000000000000000",
            "SALIG_DATA_ROOT": "/srv/salig",
            "SALUTAPP_INTERNAL_NETWORK": "salutapp-app-internal",
        }
        errors = validator.ValidationErrors()
        validator.validate_deployment_env(values, errors)
        self.assertTrue(any("repository@sha256" in item for item in errors.items))

    def test_empty_artifact_pins_are_rejected_for_accepted_deployment(self):
        errors = validator.ValidationErrors()
        values = {
            "SALIG_UPSTREAM_REPOSITORY": "mudler/LocalAI",
            "SALIG_FORK_REPOSITORY": "ThatisMyGitHub/SALIG",
            "SALIG_UPSTREAM_BRANCH": "master",
            "SALIG_INTEGRATION_BRANCH": "salig/integration",
            "SALIG_UPSTREAM_COMMIT": "c" * 40,
            "SALIG_BASELINE_RECORDED_AT": "2026-08-02",
            "SALIG_LOCALAI_IMAGE": "",
            "SALIG_LOCALAI_IMAGE_DIGEST": "",
            "SALIG_BACKEND_NAME": "",
            "SALIG_BACKEND_DIGEST": "",
            "SALIG_MODEL_ALIAS": "",
            "SALIG_MODEL_SHA256": "",
            "SALIG_CONFIGURATION_SHA256": "",
        }
        validator.validate_baseline_values(values, errors, "accepted-deployment")
        self.assertTrue(any("requires a non-placeholder" in item for item in errors.items))

    @staticmethod
    def approved_model(alias: str):
        return {
            "alias": alias,
            "status": "approved",
            "source": "hf://synthetic/model@0123456789abcdef",
            "filename": "synthetic-model.Q4_K_M.gguf",
            "sha256": "b" * 64,
            "license": "synthetic-review-only",
            "backend": "llama-cpp",
            "quantization": "Q4_K_M",
            "maximum_context_tokens": 4096,
            "maximum_output_tokens": 512,
            "approved_operations": ["summarize.selected_text@v1"],
            "approved_environments": ["qnap-poc"],
            "approved_at": "2026-08-02",
            "approved_by": "synthetic-validator",
            "notes": "Test fixture only; not an approved model.",
        }


if __name__ == "__main__":
    unittest.main()
