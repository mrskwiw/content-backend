import { useState, memo, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { CheckCircle2, Circle, FlaskConical, ArrowRight, Loader2, DollarSign, Clock, Link2, AlertCircle } from 'lucide-react';
import { researchApi, ResearchTool } from '@/api/research';
import { getApiErrorMessage } from '@/utils/apiError';
import { ResearchDataCollectionPanel } from './ResearchDataCollectionPanel';

// Tool prerequisites mapping (from backend research_prerequisites.py)
const TOOL_PREREQUISITES: Record<string, { required: string[]; recommended: string[] }> = {
  // Tier 1 - Foundation (no prerequisites)
  voice_analysis: { required: [], recommended: [] },
  brand_archetype: { required: [], recommended: [] },
  seo_keyword_research: { required: [], recommended: [] },
  audience_research: { required: [], recommended: [] },
  competitive_analysis: { required: [], recommended: [] },

  // Tier 2 - Analysis
  content_gap_analysis: { required: [], recommended: ['competitive_analysis', 'seo_keyword_research'] },
  market_trends_research: { required: [], recommended: ['seo_keyword_research'] },
  icp_workshop: { required: [], recommended: ['audience_research'] },
  content_audit: { required: [], recommended: [] },

  // Tier 3 - Strategy
  platform_strategy: { required: ['audience_research'], recommended: ['content_gap_analysis', 'market_trends_research'] },
  story_mining: { required: [], recommended: ['voice_analysis', 'brand_archetype'] },

  // Tier 4 - Execution
  content_calendar: { required: ['seo_keyword_research', 'platform_strategy'], recommended: ['content_gap_analysis', 'market_trends_research'] },
};

// Tool name label mapping
const TOOL_LABELS: Record<string, string> = {
  voice_analysis: 'Voice Analysis',
  brand_archetype: 'Brand Archetype',
  seo_keyword_research: 'SEO Keywords',
  audience_research: 'Audience Research',
  competitive_analysis: 'Competitive Analysis',
  content_gap_analysis: 'Content Gap',
  market_trends_research: 'Market Trends',
  icp_workshop: 'ICP Workshop',
  content_audit: 'Content Audit',
  platform_strategy: 'Platform Strategy',
  story_mining: 'Story Mining',
  content_calendar: 'Content Calendar',
};

interface Props {
  projectId?: string;
  clientId?: string;
  onContinue?: () => void;
}

type Step = 'selection' | 'data-collection' | 'executing';

// Memoized to prevent re-renders when parent updates (Performance optimization - December 25, 2025)
export const ResearchPanel = memo(function ResearchPanel({ projectId, clientId, onContinue }: Props) {
  const [step, setStep] = useState<Step>('selection');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [collectedData, setCollectedData] = useState<Record<string, any>>({});
  const [results, setResults] = useState<Map<string, any>>(new Map());

  // Fetch available research tools
  const { data: tools = [], isLoading } = useQuery({
    queryKey: ['research', 'tools'],
    queryFn: () => researchApi.listTools(),
  });

  // Fetch research history for current client
  const { data: historyData } = useQuery({
    queryKey: ['research', 'history', clientId],
    queryFn: () => clientId ? researchApi.getClientHistory(clientId) : Promise.resolve(null),
    enabled: !!clientId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch completed tools for current project (for prerequisite checking)
  const { data: completedToolsData } = useQuery({
    queryKey: ['research', 'completed', projectId],
    queryFn: () => projectId ? researchApi.getClientHistory(projectId) : Promise.resolve(null),
    enabled: !!projectId,
    staleTime: 60 * 1000, // 1 minute
  });

  // Process history into map: tool_name -> most recent run date
  const toolHistory = useMemo(() => {
    if (!historyData?.results) return new Map<string, Date>();

    const map = new Map<string, Date>();
    historyData.results.forEach((result) => {
      const existingDate = map.get(result.toolName);
      const newDate = new Date(result.createdAt);

      // Keep only the most recent run
      if (!existingDate || newDate > existingDate) {
        map.set(result.toolName, newDate);
      }
    });

    return map;
  }, [historyData]);

  // Process completed tools for prerequisite checking
  const completedTools = useMemo(() => {
    if (!completedToolsData?.results) return new Set<string>();

    const completed = new Set<string>();
    completedToolsData.results.forEach((result) => {
      if (result.status === 'completed') {
        completed.add(result.toolName);
      }
    });

    return completed;
  }, [completedToolsData]);

  // Helper: Check if a prerequisite is fulfilled
  const isPrerequisiteFulfilled = (prereqToolName: string): boolean => {
    // Prerequisite is fulfilled if it's already completed OR if it's in the current selection
    return completedTools.has(prereqToolName) || selected.has(prereqToolName);
  };

  // Helper: Get prerequisite status for a tool
  const getPrerequisiteStatus = (toolName: string) => {
    const prereqs = TOOL_PREREQUISITES[toolName];
    if (!prereqs) return { fulfilled: [], unfulfilled: [], hasUnfulfilled: false };

    const allPrereqs = [...prereqs.required, ...prereqs.recommended];
    const fulfilled = allPrereqs.filter(p => isPrerequisiteFulfilled(p));
    const unfulfilled = allPrereqs.filter(p => !isPrerequisiteFulfilled(p));

    return {
      fulfilled,
      unfulfilled,
      hasUnfulfilled: unfulfilled.length > 0,
      requiredUnfulfilled: prereqs.required.filter(p => !isPrerequisiteFulfilled(p)),
    };
  };

  // Run research mutation
  const runResearchMutation = useMutation({
    mutationFn: ({ tool, params }: { tool: string; params?: Record<string, any> }) =>
      researchApi.run({
        projectId: projectId!,
        clientId: clientId!,
        tool,
        params: params || {},
      }),
    onSuccess: (data, variables) => {
      setResults(new Map(results).set(variables.tool, data));
    },
    onError: (error, variables) => {
      alert(`Failed to run research tool "${variables.tool}": ${getApiErrorMessage(error)}`);
    },
  });

  const toggleTool = (toolName: string) => {
    const newSelected = new Set(selected);
    if (newSelected.has(toolName)) {
      newSelected.delete(toolName);
    } else {
      newSelected.add(toolName);
    }
    setSelected(newSelected);
  };

  const selectByCategory = (category: string) => {
    const categoryTools = tools.filter((t) => t.category === category && t.status === 'available');
    const newSelected = new Set(selected);
    categoryTools.forEach((t) => newSelected.add(t.name));
    setSelected(newSelected);
  };

  const selectAvailable = () => {
    const available = tools.filter((t) => t.status === 'available');
    setSelected(new Set(available.map((t) => t.name)));
  };

  const clearAll = () => {
    setSelected(new Set());
  };

  const handleContinueFromSelection = () => {
    if (selected.size === 0) {
      // Skip research entirely
      if (onContinue) {
        onContinue();
      }
    } else {
      // Move to data collection step
      setStep('data-collection');
    }
  };

  const handleDataCollected = (data: Record<string, any>) => {
    setCollectedData(data);
    setStep('executing');
    runSelectedResearch(data);
  };

  const runSelectedResearch = async (params: Record<string, any>) => {
    if (!projectId || !clientId) {
      alert('Project and client must be selected first');
      return;
    }

    const failed: string[] = [];

    for (const tool of selected) {
      const toolParams = params[tool] || params;
      try {
        await runResearchMutation.mutateAsync({ tool, params: toolParams });
      } catch {
        // Tool failed - record and continue; successful results still shown
        failed.push(tool);
      }
    }

    if (failed.length > 0 && failed.length === selected.size) {
      alert('All research tools failed. Please check your client profile.');
      return;
    }

    if (onContinue) {
      onContinue();
    }
  };


  const formatLastRun = (date: Date | undefined): { text: string; variant: 'fresh' | 'stale' | 'never' } => {
    if (!date) return { text: 'Never run', variant: 'never' };

    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return { text: 'Today', variant: 'fresh' };
    if (diffDays === 1) return { text: 'Yesterday', variant: 'fresh' };
    if (diffDays < 7) return { text: `${diffDays} days ago`, variant: 'fresh' };
    if (diffDays < 30) return { text: `${Math.floor(diffDays / 7)} weeks ago`, variant: 'fresh' };
    if (diffDays < 365) return { text: `${Math.floor(diffDays / 30)} months ago`, variant: 'stale' };
    return { text: 'Over a year ago', variant: 'stale' };
  };

  const getStatusBadge = (status?: string) => {
    if (status === 'coming_soon') {
      return (
        <span className="inline-block rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
          Coming Soon
        </span>
      );
    }
    return (
      <span className="inline-block rounded-md bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-700">
        Available
      </span>
    );
  };

  const getCategoryTools = (category: string) => {
    return tools.filter((t) => t.category === category);
  };

  const categories = [
    { name: 'foundation', label: 'Client Foundation', description: 'Build foundational understanding' },
    { name: 'seo', label: 'SEO & Competition', description: 'Research keywords and competitors' },
    { name: 'market', label: 'Market Intelligence', description: 'Track trends and opportunities' },
    { name: 'strategy', label: 'Strategy & Planning', description: 'Plan content strategy' },
    { name: 'workshop', label: 'Workshop Assistants', description: 'Guided discovery sessions' },
  ];

  const totalPrice = Array.from(selected).reduce((sum, toolName) => {
    const tool = tools.find((t) => t.name === toolName);
    return sum + (tool?.price || 0);
  }, 0);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-slate-200 bg-white p-12 shadow-sm">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        <span className="ml-2 text-sm text-slate-600">Loading research tools...</span>
      </div>
    );
  }

  // Show data collection step
  if (step === 'data-collection') {
    return (
      <ResearchDataCollectionPanel
        selectedTools={Array.from(selected)}
        onContinue={handleDataCollected}
        onBack={() => setStep('selection')}
      />
    );
  }

  // Show executing step
  if (step === 'executing') {
    return (
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-neutral-900 p-8 shadow-sm">
        <div className="flex flex-col items-center justify-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 dark:text-blue-400" />
          <div className="text-center">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
              Running Research Tools
            </h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Executing {selected.size} research {selected.size === 1 ? 'tool' : 'tools'}...
            </p>
            <p className="text-xs text-neutral-500 dark:text-neutral-500 mt-2">
              Tools: {Array.from(selected).join(', ')}
            </p>
          </div>
          <div className="mt-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 px-4 py-3 max-w-md">
            <p className="text-sm text-blue-800 dark:text-blue-300">
              {results.size} of {selected.size} completed
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Show tool selection step
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FlaskConical className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-slate-900">Research Tools</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={selectAvailable}
            className="rounded-md border border-blue-600 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-100"
          >
            Select All Available
          </button>
          <button
            onClick={clearAll}
            className="rounded-md border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Clear
          </button>
        </div>
      </div>

      <p className="mb-6 text-sm text-slate-600">
        Select research tools to run for this project. Research adds depth to content generation and helps identify
        opportunities.
      </p>

      {totalPrice > 0 && (
        <div className="mb-4 rounded-md bg-blue-50 px-4 py-3 text-sm text-blue-800">
          <div className="flex items-center justify-between">
            <div>
              <strong>{selected.size} tools selected</strong>
              {selected.size > 0 && ` (${Array.from(selected).join(', ')})`}
            </div>
            <div className="flex items-center gap-1 font-semibold">
              <DollarSign className="h-4 w-4" />
              {totalPrice.toFixed(2)}
            </div>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {categories.map((category) => {
          const categoryTools = getCategoryTools(category.name);
          if (categoryTools.length === 0) return null;

          return (
            <div key={category.name} className="rounded-lg border border-slate-200 p-4">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">{category.label}</h4>
                  <p className="text-xs text-slate-600">{category.description}</p>
                </div>
                <button
                  onClick={() => selectByCategory(category.name)}
                  className="text-xs font-medium text-blue-600 hover:text-blue-700"
                >
                  Select All
                </button>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {categoryTools.map((tool) => {
                  const isSelected = selected.has(tool.name);
                  const isAvailable = tool.status === 'available';
                  const hasResult = results.has(tool.name);

                  return (
                    <button
                      key={tool.name}
                      onClick={() => isAvailable && toggleTool(tool.name)}
                      disabled={!isAvailable}
                      className={`group relative rounded-lg border-2 p-3 text-left transition-all ${
                        isSelected
                          ? 'border-blue-600 bg-blue-50 shadow-md'
                          : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
                      } ${!isAvailable && 'cursor-not-allowed opacity-60'}`}
                    >
                      <div className="flex items-start gap-2">
                        {isSelected ? (
                          <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-blue-600" />
                        ) : (
                          <Circle className="h-5 w-5 flex-shrink-0 text-slate-300 group-hover:text-slate-400" />
                        )}
                        <div className="flex-1 min-w-0">
                          <h5 className={`text-sm font-semibold ${isSelected ? 'text-blue-900' : 'text-slate-900'}`}>
                            {tool.label}
                          </h5>
                          {tool.description && <p className="mt-1 text-xs text-slate-600">{tool.description}</p>}
                          <div className="mt-2 flex items-center justify-between gap-2">
                            {getStatusBadge(tool.status)}
                            {tool.price && (
                              <span className="text-xs font-medium text-slate-700">${tool.price.toFixed(2)}</span>
                            )}
                          </div>
                          {(() => {
                            const lastRunDate = toolHistory.get(tool.name);
                            const lastRun = formatLastRun(lastRunDate);
                            const colorClass = lastRun.variant === 'fresh'
                              ? 'text-emerald-600 dark:text-emerald-400'
                              : lastRun.variant === 'stale'
                              ? 'text-amber-600 dark:text-amber-400'
                              : 'text-slate-500 dark:text-slate-400';

                            return (
                              <div className={`mt-2 flex items-center gap-1 text-xs ${colorClass}`}>
                                <Clock className="h-3 w-3" />
                                <span>Last run: {lastRun.text}</span>
                              </div>
                            );
                          })()}
                          {(() => {
                            const prereqs = TOOL_PREREQUISITES[tool.name];
                            if (!prereqs || (prereqs.required.length === 0 && prereqs.recommended.length === 0)) {
                              return null;
                            }

                            const status = getPrerequisiteStatus(tool.name);

                            return (
                              <div className="mt-2 space-y-1">
                                {status.requiredUnfulfilled.length > 0 && (
                                  <div className="flex items-start gap-1 text-xs text-amber-700 dark:text-amber-400">
                                    <AlertCircle className="h-3 w-3 flex-shrink-0 mt-0.5" />
                                    <span className="font-medium">Requires: {status.requiredUnfulfilled.map(p => TOOL_LABELS[p] || p).join(', ')}</span>
                                  </div>
                                )}
                                {(status.fulfilled.length > 0 || status.unfulfilled.length > 0) && (
                                  <div className="flex flex-wrap gap-1">
                                    {prereqs.required.map(prereqToolName => {
                                      const isFulfilled = isPrerequisiteFulfilled(prereqToolName);
                                      return (
                                        <span
                                          key={prereqToolName}
                                          className={`inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-xs font-semibold ${
                                            isFulfilled
                                              ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                                              : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                                          }`}
                                        >
                                          <Link2 className="h-2.5 w-2.5" />
                                          {TOOL_LABELS[prereqToolName] || prereqToolName}
                                        </span>
                                      );
                                    })}
                                    {prereqs.recommended.map(prereqToolName => {
                                      const isFulfilled = isPrerequisiteFulfilled(prereqToolName);
                                      return (
                                        <span
                                          key={prereqToolName}
                                          className={`inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-xs font-normal ${
                                            isFulfilled
                                              ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400'
                                              : 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400'
                                          }`}
                                        >
                                          <Link2 className="h-2.5 w-2.5" />
                                          {TOOL_LABELS[prereqToolName] || prereqToolName}
                                        </span>
                                      );
                                    })}
                                  </div>
                                )}
                              </div>
                            );
                          })()}
                          {hasResult && (
                            <div className="mt-2 rounded bg-emerald-50 px-2 py-1 text-xs text-emerald-700">
                              ✓ Research completed
                            </div>
                          )}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 flex items-center justify-between border-t border-slate-200 pt-4">
        <div className="text-sm text-slate-600">
          {selected.size === 0 && 'Research is optional - you can skip this step'}
          {selected.size > 0 && 'Click "Continue" to provide required data and run research'}
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleContinueFromSelection}
            disabled={!projectId || !clientId}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {selected.size === 0 ? 'Skip Research' : 'Continue'}
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
});
