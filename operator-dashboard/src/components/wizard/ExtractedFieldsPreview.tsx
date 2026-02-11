import { CheckCircle2, Clock, Circle } from 'lucide-react';

export type FieldStatus = 'extracted' | 'partial' | 'pending';

export interface ExtractedField {
  name: string;
  label: string;
  value?: string;
  status: FieldStatus;
  confidence?: number;
}

export interface ExtractedFieldsPreviewProps {
  fields: ExtractedField[];
  onEdit?: () => void;
}

/**
 * Shows preview of extracted data from AI conversation
 * Visual feedback on what fields have been populated
 */
export function ExtractedFieldsPreview({ fields, onEdit }: ExtractedFieldsPreviewProps) {
  const getStatusIcon = (status: FieldStatus) => {
    switch (status) {
      case 'extracted':
        return <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />;
      case 'partial':
        return <Clock className="h-4 w-4 text-amber-600 dark:text-amber-400" />;
      case 'pending':
        return <Circle className="h-4 w-4 text-neutral-400 dark:text-neutral-600" />;
    }
  };

  const getStatusColor = (status: FieldStatus) => {
    switch (status) {
      case 'extracted':
        return 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20';
      case 'partial':
        return 'border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20';
      case 'pending':
        return 'border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800/50';
    }
  };

  const extractedCount = fields.filter(f => f.status === 'extracted').length;
  const totalRequired = fields.filter(f => f.name !== 'tonePreference' && f.name !== 'platforms').length;
  const progressPercentage = (extractedCount / totalRequired) * 100;

  return (
    <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
          Extracted Information
        </h3>
        {onEdit && (
          <button
            onClick={onEdit}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            Edit
          </button>
        )}
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-xs text-neutral-600 dark:text-neutral-400 mb-1">
          <span>Progress</span>
          <span>{Math.round(progressPercentage)}%</span>
        </div>
        <div className="h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Field list */}
      <div className="space-y-2">
        {fields.map((field) => (
          <div
            key={field.name}
            className={`rounded-md border p-3 transition-all ${getStatusColor(field.status)}`}
          >
            <div className="flex items-start gap-2">
              <div className="mt-0.5">{getStatusIcon(field.status)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                    {field.label}
                  </p>
                  {field.confidence !== undefined && field.status === 'extracted' && (
                    <span className="text-xs text-neutral-500 dark:text-neutral-400">
                      {Math.round(field.confidence * 100)}%
                    </span>
                  )}
                </div>
                {field.value ? (
                  <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1 line-clamp-2">
                    {field.value}
                  </p>
                ) : (
                  <p className="text-xs text-neutral-500 dark:text-neutral-500 mt-1 italic">
                    {field.status === 'partial' ? 'Gathering...' : 'Pending'}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
