import { useState, memo } from 'react';
import { CheckCircle2, Circle, FileText, ArrowRight, Link2 } from 'lucide-react';
import { PlatformSelector } from './PlatformSelector';

interface Template {
  id: number;
  name: string;
  description: string;
  bestFor: string;
  difficulty: 'fast' | 'medium' | 'slow';
  requiredTools?: string[];
  recommendedTools?: string[];
}

const TEMPLATES: Template[] = [
  {
    id: 1,
    name: 'Problem Recognition',
    description: 'Hook problem → Validate feeling → Hint at solution',
    bestFor: 'Building awareness, getting engagement',
    difficulty: 'fast',
    requiredTools: [],
    recommendedTools: ['audience_research', 'seo_keyword_research'],
  },
  {
    id: 2,
    name: 'Statistic + Insight',
    description: 'Stat → What it means → Unexpected angle',
    bestFor: 'Credibility, thought leadership',
    difficulty: 'fast',
    requiredTools: [],
    recommendedTools: ['content_gap_analysis', 'market_trends_research', 'seo_keyword_research'],
  },
  {
    id: 3,
    name: 'Contrarian Take',
    description: 'Challenge conventional wisdom → Show why → Give nuance',
    bestFor: 'Differentiation, starting conversations',
    difficulty: 'medium',
    requiredTools: [],
    recommendedTools: ['competitive_analysis', 'market_trends_research', 'voice_analysis'],
  },
  {
    id: 4,
    name: 'What Changed',
    description: 'Old way → What changed → New results',
    bestFor: 'Authority, sharing lessons',
    difficulty: 'medium',
    requiredTools: [],
    recommendedTools: ['market_trends_research', 'competitive_analysis'],
  },
  {
    id: 5,
    name: 'Question Post',
    description: 'Thought-provoking question with context',
    bestFor: 'Engagement magnet',
    difficulty: 'fast',
    requiredTools: [],
    recommendedTools: ['audience_research', 'content_gap_analysis'],
  },
  {
    id: 6,
    name: 'Personal Story',
    description: 'Vulnerable narrative with lesson learned',
    bestFor: 'Connection, vulnerability',
    difficulty: 'slow',
    requiredTools: [],
    recommendedTools: ['story_mining', 'voice_analysis', 'brand_archetype'],
  },
  {
    id: 7,
    name: 'Myth Busting',
    description: 'Common belief → Why it is wrong → What is true',
    bestFor: 'Education, correction',
    difficulty: 'medium',
    requiredTools: [],
    recommendedTools: ['content_gap_analysis', 'audience_research', 'seo_keyword_research'],
  },
  {
    id: 8,
    name: 'Things I Got Wrong',
    description: 'Past mistakes and lessons learned',
    bestFor: 'Credibility, humility',
    difficulty: 'slow',
    requiredTools: [],
    recommendedTools: ['story_mining', 'voice_analysis', 'brand_archetype'],
  },
  {
    id: 9,
    name: 'How-To',
    description: 'Step-by-step actionable guide',
    bestFor: 'Actionable value',
    difficulty: 'fast',
    requiredTools: [],
    recommendedTools: ['seo_keyword_research', 'content_gap_analysis', 'audience_research'],
  },
  {
    id: 10,
    name: 'Comparison',
    description: 'Option A vs Option B breakdown',
    bestFor: 'Decision-making',
    difficulty: 'fast',
    requiredTools: [],
    recommendedTools: ['competitive_analysis', 'content_gap_analysis'],
  },
  {
    id: 11,
    name: 'What I Learned From',
    description: 'Lessons from books, events, or experiences',
    bestFor: 'Cultural relevance',
    difficulty: 'medium',
    requiredTools: [],
    recommendedTools: ['voice_analysis', 'content_audit'],
  },
  {
    id: 12,
    name: 'Inside Look',
    description: 'Behind-the-scenes process reveal',
    bestFor: 'Transparency, trust',
    difficulty: 'slow',
    requiredTools: [],
    recommendedTools: ['story_mining', 'brand_archetype', 'voice_analysis'],
  },
  {
    id: 13,
    name: 'Future Thinking',
    description: 'Predictions and forward-looking insights',
    bestFor: 'Thought leadership',
    difficulty: 'medium',
    requiredTools: [],
    recommendedTools: ['market_trends_research', 'competitive_analysis'],
  },
  {
    id: 14,
    name: 'Reader Q Response',
    description: 'Answer common customer questions',
    bestFor: 'Community building',
    difficulty: 'medium',
    requiredTools: [],
    recommendedTools: ['audience_research', 'content_gap_analysis'],
  },
  {
    id: 15,
    name: 'Milestone',
    description: 'Celebrate achievements and progress',
    bestFor: 'Celebration',
    difficulty: 'slow',
    requiredTools: [],
    recommendedTools: ['story_mining', 'brand_archetype'],
  },
];

// Tool labels for prerequisite badges
const TOOL_LABELS: Record<string, string> = {
  voice_analysis: 'Voice Analysis',
  brand_archetype: 'Brand Archetype',
  seo_keyword_research: 'SEO Keywords',
  competitive_analysis: 'Competitive Analysis',
  content_gap_analysis: 'Content Gap',
  market_trends_research: 'Market Trends',
  content_audit: 'Content Audit',
  platform_strategy: 'Platform Strategy',
  content_calendar: 'Content Calendar',
  audience_research: 'Audience Research',
  icp_workshop: 'ICP Workshop',
  story_mining: 'Story Mining',
};

interface Props {
  initialSelection?: number[];
  targetPlatform?: string;
  onPlatformChange?: (platform: string) => void;
  onContinue?: (selectedIds: number[]) => void;
}

