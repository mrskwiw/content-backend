/**
 * Test data fixtures for frontend tests.
 *
 * Provides consistent test data for components and integration tests.
 */

import type { Client, Project, Post, Deliverable, Run } from '@/types/domain';

export const mockClients: Client[] = [
  {
    id: 'client-1',
    name: 'Acme Corp',
    email: 'contact@acme.com',
    businessDescription: 'Leading provider of cloud solutions for small businesses',
    idealCustomer: 'Small businesses with 10-50 employees',
    mainProblemSolved: 'Inefficient workflow management',
    tonePreference: 'professional',
    platforms: ['linkedin', 'twitter'],
    customerPainPoints: ['Manual processes', 'Poor collaboration', 'Data silos'],
    customerQuestions: ['How to automate workflows?', 'What metrics to track?'],
    createdAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'client-2',
    name: 'TechStart Inc',
    email: 'hello@techstart.com',
    businessDescription: 'Innovative startup accelerator',
    idealCustomer: 'Tech entrepreneurs and early-stage startups',
    mainProblemSolved: 'Lack of mentorship and funding',
    tonePreference: 'casual',
    platforms: ['twitter', 'linkedin'],
    customerPainPoints: ['Finding investors', 'Market validation', 'Team building'],
    customerQuestions: ['How to pitch to VCs?', 'When to scale?'],
    createdAt: '2024-01-02T00:00:00Z',
  },
];

export const mockProjects: Project[] = [
  {
    id: 'proj-1',
    clientId: 'client-1',
    name: 'January Content Campaign',
    status: 'active',
    numPosts: 30,
    platforms: ['linkedin', 'twitter'],
    templates: ['1', '2', '9'],
    templateQuantities: { '1': 10, '2': 10, '9': 10 },
    pricePerPost: 40.0,
    researchPricePerPost: 0.0,
    totalPrice: 1200.0,
    tone: 'professional',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'proj-2',
    clientId: 'client-1',
    name: 'February Content Campaign',
    status: 'draft',
    numPosts: 30,
    platforms: ['linkedin'],
    templates: ['1', '2', '3'],
    templateQuantities: { '1': 10, '2': 10, '3': 10 },
    pricePerPost: 40.0,
    researchPricePerPost: 0.0,
    totalPrice: 1200.0,
    tone: 'professional',
    createdAt: '2024-02-01T00:00:00Z',
    updatedAt: '2024-02-01T00:00:00Z',
  },
];

export const mockPosts: Post[] = Array.from({ length: 30 }, (_, i) => ({
  id: `post-${i + 1}`,
  projectId: 'proj-1',
  runId: 'run-1',
  content: `Test post content ${i + 1}...\n\nThis is a compelling post about productivity.\n\n[CTA: Learn more]`,
  templateId: (i % 15) + 1,
  templateName: 'Problem Recognition',
  targetPlatform: 'linkedin',
  wordCount: 150 + i * 5,
  hasCta: true,
  readabilityScore: 65 + i,
  status: i % 5 === 0 ? 'flagged' : 'approved',
  flags: i % 5 === 0 ? ['too_short'] : [],
  variant: 0,
  createdAt: `2024-01-01T${10 + Math.floor(i / 6)}:${(i * 2) % 60}:00Z`,
}));

export const mockRuns: Run[] = [
  {
    id: 'run-1',
    projectId: 'proj-1',
    status: 'completed',
    isBatch: true,
    startedAt: '2024-01-01T10:00:00Z',
    completedAt: '2024-01-01T10:05:00Z',
    logs: [
      { timestamp: '2024-01-01T10:00:00Z', message: 'Generation started' },
      { timestamp: '2024-01-01T10:03:00Z', message: 'Processing posts 1-10' },
      { timestamp: '2024-01-01T10:05:00Z', message: 'Generation complete' },
    ],
    errorMessage: null,
    createdAt: '2024-01-01T10:00:00Z',
  },
  {
    id: 'run-2',
    projectId: 'proj-1',
    status: 'running',
    isBatch: true,
    startedAt: '2024-01-02T10:00:00Z',
    completedAt: null,
    logs: [
      { timestamp: '2024-01-02T10:00:00Z', message: 'Generation started' },
      { timestamp: '2024-01-02T10:02:00Z', message: 'Processing posts 1-10' },
    ],
    errorMessage: null,
    createdAt: '2024-01-02T10:00:00Z',
  },
];

