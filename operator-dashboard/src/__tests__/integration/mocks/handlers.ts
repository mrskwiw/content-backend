/**
 * Mock Service Worker (MSW) handlers for API mocking.
 * Prevents real API calls during frontend tests.
 *
 * All handlers mock the backend API at http://localhost:8000/api
 */
import { http, HttpResponse } from 'msw';

const BASE_URL = 'http://localhost:8000/api';

export const handlers = [
  // ==================== Auth Handlers ====================

  http.post(`${BASE_URL}/auth/login`, async ({ request }) => {
    const body = await request.json() as { email: string; password: string };

    // Mock successful login
    if (body.email && body.password) {
      return HttpResponse.json({
        access_token: 'mock-access-token-12345',
        refresh_token: 'mock-refresh-token-67890',
        token_type: 'bearer',
        user: {
          id: 'user-test-123',
          email: body.email,
          full_name: 'Test User',
          is_active: true,
        },
      });
    }

    // Mock failed login
    return new HttpResponse(null, { status: 401 });
  }),

  http.post(`${BASE_URL}/auth/refresh`, () => {
    return HttpResponse.json({
      access_token: 'mock-new-access-token',
      refresh_token: 'mock-new-refresh-token',
      token_type: 'bearer',
    });
  }),

  // ==================== Clients Handlers ====================

  http.get(`${BASE_URL}/clients/`, ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const perPage = parseInt(url.searchParams.get('per_page') || '10');

    return HttpResponse.json({
      items: [
        {
          id: 'client-1',
          name: 'Acme Corp',
          email: 'contact@acme.com',
          business_description: 'Leading provider of cloud solutions',
          ideal_customer: 'Small businesses',
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'client-2',
          name: 'TechStart Inc',
          email: 'hello@techstart.com',
          business_description: 'Innovative startup accelerator',
          ideal_customer: 'Tech entrepreneurs',
          created_at: '2024-01-02T00:00:00Z',
        },
      ],
      metadata: {
        strategy: 'offset',
        total_count: 2,
        page,
        page_size: perPage,
      },
    });
  }),

  http.get(`${BASE_URL}/clients/:clientId`, ({ params }) => {
    return HttpResponse.json({
      id: params.clientId,
      name: 'Test Client',
      email: 'test@client.com',
      business_description: 'Test business description',
      ideal_customer: 'Test ideal customer',
      main_problem_solved: 'Test problem',
      tone_preference: 'professional',
      platforms: ['linkedin', 'twitter'],
      customer_pain_points: ['Pain 1', 'Pain 2'],
      customer_questions: ['Question 1', 'Question 2'],
      created_at: '2024-01-01T00:00:00Z',
    });
  }),

  http.post(`${BASE_URL}/clients/`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;

    return HttpResponse.json(
      {
        id: 'client-new-123',
        ...body,
        created_at: new Date().toISOString(),
      },
      { status: 201 }
    );
  }),

  http.patch(`${BASE_URL}/clients/:clientId`, async ({ params, request }) => {
    const body = await request.json() as Record<string, unknown>;

    return HttpResponse.json({
      id: params.clientId,
      ...body,
      updated_at: new Date().toISOString(),
    });
  }),

  // ==================== Projects Handlers ====================

  http.get(`${BASE_URL}/projects/`, ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const clientId = url.searchParams.get('client_id');

    const projects = [
      {
        id: 'proj-1',
        client_id: clientId || 'client-1',
        name: 'January Content',
        status: 'active',
        num_posts: 30,
        created_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 'proj-2',
        client_id: clientId || 'client-1',
        name: 'February Content',
        status: 'draft',
        num_posts: 30,
        created_at: '2024-02-01T00:00:00Z',
      },
    ];

    const filteredProjects = status
      ? projects.filter((p) => p.status === status)
      : projects;

    return HttpResponse.json({
      items: filteredProjects,
      metadata: {
        strategy: 'offset',
        total_count: filteredProjects.length,
        page: 1,
        page_size: 10,
      },
    });
  }),

  http.get(`${BASE_URL}/projects/:projectId`, ({ params }) => {
    return HttpResponse.json({
      id: params.projectId,
      client_id: 'client-1',
      name: 'Test Project',
      status: 'active',
      num_posts: 30,
      platforms: ['linkedin', 'twitter'],
      template_quantities: { '1': 10, '2': 10, '9': 10 },
      price_per_post: 40.0,
      total_price: 1200.0,
      created_at: '2024-01-01T00:00:00Z',
    });
  }),

  http.post(`${BASE_URL}/projects/`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;

    return HttpResponse.json(
      {
        id: 'proj-new-123',
        ...body,
        status: 'draft',
        created_at: new Date().toISOString(),
      },
      { status: 201 }
    );
  }),

  http.patch(`${BASE_URL}/projects/:projectId`, async ({ params, request }) => {
    const body = await request.json() as Record<string, unknown>;

    return HttpResponse.json({
      id: params.projectId,
      ...body,
      updated_at: new Date().toISOString(),
    });
  }),

  // ==================== Generator Handlers ====================

  http.post(`${BASE_URL}/generator/generate-all`, async ({ request }) => {
    const body = await request.json() as { project_id: string };

    return HttpResponse.json({
      run_id: 'run-mock-123',
      status: 'pending',
      message: 'Generation started',
      project_id: body.project_id,
    });
  }),

  http.post(`${BASE_URL}/generator/regenerate`, async ({ request }) => {
    const body = await request.json() as { project_id: string; post_ids: string[] };

    return HttpResponse.json({
      run_id: 'run-regen-123',
      status: 'pending',
      message: `Regenerating ${body.post_ids.length} posts`,
      project_id: body.project_id,
    });
  }),

  http.post(`${BASE_URL}/generator/export`, async ({ request }) => {
    const body = await request.json() as { project_id: string; format: string };

    return HttpResponse.json({
      deliverable_id: 'deliv-mock-123',
      project_id: body.project_id,
      format: body.format,
      file_path: `/data/outputs/TestClient/deliverable.${body.format}`,
    });
  }),

  // ==================== Runs Handlers ====================

  http.get(`${BASE_URL}/runs/`, ({ request }) => {
    const url = new URL(request.url);
    const projectId = url.searchParams.get('project_id');

    return HttpResponse.json({
      items: [
        {
          id: 'run-1',
          project_id: projectId || 'proj-1',
          status: 'completed',
          is_batch: true,
          started_at: '2024-01-01T10:00:00Z',
          completed_at: '2024-01-01T10:05:00Z',
        },
      ],
      metadata: {
        total_count: 1,
        page: 1,
        page_size: 10,
      },
    });
  }),

  http.get(`${BASE_URL}/runs/:runId`, ({ params }) => {
    // Simulate run completion after first call
    const isCompleted = Math.random() > 0.3; // 70% chance of being complete

    return HttpResponse.json({
      id: params.runId,
      project_id: 'proj-1',
      status: isCompleted ? 'completed' : 'running',
      is_batch: true,
      started_at: '2024-01-01T10:00:00Z',
      completed_at: isCompleted ? '2024-01-01T10:05:00Z' : null,
      progress_percent: isCompleted ? 100 : 65,
      logs: [
        { timestamp: '2024-01-01T10:00:00Z', message: 'Generation started' },
        { timestamp: '2024-01-01T10:03:00Z', message: 'Processing posts' },
      ],
    });
  }),

  // ==================== Posts Handlers ====================

  http.get(`${BASE_URL}/posts/`, ({ request }) => {
    const url = new URL(request.url);
    const projectId = url.searchParams.get('project_id');
    const status = url.searchParams.get('status');
    const needsReview = url.searchParams.get('needs_review');

    const posts = Array.from({ length: 30 }, (_, i) => ({
      id: `post-${i + 1}`,
      project_id: projectId || 'proj-1',
      content: `Test post content ${i + 1}...\n\n[CTA]`,
      template_id: (i % 15) + 1,
      template_name: 'Problem Recognition',
      target_platform: 'linkedin',
      word_count: 150 + i * 5,
      has_cta: true,
      readability_score: 65 + i,
      status: i % 5 === 0 ? 'flagged' : 'approved',
      flags: i % 5 === 0 ? ['too_short'] : [],
      created_at: `2024-01-01T${10 + Math.floor(i / 6)}:${i * 2}:00Z`,
    }));

    let filteredPosts = posts;
    if (status) {
      filteredPosts = posts.filter((p) => p.status === status);
    }
    if (needsReview === 'true') {
      filteredPosts = posts.filter((p) => p.flags.length > 0);
    }

    return HttpResponse.json({
      items: filteredPosts,
      metadata: {
        total_count: filteredPosts.length,
        page: 1,
        page_size: 50,
      },
    });
  }),

  http.get(`${BASE_URL}/posts/:postId`, ({ params }) => {
    return HttpResponse.json({
      id: params.postId,
      project_id: 'proj-1',
      content: 'Test post content...\n\n[CTA]',
      template_id: 1,
      template_name: 'Problem Recognition',
      target_platform: 'linkedin',
      word_count: 150,
      has_cta: true,
      readability_score: 72.5,
      status: 'approved',
      flags: [],
      created_at: '2024-01-01T10:00:00Z',
    });
  }),

  http.patch(`${BASE_URL}/posts/:postId`, async ({ params, request }) => {
    const body = await request.json() as { content?: string };

    return HttpResponse.json({
      id: params.postId,
      content: body.content || 'Updated content',
      word_count: body.content ? body.content.split(' ').length : 150,
      has_cta: body.content?.includes('[CTA]') || false,
      updated_at: new Date().toISOString(),
    });
  }),

  // ==================== Deliverables Handlers ====================

  http.get(`${BASE_URL}/deliverables/`, ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');

    const deliverables = [
      {
        id: 'deliv-1',
        project_id: 'proj-1',
        client_id: 'client-1',
        format: 'txt',
        path: '/data/outputs/TestClient/deliverable.txt',
        status: 'ready',
        file_size_bytes: 15360,
        created_at: '2024-01-01T10:10:00Z',
      },
      {
        id: 'deliv-2',
        project_id: 'proj-2',
        client_id: 'client-1',
        format: 'docx',
        path: '/data/outputs/TestClient/deliverable.docx',
        status: 'delivered',
        file_size_bytes: 45120,
        created_at: '2024-01-02T10:10:00Z',
        delivered_at: '2024-01-02T15:00:00Z',
        proof_url: 'https://example.com/proof',
      },
    ];

    const filteredDeliverables = status
      ? deliverables.filter((d) => d.status === status)
      : deliverables;

    return HttpResponse.json({
      items: filteredDeliverables,
      metadata: {
        total_count: filteredDeliverables.length,
        page: 1,
        page_size: 10,
      },
    });
  }),

  http.get(`${BASE_URL}/deliverables/:deliverableId`, ({ params }) => {
    return HttpResponse.json({
      id: params.deliverableId,
      project_id: 'proj-1',
      client_id: 'client-1',
      format: 'txt',
      path: '/data/outputs/TestClient/deliverable.txt',
      status: 'ready',
      file_size_bytes: 15360,
      created_at: '2024-01-01T10:10:00Z',
    });
  }),

  http.get(`${BASE_URL}/deliverables/:deliverableId/download`, () => {
    // Return a mock text file
    const mockContent = '# 30-Day Content Jumpstart Deliverable\n\nPost 1...\nPost 2...';
    return new HttpResponse(mockContent, {
      headers: {
        'Content-Type': 'text/plain',
        'Content-Disposition': 'attachment; filename="deliverable.txt"',
      },
    });
  }),

  http.patch(`${BASE_URL}/deliverables/:deliverableId/mark-delivered`, async ({ params, request }) => {
    const body = await request.json() as { proof_url?: string; proof_notes?: string };

    return HttpResponse.json({
      id: params.deliverableId,
      status: 'delivered',
      delivered_at: new Date().toISOString(),
      proof_url: body.proof_url,
      proof_notes: body.proof_notes,
    });
  }),

  // ==================== Briefs Handlers ====================

  http.post(`${BASE_URL}/briefs/create`, async ({ request }) => {
    const body = await request.json() as { project_id: string; content: string };

    return HttpResponse.json(
      {
        id: 'brief-mock-123',
        project_id: body.project_id,
        content: body.content,
        source: 'paste',
        created_at: new Date().toISOString(),
      },
      { status: 201 }
    );
  }),

  http.post(`${BASE_URL}/briefs/upload`, async () => {
    return HttpResponse.json(
      {
        id: 'brief-mock-123',
        project_id: 'proj-1',
        source: 'upload',
        file_path: '/path/to/brief.txt',
        created_at: new Date().toISOString(),
      },
      { status: 201 }
    );
  }),

  http.get(`${BASE_URL}/briefs/:briefId`, ({ params }) => {
    return HttpResponse.json({
      id: params.briefId,
      project_id: 'proj-1',
      content: 'Company Name: Test Company\nBusiness Description: Test...',
      source: 'paste',
      created_at: '2024-01-01T00:00:00Z',
    });
  }),

  // ==================== Health Check ====================

  http.get(`${BASE_URL}/health`, () => {
    return HttpResponse.json({
      status: 'healthy',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
    });
  }),
];
