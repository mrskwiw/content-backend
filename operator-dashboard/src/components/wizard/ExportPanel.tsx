import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { generatorApi } from '@/api/generator';
import { researchApi } from '@/api/research';
import type { ExportInput } from '@/types/domain';
import { Download, Loader2, CheckCircle, FlaskConical, DollarSign, Info } from 'lucide-react';

interface Props {
  projectId: string;
  clientId: string;
  onExported?: () => void;
}

export function ExportPanel({ projectId, clientId, onExported }: Props) {
  const [format, setFormat] = useState<'txt' | 'md' | 'docx'>('docx');
  const [includeAuditLog, setIncludeAuditLog] = useState(false);
  const [includeResearch, setIncludeResearch] = useState(false);

  // Fetch research results for preview
  // IMPORTANT: Query by projectId to match what will be included in export
  const { data: researchResults } = useQuery({
    queryKey: ['research-results', projectId],
    queryFn: () => researchApi.getProjectResearchResults(projectId),
    enabled: !!projectId,
  });

  const completedResearch = researchResults?.results?.filter(r => r.status === 'completed') || [];
  const totalInvestment = completedResearch.reduce((sum, r) => sum + (r.toolPrice || 0), 0);

  const exportMut = useMutation({
    mutationFn: (input: ExportInput) => generatorApi.exportPackage(input),
    onSuccess: () => onExported?.(),
  });

  const handleExport = () => {
    exportMut.mutate({
      projectId,
      clientId,
      format,
      includeAuditLog,
      includeResearch,
    });
  };

  return (
    <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">Export Package</h3>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">Generate deliverable file and create download record.</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="rounded-md border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-3 py-2 text-sm text-neutral-800 dark:text-neutral-200"
            value={format}
            onChange={(e) => setFormat(e.target.value as 'txt' | 'md' | 'docx')}
          >
            <option value="docx">DOCX</option>
            <option value="md">Markdown</option>
            <option value="txt">TXT</option>
          </select>
          <label className="inline-flex items-center gap-2 rounded-md border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-3 py-2 text-sm text-neutral-800 dark:text-neutral-200">
            <input
              type="checkbox"
              checked={includeAuditLog}
              onChange={(e) => setIncludeAuditLog(e.target.checked)}
              className="h-4 w-4 rounded border-neutral-300 dark:border-neutral-600 text-blue-600 focus:ring-blue-500 dark:focus:ring-blue-400"
            />
            Include audit log
          </label>
          <label className="inline-flex items-center gap-2 rounded-md border-2 border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 px-3 py-2 text-sm font-medium text-amber-900 dark:text-amber-100 hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors">
            <input
              type="checkbox"
              checked={includeResearch}
              onChange={(e) => setIncludeResearch(e.target.checked)}
              className="h-4 w-4 rounded border-amber-400 dark:border-amber-700 text-amber-600 focus:ring-amber-500 dark:focus:ring-amber-400"
            />
            <FlaskConical className="h-4 w-4" />
            Include research results
            {completedResearch.length > 0 && (
              <span className="ml-1 rounded-full bg-amber-200 dark:bg-amber-900/40 px-2 py-0.5 text-xs font-semibold text-amber-900 dark:text-amber-200">
                {completedResearch.length}
              </span>
            )}
          </label>
          <button
            disabled={exportMut.isPending}
            onClick={handleExport}
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 dark:hover:bg-indigo-800 disabled:opacity-50"
          >
            {exportMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            {exportMut.isPending ? 'Exporting...' : 'Export'}
          </button>
        </div>
      </div>

      {/* Research Preview */}
      {includeResearch && completedResearch.length > 0 && (
        <div className="mt-4 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-amber-900 dark:text-amber-100 mb-2">
                Research Results to Include
              </h4>
              <div className="flex items-center gap-4 mb-3 text-sm text-amber-800 dark:text-amber-200">
                <span className="flex items-center gap-1.5">
                  <FlaskConical className="h-4 w-4" />
                  <strong>{completedResearch.length}</strong> {completedResearch.length === 1 ? 'tool' : 'tools'}
                </span>
                {totalInvestment > 0 && (
                  <span className="flex items-center gap-1.5">
                    <DollarSign className="h-4 w-4" />
                    <strong>${totalInvestment.toFixed(0)}</strong> research investment
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {completedResearch.map((result) => (
                  <span
                    key={result.id}
                    className="inline-flex items-center gap-1 rounded-md bg-white dark:bg-neutral-900 px-2.5 py-1 text-xs font-medium text-amber-900 dark:text-amber-100 border border-amber-300 dark:border-amber-700"
                  >
                    {result.toolLabel}
                    {result.toolPrice && (
                      <span className="text-amber-700 dark:text-amber-300">(${result.toolPrice})</span>
                    )}
                  </span>
                ))}
              </div>
              <p className="mt-3 text-xs text-amber-700 dark:text-amber-300">
                Research findings will be formatted and appended to your deliverable with detailed insights and recommendations.
              </p>
            </div>
          </div>
        </div>
      )}

      {includeResearch && completedResearch.length === 0 && (
        <div className="mt-4 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-neutral-500 dark:text-neutral-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                No research results available for this client. Research tools can be run from the Wizard.
              </p>
            </div>
          </div>
        </div>
      )}

      {exportMut.isSuccess && (
        <div className="mt-3 flex items-center gap-2 rounded-md bg-green-50 dark:bg-green-900/20 px-3 py-2 text-sm text-green-700 dark:text-green-300">
          <CheckCircle className="h-4 w-4" />
          Export created successfully! Check the Deliverables page to download.
        </div>
      )}
      {exportMut.error && (
        <div className="mt-3 rounded-md bg-rose-50 dark:bg-rose-900/20 px-3 py-2 text-sm text-rose-700 dark:text-rose-300">
          {(exportMut.error as Error).message || 'Export failed'}
        </div>
      )}
    </div>
  );
}
