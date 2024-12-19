import { EpistemicMeClient } from "@epistemicme/sdk";
import { v4 as uuidv4 } from 'uuid';

export class AuthService {
  private static instance: AuthService;
  private apiKey: string | null = null;
  private initializationPromise: Promise<string> | null = null;
  private client: EpistemicMeClient;

  private constructor() {
    this.client = new EpistemicMeClient({
      baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
    });
  }

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  async initialize(): Promise<string> {
    if (this.apiKey) return this.apiKey;
    
    if (!this.initializationPromise) {
      this.initializationPromise = this.createDeveloperAndGetApiKey();
    }
    
    return this.initializationPromise;
  }

  private async createDeveloperAndGetApiKey(): Promise<string> {
    const developerName = `Chat Survey User ${uuidv4()}`;
    const developerEmail = `chat_survey_${uuidv4()}@example.com`;
    
    const createResponse = await this.client.createDeveloper({
      name: developerName,
      email: developerEmail
    });
    
    if (!createResponse.developer?.apiKeys?.[0]) {
      throw new Error('Failed to get API key from developer response');
    }

    this.apiKey = createResponse.developer.apiKeys[0];
    return this.apiKey;
  }

  async getApiKey(): Promise<string> {
    if (!this.apiKey) {
      await this.initialize();
    }
    if (!this.apiKey) {
      throw new Error('API key not initialized');
    }
    return this.apiKey;
  }
} 