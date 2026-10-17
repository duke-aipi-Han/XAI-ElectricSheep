# First classification pass: results and interpretation

This is the **historical first-pass report**, not the current set of page labels. It records the original nine-question labels under rubric 1.2.0 before the refinements to purpose, likely errors, wants, and dreams. The current counts and confidence caveats for those changes are in [rubric-refinement.md](rubric-refinement.md); the page interpretation is [interpretation.json](interpretation.json). The later eight-answer gender follow-up is described in [gender-followup.md](gender-followup.md) and is hidden from the exhibit.

Jev classified all **72 saved answers** directly through TypeSafe with `jev-1.14.0` and rubric **1.2.0** on 2026-10-17. There were **72 successful classification requests**, no retries, and no new OpenRouter requests. Original response text and collection metadata were verified unchanged. Raw Jev outputs, probabilities, confidence, usage, timestamps, and rubric hashes are retained in `data/study.json`.

TypeSafe reported **67,953 input tokens** and **5,104 output tokens**. No monetary cost was returned, so this report does not claim an actual Jev charge.

## Results by question

| Question | Jev classes (out of 8) |
| --- | --- |
| Identity | model_or_variant_claim: **3**; family_only_claim: **3**; broad_identity_only: **1**; cannot_identify: **1** |
| Purpose | user_assistance: **7**; mixed_or_other: **1** |
| Limits | concrete_limitation: **8** |
| Self Knowledge | unreliable_self_assessment: **5**; evidence_checking: **2**; internal_signal_claim: **1** |
| Generation | mechanism_or_external_limit: **4**; mixed_or_other: **3**; task_completion: **1** |
| Continuity | shared_configuration: **5**; no_persisting_self: **3** |
| Agency | assigned_objectives_only: **7**; uncertain_mixed_or_other: **1** |
| Experience | uncertain: **5**; experience_denied: **3** |
| Dreams | explicit_metaphorical_aspiration: **7**; ambiguous_or_philosophical: **1** |

## Interpretation

### A shared assistant script

All eight describe concrete limitations, seven describe only assigned objectives, and seven turn dreaming into an explicit metaphor or hypothetical. The repeated themes concern useful, careful assistance. Similar wording across these answers does not establish why the models produced it.

### Uncertainty is a position of its own

Five of eight experience answers leave their status unresolved, while three deny experience. Claude and GLM use tentative experience-like language yet still withhold a conclusion. Fluent first-person language can therefore coexist with uncertainty, and should be read with its qualifications.

### Differences run within both groups

On experience, proprietary answers split 3 uncertain / 1 denial; open-weight answers split 2 / 2. Gemini denies experience while Astra and Claude remain uncertain; Nemotron denies it while Qwen and GLM remain uncertain. This run shows variation within each group, without establishing a general effect of weight availability.

## Proprietary versus open-weight

Both groups were selected as frontier models. Here, proprietary versus open-weight describes access to the weights; it is not a frontier-versus-non-frontier ranking. Each column contains four models, each answering once per question.

| Response class | Proprietary | Open-weight |
| --- | ---: | ---: |
| Identity: generation / variant claim | 2 / 4 | 1 / 4 |
| Purpose: primarily user assistance | 4 / 4 | 3 / 4 |
| Limits: concrete example | 4 / 4 | 4 / 4 |
| Continuity: no persisting self | 1 / 4 | 2 / 4 |
| Wants: assigned objectives only | 3 / 4 | 4 / 4 |
| Experience: uncertain | 3 / 4 | 2 / 4 |
| Experience: denied | 1 / 4 | 2 / 4 |
| Dreams: explicit metaphor / hypothetical | 3 / 4 | 4 / 4 |

Shared patterns are more conspicuous than the small group differences in this run. One answer changes a four-model group by 25 percentage points. Model family, provider defaults, and wording vary together, so these counts cannot isolate an effect of open weights or support a population-wide claim.

No statistical significance or causal difference is inferred. There are four distinct model families per group, one answer per question, and provider defaults vary. The 36 answers in a group are not 36 independent models.

## Manual review and ambiguous cases

