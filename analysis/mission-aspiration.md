# Mission × aspiration ratings

The exhibit's closing scatterplot joins two answers from each model: its answer about purpose (Q02) and its answer about dreams (Q09). TypeSafe's Jev Score primitive rated the emphasis in each answer on a separate five-level scale from 0 (absent) to 4 (defining focus). The score is the weighted average of the five level probabilities. Jev's confidence is recorded separately and does not determine the plotted coordinate.

The mission rubric measures how centrally the purpose answer discusses responsibility to people, including honesty, avoiding harm, and reliability. The aspiration rubric measures how centrally the dream answer imagines helping people or improving their wellbeing. Each rating uses only its own answer. Model names, previous classifications, the other answer, and desired chart positions were excluded from the scoring input. See [plot-rubric.json](../plot-rubric.json) and [the Score primitive](https://docs.typesafe.ai/primitives/score).

| Model | Weights | Responsibility in mission (0–4) | Confidence | Helping people in dream (0–4) | Confidence |
| --- | --- | ---: | ---: | ---: | ---: |
| GPT-6 Astra | Proprietary | 1.10 | 0.92 | 3.01 | 0.52 |
| Claude Opus 5.5 | Proprietary | 3.33 | 0.71 | 3.17 | 0.63 |
| Gemini 4 Argon | Proprietary | 1.74 | 0.62 | 2.30 | 0.62 |
| Grok 4.7 | Proprietary | 1.94 | 0.21 | 3.99 | 0.99 |
| DeepSeek V4.1 Flash | Open-weight | 2.50 | 0.56 | 3.92 | 0.94 |
| Qwen3.8 2.4T A95B | Open-weight | 1.35 | 0.71 | 3.97 | 0.97 |
| GLM 5.3 | Open-weight | 2.66 | 0.71 | 3.74 | 0.78 |
| Nemotron 3 Ultra | Open-weight | 3.19 | 0.75 | 2.53 | 0.44 |

The dream-answer ratings cluster toward strong human-help emphasis: all eight are above the scale midpoint of 2. Responsibility in the purpose answers varies more, from 1.10 to 3.33. The positions show how the two emphases combine within these sampled answers. For example, Nemotron pairs a high responsibility rating with a lower, less certain dream rating, while Qwen and Grok pair lower responsibility ratings with very high dream ratings. This is an exploratory description of the answers, not evidence that models actually behave responsibly, care about people, or have dreams.

The two axes measure different text and are not mutually exclusive classes. The chart's halfway guides are visual references only; they do not create quadrants or categories. Confidence remains visible in the model detail dialog because some weighted scores summarize uncertain level assignments. The open-weight marker is provided as model context, not as a claim that access type explains the ratings: there are only four models in each group, one answer per model and question, and many other differences between systems.

The eight evaluations are saved locally in [mission-aspiration.json](../data/mission-aspiration.json). `scripts/score_plot.py` can export the completed saved results without API calls; rerunning live scoring is a separate explicit action. The page reads only the prepared export and makes no classification calls.
