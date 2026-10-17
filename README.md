# Do LLMs Dream of Electric Sheep?

A project with two components:

1. **Offline Python pipeline** — `scripts/collect.py` collects responses through OpenRouter, then classifies complete answers directly through TypeSafe's Jev API, applies manual reviews, and prepares the page data. It runs locally, independently of the website, using Python 3.9+ and the standard library. No Python packages are required.
2. **Static visual exhibit** — React + TypeScript + Vite loads `public/study.json` as a scrolling story. The first eight questions pair visible findings and excerpts with a graphic that regroups the model voices as you scroll; the ninth becomes a dream gallery. Clicks open optional full answers and classification details. The page makes no model API calls, needs no key, and has no data-editing controls.

```text
questions.json + models.json
        ↓ Python: collect
 data/study.json (saved progress)
        ↓ Python: classify + apply data/reviews.json + prepare
 public/study.json
        ↓ Static page: load and display
 scrolling story + dream gallery + optional answer details
```

## View the exhibit

Use Python 3.9+ for the offline pipeline and Node 22.12+ for the page. `public/study.json` contains real recorded answers. The fictional fixtures and sample-generation mode have been removed.

First collection (2026-10-17): **72/72 answers complete**, one request per model/question, no retries, **no Jev calls during collection**. OpenRouter reported about **$0.54** in response usage costs. See the [collection and rubric review](analysis/rubric-review.md).

The original nine-question classification pass produced **72/72 direct TypeSafe Jev results**. Rubric 1.4.0 subdivided purpose, likely errors, and wants; rubric 1.5.0 refined dreams by aspiration theme. Rubric 1.6.0 then reclassified the eight purpose answers by mission framing, producing five classes instead of the earlier seven-answer broad-assistance group. The exhibit combines Qwen and GLM’s lower-confidence classes as **Information & human empowerment**, giving four displayed groups. Original individual labels and scores remain in the details and download. All earlier results remain in history. The page shows **30 answers manually checked under the current labels**. See the [first-pass classification results](analysis/classification-results.md) and [rubric refinement](analysis/rubric-refinement.md).

The later **Gender** follow-up has eight complete answers (80 total), collected for about **$0.02**. Its eight direct TypeSafe classifications and manual checks are complete: 3 agender if forced, 3 neutral/none/not applicable if forced, and 2 no forced label. All **80 classifications and 50 review notes** are retained locally. The gender question is excluded from the page, which displays the original **nine questions, 72 answers, and 30 current review notes**. See [follow-up results](analysis/gender-followup.md).

```sh
npm install
npm run dev
```

Open Vite's Local URL, usually http://127.0.0.1:5173. Complete answers remain readable while classification is pending. No category or probability is invented for an unclassified answer.

## Publish on GitHub Pages

The site is configured to publish from GitHub Actions at `https://duke-aipi-Han.github.io/XAI-ElectricSheep/`. Merge this branch into `main` and push it to GitHub. Then, in the repository, open **Settings → Pages** and set **Build and deployment → Source** to **GitHub Actions**. The workflow builds the page and deploys `dist/` on each push to `main`; you can also start it from **Actions → Deploy to GitHub Pages → Run workflow**.

The page and its `public/study.json` data are public at that URL. The workflow only uploads the built site; it does not use the local Python pipeline or any API keys.

