import { useState } from 'react';
import { X, FlaskConical, Calendar, Clock, CheckCircle2, AlertCircle, Loader2, Download } from 'lucide-react';
import { format } from 'date-fns';
import type { ResearchResult } from '@/types/domain';
import { researchApi } from '@/api/research';

interface ResearchResultsDrawerProps {
  result: ResearchResult | null;
  open: boolean;
  onClose: () => void;
}

export function ResearchResultsDrawer({ result, open, onClose }: ResearchResultsDrawerProps) {
  const [expandedOutput, setExpandedOutput] = useState<string | null>(null);
  const [outputContent, setOutputContent] = useState<Record<string, string>>({});
  const [loadingOutput, setLoadingOutput] = useState<string | null>(null);

  if (!open || !result) return null;

  const formatToolName = (name: string) => {
    return name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const handleViewOutput = async (outputFormat: string) => {
    // If already expanded, collapse it
    if (expandedOutput === outputFormat) {
      setExpandedOutput(null);
      return;
    }

    // If content already loaded, just expand
    if (outputContent[outputFormat]) {
      setExpandedOutput(outputFormat);
      return;
    }

    // Fetch content
    setLoadingOutput(outputFormat);
    try {
      const data = await researchApi.getResearchOutputContent(result.id, outputFormat);
      setOutputContent((prev) => ({ ...prev, [outputFormat]: data.content }));
      setExpandedOutput(outputFormat);
    } catch (error) {
      console.error('Failed to load output content:', error);
      alert(`Failed to load ${outputFormat} content. The file may not exist or be accessible.`);
    } finally {
      setLoadingOutput(null);
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-3xl bg-white dark:bg-neutral-900 shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 px-6 py-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <FlaskConical className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                  {result.toolLabel || formatToolName(result.toolName)}
                </h2>
              </div>
              <div className="flex items-center gap-4 text-sm text-neutral-600 dark:text-neutral-400">
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {format(new Date(result.createdAt), 'MMM d, yyyy')}
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {format(new Date(result.createdAt), 'h:mm a')}
                </div>
                {result.durationSeconds && (
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {result.durationSeconds.toFixed(1)}s
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-2 text-neutral-500 hover:bg-neutral-200 dark:hover:bg-neutral-700 dark:text-neutral-400"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Status Badge */}
          <div className="mt-3">
            <span
              className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${
                result.status === 'completed'
                  ? 'bg-emerald-100 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-300'
                  : result.status === 'failed'
                  ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
                  : 'bg-amber-100 dark:bg-amber-900/20 text-amber-800 dark:text-amber-300'
              }`}
            >
              {result.status === 'completed' ? (
                <CheckCircle2 className="mr-1.5 h-4 w-4" />
              ) : result.status === 'failed' ? (
                <AlertCircle className="mr-1.5 h-4 w-4" />
              ) : null}
              {result.status.charAt(0).toUpperCase() + result.status.slice(1)}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {/* Error Message */}
          {result.status === 'failed' && result.errorMessage && (
            <div className="mb-6 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                <div>
                  <h3 className="font-medium text-red-900 dark:text-red-100">Error</h3>
                  <p className="mt-1 text-sm text-red-800 dark:text-red-200">{result.errorMessage as string}</p>
                </div>
              </div>
            </div>
          ) as React.ReactNode}

          {/* Executive Summary */}
          {result.data && typeof result.data === 'object' && 'summary' in result.data && result.data.summary && (
            <section className="mb-6">
              <h3 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Executive Summary
              </h3>
              <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 p-4">
                <p className="text-sm text-neutral-900 dark:text-neutral-100 leading-relaxed">
                  {result.data.summary as string}
                </p>
              </div>
            </section>
          ) as React.ReactNode}

          {/* Key Findings (if available in data) */}
          {result.data?.key_findings && Array.isArray(result.data.key_findings) && (
            <section className="mb-6">
              <h3 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Key Findings
              </h3>
              <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4">
                <ul className="space-y-2">
                  {result.data.key_findings.map((finding: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-neutral-700 dark:text-neutral-300">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span>{finding}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          )}

          {/* Recommendations (if available in data) */}
          {result.data?.recommendations && Array.isArray(result.data.recommendations) && (
            <section className="mb-6">
              <h3 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Recommendations
              </h3>
              <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4">
                <ul className="space-y-2">
                  {result.data.recommendations.map((rec: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-neutral-700 dark:text-neutral-300">
                      <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary-100 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 text-xs font-medium flex-shrink-0">
                        {idx + 1}
                      </span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          )}

          {/* Output Files */}
          {result.outputs && Object.keys(result.outputs).length > 0 && (
            <section className="mb-6">
              <h3 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                Output Files
              </h3>
              <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 overflow-hidden">
                <div className="divide-y divide-neutral-200 dark:divide-neutral-700">
                  {Object.entries(result.outputs).map(([format, path]) => (
                    <div key={format} className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center rounded bg-neutral-200 dark:bg-neutral-700 px-2 py-1 text-xs font-mono font-medium text-neutral-700 dark:text-neutral-300">
                            {format.toUpperCase()}
                          </span>
                          <span className="text-sm text-neutral-600 dark:text-neutral-400 truncate max-w-md">
                            {path}
                          </span>
                        </div>
                        <button
                          onClick={() => handleViewOutput(format)}
                          disabled={loadingOutput === format}
                          className="inline-flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 disabled:opacity-50"
                        >
                          {loadingOutput === format ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              Loading...
                            </>
                          ) : expandedOutput === format ? (
                            'Hide'
                          ) : (
                            <>
                              <Download className="h-4 w-4" />
                              View
                            </>
                          )}
                        </button>
                      </div>

                      {/* Expanded Content */}
                      {expandedOutput === format && outputContent[format] && (
                        <div className="mt-3 rounded-md border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 p-4 max-h-96 overflow-y-auto">
                          <pre className="text-xs text-neutral-800 dark:text-neutral-200 whitespace-pre-wrap font-mono">
                            {outputContent[format]}
                          </pre>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Raw Data (collapsible) */}
          {result.data && (
            <section className="mb-6">
              <details className="group">
                <summary className="cursor-pointer text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2 list-none flex items-center gap-2">
                  <span className="inline-block transition-transform group-open:rotate-90">▶</span>
                  Raw Data
                </summary>
                <div className="mt-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 p-4">
                  <pre className="text-xs text-neutral-800 dark:text-neutral-200 overflow-x-auto">
                    {JSON.stringify(result.data, null, 2)}
                  </pre>
                </div>
              </details>
            </section>
          )}

          {/* Metadata */}
          {result.params && Object.keys(result.params).length > 0 && (
            <section>
              <details className="group">
                <summary className="cursor-pointer text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2 list-none flex items-center gap-2">
                  <span className="inline-block transition-transform group-open:rotate-90">▶</span>
                  Parameters
                </summary>
                <div className="mt-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 p-4">
                  <pre className="text-xs text-neutral-800 dark:text-neutral-200 overflow-x-auto">
                    {JSON.stringify(result.params, null, 2)}
                  </pre>
                </div>
              </details>
            </section>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 px-6 py-4">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="rounded-lg bg-neutral-200 dark:bg-neutral-700 px-4 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-300 dark:hover:bg-neutral-600"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
