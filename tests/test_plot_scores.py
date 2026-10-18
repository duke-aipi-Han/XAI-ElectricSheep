"""The plot scorer uses mocked TypeSafe requests and temporary files only."""
import contextlib
import copy
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import collect, score_plot

ROOT = Path(__file__).resolve().parents[1]


class PlotScoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.rubric = collect.read_json(ROOT / "plot-rubric.json")
        collect.save_json(self.root / "plot-rubric.json", self.rubric)
        study = collect.read_json(ROOT / "data/study.json")
        study["models"] = study["models"][:1]
        study["questions"] = [q for q in study["questions"] if q["id"] in ("q02_purpose", "q09_dreams")]
        study["records"] = [r for r in study["records"] if r["requested_model"] == study["models"][0]["id"] and r["question_id"] in ("q02_purpose", "q09_dreams")]
        collect.save_json(self.root / "data/study.json", study)
        self.original = (self.root / "data/study.json").read_bytes()
        self.calls = []
        self.raw = {"model": "jev-1.14.0", "answers": {
            "mission": {"type": "score", "score": 1.5, "confidence": 0.5,
                        "probabilities": {"0": 0, "1": 0.5, "2": 0.5, "3": 0, "4": 0}},
            "aspiration": {"type": "score", "score": 3.4, "confidence": 0.6,
                           "probabilities": {"0": 0, "1": 0, "2": 0, "3": 0.6, "4": 0.4}},
        }}
        environment = patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only-key"})
        environment.start()
        self.addCleanup(environment.stop)
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def mock(self, endpoint, body, key):
        self.assertEqual(endpoint, collect.TYPESAFE_ENDPOINT)
        self.assertEqual(key, "test-only-key")
        self.calls.append(body)
        return copy.deepcopy(self.raw)

    def run_scorer(self, *args, transport=None):
        return score_plot.main(list(args), root=self.root, transport=transport or self.mock)

    def test_live_scores_both_axes_anonymously_and_reuses_results(self):
        self.run_scorer("--live")
        self.assertEqual(len(self.calls), 1)
        body = self.calls[0]
        self.assertEqual(set(body["questions"]), {"mission", "aspiration"})
        self.assertTrue(all(q["type"] == "score" for q in body["questions"].values()))
        for evidence in body["state"].values():
            self.assertEqual(set(evidence), {"question", "response"})
        page = collect.read_json(self.root / "public/study.json")
        scores = page["mission_aspiration"]["records"][0]["scores"]
        self.assertEqual(scores["mission"]["normalized_score"], 0.375)
        self.assertEqual(scores["aspiration"]["normalized_score"], 0.85)
        self.assertEqual(scores["mission"]["confidence"], 0.5)
        self.assertEqual((self.root / "data/study.json").read_bytes(), self.original)
        self.run_scorer("--live")
        self.assertEqual(len(self.calls), 1)

    def test_offline_exports_without_calls_and_filters_changed_answers(self):
        self.run_scorer("--live")
        self.run_scorer()
        self.assertEqual(len(self.calls), 1)
        study = collect.read_json(self.root / "data/study.json")
        study["records"][0]["response"] += " A changed response."
        collect.save_json(self.root / "data/study.json", study)
        self.run_scorer()
        page = collect.read_json(self.root / "public/study.json")
        self.assertEqual(page["mission_aspiration"]["records"], [])
        self.assertEqual(len(self.calls), 1)

    def test_old_rubric_is_not_exported_or_overwritten(self):
        self.run_scorer("--live")
        changed = copy.deepcopy(self.rubric)
        changed["rubric_version"] = "2.0.0"
        collect.save_json(self.root / "plot-rubric.json", changed)
        study = collect.read_json(self.root / "data/study.json")
        collect.prepare(study, self.root)
        self.assertIsNone(collect.read_json(self.root / "public/study.json")["mission_aspiration"])
        with self.assertRaises(ValueError):
            self.run_scorer("--live")
        self.assertEqual(len(self.calls), 1)

    def test_interrupted_request_requires_explicit_retry(self):
        def interrupted(*args):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.run_scorer("--live", transport=interrupted)
        self.run_scorer("--live")
        self.assertEqual(len(self.calls), 0)
        self.run_scorer("--live", "--retry-failed")
        self.assertEqual(len(self.calls), 1)

    def test_rejects_malformed_score_responses(self):
        for field, value in (("score", float("nan")), ("score", True),
                             ("score", 4.1), ("score", 0), ("confidence", 1.5),
                             ("probabilities", {"0": 1}),
                             ("probabilities", {str(i): 0.1 for i in range(5)})):
            with self.subTest(field=field, value=value):
                raw = copy.deepcopy(self.raw)
                raw["answers"]["mission"][field] = value
                with self.assertRaises(ValueError):
                    collect.parse_plot_scores(raw, self.rubric)


if __name__ == "__main__":
    unittest.main()
