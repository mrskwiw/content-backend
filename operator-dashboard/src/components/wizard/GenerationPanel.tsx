import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { generatorApi } from '@/api/generator';
import { runsApi } from '@/api/runs';
import type { GenerateAllInput, Run } from '@/types/domain';
import { Play, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { getApiErrorMessage } from '@/utils/apiError';

interface Props {
  projectId: string;
  clientId: string;
  templateQuantities?: Record<number, number>;
  customTopics?: string[];  // NEW: topic override for content generation
  targetPlatform?: string;  // NEW: target platform for platform-specific generation
  onStarted?: (run: Run) => void;
}

export function GenerationPanel({ projectId, clientId, templateQuantities, customTopics, targetPlatform, onStarted }: Props) {
  const [runId, setRunId] = useState<string | null>(null);
  const [pollingEnabled, setPollingEnabled] = useState(false);
  // Ref to prevent onStarted firing multiple times when parent re-renders
  const onStartedCalledRef = useRef(false);
  const onStartedRef = useRef(onStarted);
  useEffect(() => { onStartedRef.current = onStarted; }, [onStarted]);
  // Reset the guard when a new run starts
  useEffect(() => { onStartedCalledRef.current = false; }, [runId]);
  // Safety: stop polling after 5 minutes to prevent infinite spinner
  useEffect(() => {
    if (!pollingEnabled) return;
    const timeout = setTimeout(() => setPollingEnabled(false), 5 * 60 * 1000);
    return () => clearTimeout(timeout);
  }, [pollingEnabled]);

  const generate = useMutation({
    mutationFn: (input: GenerateAllInput) => generatorApi.generateAll(input),
    onSuccess: (run) => {
      setRunId(run.id);
      setPollingEnabled(true);
    },
    onError: (error) => {
      alert(`Failed to start generation: ${getApiErrorMessage(error)}`);
    },
  });

  // Poll for run status every 2s while pollingEnabled; effect handles stopping
  const { data: runStatus } = useQuery({
    queryKey: ['run-status', runId],
    queryFn: () => (runId ? runsApi.get(runId) : null),
    enabled: pollingEnabled && !!runId,
    refetchInterval: 2000,
    staleTime: 0,
  });

  // Handle status changes — use ref for onStarted to avoid effect loop when parent re-renders
  useEffect(() => {
    if (runStatus?.status === 'succeeded' && !onStartedCalledRef.current) {
      onStartedCalledRef.current = true;
      setPollingEnabled(false);
      onStartedRef.current?.(runStatus);
    } else if (runStatus?.status === 'failed') {
      setPollingEnabled(false);
    }
  }, [runStatus]);

  const isGenerating = generate.isPending || pollingEnabled;
  // Keep button disabled after success to prevent accidental re-generation
  const isSucceeded = runStatus?.status === 'succeeded';
  const statusMessage = runStatus?.status === 'running'
    ? 'Generating posts...'
    : runStatus?.status === 'pending'
    ? 'Queued...'
    : generate.isPending
    ? 'Starting...'
    : isSucceeded
    ? 'Loading results...'
    : null;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Generate All</h3>
          <p className="text-xs text-slate-600">
            {statusMessage || 'Run full batch generation for this project.'}
          </p>
        </div>
        <button
          disabled={isGenerating || isSucceeded}
          onClick={() =>
            generate.mutate({
              projectId,
              clientId,
              isBatch: true,
              templateQuantities,
              customTopics,
              targetPlatform,
            })
          }
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {isGenerating ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : isSucceeded ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : runStatus?.status === 'failed' ? (
            <XCircle className="h-4 w-4" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {isGenerating ? statusMessage : isSucceeded ? 'Loading results...' : runStatus?.status === 'failed' ? 'Failed' : 'Generate All'}
        </button>
      </div>
      {generate.error && (
        <div className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {(generate.error as Error).message || 'Failed to queue generation'}
        </div>
      )}
      {runStatus?.status === 'failed' && runStatus.errorMessage && (
        <div className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">
          Generation failed: {runStatus.errorMessage}
        </div>
      )}
      {isSucceeded && (
        <div className="mt-3 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          Generation complete! Loading quality results...
        </div>
      )}
    </div>
  );
}
