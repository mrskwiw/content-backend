import Anthropic from '@anthropic-ai/sdk';
import type { ClientBrief } from '@/types/domain';

export interface DiscoverySession {
  id: string;
  createdAt: Date;
  firstQuestion: string;
}

export interface AIResponse {
  message: string;
  extractedFields: Partial<ClientBrief>;
  confidence: Record<string, number>;
  nextQuestion: string;
  isComplete: boolean;
}

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

/**
 * AI Discovery Service
 * Manages conversational client discovery using Claude API
 */
class AIDiscoveryServiceClass {
  private client: Anthropic;
  private sessions: Map<string, ConversationMessage[]> = new Map();

  constructor() {
    // Initialize Anthropic client
    // API key should be in environment variables
    const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error('VITE_ANTHROPIC_API_KEY is not set in environment variables');
    }
    this.client = new Anthropic({
      apiKey,
      dangerouslyAllowBrowser: true, // Required for frontend usage
    });
  }

  /**
   * Start a new discovery session
   */
  async startDiscovery(): Promise<DiscoverySession> {
    const sessionId = `discovery_${Date.now()}`;
    const firstQuestion = "Hi! I'll help you create a client profile through a quick conversation. Let's start with the basics - what is your client's company name?";

    // Initialize conversation history
    this.sessions.set(sessionId, [
      {
        role: 'assistant',
        content: firstQuestion,
      },
    ]);

    return {
      id: sessionId,
      createdAt: new Date(),
      firstQuestion,
    };
  }

  /**
   * Send a message and get AI response with extracted data
   */
  async sendMessage(sessionId: string, userMessage: string): Promise<AIResponse> {
    // Get conversation history
    const history = this.sessions.get(sessionId) || [];

    // Add user message to history
    history.push({
      role: 'user',
      content: userMessage,
    });

    // Build prompt for Claude
    const systemPrompt = this.buildSystemPrompt();
    const conversationContext = this.buildConversationContext(history);

    try {
      // Call Claude API
      const response = await this.client.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 1024,
        system: systemPrompt,
        messages: [
          {
            role: 'user',
            content: conversationContext,
          },
        ],
      });

      // Parse response
      const assistantMessage = response.content[0].type === 'text' ? response.content[0].text : '';

      // Extract structured data using a second API call
      const extractedData = await this.extractData(history, userMessage);

      // Add assistant message to history
      history.push({
        role: 'assistant',
        content: assistantMessage,
      });

      // Update session
      this.sessions.set(sessionId, history);

      // Determine if discovery is complete
      const isComplete = this.checkCompleteness(extractedData);

      return {
        message: assistantMessage,
        extractedFields: extractedData.fields,
        confidence: extractedData.confidence,
        nextQuestion: assistantMessage,
        isComplete,
      };
    } catch (error) {
      console.error('AI Discovery error:', error);
      throw new Error('Failed to process message. Please try again.');
    }
  }

  /**
   * Build system prompt for conversational discovery
   */
  private buildSystemPrompt(): string {
    return `You are a helpful assistant conducting a client discovery interview for a content generation service.

Your goal is to extract the following information through natural conversation:
- company_name (required)
- business_description (required, min 70 chars)
- ideal_customer (required, min 20 chars)
- main_problem_solved (required, min 30 chars)
- tone_preference (optional)
- platforms (optional array)
- customer_pain_points (optional array)
- customer_questions (optional array)

Guidelines:
1. Be conversational and friendly, not robotic
2. Ask one question at a time
3. Follow up naturally based on responses
4. Don't overwhelm with too many questions at once
5. Acknowledge their responses before asking the next question
6. Once you have the core information (company name, business description, ideal customer, main problem), you can ask about optional fields
7. Keep questions concise and clear

Start by asking for the company name, then naturally flow to understanding their business, target audience, and the problem they solve.`;
  }

  /**
   * Build conversation context from history
   */
  private buildConversationContext(history: ConversationMessage[]): string {
    const conversationText = history
      .map(msg => `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`)
      .join('\n\n');

    return `${conversationText}\n\nAssistant:`;
  }

  /**
   * Extract structured data from conversation
   */
  private async extractData(
    history: ConversationMessage[],
    latestMessage: string
  ): Promise<{ fields: Partial<ClientBrief>; confidence: Record<string, number> }> {
    // Build extraction prompt
    const extractionPrompt = `You are analyzing a client discovery conversation to extract structured data.

CONVERSATION HISTORY:
${history.map(msg => `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`).join('\n')}

Extract the following fields if mentioned in the conversation:
- company_name
- business_description
- ideal_customer
- main_problem_solved
- tone_preference
- platforms (array of: linkedin, twitter, blog, email, generic)
- customer_pain_points (array of strings)
- customer_questions (array of strings)

For each field, also provide a confidence score (0.0 to 1.0) indicating how certain you are about the extracted value.

Respond ONLY with valid JSON in this exact format:
{
  "fields": {
    "company_name": "extracted value or null",
    "business_description": "extracted value or null",
    "ideal_customer": "extracted value or null",
    "main_problem_solved": "extracted value or null",
    "tone_preference": "extracted value or null",
    "platforms": ["platform1", "platform2"] or [],
    "customer_pain_points": ["pain1", "pain2"] or [],
    "customer_questions": ["question1", "question2"] or []
  },
  "confidence": {
    "company_name": 0.95,
    "business_description": 0.80
  }
}

Only include fields that were explicitly mentioned. Use null for missing values.`;

    try {
      const response = await this.client.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 1024,
        messages: [
          {
            role: 'user',
            content: extractionPrompt,
          },
        ],
      });

      const extractedText = response.content[0].type === 'text' ? response.content[0].text : '{}';

      // Parse JSON response
      const parsed = JSON.parse(extractedText);

      // Convert to ClientBrief format
      const fields: Partial<ClientBrief> = {
        companyName: parsed.fields.company_name || undefined,
        businessDescription: parsed.fields.business_description || undefined,
        idealCustomer: parsed.fields.ideal_customer || undefined,
        mainProblemSolved: parsed.fields.main_problem_solved || undefined,
        tonePreference: parsed.fields.tone_preference || undefined,
        platforms: parsed.fields.platforms || [],
        customerPainPoints: parsed.fields.customer_pain_points || [],
        customerQuestions: parsed.fields.customer_questions || [],
      };

      return {
        fields,
        confidence: parsed.confidence || {},
      };
    } catch (error) {
      console.error('Extraction error:', error);
      // Return empty data on error
      return {
        fields: {},
        confidence: {},
      };
    }
  }

  /**
   * Check if required fields are complete
   */
  private checkCompleteness(extractedData: {
    fields: Partial<ClientBrief>;
    confidence: Record<string, number>;
  }): boolean {
    const { fields } = extractedData;

    // Required fields
    const hasCompanyName = !!fields.companyName && fields.companyName.length > 0;
    const hasBusinessDescription = !!fields.businessDescription && fields.businessDescription.length >= 70;
    const hasIdealCustomer = !!fields.idealCustomer && fields.idealCustomer.length >= 20;
    const hasMainProblem = !!fields.mainProblemSolved && fields.mainProblemSolved.length >= 30;

    return hasCompanyName && hasBusinessDescription && hasIdealCustomer && hasMainProblem;
  }

  /**
   * Get extracted client data from session
   */
  async extractClientData(sessionId: string): Promise<Partial<ClientBrief>> {
    const history = this.sessions.get(sessionId) || [];
    if (history.length === 0) {
      return {};
    }

    const extracted = await this.extractData(history, '');
    return extracted.fields;
  }

  /**
   * Clear session data
   */
  clearSession(sessionId: string): void {
    this.sessions.delete(sessionId);
  }
}

// Export singleton instance
export const aiDiscoveryService = new AIDiscoveryServiceClass();