export const mockDeliverables: Deliverable[] = [
  {
    id: 'deliv-1',
    projectId: 'proj-1',
    clientId: 'client-1',
    runId: 'run-1',
    format: 'txt',
    path: '/data/outputs/AcmeCorp/deliverable.txt',
    status: 'ready',
    fileSizeBytes: 15360,
    checksum: 'abc123def456', // pragma: allowlist secret
    createdAt: '2024-01-01T10:10:00Z',
    deliveredAt: null,
    proofUrl: null,
    proofNotes: null,
  },
  {
    id: 'deliv-2',
    projectId: 'proj-2',
    clientId: 'client-1',
    runId: null,
    format: 'docx',
    path: '/data/outputs/AcmeCorp/deliverable.docx',
    status: 'delivered',
    fileSizeBytes: 45120,
    checksum: 'def456ghi789',
    createdAt: '2024-01-02T10:10:00Z',
    deliveredAt: '2024-01-02T15:00:00Z',
    proofUrl: 'https://example.com/proof',
    proofNotes: 'Delivered via email to client contact',
  },
];

/**
 * Helper to get a single mock client by ID.
 */
export function getMockClient(id: string): Client | undefined {
  return mockClients.find((client) => client.id === id);
}

/**
 * Helper to get a single mock project by ID.
 */
export function getMockProject(id: string): Project | undefined {
  return mockProjects.find((project) => project.id === id);
}

/**
 * Helper to get mock posts for a project.
 */
export function getMockPostsForProject(projectId: string): Post[] {
  return mockPosts.filter((post) => post.projectId === projectId);
}

/**
 * Helper to get mock deliverables for a project.
 */
export function getMockDeliverablesForProject(projectId: string): Deliverable[] {
  return mockDeliverables.filter((deliverable) => deliverable.projectId === projectId);
}

/**
 * Create a custom mock client with overrides.
 */
export function createMockClient(overrides: Partial<Client> = {}): Client {
  return {
    id: `client-${Date.now()}`,
    name: 'Test Client',
    email: 'test@client.com',
    businessDescription: 'Test business description',
    idealCustomer: 'Test ideal customer',
    mainProblemSolved: 'Test problem',
    tonePreference: 'professional',
    platforms: ['linkedin'],
    customerPainPoints: ['Pain 1', 'Pain 2'],
    customerQuestions: ['Question 1'],
    createdAt: new Date().toISOString(),
    ...overrides,
  };
}

/**
 * Create a custom mock project with overrides.
 */
export function createMockProject(overrides: Partial<Project> = {}): Project {
  return {
    id: `proj-${Date.now()}`,
    clientId: 'client-1',
    name: 'Test Project',
    status: 'draft',
    numPosts: 30,
    platforms: ['linkedin'],
    templates: ['1', '2'],
    templateQuantities: { '1': 15, '2': 15 },
    pricePerPost: 40.0,
    researchPricePerPost: 0.0,
    totalPrice: 1200.0,
    tone: 'professional',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  };
}

/**
 * Create a custom mock post with overrides.
 */
export function createMockPost(overrides: Partial<Post> = {}): Post {
  return {
    id: `post-${Date.now()}`,
    projectId: 'proj-1',
    runId: 'run-1',
    content: 'Test post content...\n\n[CTA]',
    templateId: 1,
    templateName: 'Problem Recognition',
    targetPlatform: 'linkedin',
    wordCount: 150,
    hasCta: true,
    readabilityScore: 70.0,
    status: 'approved',
    flags: [],
    variant: 0,
    createdAt: new Date().toISOString(),
    ...overrides,
  };
}
