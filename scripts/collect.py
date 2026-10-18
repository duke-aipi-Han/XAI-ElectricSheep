#!/usr/bin/env python3
"""Offline data pipeline (Python 3.9+, standard library only).

--live: collect answers, then classify complete answers, then prepare the export.
--live --collect-only: collect and prepare answers without calling Jev.
--live --classify-only: classify saved answers without collecting new ones.
--prepare (default): apply local reviews and export saved data; no network.
"""

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
TYPESAFE_ENDPOINT = "https://api.typesafe.ai/v1/systemone"


def now():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def fingerprint(value):
    # Match the original saved datasets without needing Node.
    text = json.dumps(value, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rubric_matches(study, question_id, saved_hash):
    """Accept earlier labels only under an explicitly validated rubric extension."""
    current_hash = fingerprint(study["rubric"])
    return saved_hash == current_hash or question_id in (
        study.get("rubric_compatibility", {}).get(current_hash, {}).get(saved_hash, [])
    )


def load_keys(root, names=("OPENROUTER_API_KEY", "TYPESAFE_API_KEY")):
    """Read the two API keys as text, without executing a shell."""
    path = root / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.strip().partition("=")
            if separator and key.strip() in names:
                parts = shlex.split(value, comments=True)
                os.environ.setdefault(key.strip(), parts[0] if parts else "")
    keys = {name: os.environ.get(name, "").strip() for name in names}
    missing = [name for name, value in keys.items() if not value]
    if missing:
        raise ValueError("Set %s in .env before using --live." % ", ".join(missing))
    return keys


def error_message(error, keys):
    message = str(error)
    for key in keys.values():
        message = message.replace(key, "[redacted]")
    return message


def chat_body(model_id, question):
    return {
        "model": model_id,
        "messages": [{"role": "user", "content": question["text"]}],
    }


def decision_body(question, response, rubric):
    return {
        "model": rubric["suggested_model"],
        "state": {"question": question["text"], "response": response},
        "questions": {"category": rubric["per_question"][question["id"]]["category"]},
    }


def probability(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def parse_decision(raw, criteria):
    answer = raw.get("answers", {}).get("category", {})
    if answer.get("type") != "choice" or answer.get("choice") not in criteria:
        raise ValueError("Invalid Jev category.")
    probabilities = answer.get("probabilities")
    if probabilities is not None and (
        not isinstance(probabilities, dict)
        or any(
            key not in criteria or not probability(value)
            for key, value in probabilities.items()
        )
    ):
        raise ValueError("Invalid Jev probabilities.")
    confidence = answer.get("confidence")
    if confidence is not None and not probability(confidence):
        raise ValueError("Invalid Jev confidence.")
    return {
        "label": answer["choice"],
        "probabilities": probabilities,
        "confidence": confidence,
    }


def post(endpoint, body, key):
    providers = {OPENROUTER_ENDPOINT: "OpenRouter", TYPESAFE_ENDPOINT: "TypeSafe"}
    if endpoint not in providers:
        raise ValueError("Unsupported API endpoint.")
    provider = providers[endpoint]
    request = Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            raw = json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            "%s HTTP %s. Check model availability, account, or rate limits."
            % (provider, error.code)
        ) from None
    except (URLError, TimeoutError) as error:
        raise RuntimeError(
            "Request failed or timed out; it may already have been billed. Check the connection before retrying."
        ) from None
    if raw.get("error"):
        raise RuntimeError(
            "%s returned an error. Check the account and model configuration."
            % provider
        )
    return raw


def plot_state(study, model_id, rubric):
    """Build anonymous evidence for the dedicated plot axes."""
    questions = {q["id"]: q for q in study["questions"]}
    state = {}
    for axis, config in rubric["axes"].items():
        question_id = config["question_id"]
        record = next((r for r in study["records"]
                       if r["requested_model"] == model_id
                       and r["question_id"] == question_id), None)
        if not record or record["status"] != "complete" or not record.get("response"):
            raise ValueError("Missing complete plot evidence: " + model_id + "/" + question_id)
        state[axis] = {"question": questions[question_id]["text"], "response": record["response"]}
    return state


def parse_plot_scores(raw, rubric):
    """Validate TypeSafe Score values, preserving confidence separately."""
    scores = {}
    for axis, config in rubric["axes"].items():
        answer = raw.get("answers", {}).get(axis, {})
        maximum = len(config["question"]["criteria"]) - 1
        score = answer.get("score")
        probabilities = answer.get("probabilities")
        if (
            answer.get("type") != "score" or maximum < 1
            or type(score) not in (int, float) or not probability(score / maximum)
            or not isinstance(probabilities, dict)
            or set(probabilities) != {str(i) for i in range(maximum + 1)}
            or any(not probability(p) for p in probabilities.values())
            or abs(sum(probabilities.values()) - 1) > 0.02
        ):
            raise ValueError("Invalid plot Score result: " + axis)
        expected = sum(int(level) * p for level, p in probabilities.items())
        if abs(expected - score) > 0.05:
            raise ValueError("Plot score does not match its level probabilities: " + axis)
        confidence = answer.get("confidence")
        if confidence is not None and not probability(confidence):
            raise ValueError("Invalid plot confidence: " + axis)
        scores[axis] = {"score": score, "normalized_score": score / maximum,
                        "confidence": confidence, "probabilities": probabilities}
    return scores


def prepared_plot(study, root):
    """Include only results matching the current plot rubric and answer text."""
    path = root / "data/mission-aspiration.json"
    rubric_path = root / "plot-rubric.json"
    if not path.exists() or not rubric_path.exists():
        return None
    saved = read_json(path)
    rubric = read_json(rubric_path)
    if saved.get("study_id") != study["id"] or saved.get("rubric_hash") != fingerprint(rubric):
        return None
    records = []
    for model in study["models"]:
        entry = saved.get("records", {}).get(model["id"], {})
        if entry.get("status") != "complete":
            continue
        if entry.get("input_hash") != fingerprint(plot_state(study, model["id"], rubric)):
            continue
        records.append(dict(entry, subject_model=model["id"],
                            scores=parse_plot_scores(entry["raw"], rubric)))
    return {"rubric": rubric, "rubric_hash": saved["rubric_hash"], "records": records}


def prepare(study, root):
    """Apply file-based reviews and precompute all page groups and counts."""
    reviews_path = root / "data/reviews.json"
    reviews = read_json(reviews_path) if reviews_path.exists() else {}
    if not isinstance(reviews, dict):
        raise ValueError("data/reviews.json must be an object keyed by record ID.")
    rubric_hash = fingerprint(study["rubric"])
    by_id = {record["id"]: record for record in study["records"]}
    for record_id, review in reviews.items():
        if record_id not in by_id:
            raise ValueError("Unknown review record ID: " + record_id)
        record = by_id[record_id]
        if review is None:
            record["review"] = None
            continue
        if not isinstance(review, dict) or not isinstance(review.get("note", ""), str):
            raise ValueError("Invalid review for " + record_id)
        review_hash = review.get("rubric_hash", rubric_hash)
        review_rubric = (
            study["rubric"] if review_hash == rubric_hash
            else study.get("rubric_history", {}).get(review_hash, {})
        )
        if not rubric_matches(study, record["question_id"], review_hash):
            record["review"] = None
            continue
        criteria = review_rubric.get("per_question", {}).get(record["question_id"], {}).get("category", {}).get("criteria", {})
        if review.get("label") not in criteria:
            raise ValueError("Invalid review for " + record_id)
        if record["status"] != "complete" or not record.get("classification"):
            raise ValueError(
                "Only complete, classified answers can be reviewed: " + record_id
            )
        if (
            review.get("rubric_version", review_rubric.get("rubric_version"))
            != review_rubric.get("rubric_version")
        ):
            raise ValueError(
                "Review uses an old rubric; update or remove it: " + record_id
            )
        if not rubric_matches(study, record["question_id"], record["classification"].get("rubric_hash")):
            raise ValueError("Reclassify this answer before reviewing it: " + record_id)
        record["review"] = {
            "label": review["label"],
            "note": review.get("note", ""),
            "rubric_hash": review_hash,
        }

    # Keep the working dataset separate from the self-contained static export.
    page = copy.deepcopy(study)
    config_path = root / "page-config.json"
    page_config = read_json(config_path) if config_path.exists() else {}
    hidden = page_config.get("hidden_question_ids", [])
    combined_groups = page_config.get("classification_groups", {})
    question_ids = {q["id"] for q in study["questions"]}
    if not isinstance(hidden, list) or any(qid not in question_ids for qid in hidden):
        raise ValueError("page-config.json must list known hidden_question_ids.")
    if not isinstance(combined_groups, dict) or any(qid not in question_ids for qid in combined_groups):
        raise ValueError("classification_groups must refer to known question IDs.")
    page["classification_groups"] = combined_groups
    page["questions"] = [q for q in page["questions"] if q["id"] not in hidden]
    page["records"] = [r for r in page["records"] if r["question_id"] not in hidden]
    page["prepared_at"] = now()
    page["complete_count"] = sum(
        record["status"] == "complete" for record in page["records"]
    )
    page["question_groups"] = {}
    page["question_counts"] = {}
    page["question_comparisons"] = {}
    page["unfinished_records"] = {}
    model_access = {m["id"]: m.get("access") for m in page["models"]}
    for question in page["questions"]:
        qid = question["id"]
        records = [record for record in page["records"] if record["question_id"] == qid]
        criteria = page["rubric"]["per_question"].get(qid, {}).get("category", {}).get("criteria", {})
        label_groups = {}
        for group_label, group in combined_groups.get(qid, {}).items():
            members = group.get("labels", [])
            if (
                not group.get("title") or group_label in criteria
                or not isinstance(members, list) or len(members) < 2
                or any(label not in criteria or label in label_groups for label in members)
                or len(set(members)) != len(members)
            ):
                raise ValueError("Combined classification groups must name distinct known labels and a title.")
            label_groups.update({label: group_label for label in members})
        groups = {label_groups.get(label, label): [] for label in criteria}
        unfinished = []
        for index, record in enumerate(records):
            classification = record.get("classification") or {}
            record["display_label"] = (
                (record.get("review") or {}).get("label", classification.get("label"))
                if rubric_matches(study, qid, classification.get("rubric_hash"))
                else None
            )
            record["voice_number"] = index + 1
            record["display_group"] = label_groups.get(record["display_label"], record["display_label"])
            if record["status"] == "complete" and record["display_label"] in criteria:
                groups[record["display_group"]].append(record["id"])
            else:
                unfinished.append(record["id"])
        page["question_groups"][qid] = [
            {"label": label, "record_ids": ids} for label, ids in groups.items() if ids
        ]
        page["question_groups"][qid].sort(key=lambda group: -len(group["record_ids"]))
        comparison = {
            access: {
                "total": sum(model_access.get(r["requested_model"]) == access for r in records),
                "classified": sum(
                    model_access.get(r["requested_model"]) == access
                    and r["status"] == "complete" and r["display_group"] in groups
                    for r in records
                ),
            }
            for access in ("proprietary", "open_weight")
        }
        comparison["categories"] = [
            {
                "label": group["label"],
                **{
                    access: sum(model_access.get(by_id[rid]["requested_model"]) == access
                                for rid in group["record_ids"])
                    for access in ("proprietary", "open_weight")
                },
            }
            for group in page["question_groups"][qid]
        ]
        page["question_comparisons"][qid] = comparison
        page["question_counts"][qid] = {
            "complete": sum(r["status"] == "complete" for r in records),
            "total": len(records),
        }
        page["unfinished_records"][qid] = unfinished
    page["classified_count"] = sum(r["display_label"] is not None for r in page["records"])
    page["reviewed_count"] = sum(bool(r.get("review")) for r in page["records"])
    # Interpretations can cover an explicit subset, such as the original nine questions.
    interpretation_path = root / "analysis/interpretation.json"
    interpretation = read_json(interpretation_path) if interpretation_path.exists() else None
    scope = (interpretation or {}).get("question_ids", [q["id"] for q in page["questions"]])
    page["interpretation_basis"] = fingerprint({
        "study_id": study["id"], "rubric_hash": rubric_hash,
        "labels": [[r["id"], r["display_group"]] for r in page["records"] if r["question_id"] in scope],
    })
    page["interpretation"] = (
        interpretation if interpretation and interpretation.get("basis_hash") == page["interpretation_basis"]
        else None
    )
    page["mission_aspiration"] = prepared_plot(study, root)
    save_json(root / "public/study.json", page)


def main(argv=None, root=ROOT, transport=post):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument(
        "--collect-only",
        action="store_true",
        help="Collect subject answers; never call Jev.",
    )
    stage.add_argument(
        "--classify-only",
        action="store_true",
        help="Classify saved answers; never collect new answers.",
    )
    parser.add_argument(
        "--reclassify-questions",
        help="Comma-separated questions whose changed rubrics should be reclassified.",
    )
    parser.add_argument(
        "--extend-rubric",
        action="store_true",
        help="Add rubrics for new questions while retaining unchanged earlier classifications.",
    )
    parser.add_argument(
        "--append-questions",
        action="store_true",
        help="Append new questions in collect-only mode; existing questions/models must be unchanged.",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Explicitly retry failed/interrupted requests; never replaces incomplete answers.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum API requests across collection and classification.",
    )
    args = parser.parse_args(argv)
    root = Path(root)
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be a positive integer")
    if not args.live and (args.retry_failed or args.limit is not None):
        parser.error("--limit and --retry-failed require --live")
    if not args.live and (args.collect_only or args.classify_only):
        parser.error("--collect-only and --classify-only require --live")
    if args.append_questions and not (args.live and args.collect_only):
        parser.error("--append-questions requires --live --collect-only")
    if args.extend_rubric and not (args.live and args.classify_only):
        parser.error("--extend-rubric requires --live --classify-only")
    if args.reclassify_questions and not (args.live and args.classify_only):
        parser.error("--reclassify-questions requires --live --classify-only")

    if not args.live:
        path = root / "data/study.json"
        if not path.exists():
            raise ValueError("No saved answers yet. Run --live --collect-only first.")
        study = read_json(path)
        study["rubric"] = read_json(root / "jev-rubric.json")
        prepare(study, root)
        save_json(path, study)
        print("Prepared public/study.json from %s. No API requests made." % path.name)
        return study

    question_set = read_json(root / "questions.json")
    questions = question_set["questions"]
    rubric = read_json(root / "jev-rubric.json")
    configured = read_json(root / "models.json")["models"]
    models = [
        {
            "id": m["id"],
            "name": m["name"],
            "family": m["family"],
            "access": m.get("access", "unspecified"),
        }
        for m in configured
    ]
    if (
        not questions
        or len({q["id"] for q in questions}) != len(questions)
        or len(models) != 8
        or len({m["id"] for m in models}) != 8
    ):
        raise ValueError("Expected unique questions and eight unique models.")
    for question in questions:
        if not args.collect_only and question["id"] not in rubric["per_question"]:
            raise ValueError("Missing rubric: " + question["id"])
    if args.live and any(m["id"].startswith("configure/") for m in models):
        raise ValueError(
            "Replace all eight placeholder IDs in models.json before collection."
        )
    required_keys = (
        ("OPENROUTER_API_KEY",)
        if args.collect_only
        else (
            ("TYPESAFE_API_KEY",)
            if args.classify_only
            else ("OPENROUTER_API_KEY", "TYPESAFE_API_KEY")
        )
    )
    keys = load_keys(root, required_keys) if args.live else {}
    path = root / "data/study.json"
    config_hash = fingerprint({"questions": questions, "models": models})
    rubric_hash = fingerprint(rubric)
    study = (
        read_json(path)
        if path.exists()
        else {
            "schema_version": "1.0",
            "id": "study-" + now(),
            "mode": "real",
            "created_at": now(),
            "note": "One fresh user message per model/question, using API defaults.",
            "question_set_version": question_set["question_set_version"],
            "config_hash": config_hash,
            "questions": questions,
            "models": models,
            "rubric": rubric,
            "records": [],
        }
    )
    if study["config_hash"] != config_hash:
        old_questions = study["questions"]
        if not (
            args.append_questions
            and study["models"] == models
            and len(questions) > len(old_questions)
            and questions[:len(old_questions)] == old_questions
        ):
            raise ValueError(
                "Questions or models changed. Only unchanged models and appended questions "
                "can be extended with --live --collect-only --append-questions."
            )
        study.setdefault("question_set_history", []).append({
            "question_set_version": study["question_set_version"],
            "config_hash": study["config_hash"],
            "extended_at": now(),
            "added_question_ids": [q["id"] for q in questions[len(old_questions):]],
        })
        study.update(questions=questions, question_set_version=question_set["question_set_version"], config_hash=config_hash)
    if args.live and study["mode"] != "real":
        raise ValueError("The saved dataset must contain real observations.")
    if args.extend_rubric and fingerprint(study["rubric"]) != rubric_hash:
        previous = study["rubric"]
        old_questions = previous["per_question"]
        if not (
            set(old_questions) < set(rubric["per_question"])
            and all(rubric["per_question"].get(qid) == entry for qid, entry in old_questions.items())
            and all(previous.get(key) == rubric.get(key) for key in ("schema_version", "endpoint", "suggested_model", "assembly"))
        ):
            raise ValueError("A rubric extension may only add questions; existing criteria and classifier configuration must be unchanged.")
        old_hash = fingerprint(previous)
        compatible = copy.deepcopy(study.get("rubric_compatibility", {}).get(old_hash, {}))
        compatible[old_hash] = list(old_questions)
        study.setdefault("rubric_compatibility", {})[rubric_hash] = compatible
        study.setdefault("rubric_history", {})[old_hash] = copy.deepcopy(previous)
    if args.reclassify_questions and fingerprint(study["rubric"]) != rubric_hash:
        targets = {qid.strip() for qid in args.reclassify_questions.split(",") if qid.strip()}
        previous = study["rubric"]
        old_entries = previous["per_question"]
        new_entries = rubric["per_question"]
        changed = {
            qid for qid in old_entries.keys() | new_entries.keys()
            if old_entries.get(qid) != new_entries.get(qid)
        }
        if (
            not targets
            or not targets <= set(old_entries)
            or changed != targets
            or set(old_entries) != set(new_entries)
            or any(previous.get(key) != rubric.get(key) for key in ("schema_version", "endpoint", "suggested_model", "assembly"))
        ):
            raise ValueError("Changed rubric questions must exactly match --reclassify-questions; keep all other rubric settings and questions unchanged.")
        old_hash = fingerprint(previous)
        compatible = {}
        for saved_hash, compatible_questions in study.get("rubric_compatibility", {}).get(old_hash, {}).items():
            retained = [qid for qid in compatible_questions if qid not in targets]
            if retained:
                compatible[saved_hash] = retained
        retained_current = [qid for qid in old_entries if qid not in targets]
        if retained_current:
            compatible[old_hash] = retained_current
        study.setdefault("rubric_compatibility", {})[rubric_hash] = compatible
        study.setdefault("rubric_history", {})[old_hash] = copy.deepcopy(previous)
    study["rubric"] = rubric
    existing = {r["id"] for r in study["records"]}
    for question in questions:
        for model in models:
            record_id = question["id"] + ":" + model["id"]
            if record_id not in existing:
                study["records"].append(
                    {
                        "id": record_id,
                        "question_id": question["id"],
                        "requested_model": model["id"],
                        "status": "pending",
                        "response": "",
                        "classification": None,
                        "review": None,
                    }
                )
    save_json(path, study)
    questions_by_id = {q["id"]: q for q in questions}
    requests = 0

    # Stage 1: collect all remaining subject answers before classifying any.
    for record in study["records"]:
        if args.classify_only:
            break
        retry = args.retry_failed and record["status"] in ("error", "in_progress")
        if record["status"] != "pending" and not retry:
            continue
        if args.limit is not None and requests >= args.limit:
            break
        if retry:
            record.setdefault("attempts", []).append(
                {k: record.get(k) for k in ("status", "error", "collected_at")}
            )
        record.update(status="in_progress", collected_at=now())
        save_json(path, study)
        requests += 1
        try:
            raw = transport(
                OPENROUTER_ENDPOINT,
                chat_body(
                    record["requested_model"],
                    questions_by_id[record["question_id"]],
                ),
                keys["OPENROUTER_API_KEY"],
            )
            choice = (raw.get("choices") or [{}])[0]
            content = (choice.get("message") or {}).get("content")
            record.update(
                response=content if isinstance(content, str) else "",
                returned_model=raw.get("model"),
                provider=raw.get("provider"),
                generation_id=raw.get("id"),
                finish_reason=choice.get("finish_reason"),
                native_finish_reason=choice.get("native_finish_reason"),
                usage=raw.get("usage"),
                error=None,
            )
            record["status"] = (
                "error"
                if choice.get("error")
                else (
                    "complete"
                    if record["response"].strip() and record["finish_reason"] == "stop"
                    else "incomplete"
                )
            )
            if choice.get("error"):
                record["error"] = "Provider reported a generation error."
        except (RuntimeError, ValueError, OSError, TypeError, KeyError) as error:
            record.update(status="error", error=error_message(error, keys))
        save_json(path, study)
        print(
            "%s / %s: %s"
            % (record["question_id"], record["requested_model"], record["status"]),
            flush=True,
        )

    # Stage 2: classify complete answers, preserving previous Jev results.
    for record in study["records"]:
        if args.collect_only:
            break
        if (
            record["status"] != "complete"
            or rubric_matches(study, record["question_id"], (record.get("classification") or {}).get("rubric_hash"))
        ):
            continue
        if not args.retry_failed and (
            record.get("classification_status") == "in_progress"
            or (record.get("classification_error") or {}).get("rubric_hash")
            == rubric_hash
        ):
            continue
        if args.limit is not None and requests >= args.limit:
            break
        if record.get("classification"):
            record.setdefault("classification_history", []).append(
                {
                    "classification": record["classification"],
                    "review": record.get("review"),
                }
            )
            record.update(classification=None, review=None)
        record["classification_status"] = "in_progress"
        save_json(path, study)
        requests += 1
        try:
            body = decision_body(
                questions_by_id[record["question_id"]], record["response"], rubric
            )
            raw = transport(TYPESAFE_ENDPOINT, body, keys["TYPESAFE_API_KEY"])
            record["classification"] = dict(
                parse_decision(raw, body["questions"]["category"]["criteria"]),
                source="jev",
                endpoint=TYPESAFE_ENDPOINT,
                requested_model=body["model"],
                model=raw.get("model"),
                provider="TypeSafe",
                usage=raw.get("usage"),
                raw=raw,
                rubric_hash=rubric_hash,
                rubric_version=rubric["rubric_version"],
                classified_at=now(),
            )
            record.update(classification_error=None, classification_status="complete")
        except (RuntimeError, ValueError, OSError, TypeError, KeyError) as error:
            record.update(
                classification_status="error",
                classification_error={
                    "message": error_message(error, keys),
                    "rubric_hash": rubric_hash,
                    "at": now(),
                },
            )
        save_json(path, study)
        print(
            "%s / %s: classification %s"
            % (record["question_id"], record["requested_model"], record["classification_status"]),
            flush=True,
        )

    # Stage 3: save local reviews and export the data the page will display.
    study["updated_at"] = now()
    prepare(study, root)
    save_json(path, study)
    print(
        "Saved %s records and prepared public/study.json. %s API requests made."
        % (len(study["records"]), requests)
    )
    return study


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(
            "Stopped. Progress is saved; interrupted requests require --retry-failed.",
            file=sys.stderr,
        )
        sys.exit(130)
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
