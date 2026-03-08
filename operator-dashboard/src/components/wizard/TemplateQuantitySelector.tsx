import { useState, useMemo, memo } from 'react';
import { Plus, Minus, DollarSign, FileText, Calculator, TrendingUp, HelpCircle, AlertCircle, X } from 'lucide-react';
import { PlatformSelector } from './PlatformSelector';

interface Template {
  id: number;
  name: string;
  description: string;
  bestFor: string;
  difficulty: 'fast' | 'medium' | 'slow';
}

const TEMPLATES: Template[] = [
  {
    id: 1,
    name: 'Problem Recognition',
    description: 'Hook problem → Validate feeling → Hint at solution',
    bestFor: 'Building awareness, getting engagement',
    difficulty: 'fast',
  },
  {
    id: 2,
    name: 'Statistic + Insight',
    description: 'Stat → What it means → Unexpected angle',
    bestFor: 'Credibility, thought leadership',
    difficulty: 'fast',
  },
  {
    id: 3,
    name: 'Contrarian Take',
    description: 'Challenge conventional wisdom → Show why → Give nuance',
    bestFor: 'Differentiation, starting conversations',
    difficulty: 'medium',
  },
  {
    id: 4,
    name: 'What Changed',
    description: 'Old way → What changed → New results',
    bestFor: 'Authority, sharing lessons',
    difficulty: 'medium',
  },
  {
    id: 5,
    name: 'Question Post',
    description: 'Thought-provoking question with context',
    bestFor: 'Engagement magnet',
    difficulty: 'fast',
  },
  {
    id: 6,
    name: 'Personal Story',
    description: 'Vulnerable narrative with lesson learned',
    bestFor: 'Connection, vulnerability',
    difficulty: 'slow',
  },
  {
    id: 7,
    name: 'Myth Busting',
    description: 'Common belief → Why it is wrong → What is true',
    bestFor: 'Education, correction',
    difficulty: 'medium',
  },
  {
    id: 8,
    name: 'Things I Got Wrong',
    description: 'Past mistakes and lessons learned',
    bestFor: 'Credibility, humility',
    difficulty: 'slow',
  },
  {
    id: 9,
    name: 'How-To',
    description: 'Step-by-step actionable guide',
    bestFor: 'Actionable value',
    difficulty: 'fast',
  },
  {
    id: 10,
    name: 'Comparison',
    description: 'Option A vs Option B breakdown',
    bestFor: 'Decision-making',
    difficulty: 'fast',
  },
  {
    id: 11,
    name: 'What I Learned From',
    description: 'Lessons from books, events, or experiences',
    bestFor: 'Cultural relevance',
    difficulty: 'medium',
  },
  {
    id: 12,
    name: 'Inside Look',
    description: 'Behind-the-scenes process reveal',
    bestFor: 'Transparency, trust',
    difficulty: 'slow',
  },
  {
    id: 13,
    name: 'Future Thinking',
    description: 'Predictions and forward-looking insights',
    bestFor: 'Thought leadership',
    difficulty: 'medium',
  },
  {
    id: 14,
    name: 'Reader Q Response',
    description: 'Answer common customer questions',
    bestFor: 'Community building',
    difficulty: 'medium',
  },
  {
    id: 15,
    name: 'Milestone',
    description: 'Celebrate achievements and progress',
    bestFor: 'Celebration',
    difficulty: 'slow',
  },
];

interface Props {
  initialQuantities?: Record<number, number>;
  initialIncludeResearch?: boolean;
  initialTopics?: string[];  // NEW: custom topics for generation
  initialTargetPlatform?: string;  // NEW: target platform
  onContinue?: (
    quantities: Record<number, number>,
    includeResearch: boolean,
    totalPrice: number,
    customTopics: string[],
    targetPlatform: string
  ) => void;
}

const PRICE_PER_POST = 40.0;
const RESEARCH_PRICE_PER_POST = 15.0;