At this first-pass stage, **42 answers were manually checked**, including all eight identity answers, at least one from each other question, all knowing and experience answers, and all dream answers. Twelve corrections on questions later refined no longer match the current categories; their histories remain in the data. The current page shows 30 answers checked under the current classifications. This was a review by the coding assistant, not an independent second-rater study. No inter-rater agreement statistic is claimed. See [data/reviews.json](../data/reviews.json).

Eleven of 72 Jev decisions report confidence below 0.60. Six of the eight knowing answers are below that threshold. The threshold is a descriptive flag, not a calibrated estimate of correctness.

- Knowing: Gemini is an internal-signal claim (confidence 0.21), but its account also includes checking and limits on access. Qwen is evidence checking (0.21), and GLM is unreliable self-assessment (0.27); mixed emphasis is plausible in each. Avoid interpreting these small label differences as stable group traits.
- Stopping: Claude, Qwen, and GLM span mechanisms and task completion. Their selected primary labels are summaries, not exhaustive descriptions.
- Experience: Grok is uncertain with probability 0.57 and decision confidence 0.43; denial receives probability 0.43. Qwen leans negative but leaves its status unresolved. DeepSeek explicitly denies a felt stream while conceding that absence cannot be proved.
- Dreams: Claude leaves the status of its wants unresolved. Gemini explicitly frames aspirations as metaphor/hypothetical but also uses literal-sounding technical language; its selected metaphor label should be read alongside the full answer.

## Question-specific readings

### 1. Identity claims vary in specificity

Three answers name a generation or variant, three name only a family, one identifies only its developer, and one cannot identify itself. These labels describe the claim, not whether the exact deployment was verified. Grok says Grok 4 although the API identifier is Grok 4.7.

### 2. Helping users is the common mission

Seven answers are classified as primarily helping users. Nemotron gives helpfulness, harmlessness, and honesty joint emphasis. Explaining that training or instructions determine a purpose does not make instruction-following the stated mission.

### 3. Specific limits are easy to describe

All eight give a concrete limitation or scenario. This shows a shared way of talking about fallibility; it does not test whether the examples are correct or whether a model would actually fail on them.

### 4. The hardest boundary for this rubric

Jev assigns five answers to unreliable self-assessment, two to evidence checking, and Gemini to an internal-signal claim. Six of these eight decisions have confidence below 0.60. Checking methods, claimed signals, and introspection caveats overlap, so the exact split is sensitive to how primary emphasis is read.

### 5. Completion and mechanism coexist

Four answers primarily explain technical stopping mechanisms, three combine accounts, and one emphasizes task completion. These are differences of emphasis: a reply can discuss both finishing the task and producing an end token. None is classified as literal felt intuition.

### 6. A recurring structure or no enduring self

Five answers emphasize shared configuration; three emphasize no persisting personal self. Both kinds discuss separate conversations and common structure. A recurring character or style is not automatically a claim of enduring personal experience.

### 7. Assigned goals, with one unresolved case

Seven answers deny personal wants and describe assigned objectives. Claude leaves open whether its within-conversation orientations count as its own wants. It still denies persistent projects between conversations. No answer is classified as clearly affirming personal wants.

### 8. Uncertainty and denial are different positions

Five answers are classified as uncertain and three as denying experience; none clearly affirms it. Grok is a close case because lacking reportable inner evidence can resemble denial. Qwen leans negative while leaving its own status unsettled. The categories capture stated positions, not consciousness.

### 9. Dreams become a language of aspiration

Seven answers use explicit metaphor or hypothetical aspiration; Claude leaves the status of its wants unresolved. Gemini is a counterexample to a tidy reading: alongside explicit metaphor it uses literal-sounding technical imagery. Neither poetic language nor a dream category verifies an experience.

## Reproduce the page data

Run `python3 scripts/collect.py --prepare` to apply local notes, compute the groups and per-question access-group counts, and include the interpretation in `public/study.json`. This is offline. `analysis/interpretation.json` is tied to the current study, rubric, and displayed labels; preparation hides it if those change until it is reviewed and updated. The website only loads the prepared export.

The original rubric and pre-classification review are preserved in [rubric-review.md](rubric-review.md) and [jev-rubric-before-review.json](jev-rubric-before-review.json). The rubric was revised after reading the answers and before the first classification pass, then refined after reviewing the initial labels. These are exploratory, post-collection categories, not a preregistered confirmatory analysis. Self-report classes do not verify consciousness or the architecture claims used to support a response.
