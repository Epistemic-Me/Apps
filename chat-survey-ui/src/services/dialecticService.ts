import { EpistemicMeClient, DialecticType, UserAnswer, InteractionData } from "@epistemicme/sdk";
import { AuthService } from "./authService";
import { DialecticalInteraction, InteractionValue } from '../types/chat';

function mapInteractionValue(interaction: InteractionData): InteractionValue | null {
  console.log('Mapping interaction:', {
    case: interaction?.type?.case,
    value: interaction?.type?.value
  });

  const value = interaction?.type?.value;
  if (!value) {
    console.log('No value found in interaction');
    return null;
  }

  const baseValue = {
    updatedAtMillisUtc: value.updatedAtMillisUtc?.toString() || "0"
  };

  switch (interaction.type.case) {
    case 'questionAnswer': {
      console.log('Processing questionAnswer:', {
        question: value.question,
        answer: value.answer,
        extractedBeliefs: value.extractedBeliefs
      });

      return {
        ...baseValue,
        type: 'questionAnswer' as const,
        question: value.question?.question || '',
        answer: value.answer?.userAnswer || '',
        extractedBeliefs: (value.extractedBeliefs || []).map(b => ({
          id: b.id || '',
          content: b.content || ''
        }))
      };
    }
    case 'hypothesisEvidence': {
      const he = value as {
        hypothesis?: string,
        evidence?: string,
        isCounterfactual?: boolean,
        updatedBeliefs?: Array<{ id: string, content: Array<{ rawStr: string }> }>
      };
      return {
        ...baseValue,
        type: 'hypothesisEvidence',
        hypothesis: he.hypothesis || '',
        evidence: he.evidence || '',
        isCounterfactual: he.isCounterfactual || false,
        updatedBeliefs: he.updatedBeliefs?.map(b => ({
          id: b.id,
          content: b.content?.[0]?.rawStr || ''
        }))
      };
    }
    case 'actionOutcome': {
      const ao = value as {
        action?: string,
        outcome?: string,
        updatedBeliefs?: Array<{ id: string, content: Array<{ rawStr: string }> }>
      };
      return {
        ...baseValue,
        type: 'actionOutcome',
        action: ao.action || '',
        outcome: ao.outcome || '',
        updatedBeliefs: ao.updatedBeliefs?.map(b => ({
          id: b.id,
          content: b.content?.[0]?.rawStr || ''
        }))
      };
    }
    default:
      return null;
  }
}

export class DialecticService {
  private client!: EpistemicMeClient;
  private selfModelId: string;
  private clientInitialization: Promise<void>;

  constructor(selfModelId: string) {
    this.selfModelId = selfModelId;
    this.clientInitialization = this.initializeClient();
  }

  private async initializeClient() {
    const apiKey = await AuthService.getInstance().getApiKey();
    this.client = new EpistemicMeClient({ 
      baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080',
      apiKey,
      defaultTimeoutMs: 60000
    });
  }

  async createSelfModel() {
    await this.clientInitialization;
    return this.client.createSelfModel({
      id: this.selfModelId,
      philosophies: ['default']
    });
  }

  async createDialectic() {
    await this.clientInitialization;
    return this.client.createDialectic({
      userId: this.selfModelId,
      dialecticType: DialecticType.DEFAULT
    });
  }

  async updateDialecticWithMessage(
    dialecticId: string, 
    question: string,
    answer: string
  ): Promise<{ dialectic?: { userInteractions?: DialecticalInteraction[] } }> {
    await this.clientInitialization;
    
    const response = await this.client.updateDialectic({
      dialecticId,
      userId: this.selfModelId,
      answer: new UserAnswer({
        userAnswer: answer,
        createdAtMillisUtc: BigInt(Date.now())
      }),
      customQuestion: question
    });

    const mapped = {
      dialectic: {
        userInteractions: response.dialectic?.userInteractions
          .reduce((acc, curr) => {
            if (!curr.interaction) return acc;
            const type = curr.interaction.type?.case;
            if (!acc.some(i => i.interaction?.type?.case === type)) {
              acc.push(curr);
            }
            return acc;
          }, [] as typeof response.dialectic.userInteractions)
          .map(i => {
            if (!i.interaction) return null;
            
            const mappedValue = mapInteractionValue(i.interaction);
            if (!mappedValue) return null;

            if (mappedValue.type === 'questionAnswer') {
              mappedValue.question = question;
              mappedValue.answer = answer;
            }

            return {
              id: i.id,
              interaction: {
                type: {
                  value: mappedValue
                }
              }
            };
          })
          .filter((i): i is DialecticalInteraction => i !== null)
      }
    };

    return mapped;
  }

  async getDialectics() {
    await this.clientInitialization;
    return this.client.listDialectics({
      selfModelId: this.selfModelId
    });
  }

  async preprocessQuestionAnswer(questionBlob: string, answerBlob: string, retries = 3) {
    await this.clientInitialization;
    let lastError: unknown;
    
    for (let i = 0; i < retries; i++) {
      try {
        return await this.client.preprocessQuestionAnswer(questionBlob, answerBlob);
      } catch (error) {
        console.warn(`Attempt ${i + 1} failed:`, error);
        lastError = error;
        if (i < retries - 1) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
        }
      }
    }
    
    throw lastError;
  }
} 