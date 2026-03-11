/**
 * Token Usage Display Component
 *
 * Shows token usage and cost information inline after API calls.
 * Displays input/output tokens, cache usage, and cost.
 */
import { Zap, Database, DollarSign, TrendingDown } from 'lucide-react';

interface TokenUsageDisplayProps {
  inputTokens?: number;
  outputTokens?: number;
  cacheCreationTokens?: number;
  cacheReadTokens?: number;
  costUsd?: number;
  estimatedCostUsd?: number;
  variant?: 'compact' | 'detailed';
  showCacheSavings?: boolean;
}

export function TokenUsageDisplay({
  inputTokens = 0,
  outputTokens = 0,
  cacheCreationTokens = 0,
  cacheReadTokens = 0,
  costUsd,
  estimatedCostUsd,
  variant = 'compact',
  showCacheSavings = true,
}: TokenUsageDisplayProps) {
  const totalTokens = inputTokens + outputTokens + cacheCreationTokens + cacheReadTokens;

  // Calculate cache savings (cache reads are ~10x cheaper)
  const cacheSavingsUsd = cacheReadTokens > 0 ? (cacheReadTokens / 1_000_000) * 2.7 : 0;

  // Color coding based on cost
  const getCostColor = (cost: number) => {
    if (cost < 0.01) return 'text-emerald-600 dark:text-emerald-400';
    if (cost < 0.1) return 'text-blue-600 dark:text-blue-400';
    if (cost < 1.0) return 'text-amber-600 dark:text-amber-400';
    return 'text-red-600 dark:text-red-400';
  };

  const formatTokens = (tokens: number) => tokens.toLocaleString();
  const formatCost = (cost: number) => {
    if (cost >= 1) return `$${cost.toFixed(2)}`;
    return `$${cost.toFixed(4)}`;
  };

  if (variant === 'compact') {
    return (
      <div className="inline-flex items-center gap-3 text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 px-3 py-1.5 rounded-md border border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-1">
          <Zap className="h-3 w-3" />
          <span>{formatTokens(totalTokens)} tokens</span>
        </div>

        {costUsd !== undefined && (
          <div className={`flex items-center gap-1 font-medium ${getCostColor(costUsd)}`}>
            <DollarSign className="h-3 w-3" />
            <span>{formatCost(costUsd)}</span>
          </div>
        )}

        {showCacheSavings && cacheSavingsUsd > 0 && (
          <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
            <TrendingDown className="h-3 w-3" />
            <span>-{formatCost(cacheSavingsUsd)} saved</span>
          </div>
        )}
      </div>
    );
  }

  // Detailed variant
  return (
    <div className="bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Zap className="h-4 w-4 text-slate-600 dark:text-slate-400" />
        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Token Usage
        </h4>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-slate-600 dark:text-slate-400 text-xs mb-1">Input Tokens</div>
          <div className="font-medium text-slate-900 dark:text-slate-100">
            {formatTokens(inputTokens)}
          </div>
        </div>

        <div>
          <div className="text-slate-600 dark:text-slate-400 text-xs mb-1">Output Tokens</div>
          <div className="font-medium text-slate-900 dark:text-slate-100">
            {formatTokens(outputTokens)}
          </div>
        </div>

        {(cacheCreationTokens > 0 || cacheReadTokens > 0) && (
          <>
            <div>
              <div className="text-slate-600 dark:text-slate-400 text-xs mb-1 flex items-center gap-1">
                <Database className="h-3 w-3" />
                Cache Creation
              </div>
              <div className="font-medium text-slate-900 dark:text-slate-100">
                {formatTokens(cacheCreationTokens)}
              </div>
            </div>

            <div>
              <div className="text-slate-600 dark:text-slate-400 text-xs mb-1 flex items-center gap-1">
                <Database className="h-3 w-3" />
                Cache Read
              </div>
              <div className="font-medium text-emerald-600 dark:text-emerald-400">
                {formatTokens(cacheReadTokens)}
              </div>
            </div>
          </>
        )}
      </div>

      {(costUsd !== undefined || estimatedCostUsd !== undefined) && (
        <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between">
            <div className="text-slate-600 dark:text-slate-400 text-xs">Total Cost</div>
            <div className={`text-lg font-bold ${getCostColor(costUsd || estimatedCostUsd || 0)}`}>
              {costUsd !== undefined ? formatCost(costUsd) : `~${formatCost(estimatedCostUsd || 0)}`}
            </div>
          </div>

          {showCacheSavings && cacheSavingsUsd > 0 && (
            <div className="flex items-center justify-between mt-2">
              <div className="text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-1">
                <TrendingDown className="h-3 w-3" />
                Cache Savings
              </div>
              <div className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                {formatCost(cacheSavingsUsd)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
