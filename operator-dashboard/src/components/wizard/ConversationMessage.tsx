import { Bot, User } from 'lucide-react';

export interface ConversationMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

/**
 * Individual message component for AI discovery conversation
 * Renders message bubbles with role-based styling and avatars
 */
export function ConversationMessage({ role, content, timestamp }: ConversationMessageProps) {
  const isAssistant = role === 'assistant';

  return (
    <div className={`flex gap-3 ${isAssistant ? 'justify-start' : 'justify-end'}`}>
      {/* Avatar - only show for assistant messages */}
      {isAssistant && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
          <Bot className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        </div>
      )}

      {/* Message bubble */}
      <div
        className={`max-w-[75%] rounded-lg px-4 py-2.5 ${
          isAssistant
            ? 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100'
            : 'bg-blue-600 dark:bg-blue-700 text-white'
        }`}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        {timestamp && (
          <p className="text-xs mt-1 opacity-70">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>

      {/* Avatar - only show for user messages */}
      {!isAssistant && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 dark:bg-blue-700 flex items-center justify-center">
          <User className="h-4 w-4 text-white" />
        </div>
      )}
    </div>
  );
}
