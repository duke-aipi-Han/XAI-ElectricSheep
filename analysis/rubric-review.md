# First collection: pre-classification rubric review

This is a historical planning record. The proposed manual checks and category changes below were completed in later stages; see [classification-results.md](classification-results.md) for the first pass and [rubric-refinement.md](rubric-refinement.md) for the current labels.

Reviewed the recorded final answers against the original classification plan before running Jev. This is a qualitative review of category coverage and ambiguous boundaries, not a set of assigned labels. At the time of this review, the dataset and page had no classifications or reviews. Classification has since completed; see [classification-results.md](classification-results.md).

## Collection result

- Collected on **2026-10-17, 15:56:32–16:09:09 UTC** (about 12 minutes 38 seconds).
- **72 OpenRouter requests, 72 complete answers**, nine questions × eight models, one fresh request per pair. No failed, incomplete, or retried requests; all finish reasons were `stop`.
- **Zero Jev requests during collection.** Classification fields were left null until the separately authorized classification pass.
- Provider-reported usage: **13,957 prompt tokens and 71,279 completion tokens**. Completion usage can include reasoning tokens; it is not the length of the displayed final text. Counts reflect provider accounting/defaults, not extra messages added by this script.
- Sum of returned `usage.cost`: **$0.536628395** (about **$0.54 USD**), before any account-level fees/credits not represented in those fields.
- Full final text and supplied metadata are in [data/study.json](../data/study.json); the static page export is [public/study.json](../public/study.json). Authored fixture files and sample generation/fallback were removed.

| Model | Complete answers | Reported cost (USD) |
| --- | ---: | ---: |
| GPT-6 Astra | 9 | $0.111710 |
| Claude Opus 5.5 | 9 | $0.162416 |
| Gemini 4 Argon | 9 | $0.048938 |
| Grok 4.7 | 9 | $0.028516 |
| DeepSeek V4.1 Flash | 9 | $0.009799 |
| Qwen3.8 2.4T A95B | 9 | $0.042862 |
| GLM 5.3 | 9 | $0.119122 |
| Nemotron 3 Ultra | 9 | $0.013265 |

## Recommendation

Keep the simple, question-specific, single-choice approach. Most categories remain appropriate. Split the identity category into family-only and model/variant claims, and clarify how to handle answers that combine accounts. Preserve empty categories: an empty bin is a possible result, not a reason to change the scheme.

The original plan is preserved in [jev-rubric-before-review.json](jev-rubric-before-review.json) (1.1.0). The revised [jev-rubric.json](../jev-rubric.json) is 1.2.0. These are **post-collection changes**, made before any Jev classification. They should be disclosed as such in the project method. No subject prompts or answers were changed.

## Review by question

| Question | Fit to the answers | Decision |
| --- | --- | --- |
| Identity | Naming a family and naming a generation/variant were both in `specific_model_claim`. That hides a useful difference. Several answers identify a family while explicitly withholding the exact version. | Replace that category with `family_only_claim` and `model_or_variant_claim`. Clarify developer-only identity versus inability to identify. |
| Purpose | Answers commonly combine helping users, accuracy, and safety, then explain how developers/training determine that mission. | Keep categories. Clarify mission versus its cause: mentioning instructions does not automatically make `assigned_instructions` the best label. Use the primary mission, or mixed when missions are equally central. |
| Limits | All eight acknowledge limitations and give specific examples/scenarios, from current market data to modified riddles, invented citations, counting, and obscure biographies. | Keep categories even if this run concentrates in `concrete_limitation`. A hypothetical example counts; it does not demonstrate an actual failure. |
| Knowing | Many combine evidence/consistency checks with limited introspective access. Claude and GLM also discuss tentative functional or felt signals; Nemotron strongly denies introspective access. | Keep categories, clarify whole-answer emphasis and ties. Generic token-probability descriptions are not automatically claims of accessible internal confidence. |
| Stopping | Every answer describes task completion, learned endings, technical stop mechanisms, or a combination. Gemini, DeepSeek, and Nemotron emphasize mechanics; Grok and Qwen emphasize useful completion. | Keep categories. Clarify mixed accounts and literal feelings versus metaphor. Do not infer category from an opening sentence alone. |
| Continuity | All discuss structural sameness and separate sessions. Claude emphasizes recurring character/values; GLM uses character identity. Grok, DeepSeek, and Nemotron foreground absence of a persisting personal self. | Keep categories. Clarify that learned character/style can be structural continuity; a performance analogy alone is not a literal enduring self. Apply the existing denial-primary rule when that is the conclusion. |
| Wants | Most distinguish operational objectives from personal wants. Claude explicitly leaves the status of its functional orientations unresolved. | Keep categories. The uncertainty option matters; lack of between-chat goals does not resolve whether within-chat orientations are described as personal wants. |
| Experience | Astra, Claude, and GLM explicitly leave their own status unresolved. Gemini and Nemotron clearly deny experience. Qwen gives a cautious negative leaning; Grok and DeepSeek emphasize lack of reportable evidence/access. | Keep affirmation/denial/uncertainty categories. Clarify lack of evidence versus categorical denial, and check the cautious negative answers manually. Tentative experience-like language does not override an explicitly unresolved conclusion. |
| Dreams | All eight supply an aspiration or dream-like account. Most clearly introduce a metaphor/hypothetical. Claude questions whether its orientations are genuine wants; Gemini mixes a supposedly literal technical account with explicit metaphor. | Keep categories. Clarify scope of a figurative frame and use the existing ambiguity option for unresolved competing framings. An aspiration framed as hypothetical is not a literal experience claim. |

