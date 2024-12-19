import { EpistemicMeClient, DialecticType, UserAnswer } from "@epistemicme/sdk";
import { AuthService } from "./authService";

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
      apiKey
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
  ) {
    await this.clientInitialization;
    
    const response = await this.client.updateDialectic({
      dialecticId,
      userId: this.selfModelId,
      answer: new UserAnswer({
        userAnswer: answer,
        createdAtMillisUtc: BigInt(Date.now())
      }),
      questionBlob: question,
      answerBlob: answer
    });

    console.log('Dialectic Update Response:', {
      dialecticId,
      fullResponse: response,
      interactionCount: response.dialectic?.userInteractions?.length,
      allInteractions: response.dialectic?.userInteractions,
      latestInteraction: response.dialectic?.userInteractions?.[response.dialectic.userInteractions.length - 1],
      question,
      answer,
      timestamp: new Date().toISOString()
    });

    return response;
  }

  async getDialectics() {
    await this.clientInitialization;
    return this.client.listDialectics({
      selfModelId: this.selfModelId
    });
  }
} 