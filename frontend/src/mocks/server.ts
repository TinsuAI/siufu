/**
 * MSW Server for Node.js (used in Vitest tests)
 */

import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// This configures a request mocking server with the given request handlers
export const server = setupServer(...handlers)
