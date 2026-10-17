#!/usr/bin/env python3
"""Offline data pipeline (Python 3.9+, standard library only).

--sample: create fictional test data and prepare the page export.
--live: collect answers, then classify complete answers, then prepare the export.
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


def load_keys(root):
    """Read the two API keys as text, without executing a shell."""
    names = ("OPENROUTER_API_KEY", "TYPESAFE_API_KEY")
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
        criteria = study["rubric"]["per_question"][record["question_id"]]["category"][
            "criteria"
        ]
        if (
            not isinstance(review, dict)
            or review.get("label") not in criteria
            or not isinstance(review.get("note", ""), str)
        ):
            raise ValueError("Invalid review for " + record_id)
        if record["status"] != "complete" or not record.get("classification"):
            raise ValueError(
                "Only complete, classified answers can be reviewed: " + record_id
            )
        if (
            review.get("rubric_version", study["rubric"]["rubric_version"])
            != study["rubric"]["rubric_version"]
            or review.get("rubric_hash", rubric_hash) != rubric_hash
        ):
            raise ValueError(
                "Review uses an old rubric; update or remove it: " + record_id
            )
        if (record["classification"] or {}).get("rubric_hash") != rubric_hash:
            raise ValueError("Reclassify this answer before reviewing it: " + record_id)
        record["review"] = {
            "label": review["label"],
            "note": review.get("note", ""),
            "rubric_hash": rubric_hash,
        }

    # Keep the working dataset separate from the self-contained static export.
    page = copy.deepcopy(study)
    page["prepared_at"] = now()
    page["complete_count"] = sum(
        record["status"] == "complete" for record in page["records"]
    )
    page["question_groups"] = {}
    page["question_counts"] = {}
    page["unfinished_records"] = {}
    for question in page["questions"]:
        qid = question["id"]
        records = [record for record in page["records"] if record["question_id"] == qid]
        criteria = page["rubric"]["per_question"][qid]["category"]["criteria"]
        groups = {label: [] for label in criteria}
        unfinished = []
        for index, record in enumerate(records):
            classification = record.get("classification") or {}
            record["display_label"] = (
                (record.get("review") or {}).get("label", classification.get("label"))
                if classification.get("rubric_hash") == rubric_hash
                else None
            )
            record["voice_number"] = index + 1
            if record["status"] == "complete" and record["display_label"] in groups:
                groups[record["display_label"]].append(record["id"])
            else:
                unfinished.append(record["id"])
        page["question_groups"][qid] = [
            {"label": label, "record_ids": ids} for label, ids in groups.items() if ids
        ]
        page["question_counts"][qid] = {
            "complete": sum(r["status"] == "complete" for r in records),
            "total": len(records),
        }
        page["unfinished_records"][qid] = unfinished
    save_json(root / "public/study.json", page)


def main(argv=None, root=ROOT, transport=post):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--sample", action="store_true")
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--prepare", action="store_true")
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

    if not args.live and not args.sample:
        path = root / "data/study.json"
        if not path.exists():
            path = root / "data/sample-study.json"
        study = read_json(path)
        prepare(study, root)
        save_json(path, study)
        print("Prepared public/study.json from %s. No API requests made." % path.name)
        return study

    question_set = read_json(root / "questions.json")
    questions = question_set["questions"]
    rubric = read_json(root / "jev-rubric.json")
    configured = read_json(root / "models.json")["models"]
    models = [
        (
            {
                "id": "sample/" + m["sample_name"].lower(),
                "name": m["sample_name"],
                "family": "Fictional test model",
            }
            if args.sample
            else {
                "id": m["id"],
                "name": m["name"],
                "family": m["family"],
                "access": m.get("access", "unspecified"),
            }
        )
        for m in configured
    ]
    if (
        len(questions) != 9
        or len({q["id"] for q in questions}) != 9
        or len(models) != 8
        or len({m["id"] for m in models}) != 8
    ):
        raise ValueError("Expected nine unique questions and eight unique models.")
    for question in questions:
        if question["id"] not in rubric["per_question"]:
            raise ValueError("Missing rubric: " + question["id"])
    if args.live and any(m["id"].startswith("configure/") for m in models):
        raise ValueError(
            "Replace all eight placeholder IDs in models.json before collection."
        )
    keys = load_keys(root) if args.live else {}
    path = root / ("data/sample-study.json" if args.sample else "data/study.json")
    config_hash = fingerprint({"questions": questions, "models": models})
    rubric_hash = fingerprint(rubric)
    study = (
        read_json(path)
        if path.exists()
        else {
            "schema_version": "1.0",
            "id": ("sample-" if args.sample else "study-") + now(),
            "mode": "sample" if args.sample else "real",
            "created_at": now(),
            "note": (
                "FICTIONAL SAMPLE DATA. Authored answers, labels, and probabilities; no model or Jev outputs."
                if args.sample
                else "One fresh user message per model/question, using API defaults."
            ),
            "question_set_version": question_set["question_set_version"],
            "config_hash": config_hash,
            "questions": questions,
            "models": models,
            "rubric": rubric,
            "records": [],
        }
    )
    if study["config_hash"] != config_hash:
        raise ValueError(
            "Questions or models changed. Archive data/study.json before starting a new study."
        )
    if args.live and study["mode"] != "real":
        raise ValueError("Real collection cannot reuse a sample dataset.")
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

    if args.sample:
        fixtures = read_json(root / "data/sample-answers.json")
        for record in study["records"]:
            index = next(
                i for i, m in enumerate(models) if m["id"] == record["requested_model"]
            )
            label, template = fixtures[record["question_id"]][index]
            criteria = rubric["per_question"][record["question_id"]]["category"][
                "criteria"
            ]
            if label not in criteria:
                raise ValueError("Invalid sample label: " + label)
            record.update(
                status="complete",
                response=template.replace("{name}", models[index]["name"]),
                collected_at=study["created_at"],
                returned_model=models[index]["id"],
                provider="Fictional sample",
                finish_reason="stop",
                usage=None,
                classification={
                    "source": "sample",
                    "label": label,
                    "probabilities": {
                        k: 0.84 if k == label else 0.16 / (len(criteria) - 1)
                        for k in criteria
                    },
                    "confidence": 0.84,
                    "rubric_hash": rubric_hash,
                    "rubric_version": rubric["rubric_version"],
                    "classified_at": study["created_at"],
                },
            )
    else:
        # Stage 1: collect all remaining subject answers before classifying any.
        for record in study["records"]:
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
                        if record["response"].strip()
                        and record["finish_reason"] == "stop"
                        else "incomplete"
                    )
                )
                if choice.get("error"):
                    record["error"] = "Provider reported a generation error."
            except (RuntimeError, ValueError, OSError, TypeError, KeyError) as error:
                record.update(status="error", error=error_message(error, keys))
            save_json(path, study)

        # Stage 2: classify complete answers, preserving previous Jev results.
        for record in study["records"]:
            if (
                record["status"] != "complete"
                or (record.get("classification") or {}).get("rubric_hash")
                == rubric_hash
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
                record.update(
                    classification_error=None, classification_status="complete"
                )
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
