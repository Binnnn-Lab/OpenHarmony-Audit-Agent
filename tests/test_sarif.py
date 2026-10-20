import json
import tempfile
import unittest
from pathlib import Path

from openharmony_audit.evidence.normalizer import findings_from_sarif


class SarifImportTest(unittest.TestCase):
    def test_standard_codeql_locations_tags_and_multiple_runs(self):
        def location(path, line):
            return {"physicalLocation": {"artifactLocation": {"uri": path}, "region": {"startLine": line}}}

        source, sink = location("src/input.cpp", 9), location("src/copy.cpp", 42)
        flow = [{"threadFlows": [{"locations": [{"location": source}, {"location": sink}]}]}]
        run = {"tool": {"driver": {"name": "CodeQL", "rules": [{"id": "cpp/test", "properties": {"tags": ["external/cwe/cwe-120"]}}]}},
               "results": [{"ruleId": "cpp/test", "message": {"text": "fixture only"}, "locations": [sink], "codeFlows": flow}]}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "results.sarif"
            path.write_text(json.dumps({"version": "2.1.0", "runs": [run, run]}), encoding="utf-8")
            a, b = findings_from_sarif(path)
        self.assertEqual((a.file_path, a.start_line, a.cwe), ("src/copy.cpp", 42, "CWE-120"))
        self.assertEqual(a.source["path"], "src/input.cpp")
        self.assertEqual(a.sink["startLine"], 42)
        self.assertEqual(a.provenance["rawCodeFlows"], flow)
        self.assertNotEqual(a.finding_id, b.finding_id)
        self.assertEqual(len(a.provenance["sha256"]), 64)
        run["results"][0]["codeFlows"] = flow + flow
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "multiple-paths.sarif"
            path.write_text(json.dumps({"runs": [run]}), encoding="utf-8")
            multiple = findings_from_sarif(path)[0]
        self.assertEqual(multiple.source, {})
        self.assertEqual(multiple.sink, {})
        self.assertEqual(len(multiple.provenance["rawCodeFlows"]), 2)


if __name__ == "__main__":
    unittest.main()
