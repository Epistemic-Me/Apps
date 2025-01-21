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

export interface DialecticalInteraction {
  id: string;
  interaction: InteractionData;
}