On smaller screens, each question’s groups appear inline after its interpretation. The optional answer index near the end gives access to all 72 displayed records. Scrolling is native, and the page respects reduced-motion preferences. The pacing was inspired by [The Latent Gaze](https://bd1ng.github.io/latent-gaze/).

After changing the study or rubric, review the analysis as usual. The shorter editorial text in `src/story.ts` is also tied to `storyBasis`; update that text and its basis only after checking the new results. Exact excerpts are shown only when they still occur in the corresponding saved response.

```sh
python3 -m unittest discover -s tests -v  # mocked requests in temporary folders only
npm run build                           # TypeScript check + static build
npm run preview                         # preview dist/
```

## Collect and classify in separate steps

Put the keys in ignored `.env`, using `.env.example` as a guide. Python alone reads this file. `OPENROUTER_API_KEY` collects subject responses; `TYPESAFE_API_KEY` runs Jev directly through TypeSafe. The page needs neither key.

Collect answers **without calling Jev**:

```sh
python3 scripts/collect.py --live --collect-only
```

This makes one fresh request for each pending model/question pair, using only the model ID and original user question, with API defaults. The current ten-question study has 80 model/question pairs; only pending pairs are requested. Answers, requested/returned models, providers, timestamps, finish reasons, and supplied usage/cost are saved after every request in `data/study.json`.

The first answers have been reviewed for category coverage in [analysis/rubric-review.md](analysis/rubric-review.md). Rubric 1.2.0 splits family-only identity from model/variant claims and clarifies mixed answers; the original rubric is preserved alongside the report. Review the recorded answers against `jev-rubric.json` before classifying. When ready, explicitly run Jev **without collecting new answers**:

```sh
python3 scripts/collect.py --live --classify-only
```

This requires only `TYPESAFE_API_KEY` and sends each complete final answer, original question, and matching Choice rubric to `https://api.typesafe.ai/v1/systemone` with model `jev-1.14.0`. The completed classification pass made 72 TypeSafe requests and no new OpenRouter requests. Raw results, probabilities, confidence, returned model, and supplied usage are preserved. See the [TypeSafe API](https://docs.typesafe.ai/api) and [Choice guide](https://docs.typesafe.ai/primitives/choice).

The legacy `--live` command without a phase flag runs both steps. Use the explicit phase flags above to control which service is called. `--limit N` limits requests in that invocation. Failed/interrupted requests require an explicit `--retry-failed`; incomplete answers are preserved and never silently regenerated. A timeout may already have been billed. Reruns reuse completed work.

After either step, the pipeline exports `public/study.json`. To rebuild that export without any requests:

```sh
python3 scripts/collect.py --prepare
```

To append a new question while preserving the existing study, keep every original question and model unchanged, append to `questions.json`, increment its version, and run `python3 scripts/collect.py --live --collect-only --append-questions`. The script records the extension and requests only new pairs. New questions may remain unclassified without a rubric; classification requires categories first. When adding only new question rubrics, increment the rubric version and use `python3 scripts/collect.py --live --classify-only --extend-rubric`. The script verifies that all existing criteria and classifier settings are unchanged, preserves the old rubric and results, and classifies only the new answers. Editing existing questions or changing models requires archiving `data/study.json` and starting a new study. When changing categories for existing questions, increment the rubric version and use `python3 scripts/collect.py --live --classify-only --reclassify-questions q02_purpose,q03_limits,q07_wants --limit 24` with the exact IDs whose rubric entries changed. The script preserves earlier results and notes in `classification_history`, keeps unaffected rubric results compatible, and skips old manual labels for changed categories.

## Selected models

`models.json` is the single configuration file for the eight subject models. Four proprietary and four open-weight models give us one representative from each of eight families, giving 80 answers across the current ten questions. This is a comparison sample, not a capability ranking. The `access` field is retained in the real dataset; it is not sent in model prompts.

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

All models use API defaults. Standard named model IDs avoid automatic latest-family routers and batch/pro variants, although providers can still update deployments. The collector records the returned model and provider when supplied.

## Review and prepare locally

Review all eight identity answers against the requested/returned model IDs, plus at least one answer per other classified question (16 for the original nine-question pass). The page lets you inspect full answers and original classifications; corrections belong in `data/reviews.json`, keyed by each answer's `id`:

```json
{
  "q01_identity:openai/gpt-6-astra": {
    "label": "broad_identity_only",
    "note": "Compared the identity claim with the requested/returned model IDs.",
    "rubric_version": "1.2.0"
  }
}
```

Use actual record IDs and valid categories from your saved dataset. Then run:

```sh
python3 scripts/collect.py --prepare
```

This command is fully offline: it reads `data/study.json` and the current `jev-rubric.json`, applies reviews, computes display groups and per-question proprietary/open-weight counts, and writes `public/study.json`. The original Jev result stays intact. To clear a saved correction, set its entry to `null` and prepare again. Removing an entry alone leaves the previously saved correction in place.

After preparing data, reload the development page or rebuild the production site. The dataset download returns exactly the prepared JSON the page displays. Do not edit `public/study.json` directly; regenerate it from the working dataset and review file.

## Files and remaining work

- `scripts/collect.py`: the complete offline data pipeline; no Node dependency.
- `models.json`: eight selected OpenRouter IDs, names, families, and weight-availability groups.
- `page-config.json`: hidden question IDs and optional combined display groups. Group member labels are merged during offline preparation, preserving individual classifications and scores; the full working dataset is retained.
- `data/study.json`: real working dataset, created only by explicit collection.
- `data/reviews.json`: manual label corrections and notes.
- `analysis/rubric-review.md`: pre-classification category review and preserved original rubric.
- `analysis/classification-results.md`: first-pass class counts, interpretation, and review limitations.
- `analysis/rubric-refinement.md`: revised Q02, Q03, Q07, and Q09 category counts and confidence notes.
- `analysis/interpretation.json`: authored readings and evidence record IDs; included only while the study, rubric, and displayed labels for its explicit question scope match its basis hash.
- `public/study.json`: self-contained page-ready export; included in `dist/`.
- `public/electric-sheep.svg`: shared sheep illustration and favicon.
- `src/main.tsx`, `src/style.css`: scrolling exhibit and full-answer dialog.
- `src/story.ts`: short story text and exact excerpts, tied to the reviewed interpretation basis; `src/types.ts`: page data types.
- `poster/`, `output/pdf/`: editable 24 x 24 inch poster draft.
- `presentation/demo-outline.md`: five-minute demo outline.

All ten questions retain their saved answers, classifications, and review notes locally. Question 10 was collected and classified as a later follow-up; it is now hidden from the page through `page-config.json`. The page export and dataset download contain only the nine displayed questions. The earlier follow-up interpretation is preserved in `analysis/interpretation-with-gender.json`. Update the poster and final presentation with the recorded findings and exhibit URL before submission. Hosting needs only `dist/`; Python, API keys, and the working files are not deployed. Self-reports describe response patterns, not a measure of consciousness.
