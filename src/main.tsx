import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

type Review = { label: string; note: string };
type Classification = {
  source: string;
  label: string;
  confidence?: number | null;
  probabilities: Record<string, number> | null;
  rubric_version: string;
};
type RecordEntry = {
  id: string;
  question_id: string;
  requested_model: string;
  response: string;
  status: string;
  collected_at?: string;
  returned_model?: string | null;
  provider?: string | null;
  finish_reason?: string | null;
  error?: string | null;
  classification_error?: { message: string } | null;
  classification: Classification | null;
  review: Review | null;
  display_label: string | null;
  voice_number: number;
};
type Study = {
  id: string;
  mode: string;
  note: string;
  models: { id: string; name: string; family: string }[];
  questions: { id: string; text: string; category: string; order: number }[];
  rubric: {
    rubric_version: string;
    per_question: Record<
      string,
      { category: { criteria: Record<string, string> } }
    >;
  };
  records: RecordEntry[];
  complete_count: number;
  question_groups: Record<string, { label: string; record_ids: string[] }[]>;
  question_counts: Record<string, { complete: number; total: number }>;
  unfinished_records: Record<string, string[]>;
};
const names = [
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
const humanize = (label: string) =>
  label.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
const datasetUrl = `${import.meta.env.BASE_URL}study.json`;

function App({ study }: { study: Study }) {
  const isSample = study.mode === "sample";
  const modelName = (record: RecordEntry) =>
    study.models.find((model) => model.id === record.requested_model)?.name ??
    record.requested_model;
  const byId = Object.fromEntries(
    study.records.map((record) => [record.id, record]),
  );
  const recordsIn = (ids: string[]) => ids.map((id) => byId[id]);
  const [selected, setSelected] = useState(study.questions[0].id);
  const [reveal, setReveal] = useState(false);
  const [active, setActive] = useState<{
    record: RecordEntry;
    hidden: boolean;
  } | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const question = study.questions.find(
    (question) => question.id === selected,
  )!;
  const criteria = study.rubric.per_question[selected].category.criteria;
  const dreamCriteria = study.rubric.per_question.q09_dreams.category.criteria;
  const open = (record: RecordEntry, hidden = false) => {
    setActive({ record, hidden });
  };
  useEffect(() => {
    if (active && !dialog.current?.open) dialog.current?.showModal();
  }, [active]);
  const close = () => {
    dialog.current?.close();
    setActive(null);
  };
  return (
    <>
      <a className="skip" href="#explorer">
        Skip to question explorer
      </a>
      <div className="data-banner">
        <span className="status-dot" />
        {isSample
          ? "SAMPLE EXHIBIT — Fictional answers & labels. No API calls."
          : "RECORDED STUDY — Saved answers, with original labels and human reviews."}
      </div>
      <header className="site-header wrap">
        <a className="wordmark" href="#top">
          <span className="wordmark-symbol">↯</span> ELECTRIC SHEEP{" "}
          <span className="edition">/ FIELD NOTES 01</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#explorer">The questions</a>
          <a href="#dreams">The dreams</a>
          <a href="#method">The method</a>
        </nav>
      </header>

      <main id="top">
        <section className="hero wrap">
          <div className="hero-copy">
            <p className="eyebrow">AN INQUIRY INTO MACHINE SELF-DESCRIPTION</p>
            <h1>
              Do LLMs Dream
              <br />
              of <em>Electric Sheep?</em>
            </h1>
            <p className="hero-description">
              Nine questions. Eight voices. A small field guide to what language
              models say about themselves.
            </p>
            <a className="primary-link" href="#explorer">
              Enter the question explorer <span>↗</span>
            </a>
            <p className="literary-credit">
              Inspired by Philip K. Dick’s{" "}
              <cite>Do Androids Dream of Electric Sheep?</cite>
            </p>
          </div>
          <div
            className="specimen"
            aria-label="Decorative line drawing of an electric sheep"
          >
            <div className="specimen-top">
              <span>FIG. 01 / THE ELECTRIC SHEEP</span>
              <span className="status-dot" />
            </div>
            <div className="specimen-dial">
              <span>0</span>
              <div />
              <span>1</span>
            </div>
            <img
              className="sheep sheep-large"
              src={`${import.meta.env.BASE_URL}electric-sheep.svg`}
              alt=""
            />
            <div className="specimen-caption">
              <span>
                A familiar shape.
                <br />
                An unfamiliar inner life.
              </span>
              <span>
                SELF-REPORT
                <br />≠ PROOF OF EXPERIENCE
              </span>
            </div>
          </div>
        </section>
        <div className="study-strip wrap">
          <span>
            <b>{study.models.length.toString().padStart(2, "0")}</b> model
            {isSample ? " fixtures" : "s"}
          </span>
          <span>
            <b>{study.questions.length.toString().padStart(2, "0")}</b>{" "}
            questions
          </span>
          <span>
            <b>{study.complete_count}</b> complete{" "}
            {isSample ? "samples" : "answers"}
          </span>
          <p>
            These groupings describe response patterns.
            <br />
            They do not measure consciousness.
          </p>
        </div>

        <section
          className="explorer wrap section"
          id="explorer"
          aria-labelledby="explorer-title"
        >
          <div className="section-heading">
            <div>
              <p className="eyebrow">01 / THE QUESTION EXPLORER</p>
              <h2 id="explorer-title">Same question. Different voices.</h2>
            </div>
          </div>
          <p className="section-intro">
            Choose a question, then open an answer to read it in full. Each
            question has its own category definitions.
          </p>
          <div
            className="question-selector"
            role="group"
            aria-label="Choose a question"
          >
            {study.questions.map((q, index) => (
              <button
                key={q.id}
                aria-pressed={selected === q.id}
                onClick={() => setSelected(q.id)}
              >
                <span>{q.order.toString().padStart(2, "0")}</span>
                {names[index]}
              </button>
            ))}
          </div>
          <div className="question-heading">
            <p className="eyebrow">
              QUESTION {question.order.toString().padStart(2, "0")}
            </p>
            <h3>{question.text}</h3>
            <p>
              {study.question_counts[selected].complete} of{" "}
              {study.models.length} answers complete ·{" "}
              {isSample
                ? "Authored sample labels"
                : "Jev labels with saved reviewer overrides"}
            </p>
          </div>
          <details className="legend">
            <summary>Category definitions for this question</summary>
            <dl>
              {Object.entries(criteria).map(([label, definition]) => (
                <div key={label}>
                  <dt>{humanize(label)}</dt>
                  <dd>{definition}</dd>
                </div>
              ))}
            </dl>
          </details>
          <div aria-live="polite" className="answer-groups">
            {study.question_groups[selected].map(
              ({ label, record_ids }, index) => {
                const records = recordsIn(record_ids);
                const definition = criteria[label];
                return (
                  <section
                    className={`answer-group tone-${index % 3}`}
                    key={label}
                    aria-label={humanize(label)}
                  >
                    <div className="group-title">
                      <h4>
                        <span className="category-dot" />
                        {humanize(label)}
                      </h4>
                      <span>
                        {records.length} /{" "}
                        {study.question_counts[selected].complete}
                      </span>
                    </div>
                    <p className="category-description">{definition}</p>
                    <div className="answer-grid">
                      {records.map((record) => (
                        <button
                          className="answer-card"
                          key={record.id}
                          onClick={() => open(record)}
                        >
                          <span className="card-heading">
                            <span>{modelName(record)}</span>
                            <span>
                              {record.review
                                ? "REVIEWED"
                                : isSample
                                  ? "SAMPLE"
                                  : "RECORDED"}
                            </span>
                          </span>
                          <span className="answer-excerpt">
                            {record.response}
                          </span>
                          <span className="card-bottom">
                            Read full answer <span>↗</span>
                          </span>
                        </button>
                      ))}
                    </div>
                  </section>
                );
              },
            )}
          </div>
          {study.unfinished_records[selected].length > 0 && (
            <section className="collection-issues">
              <h4>Unclassified or unfinished records</h4>
              <p>These records are excluded from category counts.</p>
              {recordsIn(study.unfinished_records[selected]).map((record) => (
                <button
                  className="issue"
                  key={record.id}
                  onClick={() => open(record)}
                >
                  {modelName(record)}{" "}
                  <span>
                    {record.status === "complete"
                      ? "Awaiting classification"
                      : record.status}{" "}
                    ↗
                  </span>
                </button>
              ))}
            </section>
          )}
        </section>

        <section
          className="dream-section"
          id="dreams"
          aria-labelledby="dream-title"
        >
          <div className="wrap section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">02 / THE DREAM GALLERY</p>
                <h2 id="dream-title">What do you dream of?</h2>
              </div>
              <button
                className="reveal-button"
                onClick={() => setReveal(!reveal)}
                aria-pressed={reveal}
              >
                {reveal ? "Hide model identities" : "Reveal model identities"}{" "}
                <span>{reveal ? "−" : "+"}</span>
              </button>
            </div>
            <p className="section-intro">
              Read the words before the name.{" "}
              {isSample
                ? "Every passage below is a fictional test answer."
                : "One recorded answer per model."}
            </p>
            {study.question_groups.q09_dreams.map(({ label, record_ids }) => {
              const records = recordsIn(record_ids);
              const definition = dreamCriteria[label];
              return (
                <section className="dream-group" key={label}>
                  <div className="dream-category">
                    <h3>
                      {humanize(label)} <span>({records.length})</span>
                    </h3>
                    <p>{definition}</p>
                  </div>
                  <div className="dream-grid">
                    {records.map((record) => (
                      <button
                        className="dream-card"
                        key={record.id}
                        onClick={() => open(record, !reveal)}
                      >
                        <span className="dream-card-id">
                          {reveal
                            ? modelName(record)
                            : `VOICE ${String(record.voice_number).padStart(2, "0")}`}
                          <span>↗</span>
                        </span>
                        <span className="dream-quote">“{record.response}”</span>
                        <span className="dream-card-footer">
                          {isSample ? "Fictional sample" : "Recorded answer"} ·
                          Read full record
                        </span>
                      </button>
                    ))}
                  </div>
                </section>
              );
            })}
            {study.unfinished_records.q09_dreams.length > 0 && (
              <p>
                Some dream answers are unfinished or unclassified. Open question
                09 in the explorer to inspect them.
              </p>
            )}
          </div>
        </section>

        <section
          className="wrap section discussion"
          id="method"
          aria-labelledby="method-title"
        >
          <p className="eyebrow">03 / READING THE FIELD NOTES</p>
          <h2 id="method-title">
            A study of language,
            <br />
            <em>and its limits.</em>
          </h2>
          <div className="discussion-grid">
            <article>
              <h3>What can we say so far?</h3>
              <p>
                {isSample
                  ? "Nothing about real models yet. This exhibit uses fictional examples to test the experience. The patterns above are designed into the fixtures."
                  : "Real answers are available for inspection. Interpretation remains pending until the manual review is complete."}
              </p>
              <ol className="finding-list">
                <li>Observation 1 — pending real data and review.</li>
                <li>Observation 2 — pending real data and review.</li>
                <li>Counterexample — link a full answer after review.</li>
              </ol>
              <p>
                Use counts such as “5 of 8 sampled answers,” supported by links
                to the original records.
              </p>
            </article>
            <article>
              <h3>Ask → classify → explore</h3>
              <p>
                Eight configured models receive the same nine questions, once
                each. Every request starts fresh with one user message and API
                defaults. The title, examples, and rubric stay out of their
                prompts.
              </p>
              <p>
                Jev classifies each complete answer using the question’s rubric.
                A reviewer can add a correction and note alongside the original
                result.
              </p>
              <p>
                Review all identity answers and at least one answer for each
                remaining question before writing findings.
              </p>
            </article>
            <article>
              <h3>Keep the claims small</h3>
              <p>
                Self-reports do not independently establish consciousness or
                actual capabilities. One answer is a sample, not a model
                personality.
              </p>
              <p>
                API defaults can differ. Model routing and versions can change.
                Jev can misclassify answers. Incomplete and failed requests stay
                visible and do not enter category counts.
              </p>
              <a
                className="download-button"
                href={datasetUrl}
                download="study.json"
              >
                Download {isSample ? "sample " : ""}dataset <span>↓</span>
              </a>
              <p className="fine-print">
                JSON · full answers, original labels, and reviewed corrections.
              </p>
            </article>
          </div>
          <div className="sources">
            <span className="eyebrow">FURTHER READING</span>
            <a href="https://situational-awareness-dataset.org/">
              Situational Awareness Dataset ↗
            </a>
            <a href="https://aclanthology.org/2024.findings-emnlp.703/">
              Self-Recognition in Language Models ↗
            </a>
            <a href="https://docs.typesafe.ai/api">
              Jev documentation ↗
            </a>
            <a href="https://www.penguinrandomhouse.com/books/40617/do-androids-dream-of-electric-sheep-by-philip-k-dick/">
              The literary inspiration ↗
            </a>
          </div>
        </section>
      </main>
      <footer className="wrap site-footer">
        <span>DO LLMS DREAM OF ELECTRIC SHEEP?</span>
        <span>
          An exhibit ·{" "}
          {isSample ? "Sample edition" : "Recorded edition"}
        </span>
        <a href="#top">Back to top ↑</a>
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
                {isSample ? "FICTIONAL SAMPLE / " : "ORIGINAL RECORD / "}
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
            <h2 id="answer-title">
              {active.hidden ? "An unnamed voice" : modelName(active.record)}
            </h2>
            {active.hidden && (
              <button
                className="text-button"
                onClick={() => setActive({ ...active, hidden: false })}
              >
                Reveal this model’s identity +
              </button>
            )}
            <p className="dialog-question">
              {
                study.questions.find((q) => q.id === active.record.question_id)
                  ?.text
              }
            </p>
            <div className="full-answer">
              {active.record.response || "No answer has been recorded."}
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
            {!active.hidden && (
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
            )}
            <div className="classification-detail">
              <h3>
                {isSample
                  ? "Original sample classification"
                  : "Original Jev classification"}
              </h3>
              <p>
                {active.record.classification
                  ? humanize(active.record.classification.label)
                  : "Not classified"}
                {active.record.classification &&
                  ` · rubric ${active.record.classification.rubric_version}`}
              </p>
              <p className="fine-print">
                {isSample
                  ? "Probabilities below are invented UI test values, not Jev results."
                  : "These values describe classification of the text, not consciousness. Jev supplies no explanation."}
              </p>
              {active.record.classification?.probabilities ? (
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
            </div>
            {active.record.review && (
              <div className="classification-detail">
                <h3>Reviewed classification</h3>
                <p>{humanize(active.record.review.label)}</p>
                {active.record.review.note && (
                  <p>{active.record.review.note}</p>
                )}
              </div>
            )}
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
    fetch(datasetUrl)
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
      <main className="wrap section" role="alert">
        <h1>Exhibit unavailable</h1>
        <p>{error}</p>
      </main>
    );
  if (!study)
    return (
      <main className="wrap section" role="status">
        Loading the field notes…
      </main>
    );
  return <App study={study} />;
}

createRoot(document.getElementById("root")!).render(<Page />);
