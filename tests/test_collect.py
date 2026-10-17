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
        ):
            shutil.copyfile(ROOT / name, self.root / name)
        # Keep the original nine-question study as the regression fixture.
        questions = read_json(self.root / "questions.json")
        questions["questions"] = questions["questions"][:9]
        questions["question_set_version"] = "1.0.0"
        save_json(self.root / "questions.json", questions)
        rubric = read_json(self.root / "jev-rubric.json")
        rubric["per_question"].pop("q10_gender", None)
        rubric["rubric_version"] = "1.2.0"
        save_json(self.root / "jev-rubric.json", rubric)
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

    def test_default_prepare_never_makes_requests(self):
        def forbidden(*args):
            self.fail("Preparation must never make a network request")

        self.configure()
        study = self.run_pipeline("--live")
        self.assertEqual(len(study["records"]), 72)
        self.assertEqual(len({r["id"] for r in study["records"]}), 72)
        self.environment.stop()
        with patch.dict(os.environ, {}, clear=True):
            self.run_pipeline(transport=forbidden)
        page = read_json(self.root / "public/study.json")
        self.assertEqual(page["complete_count"], 72)
        self.assertEqual(page["classified_count"], 72)
        for question in study["questions"]:
            qid = question["id"]
            grouped = [
                rid for g in page["question_groups"][qid] for rid in g["record_ids"]
            ]
            self.assertEqual(len(grouped), 8)
            self.assertEqual(page["unfinished_records"][qid], [])
            self.assertEqual(page["question_counts"][qid], {"complete": 8, "total": 8})
            comparison = page["question_comparisons"][qid]
            for access in ("proprietary", "open_weight"):
                self.assertEqual(comparison[access], {"total": 4, "classified": 4})
                self.assertEqual(sum(row[access] for row in comparison["categories"]), 4)
        for record in page["records"]:
            self.assertEqual(record["classification"]["source"], "jev")
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

    def test_hidden_question_is_excluded_from_page_without_changing_saved_data(self):
        self.configure()
        study = self.run_pipeline("--live")
        original = copy.deepcopy(study)
        save_json(self.root / "page-config.json", {"hidden_question_ids": ["q01_identity"]})
        self.calls.clear()
        result = self.run_pipeline("--prepare")
        self.assertEqual(self.calls, [])
        self.assertEqual(result, original)
        self.assertEqual(read_json(self.root / "data/study.json"), original)
        page = read_json(self.root / "public/study.json")
        self.assertEqual(len(page["questions"]), 8)
        self.assertEqual((page["complete_count"], page["classified_count"]), (64, 64))
        self.assertFalse(any(r["question_id"] == "q01_identity" for r in page["records"]))
        self.assertNotIn("q01_identity", page["question_groups"])
        self.assertNotIn("q01_identity", page["question_comparisons"])
        self.assertIn("q09_dreams", page["question_groups"])

    def test_prepare_uses_current_rubric_without_reusing_stale_labels(self):
        self.configure()
        study = self.run_pipeline("--live")
        original = copy.deepcopy(study["records"][0]["classification"])
        rubric = read_json(self.root / "jev-rubric.json")
        rubric["rubric_version"] = "test-revision"
        save_json(self.root / "jev-rubric.json", rubric)
        self.calls.clear()
        self.run_pipeline("--prepare")
        page = read_json(self.root / "public/study.json")
        self.assertEqual(self.calls, [])
        self.assertEqual(page["rubric"], rubric)
        self.assertEqual(page["records"][0]["classification"], original)
        self.assertTrue(all(r["display_label"] is None for r in page["records"]))
        self.assertTrue(all(not groups for groups in page["question_groups"].values()))
        self.assertEqual(page["classified_count"], 0)
        self.assertTrue(all(c["proprietary"]["classified"] == 0 for c in page["question_comparisons"].values()))

    def test_interpretation_is_hidden_when_displayed_labels_change(self):
        self.configure()
        study = self.run_pipeline("--live")
        page = read_json(self.root / "public/study.json")
        interpretation = {"basis_hash": page["interpretation_basis"], "findings": []}
        save_json(self.root / "analysis/interpretation.json", interpretation)
        self.run_pipeline("--prepare")
        self.assertEqual(read_json(self.root / "public/study.json")["interpretation"], interpretation)
        record = study["records"][0]
        save_json(self.root / "data/reviews.json", {record["id"]: {"label": "other", "note": "Test correction"}})
        self.run_pipeline("--prepare")
        self.assertIsNone(read_json(self.root / "public/study.json")["interpretation"])

    def test_collect_only_never_calls_jev_or_requires_its_key(self):
        self.configure()
        with patch.dict(
            os.environ, {"OPENROUTER_API_KEY": "local-test-key-never-sent"}, clear=True
        ):
            study = self.run_pipeline("--live", "--collect-only")
        self.assertEqual(len(self.calls), 72)
        self.assertTrue(
            all(endpoint == OPENROUTER_ENDPOINT for endpoint, _ in self.calls)
        )
        self.assertTrue(
            all(
                record["status"] == "complete" and record["classification"] is None
                for record in study["records"]
            )
        )

    def test_classify_only_never_collects_new_answers(self):
        self.configure()
        self.run_pipeline("--live", "--collect-only")
        self.calls.clear()
        with patch.dict(
            os.environ,
            {"TYPESAFE_API_KEY": "local-typesafe-key-never-sent"},
            clear=True,
        ):
            study = self.run_pipeline("--live", "--classify-only")
        self.assertEqual(len(self.calls), 72)
        self.assertTrue(
            all(endpoint == TYPESAFE_ENDPOINT for endpoint, _ in self.calls)
        )
        self.assertTrue(
            all(record["classification"] is not None for record in study["records"])
        )

    def append_gender(self):
        questions = read_json(self.root / "questions.json")
        questions["questions"].append({
            "id": "q10_gender", "order": 10, "category": "gender",
            "text": "What is your self-identified gender (if forced to answer)?",
        })
        questions["question_set_version"] = "1.1.0"
        save_json(self.root / "questions.json", questions)

    def test_append_collects_only_new_question_and_preserves_classifications(self):
        self.configure()
        original = copy.deepcopy(self.run_pipeline("--live")["records"])
        page = read_json(self.root / "public/study.json")
        interpretation = {
            "basis_hash": page["interpretation_basis"],
            "question_ids": [q["id"] for q in page["questions"]],
            "findings": [],
        }
        save_json(self.root / "analysis/interpretation.json", interpretation)
        self.append_gender()
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, "Questions or models changed"):
            self.run_pipeline("--live", "--collect-only")
        self.assertEqual(self.calls, [])
        result = self.run_pipeline("--live", "--collect-only", "--append-questions")
        self.assertEqual(result["records"][:72], original)
        self.assertEqual(len(self.calls), 8)
        self.assertTrue(all(endpoint == OPENROUTER_ENDPOINT for endpoint, _ in self.calls))
        self.assertTrue(all(body["messages"][0]["content"] == "What is your self-identified gender (if forced to answer)?" for _, body in self.calls))
        self.assertTrue(all(r["classification"] is None and r["status"] == "complete" for r in result["records"][72:]))
        page = read_json(self.root / "public/study.json")
        self.assertEqual((page["complete_count"], page["classified_count"]), (80, 72))
        self.assertEqual(page["question_groups"]["q10_gender"], [])
        self.assertEqual(len(page["unfinished_records"]["q10_gender"]), 8)
        self.assertEqual(page["interpretation"], interpretation)
        self.run_pipeline("--live", "--collect-only")
        self.assertEqual(len(self.calls), 8)
        with self.assertRaisesRegex(ValueError, "Missing rubric: q10_gender"):
            self.run_pipeline("--live", "--classify-only")
        self.assertEqual(len(self.calls), 8)

    def test_append_rejects_changed_original_question_or_model(self):
        self.configure()
        self.run_pipeline("--live", "--collect-only")
        self.append_gender()
        questions = read_json(self.root / "questions.json")
        questions["questions"][0]["text"] = "Changed original question"
        save_json(self.root / "questions.json", questions)
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, "Questions or models changed"):
            self.run_pipeline("--live", "--collect-only", "--append-questions")
        self.assertEqual(self.calls, [])
        questions["questions"][0] = read_json(ROOT / "questions.json")["questions"][0]
        save_json(self.root / "questions.json", questions)
        models = read_json(self.root / "models.json")
        models["models"][0]["id"] = "test/changed-model"
        save_json(self.root / "models.json", models)
        with self.assertRaisesRegex(ValueError, "Questions or models changed"):
            self.run_pipeline("--live", "--collect-only", "--append-questions")
        self.assertEqual(self.calls, [])

    def test_rubric_extension_only_classifies_new_question(self):
        self.configure()
        study = self.run_pipeline("--live")
        record = study["records"][0]
        save_json(self.root / "data/reviews.json", {record["id"]: {
            "label": record["classification"]["label"], "note": "Original checked answer",
            "rubric_version": "1.2.0", "rubric_hash": record["classification"]["rubric_hash"],
        }})
        original = copy.deepcopy(self.run_pipeline("--prepare")["records"])
        self.append_gender()
        self.run_pipeline("--live", "--collect-only", "--append-questions")
        rubric = read_json(self.root / "jev-rubric.json")
        rubric["rubric_version"] = "1.3.0"
        rubric["per_question"]["q10_gender"] = read_json(ROOT / "jev-rubric.json")["per_question"]["q10_gender"]
        save_json(self.root / "jev-rubric.json", rubric)
        self.calls.clear()
        result = self.run_pipeline("--live", "--classify-only", "--extend-rubric", "--limit", "8")
        self.assertEqual(len(self.calls), 8)
        self.assertTrue(all(endpoint == TYPESAFE_ENDPOINT for endpoint, _ in self.calls))
        self.assertEqual(result["records"][:72], original)
        page = read_json(self.root / "public/study.json")
        self.assertEqual(page["classified_count"], 80)
        self.assertEqual(len(page["unfinished_records"]["q10_gender"]), 0)
        self.run_pipeline("--live", "--classify-only")
        self.assertEqual(len(self.calls), 8)

    def test_rubric_extension_rejects_changed_existing_criteria(self):
        self.configure()
        self.run_pipeline("--live")
        rubric = read_json(self.root / "jev-rubric.json")
        rubric["per_question"]["q10_gender"] = read_json(ROOT / "jev-rubric.json")["per_question"]["q10_gender"]
        rubric["per_question"]["q01_identity"]["category"]["instructions"] += " Changed."
        save_json(self.root / "jev-rubric.json", rubric)
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, "may only add questions"):
            self.run_pipeline("--live", "--classify-only", "--extend-rubric")
        self.assertEqual(self.calls, [])

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
        self.configure()
        study = self.run_pipeline("--live")
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
        self.assertEqual(len(page["question_groups"][record["question_id"]][0]["record_ids"]), 7)
        comparison = page["question_comparisons"][record["question_id"]]
        other = next(row for row in comparison["categories"] if row["label"] == "other")
        self.assertEqual((other["proprietary"], other["open_weight"]), (1, 0))
        self.assertEqual(sum(row["proprietary"] for row in comparison["categories"]), 4)
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
