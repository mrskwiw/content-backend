import { useState } from 'react';
import { X, Loader2, BookOpen, Plus, Trash2 } from 'lucide-react';
import type { CreateStoryInput } from '@/api/stories';

interface AddStoryDialogProps {
  clientId: string;
  projectId?: string;
  open: boolean;
  onClose: () => void;
  onSubmit: (story: CreateStoryInput) => void;
  isSubmitting?: boolean;
}

export function AddStoryDialog({
  clientId,
  projectId,
  open,
  onClose,
  onSubmit,
  isSubmitting = false,
}: AddStoryDialogProps) {
  const [storyType, setStoryType] = useState('customer_win');
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [emotionalHook, setEmotionalHook] = useState('');
  const [keyMetrics, setKeyMetrics] = useState<Record<string, string>>({});
  const [newMetricKey, setNewMetricKey] = useState('');
  const [newMetricValue, setNewMetricValue] = useState('');

  const handleAddMetric = () => {
    if (newMetricKey && newMetricValue) {
      setKeyMetrics({ ...keyMetrics, [newMetricKey]: newMetricValue });
      setNewMetricKey('');
      setNewMetricValue('');
    }
  };

  const handleRemoveMetric = (key: string) => {
    const updated = { ...keyMetrics };
    delete updated[key];
    setKeyMetrics(updated);
  };

  const handleSubmit = () => {
    onSubmit({
      clientId,
      projectId,
      storyType,
      title: title || undefined,
      summary: summary || undefined,
      emotionalHook: emotionalHook || undefined,
      keyMetrics: Object.keys(keyMetrics).length > 0 ? keyMetrics : undefined,
      source: 'manual_entry',
    });
  };

  const handleCancel = () => {
    // Reset form
    setStoryType('customer_win');
    setTitle('');
    setSummary('');
    setEmotionalHook('');
    setKeyMetrics({});
    setNewMetricKey('');
    setNewMetricValue('');
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 transition-opacity"
        onClick={handleCancel}
      />

      {/* Dialog */}
      <div className="absolute inset-y-0 right-0 flex max-w-full pl-10">
        <div className="w-screen max-w-2xl">
          <div className="flex h-full flex-col overflow-y-scroll bg-white dark:bg-neutral-900 shadow-xl">
            {/* Header */}
            <div className="border-b border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 px-6 py-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/20">
                    <BookOpen className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                      Add Story Manually
                    </h2>
                    <p className="mt-1 text-sm text-neutral-600 dark:text-neutral-400">
                      Enter customer success story details
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleCancel}
                  className="rounded-lg p-2 text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-600 dark:hover:text-neutral-300"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Form */}
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
              {/* Story Type */}
              <div>
                <label className="block text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                  Story Type
                </label>
                <select
                  value={storyType}
                  onChange={(e) => setStoryType(e.target.value)}
                  className="w-full rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 px-3 py-2 text-sm focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:focus:ring-primary-400"
                >
                  <option value="customer_win">Customer Win</option>
                  <option value="case_study">Case Study</option>
                  <option value="testimonial">Testimonial</option>
                  <option value="success_story">Success Story</option>
                  <option value="transformation">Transformation</option>
                </select>
              </div>

              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                  Story Title <span className="text-neutral-500 dark:text-neutral-400">(Optional)</span>
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., How Acme Corp Increased Revenue by 300%"
                  className="w-full rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 px-3 py-2 text-sm placeholder-neutral-400 dark:placeholder-neutral-500 focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:focus:ring-primary-400"
                />
              </div>

              {/* Summary */}
              <div>
                <label className="block text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                  Summary <span className="text-neutral-500 dark:text-neutral-400">(Optional)</span>
                </label>
                <textarea
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  placeholder="Brief one-sentence summary of the story..."
                  rows={3}
                  className="w-full rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 px-3 py-2 text-sm placeholder-neutral-400 dark:placeholder-neutral-500 focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:focus:ring-primary-400"
                />
              </div>

              {/* Emotional Hook / Key Quote */}
              <div>
                <label className="block text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                  Key Quote / Emotional Hook <span className="text-neutral-500 dark:text-neutral-400">(Optional)</span>
                </label>
                <input
                  type="text"
                  value={emotionalHook}
                  onChange={(e) => setEmotionalHook(e.target.value)}
                  placeholder="e.g., This solution completely transformed our workflow"
                  className="w-full rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 px-3 py-2 text-sm placeholder-neutral-400 dark:placeholder-neutral-500 focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:focus:ring-primary-400"
                />
              </div>

              {/* Key Metrics */}
              <div>
                <label className="block text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                  Key Metrics <span className="text-neutral-500 dark:text-neutral-400">(Optional)</span>
                </label>

                {/* Existing Metrics */}
                {Object.keys(keyMetrics).length > 0 && (
                  <div className="mb-3 space-y-2">
                    {Object.entries(keyMetrics).map(([key, value]) => (
                      <div
                        key={key}
                        className="flex items-center gap-2 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 p-2"
                      >
                        <div className="flex-1 grid grid-cols-2 gap-2">
                          <div className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                            {key}
                          </div>
                          <div className="text-sm text-neutral-900 dark:text-neutral-100">
                            {value}
                          </div>
                        </div>
                        <button
                          onClick={() => handleRemoveMetric(key)}
                          className="rounded p-1 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add New Metric */}
                <div className="space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="text"
                      value={newMetricKey}
                      onChange={(e) => setNewMetricKey(e.target.value)}
                      placeholder="Metric name (e.g., revenue_increase)"
                      className="rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 px-3 py-2 text-sm placeholder-neutral-400 dark:placeholder-neutral-500 focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:focus:ring-primary-400"
                    />
                    <input
                      type="text"
                      value={newMetricValue}
                      onChange={(e) => setNewMetricValue(e.target.value)}
                      placeholder="Value (e.g., 300%)"
                      className="rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 px-3 py-2 text-sm placeholder-neutral-400 dark:placeholder-neutral-500 focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:focus:ring-primary-400"
                    />
                  </div>
                  <button
                    onClick={handleAddMetric}
                    disabled={!newMetricKey || !newMetricValue}
                    className="inline-flex items-center gap-1 rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 px-3 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Plus className="h-4 w-4" />
                    Add Metric
                  </button>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-neutral-200 dark:border-neutral-700 px-6 py-4 bg-neutral-50 dark:bg-neutral-800">
              <div className="flex justify-end gap-3">
                <button
                  onClick={handleCancel}
                  disabled={isSubmitting}
                  className="rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-4 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="inline-flex items-center gap-2 rounded-lg bg-primary-600 dark:bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 dark:hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <BookOpen className="h-4 w-4" />
                      Create Story
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
