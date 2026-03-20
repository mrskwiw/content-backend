import { useState } from 'react';
import { Bot, ChevronDown, ChevronUp, MapPin, Sparkles } from 'lucide-react';
import { Card, CardContent } from '@/components/ui';
import { useLocation } from 'react-router-dom';

export function AIAssistantPanel() {
  const [isMinimized, setIsMinimized] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const location = useLocation();

  // Get current page name from route
  const getPageName = () => {
    const path = location.pathname;
    if (path.includes('/projects')) return 'Projects';
    if (path.includes('/clients')) return 'Clients';
    if (path.includes('/deliverables')) return 'Deliverables';
    if (path.includes('/wizard')) return 'Wizard';
    if (path.includes('/content-review')) return 'QA Review';
    if (path.includes('/settings')) return 'Settings';
    return 'Dashboard';
  };

  const quickActions = [
    { label: 'New Client', icon: '➕', action: () => {} },
    { label: 'Analytics', icon: '📊', action: () => {} },
    { label: 'Voice Analysis', icon: '🔍', action: () => {} },
    { label: 'Generate', icon: '📝', action: () => {} },
  ];

  const suggestions = [
    'Review 5 pending QA items',
    'Show overdue deliverables',
    'Export all completed projects',
  ];

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    // TODO: Send message to backend
    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Card className="w-full border-blue-200 dark:border-blue-800">
      {/* Header */}
      <div className="p-4 border-b border-neutral-200 dark:border-neutral-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30">
              <Bot className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                AI Assistant
              </h3>
              <div className="flex items-center gap-1 text-xs text-neutral-600 dark:text-neutral-400">
                <MapPin className="h-3 w-3" />
                <span>{getPageName()} Page</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors rounded-md hover:bg-neutral-100 dark:hover:bg-neutral-800"
          >
            {isMinimized ? (
              <>
                <ChevronDown className="h-3.5 w-3.5" />
                Expand
              </>
            ) : (
              <>
                <ChevronUp className="h-3.5 w-3.5" />
                Minimize
              </>
            )}
          </button>
        </div>
      </div>

      {/* Content (hidden when minimized) */}
      {!isMinimized && (
        <CardContent className="p-4 space-y-4">
          {/* Quick Actions */}
          <div>
            <p className="text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-2">
              Quick Actions:
            </p>
            <div className="flex flex-wrap gap-2">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={action.action}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
                >
                  <span>{action.icon}</span>
                  <span>{action.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Conversation Area */}
          <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800/50 p-4 min-h-[200px] max-h-[400px] overflow-y-auto">
            <div className="space-y-3">
              {/* Welcome message */}
              <div className="flex gap-2">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <Bot className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="flex-1 bg-white dark:bg-neutral-900 rounded-lg px-3 py-2">
                  <p className="text-sm text-neutral-900 dark:text-neutral-100">
                    👋 Hi! I'm your AI assistant. I can help you with:
                  </p>
                  <ul className="mt-2 text-xs text-neutral-600 dark:text-neutral-400 space-y-1">
                    <li>• Creating and managing clients and projects</li>
                    <li>• Running research tools and voice analysis</li>
                    <li>• Generating content and reviewing deliverables</li>
                    <li>• Answering questions about the system</li>
                  </ul>
                  <p className="mt-2 text-sm text-neutral-900 dark:text-neutral-100">
                    What can I help you with today?
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Input Area */}
          <div className="flex gap-2">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything..."
              rows={1}
              className="flex-1 resize-none rounded-md border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-3 py-2 text-sm text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 dark:placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              className="px-4 py-2 rounded-md bg-blue-600 dark:bg-blue-500 text-white text-sm font-medium hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>

          {/* Suggestions */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Sparkles className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
              <p className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
                Suggestions:
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => setInputValue(suggestion)}
                  className="px-3 py-1.5 text-xs bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 rounded-md hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors border border-amber-200 dark:border-amber-800"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
