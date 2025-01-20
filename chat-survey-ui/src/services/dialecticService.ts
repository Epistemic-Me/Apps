import { EpistemicMeClient, DialecticType, UserAnswer, InteractionData } from "@epistemicme/sdk";
import { AuthService } from "./authService";

// Return type should match the actual structure we see in logs
type DialecticalInteraction = {
  id: string;
  interaction: InteractionData;
};

function replacer(key: string, value: any) {
  if (typeof value === 'bigint') {
    return value.toString();
  }
  return value;
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
    
    console.log('Sending update request:', {
      dialecticId,
      question,
      answer
    });

    const response = await this.client.updateDialectic({
      dialecticId,
      userId: this.selfModelId,
      answer: new UserAnswer({
        userAnswer: answer,
        createdAtMillisUtc: BigInt(Date.now())
      }),
      customQuestion: question
    });

    console.log('Full interaction structure:', JSON.stringify({
      interaction: response.dialectic?.userInteractions?.[0]?.interaction,
    }, replacer, 2));

    console.log('Raw response from server:', {
      dialecticId: response.dialectic?.id,
      interactionCount: response.dialectic?.userInteractions?.length,
      firstInteraction: {
        id: response.dialectic?.userInteractions?.[0]?.id,
        interaction: JSON.stringify(response.dialectic?.userInteractions?.[0]?.interaction, replacer)
      }
    });

    console.log('First interaction:', {
      id: response.dialectic?.userInteractions?.[0]?.id,
      interaction: response.dialectic?.userInteractions?.[0]?.interaction,
      type: response.dialectic?.userInteractions?.[0]?.interaction?.type,
      case: response.dialectic?.userInteractions?.[0]?.interaction?.type?.case,
      value: response.dialectic?.userInteractions?.[0]?.interaction?.type?.value,
    });

    console.log('Interaction type:', {
      type: typeof response.dialectic?.userInteractions?.[0]?.interaction,
      properties: Object.keys(response.dialectic?.userInteractions?.[0]?.interaction || {})
    });

    console.log('Raw interaction before mapping:', {
      id: response.dialectic?.userInteractions?.[0]?.id,
      interaction: response.dialectic?.userInteractions?.[0]?.interaction,
      type: response.dialectic?.userInteractions?.[0]?.interaction?.type,
      value: response.dialectic?.userInteractions?.[0]?.interaction?.type?.value,
      question: response.dialectic?.userInteractions?.[0]?.interaction?.type?.value?.question?.question,
      answer: response.dialectic?.userInteractions?.[0]?.interaction?.type?.value?.answer?.userAnswer,
      beliefs: response.dialectic?.userInteractions?.[0]?.interaction?.type?.value?.extractedBeliefs?.map(b => ({
        id: b.id,
        content: b.content?.[0]?.rawStr
      }))
    });

    const mapped = {
      dialectic: {
        userInteractions: response.dialectic?.userInteractions?.map(i => {
          if (!i.interaction) return null;
          const interaction: DialecticalInteraction = {
            id: i.id,
            interaction: {
              ...i.interaction,
              type: {
                ...i.interaction.type,
                value: {
                  ...i.interaction.type?.value,
                  question: {
                    ...i.interaction.type?.value?.question,
                    question: question,
                    createdAtMillisUtc: "0"
                  },
                  answer: {
                    ...i.interaction.type?.value?.answer,
                    createdAtMillisUtc: i.interaction.type?.value?.answer?.createdAtMillisUtc?.toString() || "0"
                  }
                }
              }
            }
          };
          return interaction;
        }).filter((i): i is DialecticalInteraction => i !== null)
      }
    };

    console.log('Mapped response:', JSON.stringify(mapped, replacer, 2));
    return mapped;
  }

  async getDialectics() {
    await this.clientInitialization;
    return this.client.listDialectics({
      selfModelId: this.selfModelId
    });
  }

  async preprocessQA(questionBlob: string, answerBlob: string, retries = 3) {
    await this.clientInitialization;
    let lastError: unknown;
    
    for (let i = 0; i < retries; i++) {
      try {
        return await this.client.preprocessQA(questionBlob, answerBlob);
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