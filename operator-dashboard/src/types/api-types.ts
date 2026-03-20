/**
 * Helper types to extract request/response types from OpenAPI schema
 *
 * Usage examples:
 *
 * // Get response type for an endpoint:
 * type ProjectResponse = ApiResponse<'/api/projects/{projectId}', 'get'>;
 *
 * // Get request body type:
 * type CreateProjectBody = ApiRequestBody<'/api/projects/', 'post'>;
 *
 * // Get path parameters:
 * type ProjectPathParams = ApiPathParams<'/api/projects/{projectId}', 'get'>;
 *
 * // Get query parameters:
 * type ProjectListQuery = ApiQueryParams<'/api/projects/', 'get'>;
 */

import type { paths, components } from './api-schema';

/**
 * Extract the successful (200/201) response type for an endpoint
 */
export type ApiResponse<
  Path extends keyof paths,
  Method extends keyof paths[Path]
> = paths[Path][Method] extends { responses: infer R }
  ? R extends { 200: { content: { 'application/json': infer T } } }
    ? T
    : R extends { 201: { content: { 'application/json': infer T } } }
    ? T
    : never
  : never;

/**
 * Extract the request body type for an endpoint
 */
export type ApiRequestBody<
  Path extends keyof paths,
  Method extends keyof paths[Path]
> = paths[Path][Method] extends { requestBody: { content: { 'application/json': infer T } } }
  ? T
  : never;

/**
 * Extract path parameters for an endpoint
 */
export type ApiPathParams<
  Path extends keyof paths,
  Method extends keyof paths[Path]
> = paths[Path][Method] extends { parameters: { path: infer P } }
  ? P
  : never;

/**
 * Extract query parameters for an endpoint
 */
export type ApiQueryParams<
  Path extends keyof paths,
  Method extends keyof paths[Path]
> = paths[Path][Method] extends { parameters: { query: infer Q } }
  ? Q
  : never;

/**
 * Direct access to component schemas (models from backend)
 */
export type Schemas = components['schemas'];

/**
 * Example typed API client method using generated types
 *
 * @example
 * ```typescript
 * async function getProject(projectId: string): Promise<ProjectResponse> {
 *   const { data } = await apiClient.get(`/api/projects/${projectId}`);
 *   return data;
 * }
 *
 * // TypeScript knows the exact shape of ProjectResponse!
 * ```
 */

// Convenience type exports for commonly used endpoints
export type Project = Schemas['ProjectResponse'];
export type Client = Schemas['ClientResponse'];
export type Post = Schemas['PostResponse'];
export type Run = Schemas['RunResponse'];
export type Deliverable = Schemas['DeliverableResponse'];
export type User = Schemas['UserResponse'];
export type ResearchResult = Schemas['ResearchResultResponse'];

// Example: Extract specific endpoint types
export type ProjectListResponse = ApiResponse<'/api/projects/', 'get'>;
export type CreateProjectRequest = ApiRequestBody<'/api/projects/', 'post'>;
export type GetProjectResponse = ApiResponse<'/api/projects/{project_id}', 'get'>;
export type GetProjectParams = ApiPathParams<'/api/projects/{project_id}', 'get'>;

/**
 * API Error response structure
 */
export interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
    status?: number;
  };
  message?: string;
}
