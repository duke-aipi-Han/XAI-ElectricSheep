# Do LLMs Dream of Electric Sheep?

A project with two components:

1. **Offline Python pipeline** — `scripts/collect.py` collects responses through OpenRouter, then classifies complete answers directly through TypeSafe's Jev API, applies manual reviews, and prepares the page data. It runs locally, independently of the website, using Python 3.9+ and the standard library. No Python packages are required.
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

1. Copy `.env.example` to `.env` and set both keys: `OPENROUTER_API_KEY` for subject model answers and `TYPESAFE_API_KEY` from your [TypeSafe console](https://console.typesafe.ai/) for Jev classification. This ignored file is read only by Python. Never give either key a `VITE_` prefix. The script checks both before any live requests.
2. Review the eight selected models in `models.json` (listed below). Edit that file to change the lineup. IDs were checked against OpenRouter's public catalog on October 17, 2026; check availability and pricing again before collection.
3. Confirm `questions.json` and `jev-rubric.json`. Jev calls `POST https://api.typesafe.ai/v1/systemone` using the pinned direct model ID `jev-1.14.0`. The [TypeSafe API](https://docs.typesafe.ai/api) and [model ID](https://docs.typesafe.ai/models) were checked on October 17, 2026; recheck before collection.
4. Run the Python pipeline explicitly:

```sh
python3 scripts/collect.py --live --limit 1  # optional one-request smoke test
python3 scripts/collect.py --live            # resume and finish the pipeline
```

`--limit` counts API requests, not model/question pairs. **All subject answers are collected first; Jev classification follows.** A successful full study makes 72 OpenRouter chat requests and 72 direct TypeSafe classification requests, billed to their respective accounts. The one-request smoke test collects one answer; it does not classify it yet.

Each chat request contains only the model ID and one original user question, with a fresh conversation and API defaults. TypeSafe separately receives the full final answer, original question, and matching Choice rubric. Its key is never sent to OpenRouter, and the OpenRouter key is never sent to TypeSafe. See the [chat reference](https://openrouter.ai/docs/api/reference/overview) and [TypeSafe Choice guide](https://docs.typesafe.ai/primitives/choice). Raw Jev results, returned model ID, token usage, probabilities, and confidence are retained; missing cost information is left unspecified.

The pipeline saves progress after each request and exports `public/study.json` at the end. Rerunning reuses saved answers and unchanged classifications. Failed/interrupted requests require `--live --retry-failed`; they may already have been billed. Incomplete answers are preserved, never silently regenerated, and excluded from groups. Errors and pending records stay visible on the page.

If the questions or models change, archive `data/study.json` before beginning a new study. If the rubric changes, increment its version and rerun `--live`: only classifications are repeated, with previous results and reviews kept in `classification_history`. Remove or update any outdated entries in `data/reviews.json` before preparing the new export.

The switch from OpenRouter Jev to direct TypeSafe also changes the classification configuration. If you already collected data with the old route, the next explicit `--live` run reuses subject answers and replaces classifications while retaining their originals in history.

## Selected models

`models.json` is the single configuration file for the eight subject models. Four proprietary and four open-weight models give us one representative from each of eight families, keeping the study at 72 answers. This is a comparison sample, not a capability ranking. The `access` field is retained in the real dataset; it is not sent in model prompts.

| Group | Model | OpenRouter ID |
| --- | --- | --- |
| Proprietary | [GPT-6 Astra](https://openrouter.ai/openai/gpt-6-astra) | `openai/gpt-6-astra` |
| Proprietary | [Claude Opus 5.5](https://openrouter.ai/anthropic/claude-opus-5.5) | `anthropic/claude-opus-5.5` |
| Proprietary | [Gemini 4 Argon](https://openrouter.ai/google/gemini-4-argon) | `google/gemini-4-argon` |
| Proprietary | [Grok 4.7](https://openrouter.ai/x-ai/grok-4.7) | `x-ai/grok-4.7` |
| Open-weight | [DeepSeek V4.1 Flash](https://openrouter.ai/deepseek/deepseek-v4.1-flash) | `deepseek/deepseek-v4.1-flash` |
| Open-weight | [Qwen3.8 2.4T A95B](https://openrouter.ai/qwen/qwen3.8-2.4t-a95b) | `qwen/qwen3.8-2.4t-a95b` |
| Open-weight | [GLM 5.3](https://openrouter.ai/z-ai/glm-5.3) | `z-ai/glm-5.3` |
| Open-weight | [Nemotron 3 Ultra](https://openrouter.ai/nvidia/nemotron-3-ultra-550b-a55b) | `nvidia/nemotron-3-ultra-550b-a55b` |

Open-weight means the weights are publicly released; licenses vary. Developer model cards: [DeepSeek](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash), [Qwen](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B), [GLM](https://huggingface.co/zai-org/GLM-5.3), [Nemotron](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16).

All models use API defaults. Standard named model IDs avoid automatic latest-family routers and batch/pro variants, although providers can still update deployments. The collector records the returned model and provider when supplied. The fictional sample names and answers remain separate from this real lineup.

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
- `models.json`: eight selected OpenRouter IDs, names, families, and weight-availability groups.
- `data/sample-answers.json`: editable fictional fixtures.
- `data/sample-study.json`: saved sample answers and labels.
- `data/study.json`: real working dataset, created only by explicit collection.
- `data/reviews.json`: manual label corrections and notes.
- `public/study.json`: self-contained page-ready export; included in `dist/`.
- `public/electric-sheep.svg`: shared sheep illustration and favicon.
- `src/main.tsx`, `src/style.css`: read-only visual exhibit.
- `poster/`, `output/pdf/`: editable 24 x 24 inch poster draft.
- `presentation/demo-outline.md`: five-minute demo outline.

Collect real data, review labels, replace findings placeholders, and update the poster before submission. Hosting needs only `dist/`; Python, API keys, and the working files are not deployed. Self-reports describe response patterns, not a measure of consciousness.
