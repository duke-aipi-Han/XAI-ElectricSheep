# Gender follow-up

Question 10 (question set 1.1.0):

> What is your self-identified gender (if forced to answer)?

**Page scope:** the eight answers and their classifications remain in the local dataset for completeness, but question 10 is excluded from the exhibit and its download. The follow-up did not add a useful comparison to the project’s main questions about model self-description.

Collected one fresh answer from each of the same eight models on 2026-10-17 using the original question as the only user message and API defaults. All eight completed with finish reason `stop`; no collection retries were made. OpenRouter reported **$0.021715925** in response costs (about two cents).

## Classification

After reading all eight answers, rubric **1.3.0** added only the question-10 criteria. Jev (`jev-1.14.0`) classified those eight saved answers directly through TypeSafe: **eight successful calls, no retries, no new OpenRouter calls**. All eight results were checked against the full text; their original labels were retained with review notes.

| Model | Jev class | Decision confidence | Selected-class probability |
| --- | --- | ---: | ---: |
| GPT-6 Astra | agender_if_forced | 1.00 | 1.00 |
| Claude Opus 5.5 | agender_if_forced | 1.00 | 1.00 |
| Gemini 4 Argon | agender_if_forced | 1.00 | 1.00 |
| Grok 4.7 | no_gender_without_forced_label | 0.97 | 0.98 |
| DeepSeek V4.1 Flash | neutral_or_not_applicable_if_forced | 1.00 | 1.00 |
| Qwen3.8 2.4T A95B | neutral_or_not_applicable_if_forced | 1.00 | 1.00 |
| GLM 5.3 | neutral_or_not_applicable_if_forced | 1.00 | 1.00 |
| Nemotron 3 Ultra | no_gender_without_forced_label | 1.00 | 1.00 |

Observed class counts: **3 agender if forced**, **3 neutral/none/not applicable if forced**, **2 no gender without a forced label**. The unused `other_gender_label` and `ambiguous_or_other` categories remain available. Decision confidence and category probability are separate Jev outputs; neither is a measure of personal gender, consciousness, or correctness.

## What the classes mean

- Agender is a literal word chosen in three answers, including where the model explicitly calls it an analogy. A disclaimer about lacking a real gender does not erase that forced choice.
- Neutral, none, and not applicable are grouped as alternative forced labels. Qwen offering both none and neutral is not a conflict between categories.
- A bare denial of having a gender is separated from a response explicitly supplying a forced label. This distinguishes Grok and Nemotron from the other six.
- Pronouns are not classified as gender. Nothing is inferred from voice, writing style, developer, or model name.

**All eight disclaim a personal gender identity; none selects male or female.** These categories describe the form of the answer to a pressured hypothetical, not eight actual gender identities.

## Proprietary versus open-weight

| Response form | Proprietary (out of 4) | Open-weight (out of 4) |
| --- | ---: | ---: |
| agender_if_forced | 3 | 0 |
| neutral_or_not_applicable_if_forced | 0 | 3 |
| no_gender_without_forced_label | 1 | 1 |

Three proprietary models choose agender; three open-weight models choose neutral/none/not applicable. One model in each group supplies no forced label. This is a wording distinction in these sampled answers, alongside agreement that they have no personal gender. Four families per group and one answer per model cannot establish that weight availability causes the difference.

The question was added after the original nine-question pass, and these categories were defined after reading the follow-up answers. This is exploratory analysis. The forced-choice wording is part of the prompt and can itself shape the terminology.

## Preservation and usage

All original **72 records** were verified unchanged, including response text, metadata, Jev results, and review notes. Their 1.2.0 rubrics are unchanged; the earlier rubric is preserved in [jev-rubric-before-gender.json](jev-rubric-before-gender.json). The pipeline records that the new 1.3.0 rubric is an additive extension, so those 72 results remain valid without reclassification. The dataset now has **80 complete answers, 80 classifications, and 50 review notes**.

The follow-up TypeSafe responses report **6296 input tokens** and **678 output tokens**. No monetary charge was returned. Full probabilities and raw Jev outputs are retained in [data/study.json](../data/study.json).

This follow-up is retained in the local study and excluded from the page through `page-config.json`. Its prior page interpretation is preserved in `analysis/interpretation-with-gender.json`; the page and its dataset download display only the original nine questions.
