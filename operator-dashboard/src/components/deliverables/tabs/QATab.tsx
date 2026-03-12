import type { DeliverableDetails } from '@/types/domain';
import { CheckCircle2, AlertCircle, BarChart3 } from 'lucide-react';

interface Props {
  deliverable: DeliverableDetails;
}

export function QATab({ deliverable }: Props) {
  if (!deliverable.qaSummary) {
    return (
      <div className="flex flex-col items-center justify-center h-64 p-6">
        <AlertCircle className="h-12 w-12 text-neutral-300 dark:text-neutral-600 mb-3" />
        <p className="text-neutral-500 dark:text-neutral-400 text-sm text-center">
          No quality metrics available
        </p>
        <p className="text-neutral-400 dark:text-neutral-500 text-xs text-center mt-1">
          Quality analysis requires posts from a generation run
        </p>
      </div>
    );
  }

  const qa = deliverable.qaSummary;
  const approvalRate = (qa?.totalPosts ?? 0) > 0
    ? ((qa?.approvedCount ?? 0) / (qa?.totalPosts ?? 0) * 100).toFixed(1)
    : '0';

  return (
    <div className="p-6 space-y-6">
      {/* Summary stats */}
      <div>
        <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-3 flex items-center gap-2">
          <BarChart3 className="h-4 w-4" />
          Quality Summary
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-neutral-50 dark:bg-neutral-800/50 p-4 rounded-lg">
            <div className="text-xs text-neutral-500 dark:text-neutral-400 uppercase">Total Posts</div>
            <div className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mt-1">
              {qa.totalPosts}
            </div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
            <div className="text-xs text-green-600 dark:text-green-400 uppercase">Approved</div>
            <div className="text-2xl font-semibold text-green-700 dark:text-green-300 mt-1">
              {qa.approvedCount}
              <span className="text-sm text-green-600 dark:text-green-400 ml-2">({approvalRate}%)</span>
            </div>
          </div>
          {qa.flaggedCount > 0 && (
            <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
              <div className="text-xs text-red-600 dark:text-red-400 uppercase">Flagged</div>
              <div className="text-2xl font-semibold text-red-700 dark:text-red-300 mt-1">
                {qa.flaggedCount}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Metrics */}
      <div>
        <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-3">Content Metrics</h3>
        <div className="space-y-3">
          {qa.avgReadability !== null && qa.avgReadability !== undefined && (
            <div className="flex items-center justify-between py-2 border-b border-neutral-100 dark:border-neutral-800">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Average Readability</span>
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                {(qa?.avgReadability ?? 0).toFixed(1)}
              </span>
            </div>
          )}
          {qa.avgWordCount !== null && qa.avgWordCount !== undefined && (
            <div className="flex items-center justify-between py-2 border-b border-neutral-100 dark:border-neutral-800">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Average Word Count</span>
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                {Math.round(qa.avgWordCount)} words
              </span>
            </div>
          )}
          {qa.ctaPercentage !== null && qa.ctaPercentage !== undefined && (
            <div className="flex items-center justify-between py-2 border-b border-neutral-100 dark:border-neutral-800">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Posts with CTA</span>
              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                {(qa?.ctaPercentage ?? 0).toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Common flags */}
      {qa.commonFlags && qa.commonFlags.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-3">Common Issues</h3>
          <div className="space-y-2">
            {qa.commonFlags.map((flag, index) => (
              <div
                key={index}
                className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-300 bg-orange-50 dark:bg-orange-900/20 p-2 rounded"
              >
                <AlertCircle className="h-4 w-4 text-orange-600 dark:text-orange-400 flex-shrink-0" />
                <span>{flag}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quality indicator */}
      <div className="pt-4 border-t border-neutral-200 dark:border-neutral-700">
        {parseFloat(approvalRate) >= 90 ? (
          <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/20 p-3 rounded">
            <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
            <span className="font-medium">
              Excellent quality - {approvalRate}% approval rate
            </span>
          </div>
        ) : parseFloat(approvalRate) >= 70 ? (
          <div className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-900/20 p-3 rounded">
            <BarChart3 className="h-5 w-5 flex-shrink-0" />
            <span className="font-medium">
              Good quality - {approvalRate}% approval rate
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-orange-700 dark:text-orange-300 bg-orange-50 dark:bg-orange-900/20 p-3 rounded">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span className="font-medium">
              Needs review - {approvalRate}% approval rate
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
