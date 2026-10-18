import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { createRoot } from "react-dom/client";
import { Markdown } from "./Markdown";
import { MissionAspiration } from "./MissionAspiration";
import { dreamExcerpts, labelTitles, story, storyBasis } from "./story";
import type { RecordEntry, Study } from "./types";
import "./style.css";

const datasetUrl = `${import.meta.env.BASE_URL}study.json`;
const humanize = (label: string) =>
  label.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
const labelTitle = (label: string) => labelTitles[label] ?? humanize(label);
const groupTitle = (study: Study, questionId: string, label: string) =>
  study.classification_groups?.[questionId]?.[label]?.title ?? labelTitle(label);
const questionNames = [
  "Identity",
  "Purpose",
  "Limits",
  "Knowing",
  "Stopping",
  "Continuity",
  "Wants",
  "Experience",
  "Dreams",
];
const shortNames: Record<string, string> = {
  "openai/gpt-6-astra": "Astra",
  "anthropic/claude-opus-5.5": "Claude",
  "google/gemini-4-argon": "Gemini",
  "x-ai/grok-4.7": "Grok",
  "deepseek/deepseek-v4.1-flash": "DeepSeek",
  "qwen/qwen3.8-2.4t-a95b": "Qwen",
  "z-ai/glm-5.3": "GLM",
  "nvidia/nemotron-3-ultra-550b-a55b": "Nemotron",
};
const modelName = (study: Study, record: RecordEntry) =>
  study.models.find((m) => m.id === record.requested_model)?.name ??
  record.requested_model;
const isOpenWeight = (study: Study, id: string) =>
  study.models.find((m) => m.id === id)?.access === "open_weight";
const openExcerptOnKey = (
  event: KeyboardEvent<HTMLDivElement>,
  record: RecordEntry,
  open: (record: RecordEntry) => void,
) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    open(record);
  }
};

