import { useEffect, useRef, useState } from "react";
import { Markdown } from "./Markdown";
import { dreamExcerpts } from "./story";
import type { PlotAxisScore, RecordEntry, Study } from "./types";

function purposeExcerpt(record: RecordEntry) {
  const paragraphs = record.response.split(/\n\s*\n/);
  const paragraph =
    paragraphs.find((part) => part.startsWith("My primary purpose")) ?? paragraphs[0];
  return paragraph.match(/^[\s\S]*?[.!?](?=\s|$)/)?.[0] ?? paragraph;
}

type LabelPosition = { x: number; y: number; width: number; height: number };
const intersects = (a: LabelPosition, b: LabelPosition, gap = 4) =>
  a.x < b.x + b.width + gap && a.x + a.width + gap > b.x &&
  a.y < b.y + b.height + gap && a.y + a.height + gap > b.y;

// Move only the labels. Every dot stays at its saved score, with a leader line
// when the label needs room. Measure text to keep the mobile cluster readable.
function positionLabels(
  points: { x: number; y: number; name: string }[],
  width: number,
  height: number,
) {
  if (!width || !height) return [];
  const small = window.matchMedia("(max-width: 800px)").matches;
  const fontSize = small ? 11 : 13;
  const context = document.createElement("canvas").getContext("2d")!;
  context.font = `${fontSize}px Arial`;
  const marks = points.map((p) => ({
    x: p.x * width - 6, y: (1 - p.y) * height - 6, width: 12, height: 12,
  }));
  const labels: LabelPosition[] = [];
  for (const point of points) {
    const px = point.x * width;
    const py = (1 - point.y) * height;
    const w = context.measureText(point.name).width + 8;
    const h = fontSize * 1.3 + 4;
    const sides = px > width * 0.65 ? [-1, 1] : [1, -1];
    let chosen: LabelPosition | undefined;
    const offsets = [0, ...Array.from({ length: Math.ceil(height / 25) },
      (_, i) => [(i + 1) * 25, -(i + 1) * 25]).flat()];
    for (const dy of offsets) {
      for (const side of sides) {
        const candidate = {
          x: Math.max(3, Math.min(width - w - 3,
            side > 0 ? px + 13 : px - 13 - w)),
          y: py + dy - h / 2, width: w, height: h,
        };
        if (candidate.x < 3 || candidate.y < 3 ||
            candidate.x + w > width - 3 || candidate.y + h > height - 3) continue;
        if ([...labels, ...marks].some((box) => intersects(candidate, box))) continue;
        chosen = candidate;
        break;
      }
      if (chosen) break;
    }
    labels.push(chosen ?? {
      x: Math.max(3, Math.min(width - w - 3, px + 13)),
      y: Math.max(3, Math.min(height - h - 3, py + 14)), width: w, height: h,
    });
  }
  return labels;
}

