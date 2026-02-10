/**
 * Shared loading state component.
 * Provides a consistent spinner + message UI used across all pages.
 */

interface Props {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  inline?: boolean;
}

const sizeMap = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-4',
  lg: 'h-12 w-12 border-4',
};

export function LoadingSpinner({ message = 'Loading...', size = 'md', inline = false }: Props) {
  if (inline) {
    return (
      <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
        <div className={`inline-block animate-spin rounded-full border-solid border-primary-600 dark:border-primary-500 border-r-transparent ${sizeMap[size]}`} />
        {message && <span>{message}</span>}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-12 text-center">
      <div className={`inline-block animate-spin rounded-full border-solid border-primary-600 dark:border-primary-500 border-r-transparent ${sizeMap[size]}`} />
      {message && <p className="mt-4 text-sm text-neutral-600 dark:text-neutral-400">{message}</p>}
    </div>
  );
}