// Memoized to prevent re-renders when parent updates (Performance optimization - December 25, 2025)
export const TemplateSelectionPanel = memo(function TemplateSelectionPanel({
  initialSelection = [],
  targetPlatform = 'generic',
  onPlatformChange = () => {},
  onContinue
}: Props) {
  const [selected, setSelected] = useState<Set<number>>(new Set(initialSelection));

  const toggleTemplate = (id: number) => {
    const newSelected = new Set(selected);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelected(newSelected);
  };

  const selectAll = () => {
    setSelected(new Set(TEMPLATES.map((t) => t.id)));
  };

  const clearAll = () => {
    setSelected(new Set());
  };

  const selectRecommended = () => {
    // Fast templates: 1, 2, 5, 9, 10 (good for quick wins)
    setSelected(new Set([1, 2, 3, 4, 5, 9, 10]));
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
          onChange={onPlatformChange}
        />
      </div>

      {/* Template Selection */}
      <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">Template Selection</h3>
          </div>
        <div className="flex items-center gap-2">
          <button
            onClick={selectRecommended}
            className="rounded-md border border-blue-600 bg-blue-50 dark:bg-blue-900/20 px-3 py-1.5 text-sm font-medium text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/30"
          >
            Recommended (7)
          </button>
          <button
            onClick={selectAll}
            className="rounded-md border border-neutral-200 dark:border-neutral-700 px-3 py-1.5 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800"
          >
            Select All
          </button>
          <button
            onClick={clearAll}
            className="rounded-md border border-neutral-200 dark:border-neutral-700 px-3 py-1.5 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800"
          >
            Clear
          </button>
        </div>
      </div>

      <p className="mb-6 text-sm text-neutral-600 dark:text-neutral-400">
        Select templates to use for content generation. Typically 7-10 templates are selected for a 30-post package (2
        posts per template).
      </p>

      <div className="mb-4 rounded-md bg-blue-50 dark:bg-blue-900/20 px-4 py-3 text-sm text-blue-800 dark:text-blue-200">
        <strong>{selected.size} templates selected</strong>
        {selected.size > 0 && ` → ${selected.size * 2} posts (2 per template)`}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {TEMPLATES.map((template) => {
          const isSelected = selected.has(template.id);
          return (
            <button
              key={template.id}
              onClick={() => toggleTemplate(template.id)}
              className={`group relative rounded-lg border-2 p-4 text-left transition-all ${
                isSelected
                  ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20 shadow-md'
                  : 'border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 hover:border-neutral-300 dark:hover:border-neutral-600 hover:shadow-sm'
              }`}
            >
              <div className="mb-2 flex items-start justify-between">
                <div className="flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    {isSelected ? (
                      <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-blue-600" />
                    ) : (
                      <Circle className="h-5 w-5 flex-shrink-0 text-neutral-300 dark:text-neutral-600 group-hover:text-neutral-400 dark:group-hover:text-neutral-500" />
                    )}
                    <h4 className={`text-sm font-semibold ${isSelected ? 'text-blue-900 dark:text-blue-100' : 'text-neutral-900 dark:text-neutral-100'}`}>
                      #{template.id}. {template.name}
                    </h4>
                  </div>
                  <p className="ml-7 text-xs text-neutral-600 dark:text-neutral-400">{template.description}</p>
                </div>
              </div>

              {/* Prerequisites */}
              {((template.requiredTools && template.requiredTools.length > 0) ||
                (template.recommendedTools && template.recommendedTools.length > 0)) && (
                <div className="ml-7 mt-3 space-y-2">
                  {template.requiredTools && template.requiredTools.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1">
                      <Link2 className="h-3 w-3 text-red-600 dark:text-red-400" />
                      <span className="text-xs font-medium text-red-600 dark:text-red-400">Required:</span>
                      {template.requiredTools.map((toolId) => (
                        <span
                          key={toolId}
                          className="inline-flex items-center rounded-full bg-red-100 dark:bg-red-900/30 px-2 py-0.5 text-xs font-medium text-red-700 dark:text-red-400"
                        >
                          {TOOL_LABELS[toolId] || toolId}
                        </span>
                      ))}
                    </div>
                  )}
                  {template.recommendedTools && template.recommendedTools.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1">
                      <Link2 className="h-3 w-3 text-blue-600 dark:text-blue-400" />
                      <span className="text-xs font-medium text-blue-600 dark:text-blue-400">Recommended:</span>
                      {template.recommendedTools.map((toolId) => (
                        <span
                          key={toolId}
                          className="inline-flex items-center rounded-full bg-blue-100 dark:bg-blue-900/30 px-2 py-0.5 text-xs font-medium text-blue-700 dark:text-blue-400"
                        >
                          {TOOL_LABELS[toolId] || toolId}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="ml-7 mt-3 space-y-1">
                <div className="text-xs text-neutral-700 dark:text-neutral-300">
                  <strong>Best for:</strong> {template.bestFor}
                </div>
                <div>
                  <span className={`inline-block rounded-md px-2 py-1 text-xs font-medium ${getDifficultyColor(template.difficulty)}`}>
                    {getDifficultyLabel(template.difficulty)}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-6 flex items-center justify-between border-t border-neutral-200 dark:border-neutral-700 pt-4">
        <div className="text-sm text-neutral-600 dark:text-neutral-400">
          {selected.size === 0 && 'Select at least one template to continue'}
          {selected.size > 0 && selected.size < 5 && 'Consider selecting 7-10 templates for variety'}
          {selected.size >= 5 && selected.size <= 12 && '✓ Good selection'}
          {selected.size > 12 && 'You have selected many templates - generation may take longer'}
        </div>
        <button
          onClick={() => onContinue?.(Array.from(selected))}
          disabled={selected.size === 0}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 dark:hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Continue to Generation
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
      </div>
    </div>
  );
});
