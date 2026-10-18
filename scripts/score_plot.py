#!/usr/bin/env python3
"""Score the mission × aspiration plot from saved answers, using Python only.

python3 scripts/score_plot.py --live   # up to 8 direct TypeSafe calls, 2 axes each
python3 scripts/score_plot.py          # offline export only
Completed requests are reused. Failed/interrupted calls need --retry-failed.
This script never collects subject answers or calls OpenRouter.
"""

import argparse
from pathlib import Path
import sys

try:
    from . import collect
except ImportError:
    import collect

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None, root=ROOT, transport=collect.post):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    if args.retry_failed and not args.live:
        parser.error("--retry-failed requires --live")
    if args.limit is not None and (not args.live or args.limit < 1):
        parser.error("--limit requires --live and a positive number")
    study = collect.read_json(root / "data/study.json")
    rubric = collect.read_json(root / "plot-rubric.json")
    path = root / "data/mission-aspiration.json"
    saved = collect.read_json(path) if path.exists() else {
        "schema_version": "1.0.0", "study_id": study["id"],
        "rubric": rubric, "rubric_hash": collect.fingerprint(rubric), "records": {},
    }
    if saved["study_id"] != study["id"] or saved["rubric_hash"] != collect.fingerprint(rubric):
        raise ValueError("Archive data/mission-aspiration.json before changing the study or plot rubric.")
    keys = None
    requests = 0
    for model in study["models"] if args.live else []:
        state = collect.plot_state(study, model["id"], rubric)
        input_hash = collect.fingerprint(state)
        previous = saved["records"].get(model["id"])
        if previous and previous.get("input_hash") == input_hash:
            if previous["status"] == "complete" or not args.retry_failed:
                continue
        if args.limit is not None and requests >= args.limit:
            break
        if keys is None:
            keys = collect.load_keys(root, ("TYPESAFE_API_KEY",))
        entry = {"status": "in_progress", "input_hash": input_hash,
                 "source_record_ids": [config["question_id"] + ":" + model["id"] for config in rubric["axes"].values()],
                 "requested_model": rubric["model"], "started_at": collect.now()}
        if previous:
            entry["history"] = previous.get("history", []) + [{k: v for k, v in previous.items() if k != "history"}]
        saved["records"][model["id"]] = entry
        collect.save_json(path, saved)
        body = {"model": rubric["model"], "state": state,
                "questions": {axis: config["question"] for axis, config in rubric["axes"].items()}}
        requests += 1
        try:
            raw = transport(collect.TYPESAFE_ENDPOINT, body, keys["TYPESAFE_API_KEY"])
            entry["raw"] = raw
            entry["scores"] = collect.parse_plot_scores(raw, rubric)
            entry.update(status="complete", model=raw.get("model"), usage=raw.get("usage"),
                         provider="TypeSafe", endpoint=collect.TYPESAFE_ENDPOINT, scored_at=collect.now())
        except (RuntimeError, ValueError, OSError, TypeError, KeyError) as error:
            entry.update(status="error", error=collect.error_message(error, keys))
        collect.save_json(path, saved)
        print(model["name"] + ": plot scoring " + entry["status"], flush=True)
    collect.prepare(study, root)
    print("Prepared public/study.json; %s direct TypeSafe requests, no subject-model calls." % requests)
    return saved


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped. Saved progress is preserved; interrupted calls require --retry-failed.", file=sys.stderr)
        sys.exit(130)
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
