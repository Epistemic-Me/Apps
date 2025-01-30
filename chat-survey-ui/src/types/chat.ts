export interface Message {
  id: string
  type: 'question' | 'answer'
  content: string
  timestamp: Date
}

export interface Belief {
  id: string
  content: string
}

export interface QuestionAnswer {
  question: string
  answer: string
  extractedBeliefs: Belief[]
}

// Common interface for all interaction values
export interface BaseInteractionValue {
  updatedAtMillisUtc: string;
}

export interface QuestionAnswerValue extends BaseInteractionValue {
  type: 'questionAnswer';
  question: string;
  answer: string;
  extractedBeliefs?: Array<{
    id: string;
    content: string;
  }>;
}

export interface HypothesisEvidenceValue extends BaseInteractionValue {
  type: 'hypothesisEvidence';
  hypothesis: string;
  evidence: string;
  isCounterfactual: boolean;
  updatedBeliefs?: Array<{
    id: string;
    content: string;
  }>;
}

export interface ActionOutcomeValue extends BaseInteractionValue {
  type: 'actionOutcome';
  action: string;
  outcome: string;
  updatedBeliefs?: Array<{
    id: string;
    content: string;
  }>;
}

export type InteractionValue = QuestionAnswerValue | HypothesisEvidenceValue | ActionOutcomeValue;

export interface DialecticalInteraction {
  id: string;
  interaction: {
    type: {
      value: InteractionValue;
    };
  };
}

