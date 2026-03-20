/**
 * Logger Utility
 *
 * Provides environment-aware logging that:
 * - Logs to console in development
 * - Silent in production (except errors)
 * - Can be extended with external logging services
 */

const isDevelopment = import.meta.env.DEV;

export const logger = {
  /**
   * Log debug information (development only)
   */
  debug: (...args: unknown[]) => {
    if (isDevelopment) {
      console.log('[DEBUG]', ...args);
    }
  },

  /**
   * Log informational messages (development only)
   */
  info: (...args: unknown[]) => {
    if (isDevelopment) {
      console.info('[INFO]', ...args);
    }
  },

  /**
   * Log warnings (always logged)
   */
  warn: (...args: unknown[]) => {
    console.warn('[WARN]', ...args);
  },

  /**
   * Log errors (always logged)
   */
  error: (...args: unknown[]) => {
    console.error('[ERROR]', ...args);
  },
};
