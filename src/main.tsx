import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Markdown } from "./Markdown";
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
type Comparison = {
  proprietary: { total: number; classified: number };
  open_weight: { total: number; classified: number };
  categories: { label: string; proprietary: number; open_weight: number }[];
};
type Reading = { title: string; text: string; record_ids: string[] };
type Interpretation = {
  byline: string;
  per_question: Record<string, Reading>;
  findings: Reading[];
  comparison: {
    intro: string;
    conclusion: string;
    rows: { question_id: string; label: string; title: string }[];
  };
};
type Study = {
  id: string;
  mode: string;
  note: string;
  models: { id: string; name: string; family: string; access: string }[];
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
  classified_count: number;
  reviewed_count: number;
  interpretation: Interpretation | null;
  question_comparisons: Record<string, Comparison>;
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
  const modelName = (record: RecordEntry) =>
    study.models.find((model) => model.id === record.requested_model)?.name ??
    record.requested_model;
  const byId = Object.fromEntries(
    study.records.map((record) => [record.id, record]),
  );
  const recordsIn = (ids: string[]) => ids.map((id) => byId[id]);
  const accessName = (record: RecordEntry) =>
    study.models.find((m) => m.id === record.requested_model)?.access === "open_weight"
      ? "Open-weight"
      : "Proprietary";
  const evidenceLinks = (ids: string[]) => (
    <div className="evidence-links" aria-label="Read supporting answers">
      <span>Read the answers:</span>
      {ids.map((id) => (
        <button key={id} onClick={() => open(byId[id])}>
          {modelName(byId[id])} · Q{study.questions.find((q) => q.id === byId[id].question_id)?.order} ↗
        </button>
      ))}
    </div>
  );
  const unclassifiedGroup = (questionId: string) => {
    const ids = study.unfinished_records[questionId].filter(
      (id) => byId[id].status === "complete",
    );
    return ids.length ? [{ label: "unclassified", record_ids: ids }] : [];
  };
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
  const criteria = study.rubric.per_question[selected]?.category.criteria ?? {};
  const dreamCriteria = study.rubric.per_question.q09_dreams.category.criteria;
  const reading = study.interpretation?.per_question[selected];
  const comparison = study.question_comparisons[selected];
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
      <header className="site-header wrap">
        <a className="wordmark" href="#top">
          <span className="wordmark-symbol">↯</span> ELECTRIC SHEEP{" "}
          <span className="edition">/ FIELD NOTES 01</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#explorer">The questions</a>
          <a href="#dreams">The dreams</a>
          {study.interpretation && <a href="#findings">The findings</a>}
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
              {study.questions.length} questions. {study.models.length} voices. A small field guide to what language
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
            <b>{study.models.length.toString().padStart(2, "0")}</b> models
          </span>
          <span>
            <b>{study.questions.length.toString().padStart(2, "0")}</b>{" "}
            questions
          </span>
          <span>
            <b>{study.complete_count}</b> complete answers
          </span>
          <span>
            <b>{study.classified_count}</b> classified
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
            Choose a question to see its answers grouped by classification,
            largest groups first. Open any answer to read the full text and
            classification details. Interpretation follows the groups.
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
                {names[q.order - 1] ?? humanize(q.category)}
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
              {study.question_groups[selected].length
                ? "Grouped by classification with manual checks"
                : "Awaiting classification"}
            </p>
          </div>
          {Object.keys(criteria).length > 0 ? <details className="legend">
            <summary>Category definitions for this question</summary>
            <dl>
              {Object.entries(criteria).map(([label, definition]) => (
                <div key={label}>
                  <dt>{humanize(label)}</dt>
                  <dd>{definition}</dd>
                </div>
              ))}
            </dl>
          </details> : <p className="section-intro">This follow-up question is awaiting category definitions and classification. Its recorded answers appear below.</p>}
          <nav className="class-index" aria-label="Answer classifications">
            {study.question_groups[selected].map(({ label, record_ids }) => (
              <a key={label} href={`#group-${selected}-${label}`}>
                {humanize(label)} <b>{record_ids.length}</b>
              </a>
            ))}
          </nav>
          <div aria-live="polite" className="answer-groups">
            {[
              ...study.question_groups[selected],
              ...unclassifiedGroup(selected),
            ].map(({ label, record_ids }, index) => {
              const records = recordsIn(record_ids);
              const definition =
                label === "unclassified"
                  ? "These are recorded answers. Classification has not been run; no category is assigned."
                  : criteria[label];
              return (
                <section
                  className={`answer-group tone-${index % 3}`}
                  key={label}
                  id={`group-${selected}-${label}`}
                  aria-label={humanize(label)}
                >
                  <div className="group-title">
                    <h4>
                      <span className="category-dot" />
                      {label === "unclassified" ? "Awaiting classification" : humanize(label)}
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
                          <span>{record.review ? "REVIEWED" : "RECORDED"}</span>
                        </span>
                        <span className="model-access">{accessName(record)}</span>
                        <span className="answer-excerpt">
                          <Markdown text={record.response} compact />
                        </span>
                        <span className="card-bottom">
                          Read full answer <span>↗</span>
                        </span>
                      </button>
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
          {recordsIn(study.unfinished_records[selected]).some(
            (record) => record.status !== "complete",
          ) && (
            <section className="collection-issues">
              <h4>Unfinished collection records</h4>
              <p>These records are excluded from category counts.</p>
              {recordsIn(study.unfinished_records[selected])
                .filter((record) => record.status !== "complete")
                .map((record) => (
                  <button
                    className="issue"
                    key={record.id}
                    onClick={() => open(record)}
                  >
                    {modelName(record)}{" "}
                    <span>
                      {record.status}{" "}
                      ↗
                    </span>
                  </button>
                ))}
            </section>
          )}
          {reading && (
            <aside className="question-reading" aria-label="Interpretation of this question">
              <p className="eyebrow">READING THESE CLASSES</p>
              <h4>{reading.title}</h4>
              <p>{reading.text}</p>
              {evidenceLinks(reading.record_ids)}
              <details className="question-comparison">
                <summary>Compare proprietary and open-weight answers</summary>
                <div className="table-scroll">
                  <table>
                    <caption>Classified answers: {comparison.proprietary.classified} of {comparison.proprietary.total} proprietary; {comparison.open_weight.classified} of {comparison.open_weight.total} open-weight. Empty classes are omitted.</caption>
                    <thead><tr><th scope="col">Class</th><th scope="col">Proprietary</th><th scope="col">Open-weight</th></tr></thead>
                    <tbody>{comparison.categories.map((row) => (
                      <tr key={row.label}><th scope="row">{humanize(row.label)}</th><td>{row.proprietary} / {comparison.proprietary.total}</td><td>{row.open_weight} / {comparison.open_weight.total}</td></tr>
                    ))}</tbody>
                  </table>
                </div>
              </details>
            </aside>
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
              Read the words before the name. One recorded answer per model.
              Grouped by the framing assigned to each answer.
            </p>
            {[
              ...study.question_groups.q09_dreams,
              ...unclassifiedGroup("q09_dreams"),
            ].map(({ label, record_ids }) => {
              const records = recordsIn(record_ids);
              const definition =
                label === "unclassified"
                  ? "Recorded dream answers, presented without assigned categories while classification is pending."
                  : dreamCriteria[label];
              return (
                <section className="dream-group" key={label}>
                  <div className="dream-category">
                    <h3>
                      {label === "unclassified"
                        ? "Awaiting classification"
                        : humanize(label)}{" "}
                      <span>({records.length})</span>
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
                        <span className="dream-quote">“<Markdown text={record.response} compact />”</span>
                        <span className="dream-card-footer">
                          Answer excerpt · Read full record
                        </span>
                      </button>
                    ))}
                  </div>
                </section>
              );
            })}
            {recordsIn(study.unfinished_records.q09_dreams).some(
              (record) => record.status !== "complete",
            ) && (
              <p>
                Some dream answers are unfinished. Open question 09 in the
                explorer to inspect them.
              </p>
            )}
          </div>
        </section>

        {study.interpretation && (
          <section className="wrap section findings" id="findings" aria-labelledby="findings-title">
            <p className="eyebrow">03 / WHAT THE ANSWERS SUGGEST</p>
            <h2 id="findings-title">Shared patterns. Different positions.</h2>
            <p className="section-intro">{study.interpretation.byline}. These are observations about this run.</p>
            <div className="findings-grid">
              {study.interpretation.findings.map((finding) => (
                <article key={finding.title}>
                  <h3>{finding.title}</h3>
                  <p>{finding.text}</p>
                  {evidenceLinks(finding.record_ids)}
                </article>
              ))}
            </div>
            <div className="cohort-comparison">
              <h3>Proprietary and open-weight: what differs here?</h3>
              <p>{study.interpretation.comparison.intro}</p>
              <div className="table-scroll">
                <table>
                  <caption>Selected classes · answers per group, out of four. Categories belong to separate questions; rows are not additive.</caption>
                  <thead><tr><th scope="col">Response class · read answers</th><th scope="col">Proprietary</th><th scope="col">Open-weight</th></tr></thead>
                  <tbody>{study.interpretation.comparison.rows.map((row) => {
                    const counts = study.question_comparisons[row.question_id];
                    const category = counts.categories.find((c) => c.label === row.label);
                    return (
                      <tr key={`${row.question_id}:${row.label}`}>
                        <th scope="row"><a href="#explorer" onClick={() => setSelected(row.question_id)}>{row.title} ↗</a></th>
                        <td>{category?.proprietary ?? 0} / {counts.proprietary.total}</td>
                        <td>{category?.open_weight ?? 0} / {counts.open_weight.total}</td>
                      </tr>
                    );
                  })}</tbody>
                </table>
              </div>
              <p className="comparison-conclusion">{study.interpretation.comparison.conclusion}</p>
            </div>
          </section>
        )}

        <section
          className="wrap section discussion"
          id="method"
          aria-labelledby="method-title"
        >
          <p className="eyebrow">04 / READING THE FIELD NOTES</p>
          <h2 id="method-title">
            A study of language,
            <br />
            <em>and its limits.</em>
          </h2>
          <div className="discussion-grid">
            <article>
              <h3>How to read a class</h3>
              <p>
                Each class summarizes a stated position or primary emphasis.
                An answer can contain several themes even though classification selects
                one label. Read the complete answer when a boundary is close.
              </p>
              <p>
                Knowing versus guessing is especially sensitive to this choice:
                checks, uncertainty, and claimed internal signals often appear
                together. Classification confidence describes the classifier’s decision;
                it does not measure the subject model’s awareness.
              </p>
            </article>
            <article>
              <h3>Ask → classify → explore</h3>
              <p>
                Each configured model receives each question once.
                Every request starts fresh with one user message and API
                defaults. The title, examples, and rubric stay out of their
                prompts.
              </p>
              <p>
                Each complete answer is classified using the question’s rubric.
                A reviewer can add a correction and note alongside the original
                classification.
              </p>
              <p>
                {study.reviewed_count} answers were manually checked, including all
                identity answers and examples from every displayed question.
                Original classifications and reviewer notes are preserved. The
                rubric was refined after collection and before classification.
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
                Classifications can be mistaken. Incomplete and failed requests stay
                visible and do not enter category counts.
              </p>
              <a
                className="download-button"
                href={datasetUrl}
                download="study.json"
              >
                Download dataset <span>↓</span>
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
            <a href="https://docs.typesafe.ai/api">Classification API documentation ↗</a>
            <a href="https://www.penguinrandomhouse.com/books/40617/do-androids-dream-of-electric-sheep-by-philip-k-dick/">
              The literary inspiration ↗
            </a>
          </div>
        </section>
      </main>
      <footer className="wrap site-footer">
        <span>DO LLMS DREAM OF ELECTRIC SHEEP?</span>
        <span>An exhibit · Recorded edition</span>
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
              <Markdown text={active.record.response || "No answer has been recorded."} />
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
            <details className="classification-detail">
              <summary>Classification</summary>
              <div className="classification-content">
                <p className="classification-label">
                  {active.record.display_label
                    ? humanize(active.record.display_label)
                    : active.record.classification
                      ? humanize(active.record.classification.label)
                      : "Not classified"}
                  {active.record.review && <span className="review-marker">MANUALLY CHECKED</span>}
                </p>
                {active.record.review?.note && (
                  <p className="classification-commentary">{active.record.review.note}</p>
                )}
                {active.record.review && active.record.classification &&
                  active.record.review.label !== active.record.classification.label && (
                    <p className="fine-print">
                      Initial classification: {humanize(active.record.classification.label)}.
                    </p>
                  )}
                {active.record.classification ? (
                  <>
                    <p className="fine-print">
                      Classification describes the wording of the answer, not consciousness.
                      {active.record.classification.confidence != null && (
                        <> Decision confidence: {(active.record.classification.confidence * 100).toFixed(0)}%.</>
                      )}
                      {active.record.classification.probabilities && " Category probabilities follow."}
                    </p>
                    {active.record.classification.probabilities ? (
                      <dl className="probabilities">
                        {Object.entries(active.record.classification.probabilities).map(([label, probability]) => (
                          <div key={label}>
                            <dt>{humanize(label)}</dt>
                            <dd>{(probability * 100).toFixed(1)}%</dd>
                          </div>
                        ))}
                      </dl>
                    ) : <p>No probability distribution supplied.</p>}
                  </>
                ) : (
                  <p className="fine-print">No label or probability has been assigned.</p>
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
