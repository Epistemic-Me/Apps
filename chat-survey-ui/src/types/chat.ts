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

export interface DialecticInteraction {
  id: string
  question: string
  answer: string
  beliefs: Belief[]
  timestamp: Date
}

