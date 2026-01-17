/**
 * MSW server setup for Node.js test environment.
 *
 * This server intercepts all HTTP requests in tests and returns mock responses
 * based on the handlers defined in handlers.ts.
 */
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Setup MSW server with all handlers
export const server = setupServer(...handlers);