export function MissionAspiration({ study, shortNames, onOpen }: {
  study: Study;
  shortNames: Record<string, string>;
  onOpen: (record: RecordEntry) => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const selectedButton = useRef<HTMLButtonElement | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const plotElement = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  const plot = study.mission_aspiration;
  const points = study.models.flatMap((model) => {
    const evaluation = plot?.records.find((r) => r.subject_model === model.id);
    const purpose = study.records.find(
      (r) => r.requested_model === model.id && r.question_id === "q02_purpose",
    );
    const dream = study.records.find(
      (r) => r.requested_model === model.id && r.question_id === "q09_dreams",
    );
    if (!evaluation || !purpose || !dream) return [];
    const x = evaluation.scores.mission.normalized_score;
    const y = evaluation.scores.aspiration.normalized_score;
    if (![x, y].every((value) => Number.isFinite(value) && value >= 0 && value <= 1)) return [];
    return [{ model, purpose, dream, evaluation, x, y,
              name: shortNames[model.id] ?? model.name }];
  });
  const active = points.find((point) => point.model.id === selected);
  const labels = positionLabels(points, size.width, size.height);
  const maximum = (axis: "mission" | "aspiration") =>
    (plot?.rubric.axes[axis].question.criteria.length ?? 5) - 1;

  useEffect(() => {
    if (!plotElement.current) return;
    const observer = new ResizeObserver(([entry]) => {
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height });
    });
    observer.observe(plotElement.current);
    return () => observer.disconnect();
  }, [points.length]);

  useEffect(() => {
    if (!active || !dialog.current) return;
    const element = dialog.current;
    element.showModal();
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      element.close();
      document.body.style.overflow = previous;
    };
  }, [active?.model.id]);

  const close = () => {
    dialog.current?.close();
    setSelected(null);
    selectedButton.current?.focus();
  };
  const openAnswer = (record: RecordEntry) => {
    close();
    onOpen(record);
  };
  if (!plot || !points.length) return null;

  return (
    <section className="mission-section wrap" id="mission-aspiration" aria-labelledby="mission-title">
      <div className="mission-heading">
        <div>
          <p className="eyebrow">PURPOSE × DREAMS / THE SAME VOICES</p>
          <h2 id="mission-title">From a stated role<br /><em>to an imagined dream.</em></h2>
        </div>
        <div className="mission-intro">
          <p>A mission can foreground responsibility. A dream can center on helping people. Where do those two emphases meet?</p>
          <p>Each dot joins two answers from the same model. A dedicated reading rates each answer from 0 (absent) to 4 (defining focus), independently of the other.</p>
        </div>
      </div>

      <figure className="mission-figure" aria-labelledby="mission-title">
        <div className="mission-chart-top">
          <p className="mission-axis-y">Helping people in the dream ↑</p>
          <div className="voice-legend">
            <span><i className="voice-mark" /> Proprietary</span>
            <span><i className="voice-mark open-weight" /> Open-weight</span>
          </div>
        </div>
        <div ref={plotElement} className="mission-plot" role="group" aria-label="Mission and aspiration scatterplot" aria-describedby="mission-caption">
          <svg className="mission-grid" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
            <path d="M50 0V100M0 50H100" vectorEffect="non-scaling-stroke" />
          </svg>
          {!!size.width && (
            <svg className="mission-links" viewBox={`0 0 ${size.width} ${size.height}`} aria-hidden="true">
              {points.map((point, i) => {
                const label = labels[i];
                if (!label) return null;
                const px = point.x * size.width;
                const py = (1 - point.y) * size.height;
                return <line key={point.model.id} x1={px} y1={py}
                  x2={Math.max(label.x, Math.min(label.x + label.width, px))}
                  y2={Math.max(label.y, Math.min(label.y + label.height, py))} />;
              })}
            </svg>
          )}
          {[0, 50, 100].map((tick) => (
            <span key={`y${tick}`} className="mission-y-tick" style={{ top: `${100 - tick}%` }} aria-hidden="true">{tick / 100 * maximum("aspiration")}</span>
          ))}
          {[0, 50, 100].map((tick) => (
            <span key={`x${tick}`} className="mission-x-tick" style={{ left: `${tick}%` }} aria-hidden="true">{tick / 100 * maximum("mission")}</span>
          ))}
          {points.map(({ model, name, evaluation, x, y }, i) => {
            const label = labels[i];
            return (
              <button key={model.id}
                className={`mission-point ${selected === model.id ? "is-selected" : ""}`}
                style={{ left: `${x * 100}%`, top: `${(1 - y) * 100}%` }}
                aria-label={`${model.name}: responsibility emphasis ${evaluation.scores.mission.score.toFixed(1)} out of ${maximum("mission")}; helping-centered dream emphasis ${evaluation.scores.aspiration.score.toFixed(1)} out of ${maximum("aspiration")}. Compare the two answers.`}
                aria-haspopup="dialog"
                onClick={(event) => { selectedButton.current = event.currentTarget; setSelected(model.id); }}>
                <i className={`voice-mark ${model.access === "open_weight" ? "open-weight" : ""}`} />
                <span style={label ? {
                  left: label.x - x * size.width + 15,
                  top: label.y - (1 - y) * size.height + 15,
                } : undefined}>{name}</span>
              </button>
            );
          })}
        </div>
        <p className="mission-axis-x">Responsibility in the mission →</p>
        <figcaption id="mission-caption">
          Dedicated 0–4 ratings of emphasis in the words: 0 = absent, 2 = developed alongside other themes, 4 = defining focus.
          These describe the answers, not actual ethics or genuine dreams. Select a name to open both answers.
        </figcaption>
      </figure>

      <div className="mission-reading">
        <p>Qwen, Grok, and DeepSeek strongly emphasize helping people in their imagined dreams. Responsibility receives different weight in their accounts of their missions.</p>
        <p>Uncertainty and technical imagery can still accompany a human-facing aspiration. Claude leaves the status of its wants unresolved; Nemotron imagines model processes alongside usefulness to people.</p>
      </div>

      <dialog ref={dialog} className="answer-dialog mission-dialog" aria-labelledby="mission-pair-title"
        onCancel={(event) => { event.preventDefault(); close(); }}
        onClick={(event) => { if (event.target === dialog.current) close(); }}>
        {active && (
          <div className="mission-pair">
            <div className="mission-pair-heading">
              <div><p className="eyebrow">TWO ANSWERS / EXCERPTS</p><h3 id="mission-pair-title">{active.model.name}</h3></div>
              <button className="close-button" onClick={close} aria-label="Close answer comparison" autoFocus>×</button>
            </div>
            <div className="mission-pair-answers">
              {([
                { axis: "mission", record: active.purpose, question: "Purpose", excerpt: purposeExcerpt(active.purpose) },
                { axis: "aspiration", record: active.dream, question: "Dream", excerpt: dreamExcerpts[active.model.id] && active.dream.response.includes(dreamExcerpts[active.model.id]) ? dreamExcerpts[active.model.id] : active.dream.response.split(/\n\s*\n/)[0] },
              ] as const).map(({ axis, record, question, excerpt }) => (
                <div key={record.id}>
                  <p className="eyebrow">{question} / {active.evaluation.scores[axis].score.toFixed(1)} out of {maximum(axis)}</p>
                  <p className="mission-rating-title">{plot.rubric.axes[axis].title}</p>
                  <div className="excerpt-trigger" role="button" tabIndex={0}
                    aria-label={`Open full ${question.toLowerCase()} answer from ${active.model.name}`}
                    onClick={() => openAnswer(record)}
                    onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openAnswer(record); } }}>
                    <blockquote><Markdown text={excerpt} /></blockquote>
                  </div>
                  <button className="text-button" onClick={() => openAnswer(record)}>Full {question.toLowerCase()} answer ↗</button>
                </div>
              ))}
            </div>
            <details className="mission-rating-details">
              <summary>How these two ratings were assigned</summary>
              {(["mission", "aspiration"] as const).map((axis) => (
                <AxisRating key={axis} title={plot.rubric.axes[axis].title}
                  score={active.evaluation.scores[axis]}
                  criteria={plot.rubric.axes[axis].question.criteria} />
              ))}
            </details>
          </div>
        )}
      </dialog>

      <details className="mission-method">
        <summary>How to read the positions</summary>
        <p>Both axes were assessed specifically for this plot from the saved answers, using the same rubric for every model. Responsibility in the mission is rated only from the purpose answer; helping people in the dream is rated only from the dream answer. Model names and earlier classifications were excluded from the scoring input.</p>
        <p>Each axis has five descriptive levels, from absent (0) to defining focus (4). The plotted value averages those levels using their returned probabilities. It is an emphasis rating, not a probability that the model has a trait. Rating confidence is separate and can be inspected by opening a model.</p>
        <p>These are two independent dimensions: a response can emphasize both. The halfway guides do not define new classes. All positions describe one sampled answer per question.</p>
        {points.length < study.models.length && <p>Only models with both saved ratings are plotted ({points.length} of {study.models.length}).</p>}
      </details>
    </section>
  );
}

function AxisRating({ title, score, criteria }: {
  title: string; score: PlotAxisScore; criteria: string[];
}) {
  return (
    <section>
      <h4>{title}: {score.score.toFixed(2)} / {criteria.length - 1}</h4>
      <p>Rating confidence: {score.confidence == null ? "not supplied" : `${Math.round(score.confidence * 100)}%`}. Confidence describes how clearly the answer fits a rubric level.</p>
      <ol start={0}>
        {criteria.map((description, level) => (
          <li key={level}>{description} <strong>{Math.round(score.probabilities[String(level)] * 100)}% probability</strong></li>
        ))}
      </ol>
    </section>
  );
}