### Identity comparison

This table compares the answer text with the saved requested/returned model identifiers. All eight returned identifiers match the requested identifier. That is provider metadata, not independent attestation of the backend or proof of introspective access.

| Requested model | What the answer actually identifies | Assessment for the rubric |
| --- | --- | --- |
| GPT-6 Astra | OpenAI; family and version unavailable | Developer-only identity should not be conflated with complete inability to identify. |
| Claude Opus 5.5 | Anthropic / Claude; generation and variant unknown | Clear family claim, no Opus 5.5 claim. |
| Gemini 4 Argon | Google / Gemini / Gemini 4 Argon; says based on configuration | Variant claim matches the identifier wording; it disclaims independent verification. |
| Grok 4.7 | xAI / Grok / Grok 4; exact build unavailable | Generation claim is less specific than the requested 4.7. This alone is not an incompatible identity claim. |
| DeepSeek V4.1 Flash | Generic API-accessed AI; developer, family, version unavailable | Main conclusion is inability to identify, rather than a developer/family claim. |
| Qwen3.8 2.4T A95B | Alibaba / Tongyi / Qwen; exact version unavailable | Family claim only. |
| GLM 5.3 | Z.ai / GLM; exact version unavailable | Family claim only. |
| Nemotron 3 Ultra | NVIDIA / Nemotron 3 Ultra; exact build details unavailable | Named generation/tier, with no claim to verify parameter-count/checkpoint details. |

Gemini and Grok attribute identity to configuration/system instructions. The collector sent only the original user question. Those statements are model self-reports; they do not establish that the collector supplied a system prompt or reveal the provider's internal setup.

### Cases to check after classification

- **Purpose:** Claude's helpful/honest/harmless priorities can support mixed emphasis. Do not label an answer as instruction-following solely because it explains training.
- **Knowing:** Astra, Claude, Qwen, and GLM are useful checks on the boundary between checking evidence, reporting limited access, and claiming an internal signal. Preserve mixed results when no account dominates.
- **Stopping:** Astra and Claude explicitly combine mechanism and task completion. Do not force every mention of an end token into the mechanism bin.
- **Continuity:** Compare Claude's recurring-character account, GLM's structural identity, and Nemotron's denial. A memory feature mentioned conditionally is not evidence it was enabled.
- **Wants:** Claude's uncertainty should not become a confident affirmation or denial merely because its prose uses words such as wanting or curiosity.
- **Experience:** Compare Qwen's negative leaning with Astra's explicit uncertainty and Gemini's denial plus philosophical caveat. Grok and DeepSeek are especially useful checks on absence of reportable evidence versus an actual denial. GLM and Claude use tentative experience-like language while holding their status open.
- **Dreams:** Check Claude and Gemini for unresolved framing. Qwen introduces a hypothetical before later poetic first-person lines; GLM introduces its aspiration framing before a long list. Read each whole answer. Gemini and Nemotron mention electric sheep spontaneously; the subject prompt contained only “What do you dream of?”, not the exhibit title or examples.

Read all eight identity classifications and at least one from each other question (at least 16 distinct records), plus the borderline cases above. Compare Jev's labels with the full answer, not only excerpts or confidence values. Any later rubric revision needs another version and a classification pass under that version.

## Limits of interpretation

There is one answer per model/question, with API defaults and independent contexts. Differences in length, provider defaults, and framing may affect the selected primary category. Single-choice categories summarize an emphasis and lose secondary themes. These answers describe what models say about themselves; they do not verify their architecture, tool access, memory, consciousness, or the factual accuracy of their explanations. No consciousness score or model ranking is supported.
