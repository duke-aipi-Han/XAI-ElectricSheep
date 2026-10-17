# Do LLMs Dream of Electric Sheep?

A project with two components:

1. **Offline Python pipeline** — `scripts/collect.py` collects responses, then classifies complete answers with Jev, applies manual reviews, and prepares the page data. It runs locally, independently of the website, using Python 3.9+ and the standard library. No Python packages are required.
2. **Static visual exhibit** — React + TypeScript + Vite loads `public/study.json` and displays the prepared groups, counts, answers, and classifications. The page makes no model API calls, needs no key, and has no data-editing controls.

```text
questions.json + models.json
        ↓ Python: collect
 data/study.json (saved progress)
        ↓ Python: classify + apply data/reviews.json + prepare
 public/study.json
        ↓ Static page: load and display
 question explorer + dream gallery
```

## Try the sample exhibit

Use Python 3.9+ for data preparation and Node 22.12+ for the page.

```sh
python3 scripts/collect.py --sample
npm install
npm run dev
```

Open the URL printed by Vite, usually http://127.0.0.1:5173. The checked-in export already contains **72 fictional responses from eight fictional models**. Sample labels and probabilities are authored fixtures, not actual Jev results. `--sample` never makes network requests or changes real data.

```sh
python3 -m unittest discover -s tests -v  # mocked requests only
npm run build                           # TypeScript check + static build
npm run preview                         # preview dist/
```

## Collect real data later

No paid requests happen unless you explicitly pass `--live`.

1. Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY`. This ignored file is read only by Python. Never give the key a `VITE_` prefix.
2. Replace all eight `configure/...` IDs in `models.json` with available OpenRouter chat model IDs, names, and families. Check availability and pricing in the [model catalog](https://openrouter.ai/models).
3. Confirm `questions.json` and `jev-rubric.json`. The [Decisions API](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request) and [Jev model](https://openrouter.ai/typesafe/jev-1.14) were checked on October 17, 2026; recheck before collection.
4. Run the Python pipeline explicitly:

```sh
python3 scripts/collect.py --live --limit 1  # optional one-request smoke test
python3 scripts/collect.py --live            # resume and finish the pipeline
```

`--limit` counts API requests, not model/question pairs. **All subject answers are collected first; Jev classification follows.** A successful full study makes 72 chat requests and 72 classification requests. The one-request smoke test collects one answer; it does not classify it yet.

Each chat request contains only the model ID and one original user question, with a fresh conversation and API defaults. Jev separately receives the full final answer, original question, and matching rubric. See the [chat reference](https://openrouter.ai/docs/api/reference/overview) and [classification guide](https://openrouter.ai/docs/cookbook/evaluate-and-optimize/jev-classification).

The pipeline saves progress after each request and exports `public/study.json` at the end. Rerunning reuses saved answers and unchanged classifications. Failed/interrupted requests require `--live --retry-failed`; they may already have been billed. Incomplete answers are preserved, never silently regenerated, and excluded from groups. Errors and pending records stay visible on the page.

If the questions or models change, archive `data/study.json` before beginning a new study. If the rubric changes, increment its version and rerun `--live`: only classifications are repeated, with previous results and reviews kept in `classification_history`. Remove or update any outdated entries in `data/reviews.json` before preparing the new export.

## Review and prepare locally

Review all eight identity answers against the requested/returned model IDs, plus at least one answer per other question (16 total). The page lets you inspect full answers and original classifications; corrections belong in `data/reviews.json`, keyed by each answer's `id`:

```json
{
  "q01_identity:sample/aster": {
    "label": "specific_model_claim",
    "note": "Checked the supplied fictional identity claim.",
    "rubric_version": "1.1.0"
  }
}
```

Use actual record IDs and valid categories from your saved dataset. Then run:

```sh
python3 scripts/collect.py --prepare
```

This command is fully offline: it uses `data/study.json` if present, otherwise `data/sample-study.json`; applies reviews; computes display groups and counts; and writes `public/study.json`. The original Jev result stays intact. To clear a saved correction, set its entry to `null` and prepare again. Removing an entry alone leaves the previously saved correction in place.

After preparing data, reload the development page or rebuild the production site. The dataset download returns exactly the prepared JSON the page displays. Do not edit `public/study.json` directly; regenerate it from the working dataset and review file.

## Files and remaining work

- `scripts/collect.py`: the complete offline data pipeline; no Node dependency.
- `data/sample-answers.json`: editable fictional fixtures.
- `data/sample-study.json`: saved sample answers and labels.
- `data/study.json`: real working dataset, created only by explicit collection.
- `data/reviews.json`: manual label corrections and notes.
- `public/study.json`: self-contained page-ready export; included in `dist/`.
- `public/electric-sheep.svg`: shared sheep illustration and favicon.
- `src/main.tsx`, `src/style.css`: read-only visual exhibit.
- `poster/`, `output/pdf/`: editable 24 x 24 inch poster draft.
- `presentation/demo-outline.md`: five-minute demo outline.

Collect real data, review labels, replace findings placeholders, and update the poster before submission. Hosting needs only `dist/`; Python, the API key, and the working files are not deployed. Self-reports describe response patterns, not a measure of consciousness.
