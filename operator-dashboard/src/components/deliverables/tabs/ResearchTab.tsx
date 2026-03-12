import { ChevronDown, ChevronRight, Calendar, DollarSign, Clock } from 'lucide-react';
import { useState } from 'react';
import type { DeliverableDetails } from '@/types/domain';

interface Props {
  deliverable: DeliverableDetails;
}

export function ResearchTab({ deliverable }: Props) {
  const [expandedResults, setExpandedResults] = useState<Set<string>>(new Set());

  const toggleExpand = (resultId: string) => {
    setExpandedResults(prev => {
      const next = new Set(prev);
      if (next.has(resultId)) {
        next.delete(resultId);
      } else {
        next.add(resultId);
      }
      return next;
    });
  };

  const researchResults = deliverable.researchResults || [];

  if (researchResults.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <div className="text-center">
          <p className="text-neutral-600 dark:text-neutral-400 mb-2">No research results</p>
          <p className="text-sm text-neutral-500 dark:text-neutral-500">
            Research tools weren't used for this deliverable
          </p>
        </div>
      </div>
    );
  }

  const totalCost = researchResults.reduce((sum, r) => sum + (r.actualCostUsd || 0), 0);

  return (
    <div className="p-6 space-y-4">
      {/* Summary Card */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
              Research Investment
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              {researchResults.length} tool{researchResults.length !== 1 ? 's' : ''} executed
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
              ${(totalCost ?? 0).toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Research Results List */}
      <div className="space-y-3">
        {researchResults.map((result) => (
          <div
            key={result.id}
            className="border border-neutral-200 dark:border-neutral-700 rounded-lg overflow-hidden"
          >
            {/* Header - Always Visible */}
            <button
              onClick={() => toggleExpand(result.id)}
              className="w-full flex items-center justify-between p-4 hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition-colors"
            >
              <div className="flex items-center gap-3 flex-1">
                {expandedResults.has(result.id) ? (
                  <ChevronDown className="h-4 w-4 text-neutral-500 dark:text-neutral-400 flex-shrink-0" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-neutral-500 dark:text-neutral-400 flex-shrink-0" />
                )}
                <div className="text-left flex-1">
                  <p className="font-medium text-neutral-900 dark:text-neutral-100">
                    {result.toolLabel || result.toolName}
                  </p>
                  <div className="flex items-center gap-4 mt-1 text-xs text-neutral-500 dark:text-neutral-400">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {new Date(result.createdAt).toLocaleDateString()}
                    </span>
                    {result.actualCostUsd !== null && result.actualCostUsd !== undefined && (
                      <span className="flex items-center gap-1">
                        <DollarSign className="h-3 w-3" />
                        ${(result.actualCostUsd ?? 0).toFixed(2)}
                      </span>
                    )}
                    {result.durationSeconds !== null && result.durationSeconds !== undefined && (
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {(result.durationSeconds ?? 0).toFixed(1)}s
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${
                  result.status === 'completed'
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                    : result.status === 'failed'
                    ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                    : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300'
                }`}
              >
                {result.status}
              </span>
            </button>

            {/* Expanded Content */}
            {expandedResults.has(result.id) && (
              <div className="border-t border-neutral-200 dark:border-neutral-700 p-4 bg-neutral-50 dark:bg-neutral-800/30">
                {result.summary && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                      Summary
                    </p>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      {result.summary}
                    </p>
                  </div>
                )}

                {result.errorMessage && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-3">
                    <p className="text-sm text-red-800 dark:text-red-300">
                      {result.errorMessage}
                    </p>
                  </div>
                )}

                <div className="flex gap-2 mt-3">
                  <a
                    href={`/dashboard/research-tools/results?id=${result.id}`}
                    className="text-xs px-3 py-1.5 bg-blue-600 dark:bg-blue-500 text-white rounded hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors"
                  >
                    View Full Report
                  </a>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
