/**
 * Utility functions for formatting data for display.
 */

/**
 * Format bytes to human-readable file size.
 *
 * @param bytes - File size in bytes
 * @returns Formatted string (e.g., "1.5 MB", "234 KB")
 *
 * @example
 * formatFileSize(1024) // "1.0 KB"
 * formatFileSize(1536) // "1.5 KB"
 * formatFileSize(1048576) // "1.0 MB"
 * formatFileSize(0) // "0 B"
 * formatFileSize(undefined) // "Unknown"
 */
export function formatFileSize(bytes: number | undefined | null): string {
  if (bytes === undefined || bytes === null) {
    return 'Unknown';
  }

  if (bytes === 0) {
    return '0 B';
  }

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let unitIndex = 0;
  let size = bytes;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  // Format with appropriate precision
  if (size < 10) {
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  } else {
    return `${Math.round(size)} ${units[unitIndex]}`;
  }
}

/**
 * Format token count with thousands separators
 *
 * @param tokens - Number of tokens
 * @returns Formatted string with commas
 *
 * @example
 * formatTokenCount(1000) // '1,000'
 * formatTokenCount(1500000) // '1,500,000'
 */
export function formatTokenCount(tokens: number): string {
  return tokens.toLocaleString();
}

/**
 * Format currency value in USD
 *
 * Uses 2 decimal places for amounts >= $0.01, otherwise uses 4 decimal places
 * to show fractional cents for very small amounts.
 *
 * @param usd - Amount in US dollars
 * @returns Formatted currency string
 *
 * @example
 * formatCurrency(10.5) // '$10.50'
 * formatCurrency(0.0025) // '$0.0025'
 * formatCurrency(0) // '$0.00'
 */
export function formatCurrency(usd: number): string {
  if (usd === 0) {
    return '$0.00';
  }

  // Use 4 decimals for very small amounts (< 1 cent)
  if (usd < 0.01) {
    return `$${usd.toFixed(4)}`;
  }

  // Use 2 decimals for normal amounts
  return `$${usd.toFixed(2)}`;
}

/**
 * Calculate cache savings percentage
 *
 * @param readTokens - Tokens read from cache
 * @param totalTokens - Total tokens (cache + generated)
 * @returns Savings percentage (0-100)
 *
 * @example
 * calculateCacheSavings(500, 1000) // 50
 * calculateCacheSavings(0, 1000) // 0
 */
export function calculateCacheSavings(
  readTokens: number,
  totalTokens: number
): number {
  if (totalTokens === 0) {
    return 0;
  }

  return Math.round((readTokens / totalTokens) * 100);
}

/**
 * Format percentage value
 *
 * @param value - Percentage value (0-100)
 * @param decimals - Number of decimal places (default: 0)
 * @returns Formatted percentage string
 *
 * @example
 * formatPercentage(75) // '75%'
 * formatPercentage(33.333, 1) // '33.3%'
 */
export function formatPercentage(value: number, decimals = 0): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format number with compact notation (K, M, B)
 *
 * @param num - Number to format
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted compact string
 *
 * @example
 * formatCompact(1500) // '1.5K'
 * formatCompact(1500000) // '1.5M'
 * formatCompact(1500000000) // '1.5B'
 */
export function formatCompact(num: number, decimals = 1): string {
  if (num < 1000) {
    return num.toString();
  }

  const units = ['', 'K', 'M', 'B', 'T'];
  const k = 1000;
  const i = Math.floor(Math.log(num) / Math.log(k));

  return `${(num / Math.pow(k, i)).toFixed(decimals)}${units[i]}`;
}

/**
 * Format duration in milliseconds to human-readable format
 *
 * @param ms - Duration in milliseconds
 * @returns Formatted duration string
 *
 * @example
 * formatDuration(1500) // '1.5s'
 * formatDuration(65000) // '1m 5s'
 * formatDuration(3665000) // '1h 1m 5s'
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }

  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) {
    const decimal = ((ms % 1000) / 1000).toFixed(1).substring(1);
    return seconds < 10 ? `${seconds}${decimal}s` : `${seconds}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes < 60) {
    return remainingSeconds > 0
      ? `${minutes}m ${remainingSeconds}s`
      : `${minutes}m`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  return remainingMinutes > 0
    ? `${hours}h ${remainingMinutes}m`
    : `${hours}h`;
}

/**
 * Pluralize word based on count
 *
 * @param count - Number to check
 * @param singular - Singular form of word
 * @param plural - Plural form of word (optional, defaults to singular + 's')
 * @returns Pluralized string with count
 *
 * @example
 * pluralize(1, 'item') // '1 item'
 * pluralize(5, 'item') // '5 items'
 * pluralize(3, 'child', 'children') // '3 children'
 */
export function pluralize(
  count: number,
  singular: string,
  plural?: string
): string {
  const word = count === 1 ? singular : (plural || `${singular}s`);
  return `${count} ${word}`;
}
