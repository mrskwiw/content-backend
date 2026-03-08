import { useQuery } from '@tanstack/react-query';
import { FlaskConical, DollarSign, Calendar, Eye, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import { researchApi } from '@/api/research';

interface Props {
  clientId: string;
  onViewAll?: () => void;
}

export function ResearchDashboardWidget({ clientId, onViewAll }: Props) {
  const { data: researchResults, isLoading } = useQuery({
    queryKey: ['research-results', clientId],
    queryFn: () => researchApi.getClientResearchResults(clientId),
    enabled: !!clientId,
  });

  if (isLoading) {
    return (
      <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-neutral-400" />
        </div>
      </div>
    );
  }

  const completedResearch = researchResults?.results?.filter(r => r.status === 'completed') || [];
  const totalInvestment = completedResearch.reduce((sum, r) => sum + (r.toolPrice || 0), 0);
  const mostRecent = completedResearch.length > 0
    ? completedResearch.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())[0]
    : null;

  return (
    <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="flex items-center gap-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          <FlaskConical className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          Research Insights
        </h3>
        {completedResearch.length > 0 && onViewAll && (
          <button
            onClick={onViewAll}
            className="flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
          >
            <Eye className="h-4 w-4" />
            View All
          </button>
        )}
      </div>

      {completedResearch.length === 0 ? (
        <div className="text-center py-8">
          <FlaskConical className="h-12 w-12 mx-auto text-neutral-300 dark:text-neutral-600 mb-3" />
          <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-2">
            No research results yet
          </p>
          <p className="text-xs text-neutral-500 dark:text-neutral-500">
            Run research tools from the Wizard to gather insights
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 p-3">
              <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 mb-1">
                <FlaskConical className="h-4 w-4" />
                <span className="text-xs font-medium">Tools Completed</span>
              </div>
              <p className="text-2xl font-bold text-amber-900 dark:text-amber-100">
                {completedResearch.length}
              </p>
            </div>

            {totalInvestment > 0 && (
              <div className="rounded-lg bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-200 dark:border-emerald-800 p-3">
                <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 mb-1">
                  <DollarSign className="h-4 w-4" />
                  <span className="text-xs font-medium">Investment</span>
                </div>
                <p className="text-2xl font-bold text-emerald-900 dark:text-emerald-100">
                  ${totalInvestment.toFixed(0)}
                </p>
              </div>
            )}
          </div>

          {/* Most Recent Research */}
          {mostRecent && (
            <div className="rounded-lg bg-neutral-50 dark:bg-neutral-800/50 border border-neutral-200 dark:border-neutral-700 p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
                  Most Recent
                </span>
                <div className="flex items-center gap-1 text-xs text-neutral-500 dark:text-neutral-400">
                  <Calendar className="h-3 w-3" />
                  {format(new Date(mostRecent.createdAt), 'MMM d, yyyy')}
                </div>
              </div>
              <p className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
                {mostRecent.toolLabel}
              </p>
              {mostRecent.toolPrice && (
                <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1">
                  ${mostRecent.toolPrice} research tool
                </p>
              )}
            </div>
          )}

          {/* Research Tools List */}
          <div>
            <p className="text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-2">
              Completed Research
            </p>
            <div className="flex flex-wrap gap-1.5">
              {completedResearch.slice(0, 6).map((result) => (
                <span
                  key={result.id}
                  className="inline-flex items-center rounded-md bg-amber-100 dark:bg-amber-900/20 px-2 py-1 text-xs font-medium text-amber-900 dark:text-amber-300"
                  title={result.toolLabel || undefined}
                >
                  {result.toolLabel}
                </span>
              ))}
              {completedResearch.length > 6 && (
                <span className="inline-flex items-center rounded-md bg-neutral-100 dark:bg-neutral-800 px-2 py-1 text-xs font-medium text-neutral-700 dark:text-neutral-300">
                  +{completedResearch.length - 6} more
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
