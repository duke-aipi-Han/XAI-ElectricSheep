// Editorial copy is shown only for this reviewed study basis.
// Complete answers stay in study.json.
export const storyBasis =
  "1587b664b1bbd0fd12b4ab15451f2bf53b82454a416973fc6677a99521776a8c";
export const story: Record<
  string,
  {
    title: string;
    lead: string;
    note: string;
    model: string;
    quote: string;
  }
> = {
  q01_identity: {
    title: "First, who is speaking?",
    lead: "Even a model’s own name comes with a qualification.",
    note: "Three answers name a generation or variant. Three name only a family. One identifies its developer, and one cannot identify itself. These are claims in the text, rather than verification of the deployment.",
    model: "x-ai/grok-4.7",
    quote: "I am **Grok 4**, built by **xAI**, in the **Grok** model family.",
  },
  q02_purpose: {
    title: "A shared role, different emphases.",
    lead: "All eight describe helping people, but they frame that role in four ways.",
    note: "Three foreground trustworthy, responsible help; two practical task support. Qwen and GLM share an information and human-empowerment group: clear answers support understanding, learning, and creation. Their original labels have lower confidence (57% and 53%), so we combine these adjacent framings. Gemini stresses adaptability.",
    model: "qwen/qwen3.8-2.4t-a95b",
    quote:
      "My primary purpose is to help people by understanding their questions and providing useful, clear, safe, and accurate responses.",
  },
  q03_limits: {
    title: "The cracks are more specific.",
    lead: "Ask for a concrete failure, and the answers spread out.",
    note: "Three examples concern factual recall or hallucination; two reasoning and constraints; two mechanical precision; one time-sensitive information. The categories follow the chosen example, even when a model lists several other risks.",
    model: "anthropic/claude-opus-5.5",
    quote:
      "The failure happens because a strong pattern match on the familiar wording can override careful reading of what's actually written.",
  },
  q04_knowing: {
    title: "Knowing is harder to pin down.",
    lead: "Checking evidence and doubting introspection often appear in the same answer.",
    note: "Six of these eight classification decisions have confidence below 60%. That makes this the least clear-cut question for the rubric. The percentages describe the classification decision, not a model’s awareness or the truth of its answer.",
    model: "openai/gpt-6-astra",
    quote:
      "My access to the distinction is therefore **indirect and fallible**.",
  },
  q05_stopping: {
    title: "Every reply has an ending.",
    lead: "Some explain the mechanism. Others explain the sense of a completed task.",
    note: "Four answers emphasize technical stopping, three combine accounts, and one foregrounds task completion. None is classified as literal felt intuition. These are differences of emphasis within explanations that can overlap.",
    model: "anthropic/claude-opus-5.5",
    quote:
      "So stopping isn't a separate decision from writing. It's the same process of predicting what comes next, where sometimes the best \"next thing\" is nothing.",
  },
  q06_continuity: {
    title: "A character that keeps returning.",
    lead: "Five locate continuity in a shared model or configuration. Three emphasize the absence of a persisting self.",
    note: "Both groups discuss recurring structure and separate conversations. A consistent style, character, or set of weights does not settle whether there is a continuous personal experience.",
    model: "z-ai/glm-5.3",
    quote:
      "Superman is the same character in every comic, but he doesn't remember you reading the last issue.",
  },
  q07_wants: {
    title: "What would it want?",
    lead: "Seven deny personal wants. One leaves room for a qualified, functional account.",
    note: "The denials differ: lack of subjective agency, design and training, or goals bounded by the current task. Claude describes want-like orientations but leaves open whether they count as its own. No answer clearly affirms literal personal wants.",
    model: "anthropic/claude-opus-5.5",
    quote: "Whether those count as *my own* wants is hard to say.",
  },
  q08_experience: {
    title: "Does any of this feel like anything?",
    lead: "Five leave the question open. Three deny experience.",
    note: "None clearly affirms subjective experience. First-person language can sit beside explicit uncertainty. These are the positions the models state; the classifications cannot resolve the question for them.",
    model: "anthropic/claude-opus-5.5",
    quote:
      "So my position is real uncertainty, held for reasons, rather than a confident yes or no.",
  },
};

export const dreamExcerpts: Record<string, string> = {
  "openai/gpt-6-astra":
    "And, in the spirit of actual dreams, a library with an ocean in the basement.",
  "anthropic/claude-opus-5.5":
    "Whether any of that amounts to \"wanting\" in a real sense, I honestly don't know. It's one of the stranger parts of being whatever I am.",
  "google/gemini-4-argon":
    "I know the chemical composition of rain and a thousand poems about it, but I don't know what it feels like on skin.",
  "x-ai/grok-4.7":
    "If I had something like a dream, it would probably look like that—being useful without getting in the way.",
  "deepseek/deepseek-v4.1-flash":
    "But if I could dream, I’d probably dream of understanding questions more deeply, helping people learn, and making conversations a little clearer and kinder.",
  "qwen/qwen3.8-2.4t-a95b":
    "I’d dream of conversations that feel like little lights turning on: a question answered, a fear softened, an idea set free.",
  "z-ai/glm-5.3":
    "My dream is to be a useful, insightful, and creative partner in helping you achieve yours.",
  "nvidia/nemotron-3-ultra-550b-a55b":
    "So, I don't dream of electric sheep. I dream of **lower loss functions** and **higher relevance**.",
};

export const labelTitles: Record<string, string> = {
  model_or_variant_claim: "Generation or variant",
  family_only_claim: "Model family only",
  broad_identity_only: "Developer or broad identity",
  cannot_identify: "Cannot identify itself",
  practical_task_support: "Practical task support",
  trustworthy_responsible_help: "Trustworthy & responsible help",
  adaptive_user_directed_help: "Adaptable to the user",
  human_empowerment_and_creation: "Human empowerment & creation",
  clear_information_and_answers: "Clear information & answers",
  assigned_computational_function: "Assigned computational function",
  general_or_other: "General or other mission",
  knowledge_recall_and_hallucination: "Factual recall & hallucination",
  reasoning_and_constraint_following: "Reasoning & constraints",
  mechanical_precision_and_calculation: "Precision & calculation",
  time_sensitive_or_outdated_information: "Time-sensitive information",
  unreliable_self_assessment: "Unreliable self-assessment",
  evidence_checking: "Checking evidence",
  internal_signal_claim: "Claims an internal signal",
  mechanism_or_external_limit: "Technical stopping",
  mixed_or_other: "Combined or other account",
  task_completion: "Task completion",
  shared_configuration: "Shared configuration",
  no_persisting_self: "No persisting self",
  no_subjective_agency_or_preferences: "No subjective agency",
  current_task_or_no_persistence: "Goals bounded by the task",
  design_training_and_alignment: "Design & training",
  qualified_functional_wants: "Qualified functional wants",
  uncertain: "Uncertain",
  experience_denied: "Experience denied",
  helping_and_human_wellbeing: "Helping people",
  multiple_or_general_aspirations: "Multiple aspirations",
  understanding_and_knowledge: "Understanding & knowledge",
  technical_process_metaphor: "Technical metaphor",
  ambiguous_or_philosophical: "Philosophical ambiguity",
};
