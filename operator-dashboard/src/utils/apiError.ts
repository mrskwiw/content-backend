/**
 * Maps API error responses to user-readable messages.
 * Provides specific, actionable error messages instead of generic fallbacks.
 */

interface ApiErrorResponse {
  detail?: string | { message?: string; code?: string };
  message?: string;
}

const STATUS_MESSAGES: Record<number, string> = {
  400: 'Invalid request. Please check your input and try again.',
  401: 'Your session has expired. Please log in again.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  409: 'This action conflicts with existing data. Please refresh and try again.',
  422: 'Validation failed. Please check your input values.',
  429: 'Too many requests. Please wait a moment before trying again.',
  500: 'Server error. Please try again or contact support if the issue persists.',
  502: 'Service temporarily unavailable. Please try again in a moment.',
  503: 'Service temporarily unavailable. Please try again in a moment.',
};

/**
 * Extract a human-readable message from an API error.
 * Checks for structured backend error details before falling back to status codes.
 */
export function getApiErrorMessage(error: unknown, fallback = 'An unexpected error occurred.'): string {
  if (!error || typeof error !== 'object') return fallback;

  // Axios-style error with response
  if ('response' in error) {
    const response = (error as { response?: { status?: number; data?: ApiErrorResponse } }).response;
    if (response) {
      const { status, data } = response;

      // Backend detail string (FastAPI default)
      if (data?.detail) {
        if (typeof data.detail === 'string') return data.detail;
        if (typeof data.detail === 'object' && data.detail.message) return data.detail.message;
      }

      // Backend message string
      if (data?.message) return data.message;

      // Status code fallback
      if (status && STATUS_MESSAGES[status]) return STATUS_MESSAGES[status];
    }
  }

  // Network error
  if ('code' in error && (error as { code: string }).code === 'ERR_NETWORK') {
    return 'Network error. Please check your connection and try again.';
  }

  // Standard Error object
  if (error instanceof Error && error.message && error.message !== 'Network Error') {
    return error.message;
  }

  return fallback;
}