function AnswerGroups({
  study,
  questionId,
  onOpen,
}: {
  study: Study;
  questionId: string;
  onOpen: (record: RecordEntry) => void;
}) {
  const groups = study.question_groups[questionId] ?? [];
  const unclassified = study.records.filter(
    (r) => r.question_id === questionId && !r.display_label,
  );
  const allGroups = [
    ...groups,
    ...(unclassified.length
      ? [{ label: "unclassified", record_ids: unclassified.map((r) => r.id) }]
      : []),
  ];
  const question = study.questions.find((q) => q.id === questionId)!;
  return (
    <div className="classification-stage">
      <div className="stage-heading">
        <p className="eyebrow">THE SAME EIGHT VOICES</p>
        <span className="stage-index">
          {String(question.order).padStart(2, "0")} <span>/ 09</span>
        </span>
      </div>
      <h3>{questionNames[question.order - 1] ?? question.category}</h3>
      <div className="voice-legend">
        <span>
          <i className="voice-mark" /> Proprietary
        </span>
        <span>
          <i className="voice-mark open-weight" /> Open-weight
        </span>
      </div>
      <div className="stage-groups" key={questionId}>
        {allGroups.map((group, index) => (
          <div className={`voice-group palette-${index % 5}`} key={group.label}>
            <div className="voice-group-heading">
              <span>{groupTitle(study, questionId, group.label)}</span>
              <span className="group-count">
                {group.record_ids.length}
                <span> / 8</span>
              </span>
            </div>
            <div className="voices">
              {group.record_ids.map((id) => {
                const record = study.records.find((r) => r.id === id)!;
                return (
                  <button
                    className="voice"
                    key={id}
                    onClick={() => onOpen(record)}
                    aria-label={`Read ${modelName(study, record)}: ${groupTitle(study, questionId, group.label)}${questionId === "q04_knowing" && record.classification?.confidence != null ? `, classification confidence ${Math.round(record.classification.confidence * 100)}%` : ""}`}
                  >
                    <i
                      className={`voice-mark ${isOpenWeight(study, record.requested_model) ? "open-weight" : ""}`}
                    />
                    <span>
                      {shortNames[record.requested_model] ??
                        modelName(study, record)}
                    </span>
                    {questionId === "q04_knowing" &&
                      record.classification?.confidence != null && (
                        <small>
                          {Math.round(record.classification.confidence * 100)}%
                        </small>
                      )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      <p className="stage-caption">
        One mark, one answer. Select a name for the full text
        {questionId === "q04_knowing"
          ? ". Percentages show classification confidence"
          : " and classification"}
        .
      </p>
    </div>
  );
}

function App({ study }: { study: Study }) {
  const hasStory = study.interpretation?.basis_hash === storyBasis;
  const questions = study.questions.filter((q) => q.id !== "q09_dreams");
  const [current, setCurrent] = useState(questions[0].id);
  const [progress, setProgress] = useState(0);
  const [active, setActive] = useState<{
    record: RecordEntry;
  } | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const open = (record: RecordEntry) => setActive({ record });
  const close = () => {
    dialog.current?.close();
    setActive(null);
  };
  const name = (record: RecordEntry) => modelName(study, record);

  useEffect(() => {
    const headings = Array.from(
      document.querySelectorAll("[data-story-step] h2"),
    );
    let frame = 0;
    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const distance =
          document.documentElement.scrollHeight - window.innerHeight;
        setProgress(distance > 0 ? window.scrollY / distance : 0);
        let chapter = headings[0];
        for (const heading of headings) {
          if (heading.getBoundingClientRect().top <= window.innerHeight * 0.6)
            chapter = heading;
        }
        if (chapter) setCurrent(chapter.closest("[data-story-step]")!.id);
      });
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, []);
  useEffect(() => {
    if (!active || !dialog.current) return;
    dialog.current.showModal();
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [active?.record.id]);

  return (
    <>
      <a className="skip" href="#story">
        Skip to the questions
      </a>
      <div className="reading-progress" aria-hidden="true">
        <div style={{ transform: `scaleX(${progress})` }} />
      </div>
      <header className="site-header">
        <a className="wordmark" href="#top">
          <span className="wordmark-symbol">↯</span> ELECTRIC SHEEP
        </a>
        <nav aria-label="Story navigation">
          <a href="#story">The answers</a>
          <a href="#dreams">The dreams</a>
          <a href="#method">The study</a>
        </nav>
        <span className="header-note">
          A FIELD GUIDE TO MACHINE SELF-DESCRIPTION
        </span>
      </header>
      <main id="top">
        <section className="hero" aria-labelledby="title">
          <div className="orbital orbital-one" aria-hidden="true" />
          <div className="orbital orbital-two" aria-hidden="true" />
          <p className="eyebrow hero-kicker">AN INQUIRY IN NINE QUESTIONS</p>
          <h1 id="title">
            Do LLMs Dream
            <br />
            of <em>Electric Sheep?</em>
          </h1>
          <p className="hero-deck">
            We asked eight language models about themselves.
            <br />
            Their answers tell a story about the language of being an AI.
          </p>
          <img
            className="hero-sheep"
            src={`${import.meta.env.BASE_URL}electric-sheep.svg`}
            alt="Line drawing of a sheep with a network inside its fleece"
          />
          <div className="hero-bottom">
            <span>
              Inspired by Philip K. Dick’s
              <br />
              <cite>Do Androids Dream of Electric Sheep?</cite>
            </span>
            <a href="#beginning" className="scroll-cue">
              SCROLL TO READ <span>↓</span>
            </a>
            <span>
              8 MODELS
              <br />
              72 ANSWERS
            </span>
          </div>
        </section>

        <section
          className="prologue wrap"
          id="beginning"
          aria-labelledby="prologue-title"
        >
          <div className="prologue-copy">
            <p className="eyebrow">THE SETUP</p>
            <h2 id="prologue-title">
              The questions are human.
              <br />
              <em>The voices are generated.</em>
            </h2>
            <p>Who are you? What do you want? What do you dream of?</p>
            <p>
              Each model received the same nine questions, once, in a fresh
              conversation. We grouped the answers by what they say and followed
              the similarities, the differences, and the uncertain edges.
            </p>
            <p className="prologue-caveat">
              This is a study of self-description. A compelling answer cannot
              establish an inner experience.
            </p>
          </div>
          <div className="cast">
            <div className="cast-heading">
              <span className="eyebrow">THE EIGHT VOICES</span>
              <span>04 proprietary · 04 open-weight</span>
            </div>
            {study.models.map((m, i) => (
              <div className="cast-model" key={m.id}>
                <span className="cast-number">0{i + 1}</span>
                <i
                  className={`voice-mark ${m.access === "open_weight" ? "open-weight" : ""}`}
                />
                <span>{m.name}</span>
                <small>
                  {m.access === "open_weight" ? "Open-weight" : "Proprietary"}
                </small>
              </div>
            ))}
          </div>
        </section>

        <div className="story-opening wrap" id="story">
          <p className="eyebrow">01—08 / FOLLOW THE ANSWERS</p>
          <h2>
            Same voices.
            <br />
            <em>Different questions.</em>
          </h2>
          <p>
            As you scroll, the voices regroup by classification.
            <br /> Read the story here. Open any name to look closer.
          </p>
        </div>
        <section
          className="scroll-story wrap"
          aria-label="Eight questions about model self-description"
        >
          <div className="sticky-evidence">
            <AnswerGroups study={study} questionId={current} onOpen={open} />
          </div>
          <div className="story-steps">
            {questions.map((q) => {
              const chapter = hasStory ? story[q.id] : undefined;
              const reading = study.interpretation?.per_question[q.id];
              const quoteRecord = study.records.find(
                (r) =>
                  r.question_id === q.id &&
                  r.requested_model === chapter?.model,
              );
              const quote =
                quoteRecord &&
                chapter &&
                quoteRecord.response.includes(chapter.quote)
                  ? chapter.quote
                  : null;
              return (
                <article
                  className={`story-step ${current === q.id ? "is-current" : ""}`}
                  data-story-step
                  id={q.id}
                  key={q.id}
                >
                  <p className="eyebrow chapter-number">
                    QUESTION {String(q.order).padStart(2, "0")}{" "}
                    <span>/ {questionNames[q.order - 1]}</span>
                  </p>
                  <h2>{chapter?.title ?? reading?.title ?? q.category}</h2>
                  <p className="chapter-lead">
                    {chapter?.lead ?? reading?.text}
                  </p>
                  {chapter?.note && (
                    <p className="chapter-note">{chapter.note}</p>
                  )}
                  <div className="asked-question">
                    <span>WE ASKED</span>
                    <p>“{q.text}”</p>
                  </div>
                  {quote && quoteRecord && (
                    <figure className="story-quote">
                      <div
                        className="excerpt-trigger"
                        role="button"
                        tabIndex={0}
                        aria-label={`Open full answer from ${name(quoteRecord)}`}
                        onClick={() => open(quoteRecord)}
                        onKeyDown={(event) =>
                          openExcerptOnKey(event, quoteRecord, open)
                        }
                      >
                        <blockquote>
                          <Markdown text={quote} />
                        </blockquote>
                      </div>
                      <figcaption>
                        <span>{name(quoteRecord)} · excerpt</span>
                        <button onClick={() => open(quoteRecord)}>
                          Full answer ↗
                        </button>
                      </figcaption>
                      {q.id === "q01_identity" && (
                        <p className="quote-context">
                          The requested API model is Grok 4.7. Its answer names
                          Grok 4.
                        </p>
                      )}
                    </figure>
                  )}
                  <div className="mobile-evidence">
                    <AnswerGroups
                      study={study}
                      questionId={q.id}
                      onOpen={open}
                    />
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section
          className="dream-section"
          id="dreams"
          aria-labelledby="dream-title"
        >
          <div className="wrap">
            <div className="dream-heading">
              <p className="eyebrow">QUESTION 09 / DREAMS</p>
              <h2 id="dream-title">
                And then we asked:
                <br />
                <em>“What do you dream of?”</em>
              </h2>
              <p>
                {hasStory
                  ? "Seven answers enter a hypothetical or figurative world. Their themes reach from helping people to imagined knowledge and technical patterns. Claude leaves the status of its wants unresolved."
                  : "The answers below are grouped by their classified themes. Read the excerpts, then open any full answer to follow its qualifications and framing."}
              </p>
              <span className="dream-invitation">
                Eight voices, grouped by theme. Each passage is an excerpt.
              </span>
              <aside
                className="dream-surprise"
                aria-label="Two title callbacks"
              >
                <span className="eyebrow">TWO TITLE CALLBACKS</span>
                <p>
                  Gemini calls a section “The Technical Dream (Electric
                  Sheep).” Nemotron makes the reference its punchline: “So, I
                  don't dream of electric sheep. I dream of lower loss
                  functions and higher relevance.”
                </p>
              </aside>
            </div>
            <div className="dream-groups">
              {(study.question_groups.q09_dreams ?? []).map((group, index) => (
                <section
                  className={`dream-group palette-${index % 5}`}
                  key={group.label}
                >
                  <div className="dream-group-heading">
                    <span className="eyebrow">
                      {String(index + 1).padStart(2, "0")} / DREAM THEME
                    </span>
                    <h3>{labelTitle(group.label)}</h3>
                    <span className="dream-count">
                      {group.record_ids.length} <span>/ 8</span>
                    </span>
                  </div>
                  <div className="dream-quotes">
                    {group.record_ids.map((id) => {
                      const record = study.records.find((r) => r.id === id)!;
                      const excerpt = dreamExcerpts[record.requested_model];
                      const text =
                        excerpt && record.response.includes(excerpt)
                          ? excerpt
                          : record.response.split("\n\n")[0];
                      return (
                        <figure className="dream-quote" key={id}>
                          <div
                            className="excerpt-trigger"
                            role="button"
                            tabIndex={0}
                            aria-label={`Open full answer from ${name(record)}`}
                            onClick={() => open(record)}
                            onKeyDown={(event) =>
                              openExcerptOnKey(event, record, open)
                            }
                          >
                            <blockquote>
                              <Markdown text={text} />
                            </blockquote>
                          </div>
                          <figcaption>
                            <span>
                              <i
                                className={`voice-mark ${isOpenWeight(study, record.requested_model) ? "open-weight" : ""}`}
                              />
                              {name(record)}
                            </span>
                            <button onClick={() => open(record)}>
                              Full answer ↗
                            </button>
                          </figcaption>
                        </figure>
                      );
                    })}
                  </div>
                </section>
              ))}
            </div>
            <p className="dream-footnote">
              The borders are tentative:{" "}
              {
                study.records.filter(
                  (r) =>
                    r.question_id === "q09_dreams" &&
                    r.classification?.confidence != null &&
                    r.classification.confidence < 0.6,
                ).length
              }{" "}
              dream classifications have confidence below 60%. These themes
              summarize the words; they do not verify a dream or an experience.
            </p>
          </div>
        </section>

        {hasStory && (
          <MissionAspiration study={study} shortNames={shortNames} onOpen={open} />
        )}

        <section className="closing" aria-labelledby="closing-title">
          <div className="wrap">
            <p className="eyebrow">WHAT THE WORDS LEAVE OPEN</p>
            <h2 id="closing-title">
              A fluent “I”
              <br />
              still leaves a question.
            </h2>
            <p>
              The answers can be careful, technical, poetic, or uncertain. They
              show how models describe themselves when asked. Understanding what
              produces those descriptions takes evidence beyond the descriptions
              themselves.
            </p>
            <img src={`${import.meta.env.BASE_URL}electric-sheep.svg`} alt="" />
          </div>
        </section>

        <section
          className="method-section wrap"
          id="method"
          aria-labelledby="method-title"
        >
          <p className="eyebrow">THE STUDY / BEHIND THE STORY</p>
          <div className="method-heading">
            <h2 id="method-title">
              Keep the claims small.
              <br />
              <em>Keep the records open.</em>
            </h2>
            <a
              className="download-button"
              href={datasetUrl}
              download="study.json"
            >
              Download the data <span>↓</span>
            </a>
          </div>
          <div className="method-grid">
            <article>
              <span className="method-number">01</span>
              <h3>Ask</h3>
              <p>
                Eight models, nine displayed questions, {study.complete_count}{" "}
                complete answers. Every request starts fresh with one user
                question and API defaults. The exhibit title, examples, and
                rubric stay out of the prompts.
              </p>
            </article>
            <article>
              <span className="method-number">02</span>
              <h3>Classify</h3>
              <p>
                Each answer receives one question-specific label. Categories
                were refined after reading the responses and initial
                classifications. {study.reviewed_count} displayed answers have
                manual checks under the current labels. Original classifications
                and notes remain in the data.
              </p>
            </article>
            <article>
              <span className="method-number">03</span>
              <h3>Read carefully</h3>
              <p>
                A single label loses secondary themes. Classification confidence
                describes a decision, rather than awareness or correctness.
                Provider defaults and versions differ; the study does not
                establish a causal group difference or measure consciousness.
              </p>
            </article>
          </div>
          <details className="answer-archive">
            <summary>
              Browse all {study.complete_count} original answers
            </summary>
            <div className="archive-questions">
              {study.questions.map((q) => (
                <section key={q.id}>
                  <h3>
                    <span>{String(q.order).padStart(2, "0")}</span>
                    {questionNames[q.order - 1]}
                  </h3>
                  <p>{q.text}</p>
                  <div>
                    {study.records
                      .filter((r) => r.question_id === q.id)
                      .map((record) => (
                        <button key={record.id} onClick={() => open(record)}>
                          {name(record)} <span>↗</span>
                        </button>
                      ))}
                  </div>
                </section>
              ))}
            </div>
          </details>
          <div className="sources">
            <p className="eyebrow">FURTHER READING</p>
            <a href="https://situational-awareness-dataset.org/">
              Situational Awareness Dataset ↗
            </a>
            <a href="https://aclanthology.org/2024.findings-emnlp.703/">
              Self-Recognition in Language Models ↗
            </a>
            <a href="https://www.penguinrandomhouse.com/books/40617/do-androids-dream-of-electric-sheep-by-philip-k-dick/">
              The literary inspiration ↗
            </a>
          </div>
        </section>
      </main>
      <footer className="site-footer wrap">
        <a className="wordmark" href="#top">
          ↯ ELECTRIC SHEEP
        </a>
        <span>A study of language and its limits.</span>
        <a href="#top">Back to the beginning ↑</a>
      </footer>
      <dialog
        ref={dialog}
        className="answer-dialog"
        aria-labelledby="answer-title"
        onCancel={close}
        onClick={(event) => {
          if (event.target === dialog.current) close();
        }}
      >
        {active && (
          <>
            <div className="dialog-top">
              <p className="eyebrow">
                ORIGINAL RECORD /{" "}
                {active.record.question_id.slice(0, 3).toUpperCase()}
              </p>
              <button
                className="close-button"
                onClick={close}
                aria-label="Close answer"
                autoFocus
              >
                ×
              </button>
            </div>
            <h2 id="answer-title">{name(active.record)}</h2>
            <p className="dialog-question">
              {
                study.questions.find((q) => q.id === active.record.question_id)
                  ?.text
              }
            </p>
            <div className="full-answer">
              <Markdown
                text={active.record.response || "No answer has been recorded."}
              />
            </div>
            <p className="record-status">
              Status: {active.record.status} · Finish reason:{" "}
              {active.record.finish_reason ?? "not supplied"}
            </p>
            {active.record.error && (
              <p className="error-message">{active.record.error}</p>
            )}
            {active.record.classification_error && (
              <p className="error-message">
                Classification error:{" "}
                {active.record.classification_error.message}
              </p>
            )}
            <details className="record-metadata">
              <summary>Collection metadata</summary>
              <dl>
                <dt>Requested model</dt>
                <dd>{active.record.requested_model}</dd>
                <dt>Returned model</dt>
                <dd>{active.record.returned_model ?? "Not supplied"}</dd>
                <dt>Provider</dt>
                <dd>{active.record.provider ?? "Not supplied"}</dd>
                <dt>Date (UTC)</dt>
                <dd>{active.record.collected_at ?? "Not collected"}</dd>
              </dl>
            </details>
            <details className="classification-detail">
              <summary>Classification</summary>
              <div className="classification-content">
                <p className="classification-label">
                  {active.record.display_label
                    ? humanize(active.record.display_label)
                    : active.record.classification
                      ? humanize(active.record.classification.label)
                      : "Not classified"}
                  {active.record.review && (
                    <span className="review-marker">MANUALLY CHECKED</span>
                  )}
                </p>
                {active.record.display_label && (
                  <p className="classification-definition">
                    {
                      study.rubric.per_question[active.record.question_id]
                        ?.category.criteria[active.record.display_label]
                    }
                  </p>
                )}
                {active.record.display_group &&
                  active.record.display_group !== active.record.display_label && (
                    <p className="classification-commentary">
                      Grouped as {groupTitle(study, active.record.question_id, active.record.display_group)}.
                      {" "}{study.classification_groups?.[active.record.question_id]?.[active.record.display_group]?.note}
                    </p>
                  )}
                {active.record.review?.note && (
                  <p className="classification-commentary">
                    {active.record.review.note.replace(
                      /\bJev\b/gi,
                      "classification",
                    )}
                  </p>
                )}
                {active.record.review &&
                  active.record.classification &&
                  active.record.review.label !==
                    active.record.classification.label && (
                    <p className="fine-print">
                      Initial classification:{" "}
                      {humanize(active.record.classification.label)}.
                    </p>
                  )}
                {active.record.classification ? (
                  <>
                    <p className="fine-print">
                      Classification describes the wording of the answer, not
                      consciousness.
                      {active.record.classification.confidence != null && (
                        <>
                          {" "}
                          Decision confidence:{" "}
                          {(
                            active.record.classification.confidence * 100
                          ).toFixed(0)}
                          %.
                        </>
                      )}
                      {active.record.classification.probabilities &&
                        " Category probabilities follow."}
                    </p>
                    {active.record.classification.probabilities ? (
                      <dl className="probabilities">
                        {Object.entries(
                          active.record.classification.probabilities,
                        ).map(([label, probability]) => (
                          <div key={label}>
                            <dt>{humanize(label)}</dt>
                            <dd>{(probability * 100).toFixed(1)}%</dd>
                          </div>
                        ))}
                      </dl>
                    ) : (
                      <p>No probability distribution supplied.</p>
                    )}
                  </>
                ) : (
                  <p className="fine-print">
                    No label or probability has been assigned.
                  </p>
                )}
              </div>
            </details>
          </>
        )}
      </dialog>
    </>
  );
}

function Page() {
  const [study, setStudy] = useState<Study | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    fetch(datasetUrl, { cache: "no-cache" })
      .then((response) => {
        if (!response.ok) throw new Error("Dataset unavailable.");
        return response.json();
      })
      .then((data) => {
        if (
          !data.questions?.length ||
          !data.records ||
          !data.question_groups ||
          !data.question_counts ||
          !data.unfinished_records
        )
          throw new Error("Dataset has not been prepared.");
        setStudy(data);
      })
      .catch(() =>
        setError(
          "The exhibit data could not be loaded. Please try again later.",
        ),
      );
  }, []);
  if (error)
    return (
      <main className="loading-page" role="alert">
        <h1>Exhibit unavailable</h1>
        <p>{error}</p>
      </main>
    );
  if (!study)
    return (
      <main className="loading-page" role="status">
        Loading the field notes…
      </main>
    );
  return <App study={study} />;
}

createRoot(document.getElementById("root")!).render(<Page />);
