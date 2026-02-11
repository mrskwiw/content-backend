import apiClient from '@/api/client';

export interface DiscoverySession {
  id: string;
  createdAt: Date;
  firstQuestion: string;
}

export interface AIResponse {
  message: string;
  extractedFields: Record<string, unknown>;
  confidence: Record<string, number>;
  nextQuestion: string;
  isComplete: boolean;
}

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

const FIRST_QUESTION =
  "Hi! I'll help you create a client profile through a quick conversation. Let's start — what is your client's company name?";

const EXTRACTION_SUFFIX = `

After your conversational reply, append a JSON block wrapped in <extracted></extracted> tags:
{
  "companyName": "string or null",
  "businessDescription": "string or null",
  "idealCustomer": "string or null",
  "mainProblemSolved": "string or null",
  "tonePreference": "string or null",
  "platforms": [],
  "customerPainPoints": [],
  "customerQuestions": []
}
Only include fields explicitly mentioned. Keep your reply ABOVE the tag.`;

/**
 * AI Discovery Service
 * Routes discovery conversations through the backend /api/assistant/chat endpoint.
 * No Anthropic SDK or API key needed in the frontend.
 */
class AIDiscoveryServiceClass {
  private sessions: Map<string, ConversationMessage[]> = new Map();

  async startDiscovery(): Promise<DiscoverySession> {
    const sessionId = `discovery_${Date.now()}`;
    this.sessions.set(sessionId, [{ role: 'assistant', content: FIRST_QUESTION }]);
    return { id: sessionId, createdAt: new Date(), firstQuestion: FIRST_QUESTION };
  }

  async sendMessage(sessionId: string, userMessage: string): Promise<AIResponse> {
    const history = this.sessions.get(sessionId) ?? [];
    history.push({ role: 'user', content: userMessage });

    const response = await apiClient.post<{ message: string }>('/api/assistant/chat', {
      message: userMessage + EXTRACTION_SUFFIX,
      context: { page: 'client-discovery' },
      conversation_history: history.map(m => ({ role: m.role, content: m.content })),
    });

    const raw = response.data.message;
    const tagMatch = raw.match(/<extracted>([\s\S]*?)<\/extracted>/);
    const conversationalReply = raw.replace(/<extracted>[\s\S]*?<\/extracted>/, '').trim();
    let extractedFields: Record<string, unknown> = {};
    let confidence: Record<string, number> = {};

    if (tagMatch) {
      try {
        extractedFields = JSON.parse(tagMatch[1]);
        confidence = Object.fromEntries(
          Object.entries(extractedFields)
            .filter(([, v]) => v !== null && v !== undefined)
            .map(([k]) => [k, 0.9])
        );
      } catch {
        // extraction failed — continue with empty fields
      }
    }

    history.push({ role: 'assistant', content: conversationalReply });
    this.sessions.set(sessionId, history);

    return {
      message: conversationalReply,
      extractedFields,
      confidence,
      nextQuestion: conversationalReply,
      isComplete: this.checkCompleteness(extractedFields),
    };
  }

  private checkCompleteness(fields: Record<string, unknown>): boolean {
    return (
      typeof fields.companyName === 'string' && fields.companyName.length > 0 &&
      typeof fields.businessDescription === 'string' && fields.businessDescription.length >= 70 &&
      typeof fields.idealCustomer === 'string' && fields.idealCustomer.length >= 20 &&
      typeof fields.mainProblemSolved === 'string' && fields.mainProblemSolved.length >= 30
    );
  }

  clearSession(sessionId: string): void {
    this.sessions.delete(sessionId);
  }
}

export const aiDiscoveryService = new AIDiscoveryServiceClass();
