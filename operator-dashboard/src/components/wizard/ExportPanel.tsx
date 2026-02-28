import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { generatorApi } from '@/api/generator';
import type { ExportInput } from '@/types/domain';
import { Download, Loader2, CheckCircle } from 'lucide-react';

interface Props {
  projectId: string;
  clientId: string;
  onExported?: () => void;
}

export function ExportPanel({ projectId, clientId, onExported }: Props) {
  const [format, setFormat] = useState<'txt' | 'md' | 'docx'>('docx');
  const [includeAuditLog, setIncludeAuditLog] = useState(false);
  const [includeResearch, setIncludeResearch] = useState(false);

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
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Export Package</h3>
          <p className="text-xs text-slate-600">Generate deliverable file and create download record.</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
            value={format}
            onChange={(e) => setFormat(e.target.value as 'txt' | 'md' | 'docx')}
          >
            <option value="docx">DOCX</option>
            <option value="md">Markdown</option>
            <option value="txt">TXT</option>
          </select>
          <label className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800">
            <input
              type="checkbox"
              checked={includeAuditLog}
              onChange={(e) => setIncludeAuditLog(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            Include audit log
          </label>
          <label className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800">
            <input
              type="checkbox"
              checked={includeResearch}
              onChange={(e) => setIncludeResearch(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            Include research results
          </label>
          <button
            disabled={exportMut.isPending}
            onClick={handleExport}
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
          >
            {exportMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            {exportMut.isPending ? 'Exporting...' : 'Export'}
          </button>
        </div>
      </div>
      {exportMut.isSuccess && (
        <div className="mt-3 flex items-center gap-2 rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
          <CheckCircle className="h-4 w-4" />
          Export created successfully! Check the Deliverables page to download.
        </div>
      )}
      {exportMut.error && (
        <div className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {(exportMut.error as Error).message || 'Export failed'}
        </div>
      )}
    </div>
  );
}
