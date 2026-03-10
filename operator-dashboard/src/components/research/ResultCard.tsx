import React from 'react';
import { CheckCircle2, Clock, Download, Eye, DollarSign } from 'lucide-react';
import { ResearchResult } from '../../types/domain';

interface ResultCardProps {
  result: ResearchResult;
  onView: () => void;
  onDownload?: () => void;
}

export function ResultCard({ result, onView, onDownload }: ResultCardProps) {
  const formatDuration = (seconds?: number) => {
    if (!seconds) return '—';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatCost = (cost?: number) => {
    if (cost === undefined || cost === null) return '—';
    return `$${cost.toFixed(2)}`;
  };

  return (
    <div className="bg-white dark:bg-neutral-900 rounded-lg border border-gray-200 dark:border-neutral-700 p-4 hover:border-gray-300 dark:hover:border-neutral-600 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Tool Name and Status */}
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {result.toolLabel || result.toolName}
            </h3>
            <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 rounded">
              <CheckCircle2 className="h-3 w-3" />
              Completed
            </span>
            {result.isCachedResult && (
              <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 rounded">
                Cached
              </span>
            )}
          </div>

          {/* Metadata */}
          <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{new Date(result.createdAt).toLocaleDateString()} • {formatDuration(result.durationSeconds)}</span>
            </div>
            {result.toolPrice !== undefined && (
              <div className="flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                <span>{formatCost(result.toolPrice)} → {formatCost(result.actualCostUsd)} actual</span>
              </div>
            )}
          </div>

          {/* Outputs */}
          {result.outputs && Object.keys(result.outputs).length > 0 && (
            <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Outputs: {Object.keys(result.outputs).map((format, idx) => (
                <span key={format}>
                  {idx > 0 && ', '}
                  <span className="font-medium">{format}</span>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={onView}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
          >
            <Eye className="h-4 w-4" />
            View
          </button>
          {onDownload && (
            <button
              onClick={onDownload}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-800 rounded-lg transition-colors"
            >
              <Download className="h-4 w-4" />
              Download
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
