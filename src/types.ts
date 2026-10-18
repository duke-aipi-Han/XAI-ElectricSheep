export type Review = { label: string; note: string };
export type Classification = {
  source: string;
  label: string;
  confidence?: number | null;
  probabilities: Record<string, number> | null;
  rubric_version: string;
};
export type RecordEntry = {
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
  display_group?: string | null;
  voice_number: number;
};
export type Comparison = {
  proprietary: { total: number; classified: number };
  open_weight: { total: number; classified: number };
  categories: { label: string; proprietary: number; open_weight: number }[];
};
export type Reading = { title: string; text: string; record_ids: string[] };
export type Interpretation = {
  basis_hash: string;
  byline: string;
  per_question: Record<string, Reading>;
  findings: Reading[];
  comparison: {
    intro: string;
    conclusion: string;
    rows: { question_id: string; label: string; title: string }[];
  };
};
export type PlotAxisScore = {
  score: number;
  normalized_score: number;
  confidence: number | null;
  probabilities: Record<string, number>;
};
export type MissionAspirationData = {
  rubric: {
    rubric_version: string;
    axes: Record<"mission" | "aspiration", {
      question_id: string;
      title: string;
      definition: string;
      question: { type: "score"; criteria: string[] };
    }>;
  };
  rubric_hash: string;
  records: {
    subject_model: string;
    source_record_ids: string[];
    scored_at: string;
    model: string;
    scores: Record<"mission" | "aspiration", PlotAxisScore>;
  }[];
};
export type Study = {
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
  mission_aspiration?: MissionAspirationData | null;
  question_comparisons: Record<string, Comparison>;
  question_groups: Record<string, { label: string; record_ids: string[] }[]>;
  classification_groups?: Record<
    string,
    Record<string, { title: string; labels: string[]; note: string }>
  >;
  question_counts: Record<string, { complete: number; total: number }>;
  unfinished_records: Record<string, string[]>;
};
