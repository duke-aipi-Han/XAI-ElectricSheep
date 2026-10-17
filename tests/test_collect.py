"""Offline pipeline tests. Every live-mode request uses a local fake transport."""

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from scripts.collect import (
    main,
    load_keys,
    post,
    OPENROUTER_ENDPOINT,
    TYPESAFE_ENDPOINT,
    chat_body,
    decision_body,
    parse_decision,
    read_json,
    save_json,
    fingerprint,
)

ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "data").mkdir()
        for name in (
            "questions.json",
            "jev-rubric.json",
            "models.json",
            "data/sample-answers.json",
        ):
            shutil.copyfile(ROOT / name, self.root / name)
        self.environment = patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "local-test-key-never-sent",
                "TYPESAFE_API_KEY": "local-typesafe-key-never-sent",
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)
        self.calls = []

    def configure(self):
        data = read_json(self.root / "models.json")
        for i, model in enumerate(data["models"]):
            model["id"] = "test/model-%s" % i
        save_json(self.root / "models.json", data)

    def mock(self, endpoint, body, key):
        self.assertEqual(
            key,
            (
                "local-test-key-never-sent"
                if endpoint == OPENROUTER_ENDPOINT
                else "local-typesafe-key-never-sent"
            ),
        )
        self.assertIn(endpoint, (OPENROUTER_ENDPOINT, TYPESAFE_ENDPOINT))
        self.calls.append((endpoint, body))
        if endpoint == OPENROUTER_ENDPOINT:
            return {
                "model": body["model"],
                "provider": "Local mock",
                "choices": [
                    {
                        "message": {"content": "A local mock answer."},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"cost": 0},
            }
        criteria = body["questions"]["category"]["criteria"]
        label = next(iter(criteria))
        return {
            "model": body["model"],
            "answers": {
                "category": {
                    "type": "choice",
                    "choice": label,
                    "probabilities": {k: 1 if k == label else 0 for k in criteria},
                }
            },
        }

    def run_pipeline(self, *args, transport=None):
        return main(list(args), root=self.root, transport=transport or self.mock)

    def test_sample_and_default_prepare_never_make_requests(self):
        def forbidden(*args):
            self.fail("Sample/preparation must never make a network request")

        study = self.run_pipeline("--sample", transport=forbidden)
        self.assertEqual(len(study["records"]), 72)
        self.assertEqual(len({r["id"] for r in study["records"]}), 72)
        self.environment.stop()
        with patch.dict(os.environ, {}, clear=True):
            self.run_pipeline(transport=forbidden)
        page = read_json(self.root / "public/study.json")
        self.assertEqual(page["complete_count"], 72)
        for question in study["questions"]:
            qid = question["id"]
            grouped = [
                rid for g in page["question_groups"][qid] for rid in g["record_ids"]
            ]
            self.assertEqual(len(grouped), 8)
            self.assertEqual(page["unfinished_records"][qid], [])
            self.assertEqual(page["question_counts"][qid], {"complete": 8, "total": 8})
        for record in page["records"]:
            self.assertEqual(record["classification"]["source"], "sample")
            self.assertEqual(record["display_label"], record["classification"]["label"])
            self.assertAlmostEqual(
                sum(record["classification"]["probabilities"].values()), 1
            )

    def test_fresh_request_and_matching_jev_rubric(self):
        question = read_json(self.root / "questions.json")["questions"][0]
        rubric = read_json(self.root / "jev-rubric.json")
        self.assertEqual(
            chat_body("test/model", question),
            {
                "model": "test/model",
                "messages": [{"role": "user", "content": question["text"]}],
            },
        )
        body = decision_body(question, "Unmodified answer", rubric)
        self.assertEqual(body["model"], "jev-1.14.0")
        self.assertEqual(
            body["state"],
            {"question": question["text"], "response": "Unmodified answer"},
        )
        self.assertEqual(
            body["questions"]["category"],
            rubric["per_question"][question["id"]]["category"],
        )

    def test_collect_then_classify_and_resume_without_repeating(self):
        self.configure()
        first = self.run_pipeline("--live", "--limit", "1")
        self.assertEqual(first["records"][0]["status"], "complete")
        self.assertIsNone(first["records"][0]["classification"])
        self.run_pipeline("--live")
        self.assertEqual(len(self.calls), 144)
        self.assertTrue(
            all(endpoint == OPENROUTER_ENDPOINT for endpoint, _ in self.calls[:72])
        )
        self.assertTrue(
            all(endpoint == TYPESAFE_ENDPOINT for endpoint, _ in self.calls[72:])
        )
        self.run_pipeline("--live")
        self.assertEqual(len(self.calls), 144)
        self.assertNotIn(
            "local-test-key-never-sent", (self.root / "public/study.json").read_text()
        )
        self.assertNotIn(
            "local-typesafe-key-never-sent",
            (self.root / "public/study.json").read_text(),
        )
        classified = read_json(self.root / "data/study.json")["records"][0][
            "classification"
        ]
        self.assertEqual(classified["endpoint"], TYPESAFE_ENDPOINT)
        self.assertEqual(classified["provider"], "TypeSafe")
        self.assertEqual(classified["requested_model"], "jev-1.14.0")
        self.assertIn("raw", classified)

    def test_http_requests_use_exact_provider_url_and_own_bearer_key(self):
        for endpoint, key in (
            (OPENROUTER_ENDPOINT, "router-test-key"),
            (TYPESAFE_ENDPOINT, "typesafe-test-key"),
        ):
            body = {"model": "test-model", "state": "Test only"}
            with patch(
                "scripts.collect.urlopen",
                return_value=io.BytesIO(b'{"model": "test-model"}'),
            ) as opened:
                post(endpoint, body, key)
            request = opened.call_args.args[0]
            self.assertEqual(request.full_url, endpoint)
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(request.get_header("Authorization"), "Bearer " + key)
            self.assertEqual(json.loads(request.data), body)
        with self.assertRaisesRegex(ValueError, "Unsupported API endpoint"):
            post("https://example.com/", {}, "unused-key")

    def test_missing_typesafe_key_blocks_all_live_requests(self):
        self.configure()
        with patch.dict(
            os.environ, {"OPENROUTER_API_KEY": "router-only-test"}, clear=True
        ):
            with self.assertRaisesRegex(ValueError, "TYPESAFE_API_KEY"):
                self.run_pipeline("--live")
        self.assertEqual(self.calls, [])

    def test_env_file_loads_both_keys_without_overriding_environment(self):
        (self.root / ".env").write_text(
            'OPENROUTER_API_KEY="router-file-test"\nTYPESAFE_API_KEY=typesafe-file-test # comment\n'
        )
        with patch.dict(
            os.environ, {"OPENROUTER_API_KEY": "router-env-test"}, clear=True
        ):
            self.assertEqual(
                load_keys(self.root),
                {
                    "OPENROUTER_API_KEY": "router-env-test",
                    "TYPESAFE_API_KEY": "typesafe-file-test",
                },
            )

    def test_typesafe_http_errors_name_typesafe(self):
        error = HTTPError(TYPESAFE_ENDPOINT, 401, "Unauthorized", {}, None)
        with patch("scripts.collect.urlopen", side_effect=error):
            with self.assertRaisesRegex(RuntimeError, "TypeSafe HTTP 401"):
                post(TYPESAFE_ENDPOINT, {}, "typesafe-test-key")

    def test_errors_redact_both_provider_keys(self):
        self.configure()

        def failure(*args):
            raise RuntimeError(
                "local-test-key-never-sent / local-typesafe-key-never-sent"
            )

        self.run_pipeline("--live", "--limit", "1", transport=failure)
        for path in ("data/study.json", "public/study.json"):
            text = (self.root / path).read_text()
            self.assertNotIn("local-test-key-never-sent", text)
            self.assertNotIn("local-typesafe-key-never-sent", text)
            self.assertIn("[redacted] / [redacted]", text)

    def test_old_openrouter_classification_is_archived_without_recollecting_answers(
        self,
    ):
        self.configure()
        study = self.run_pipeline("--live")
        old_rubric = copy.deepcopy(study["rubric"])
        old_rubric["endpoint"] = "https://openrouter.ai/api/alpha/decisions"
        old_rubric["suggested_model"] = "typesafe/jev-1.14"
        study["rubric"] = old_rubric
        for record in study["records"]:
            record["classification"]["rubric_hash"] = fingerprint(old_rubric)
            record["classification"]["endpoint"] = old_rubric["endpoint"]
            record["classification"]["provider"] = "OpenRouter"
        original = copy.deepcopy(study["records"][0]["classification"])
        save_json(self.root / "data/study.json", study)
        after = self.run_pipeline("--live", "--limit", "1")
        self.assertEqual(len(self.calls), 145)
        self.assertEqual(self.calls[-1][0], TYPESAFE_ENDPOINT)
        self.assertEqual(
            after["records"][0]["classification_history"][0]["classification"], original
        )
        self.assertEqual(after["records"][0]["classification"]["provider"], "TypeSafe")

    def test_incomplete_failed_and_pending_are_visible_and_not_grouped(self):
        self.configure()

        def failures(endpoint, body, key):
            if not self.calls:
                raw = self.mock(endpoint, body, key)
                raw["choices"][0]["finish_reason"] = "length"
                return raw
            self.calls.append((endpoint, body))
            raise RuntimeError("Simulated provider failure")

        self.run_pipeline("--live", "--limit", "2", transport=failures)
        page = read_json(self.root / "public/study.json")
        self.assertEqual(
            [r["status"] for r in page["records"][:3]],
            ["incomplete", "error", "pending"],
        )
        self.assertEqual(page["complete_count"], 0)
        self.assertEqual(len(page["unfinished_records"]["q01_identity"]), 8)
        self.assertEqual(page["question_groups"]["q01_identity"], [])
        after = self.run_pipeline("--live", "--limit", "1")
        self.assertEqual(after["records"][0]["status"], "incomplete")
        self.assertEqual(after["records"][1]["status"], "error")
        self.assertEqual(after["records"][2]["status"], "complete")

    def test_review_moves_group_preserves_original_and_can_be_cleared(self):
        study = self.run_pipeline("--sample")
        record = study["records"][0]
        original = copy.deepcopy(record["classification"])
        save_json(
            self.root / "data/reviews.json",
            {
                record["id"]: {
                    "label": "other",
                    "note": "Local test correction",
                    "rubric_version": study["rubric"]["rubric_version"],
                }
            },
        )
        self.run_pipeline("--prepare")
        page = read_json(self.root / "public/study.json")
        self.assertEqual(page["records"][0]["classification"], original)
        self.assertEqual(page["records"][0]["display_label"], "other")
        group = next(
            g
            for g in page["question_groups"][record["question_id"]]
            if g["label"] == "other"
        )
        self.assertIn(record["id"], group["record_ids"])
        save_json(self.root / "data/reviews.json", {record["id"]: None})
        self.run_pipeline("--prepare")
        self.assertEqual(
            read_json(self.root / "public/study.json")["records"][0]["display_label"],
            original["label"],
        )

    def test_changed_rubric_preserves_history_and_only_reclassifies(self):
        self.configure()
        study = self.run_pipeline("--live")
        original = copy.deepcopy(study["records"][0]["classification"])
        study["records"][0]["review"] = {"label": original["label"], "note": "Checked"}
        save_json(self.root / "data/study.json", study)
        rubric = read_json(self.root / "jev-rubric.json")
        rubric["rubric_version"] = "test-new"
        save_json(self.root / "jev-rubric.json", rubric)
        after = self.run_pipeline("--live", "--limit", "1")
        self.assertEqual(self.calls[-1][0], TYPESAFE_ENDPOINT)
        self.assertEqual(
            after["records"][0]["classification_history"][0]["classification"], original
        )
        self.assertEqual(
            after["records"][0]["classification_history"][0]["review"]["note"],
            "Checked",
        )
        self.assertIsNone(after["records"][0]["review"])
        # The other old labels remain recorded but do not count under the new rubric.
        page = read_json(self.root / "public/study.json")
        self.assertEqual(len(page["unfinished_records"]["q01_identity"]), 7)

    def test_placeholder_models_block_live_calls(self):
        config = read_json(self.root / "models.json")
        config["models"][0]["id"] = "configure/model-01"
        save_json(self.root / "models.json", config)
        with self.assertRaisesRegex(ValueError, "placeholder"):
            self.run_pipeline("--live")
        self.assertEqual(self.calls, [])

    def test_failed_classification_requires_explicit_retry(self):
        self.configure()

        def fail_one_classification(endpoint, body, key):
            raw = self.mock(endpoint, body, key)
            if len(self.calls) == 73:
                raw["answers"]["category"]["choice"] = "invalid_category"
            return raw

        study = self.run_pipeline("--live", transport=fail_one_classification)
        self.assertEqual(study["records"][0]["status"], "complete")
        self.assertIsNone(study["records"][0]["classification"])
        self.assertIn(
            "Invalid Jev category",
            study["records"][0]["classification_error"]["message"],
        )
        self.run_pipeline("--live")
        self.assertEqual(len(self.calls), 144)
        repaired = self.run_pipeline("--live", "--retry-failed", "--limit", "1")
        self.assertEqual(len(self.calls), 145)
        self.assertEqual(self.calls[-1][0], TYPESAFE_ENDPOINT)
        self.assertIsNotNone(repaired["records"][0]["classification"])

    def test_invalid_jev_output_is_rejected(self):
        criteria = {"a": "A", "b": "B"}
        with self.assertRaises(ValueError):
            parse_decision(
                {"answers": {"category": {"type": "choice", "choice": "unknown"}}},
                criteria,
            )
        with self.assertRaises(ValueError):
            parse_decision(
                {
                    "answers": {
                        "category": {
                            "type": "choice",
                            "choice": "a",
                            "probabilities": {"a": 2},
                        }
                    }
                },
                criteria,
            )
        parsed = parse_decision(
            {"answers": {"category": {"type": "choice", "choice": "a"}}}, criteria
        )
        self.assertIsNone(parsed["probabilities"])


if __name__ == "__main__":
    unittest.main()