export const TemplateQuantitySelector = memo(function TemplateQuantitySelector({
  initialQuantities = {},
  initialIncludeResearch = false,
  initialTopics = [],  // NEW
  initialTargetPlatform = 'generic',  // NEW
  onContinue,
}: Props) {
  const [quantities, setQuantities] = useState<Record<number, number>>(initialQuantities);
  const [includeResearch, setIncludeResearch] = useState(initialIncludeResearch);
  const [customTopics, setCustomTopics] = useState<string[]>(initialTopics);  // NEW: topic override state
  const [targetPlatform, setTargetPlatform] = useState<string>(initialTargetPlatform);  // NEW: target platform state

  // Calculate totals
  const { totalPosts, totalPrice, pricePerPost } = useMemo(() => {
    const total = Object.values(quantities).reduce((sum, qty) => sum + qty, 0);
    const basePrice = PRICE_PER_POST;
    const research = includeResearch ? RESEARCH_PRICE_PER_POST : 0;
    const perPost = basePrice + research;
    return {
      totalPosts: total,
      pricePerPost: perPost,
      totalPrice: total * perPost,
    };
  }, [quantities, includeResearch]);

  const updateQuantity = (templateId: number, delta: number) => {
    setQuantities((prev) => {
      const current = prev[templateId] || 0;
      const newValue = Math.max(0, current + delta);

      if (newValue === 0) {
        const { [templateId]: _, ...rest } = prev;
        return rest;
      }

      return { ...prev, [templateId]: newValue };
    });
  };

  const setQuantity = (templateId: number, value: number) => {
    const newValue = Math.max(0, Math.min(100, value));
    setQuantities((prev) => {
      if (newValue === 0) {
        const { [templateId]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [templateId]: newValue };
    });
  };

  const clearAll = () => {
    setQuantities({});
  };

  const getDifficultyColor = (difficulty: Template['difficulty']) => {
    switch (difficulty) {
      case 'fast':
        return 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300';
      case 'medium':
        return 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300';
      case 'slow':
        return 'bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300';
    }
  };

  const getDifficultyLabel = (difficulty: Template['difficulty']) => {
    switch (difficulty) {
      case 'fast':
        return '⚡ Fast (5 min)';
      case 'medium':
        return '⏱️ Medium (7-8 min)';
      case 'slow':
        return '🕐 Slow (10 min)';
    }
  };

  return (
    <div className="space-y-8">
      {/* Platform Selector */}
      <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-6 shadow-sm">
        <PlatformSelector
          selected={targetPlatform}
          onChange={setTargetPlatform}
        />
      </div>

      {/* Template Quantity Selection */}
      <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-6 shadow-sm">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calculator className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">Custom Template Quantities</h3>
        </div>
        <button
          onClick={clearAll}
          className="rounded-md border border-neutral-200 dark:border-neutral-700 px-3 py-1.5 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800"
        >
          Clear All
        </button>
      </div>

      <p className="mb-6 text-sm text-neutral-600 dark:text-neutral-400">
        Specify exact quantities for each template. Pricing is $40/post, with optional $15/post topic research add-on.
      </p>

      {/* Pricing Summary Card */}
      <div className="mb-6 rounded-lg border-2 border-blue-200 dark:border-blue-800 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 p-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-blue-100 dark:bg-blue-900/40 p-2">
              <FileText className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{totalPosts}</div>
              <div className="text-xs text-neutral-600 dark:text-neutral-400">Total Posts</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="rounded-full bg-emerald-100 dark:bg-emerald-900/40 p-2">
              <TrendingUp className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">${pricePerPost}</div>
              <div className="text-xs text-neutral-600 dark:text-neutral-400">Per Post</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="rounded-full bg-purple-100 dark:bg-purple-900/40 p-2">
              <DollarSign className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">${totalPrice.toLocaleString()}</div>
              <div className="text-xs text-neutral-600 dark:text-neutral-400">Total Price</div>
            </div>
          </div>
        </div>

        {/* Topic Research Checkbox */}
        <div className="mt-4 flex items-center gap-2 border-t border-blue-200 dark:border-blue-800 pt-4">
          <input
            type="checkbox"
            id="include-research"
            checked={includeResearch}
            onChange={(e) => setIncludeResearch(e.target.checked)}
            className="h-4 w-4 rounded border-neutral-300 dark:border-neutral-600 text-blue-600 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
          />
          <label htmlFor="include-research" className="flex-1 cursor-pointer text-sm font-medium text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5">
            <span>Include topic research (+$15/post) {includeResearch && `= +$${(totalPosts * RESEARCH_PRICE_PER_POST).toLocaleString()}`}</span>
            <span title="Topic research identifies trending keywords and content themes for your posts. This is separate from the client research tools in the Research step.">
              <HelpCircle
                className="h-4 w-4 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
              />
            </span>
          </label>
        </div>

        {/* Topic Override Section */}
        <div className="mt-4 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="h-4 w-4 text-amber-600" />
            <label className="text-sm font-medium text-amber-900 dark:text-amber-100">
              Custom Topics (Optional)
            </label>
          </div>
          <p className="text-xs text-amber-700 dark:text-amber-300 mb-3">
            Specify topics to guide content generation. Leave empty to use research results or AI suggestions. Separate with commas.
          </p>
          <textarea
            value={customTopics.join(', ')}
            onChange={(e) => setCustomTopics(
              e.target.value.split(',').map(s => s.trim()).filter(Boolean)
            )}
            placeholder="e.g., customer retention, churn prediction, product analytics"
            className="w-full rounded-md border-amber-300 dark:border-amber-700 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 px-3 py-2 text-sm focus:border-amber-500 dark:focus:border-amber-400 focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400"
            rows={2}
          />
          {customTopics.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {customTopics.map((topic, i) => (
                <span key={i} className="inline-flex items-center gap-1 rounded-full bg-amber-100 dark:bg-amber-900/40 px-2.5 py-1 text-xs font-medium text-amber-800 dark:text-amber-200">
                  {topic}
                  <X
                    className="h-3 w-3 cursor-pointer hover:text-amber-900 dark:hover:text-amber-100"
                    onClick={() => setCustomTopics(prev => prev.filter((_, idx) => idx !== i))}
                  />
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Template Grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {TEMPLATES.map((template) => {
          const quantity = quantities[template.id] || 0;
          const hasQuantity = quantity > 0;

          return (
            <div
              key={template.id}
              className={`group relative rounded-lg border-2 p-4 transition-all ${
                hasQuantity
                  ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20 shadow-md'
                  : 'border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 hover:border-neutral-300 dark:hover:border-neutral-600'
              }`}
            >
              {/* Template Header */}
              <div className="mb-3">
                <div className="mb-1 flex items-center justify-between">
                  <h4 className={`text-sm font-semibold ${hasQuantity ? 'text-blue-900 dark:text-blue-100' : 'text-neutral-900 dark:text-neutral-100'}`}>
                    #{template.id}. {template.name}
                  </h4>
                  {hasQuantity && (
                    <span className="rounded-full bg-blue-600 px-2 py-0.5 text-xs font-bold text-white">
                      {quantity}
                    </span>
                  )}
                </div>
                <p className="text-xs text-neutral-600 dark:text-neutral-400">{template.description}</p>
              </div>

              {/* Template Details */}
              <div className="mb-3 space-y-1">
                <div className="text-xs text-neutral-700 dark:text-neutral-300">
                  <strong>Best for:</strong> {template.bestFor}
                </div>
                <div>
                  <span className={`inline-block rounded-md px-2 py-1 text-xs font-medium ${getDifficultyColor(template.difficulty)}`}>
                    {getDifficultyLabel(template.difficulty)}
                  </span>
                </div>
              </div>

              {/* Quantity Controls */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => updateQuantity(template.id, -1)}
                  disabled={quantity === 0}
                  className="flex h-8 w-8 items-center justify-center rounded-md border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-40"
                  aria-label="Decrease quantity"
                >
                  <Minus className="h-4 w-4" />
                </button>

                <input
                  type="number"
                  min="0"
                  max="100"
                  value={quantity}
                  onChange={(e) => setQuantity(template.id, parseInt(e.target.value) || 0)}
                  className="h-8 w-16 rounded-md border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 text-center text-sm font-semibold text-neutral-900 dark:text-neutral-100 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                />

                <button
                  onClick={() => updateQuantity(template.id, 1)}
                  className="flex h-8 w-8 items-center justify-center rounded-md border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800"
                  aria-label="Increase quantity"
                >
                  <Plus className="h-4 w-4" />
                </button>

                {hasQuantity && (
                  <div className="ml-auto text-xs font-semibold text-neutral-600 dark:text-neutral-400">
                    ${(quantity * pricePerPost).toLocaleString()}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="mt-6 flex items-center justify-between border-t border-neutral-200 dark:border-neutral-700 pt-4">
        <div className="text-sm text-neutral-600 dark:text-neutral-400">
          {totalPosts === 0 && 'Add at least one post to continue'}
          {totalPosts > 0 && totalPosts < 10 && 'Consider adding more posts for better content variety'}
          {totalPosts >= 10 && totalPosts <= 50 && '✓ Good quantity selection'}
          {totalPosts > 50 && 'Large order - generation may take longer'}
        </div>
        <button
          onClick={() => onContinue?.(quantities, includeResearch, totalPrice, customTopics, targetPlatform)}
          disabled={totalPosts === 0}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 dark:hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Continue to Generation
          <span className="text-xs opacity-75">(${totalPrice.toLocaleString()})</span>
        </button>
      </div>
      </div>
    </div>
  );
});
