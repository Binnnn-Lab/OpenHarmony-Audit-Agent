import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from openharmony_audit.cli import main
from openharmony_audit.contracts.models import CandidatePacket
from openharmony_audit.evidence.decision_gate import evaluate_candidate

ROOT = Path(__file__).resolve().parents[1]


class PrimaryWorkflowTests(unittest.TestCase):
    def test_primary_prepare_without_codeql_or_model(self):
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            args = ["--workflow", str(ROOT / "config/workflow.audit.example.json"),
                    "--target", str(ROOT / "config/target.openharmony.abstract.json")]
            self.assertEqual(main(["workflow", "validate", *args]), 0)
            self.assertEqual(main(["workflow", "prepare", *args, "--run-root", folder, "--allow-missing-source"]), 0)
            plan = json.loads((Path(folder) / "plan.json").read_text(encoding="utf-8"))
            units = [unit["id"] for worker in plan["workers"] for unit in worker["units"]]
            self.assertEqual(len(units), len(set(units)))
            self.assertEqual(len(units), 4)
            self.assertFalse(plan["target"]["interfaces"]["staticAnalysis"]["requiredForDiscovery"])
            prompt = (Path(folder) / "workers/worker-1/prompt.md").read_text(encoding="utf-8")
            self.assertIn("可选 CodeQL-AI", prompt)
            self.assertTrue((Path(folder) / "workers/worker-1/blind-verifier.md").exists())
            self.assertEqual(main(["workflow", "status", "--run-root", folder]), 0)

    def candidate(self):
        return CandidatePacket("c1", 1, "snapshot1", "u1", "abstract", {"sink": {"line": 3}},
                               [{"entry": "input", "sink": "copy"}], {"n": "n <= capacity"},
                               {"attacker": "external"}, {"effect": "overflow"},
                               counter_evidence=[{"check": "guard"}, {"check": "permission"}])

    def test_source_audit_does_not_require_codeql(self):
        candidate = self.candidate()
        evidence = [{"kind": "source_review", "candidate_id": "c1", "evidence_id": "e1"}]
        self.assertEqual(evaluate_candidate(candidate, evidence=evidence).verdict, "STATIC_ONLY")
        evidence.append({"kind": "symbolic_reachability", "candidate_id": "c1", "evidence_id": "e2"})
        self.assertEqual(evaluate_candidate(candidate, evidence=evidence, blind_verification=True).verdict, "STATIC_ONLY")
        evidence[-1].update(source_ref="run.json", input_hash="recorded-input", content_hash="recorded-output",
                            content={"snapshot_id": "snapshot1", "candidate_revision": 1,
                                     "reviewed": True, "result": "supported"})
        self.assertEqual(evaluate_candidate(candidate, evidence=evidence).verdict, "STATIC_ONLY")
        self.assertEqual(evaluate_candidate(candidate, evidence=evidence, blind_verification=True).verdict, "CONFIRMED")
        evidence[-1]["content"]["candidate_revision"] = 2
        self.assertEqual(evaluate_candidate(candidate, evidence=evidence, blind_verification=True).verdict, "STATIC_ONLY")
        evidence[-1]["content"].update(candidate_revision=1, result="refuted")
        evidence[-1]["kind"] = "decisive_counterevidence"
        self.assertEqual(evaluate_candidate(candidate, evidence=evidence).verdict, "REJECTED")
        evidence[-1]["candidate_id"] = "another-candidate"
        self.assertEqual(evaluate_candidate(candidate, evidence=evidence).verdict, "STATIC_ONLY")


if __name__ == "__main__":
    unittest.main()
