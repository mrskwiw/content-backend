import { z } from 'zod';

export const ClientStatusSchema = z.enum(['active', 'inactive']);
export type ClientStatus = z.infer<typeof ClientStatusSchema>;

export const ProjectStatusSchema = z.enum([
  'draft',
  'ready',
  'generating',
  'qa',
  'exported',
  'delivered',
  'error',
]);
export type ProjectStatus = z.infer<typeof ProjectStatusSchema>;

export const RunStatusSchema = z.enum(['pending', 'running', 'succeeded', 'failed']);
export type RunStatus = z.infer<typeof RunStatusSchema>;

export const DeliverableStatusSchema = z.enum(['draft', 'ready', 'delivered']);
export type DeliverableStatus = z.infer<typeof DeliverableStatusSchema>;

export const PlatformSchema = z.enum(['linkedin', 'twitter', 'facebook', 'blog', 'email', 'generic']);
export type Platform = z.infer<typeof PlatformSchema>;

export const ClientSchema = z.object({
  id: z.string(),
  name: z.string(),
  tags: z.array(z.string()).optional(),
  status: ClientStatusSchema.optional(),
  businessDescription: z.string().optional(),
  idealCustomer: z.string().optional(),
  mainProblemSolved: z.string().optional(),
  tonePreference: z.string().optional(),
  platforms: z.array(PlatformSchema).optional(),
  customerPainPoints: z.array(z.string()).optional(),
  customerQuestions: z.array(z.string()).optional(),
  industry: z.string().optional(),
  keywords: z.array(z.string()).optional(),
  competitors: z.array(z.string()).optional(),
  location: z.string().optional(),
});
export type Client = z.infer<typeof ClientSchema>;

export const ProjectSchema = z.object({
  id: z.string(),
  clientId: z.string(),
  name: z.string(),
  status: ProjectStatusSchema,
  templates: z.array(z.string()).optional().nullable(),
  platforms: z.array(PlatformSchema),
  tone: z.string().optional(),
  lastRunAt: z.string().datetime().optional(),
  updatedAt: z.string().datetime().optional(),
  createdAt: z.string().datetime().optional(),
  totalPrice: z.number().optional().nullable(),
  numPosts: z.number().int().optional().nullable(),
  pricePerPost: z.number().optional().nullable(),
  postsCost: z.number().optional().nullable(),
  researchAddonCost: z.number().optional().nullable(),
  toolsCost: z.number().optional().nullable(),
  discountAmount: z.number().optional().nullable(),
  selectedTools: z.array(z.string()).optional().nullable(),
});
export type Project = z.infer<typeof ProjectSchema>;

export const RunSchema = z.object({
  id: z.string(),
  projectId: z.string(),
  isBatch: z.boolean().optional(),
  params: z.record(z.string(), z.unknown()).optional(),
  startedAt: z.string().datetime(),
  completedAt: z.string().datetime().optional(),
  logs: z.array(z.string()).optional(),
  status: RunStatusSchema.optional(),
  errorMessage: z.string().optional(),
  totalInputTokens: z.number().int().optional(),
  totalOutputTokens: z.number().int().optional(),
  totalCacheCreationTokens: z.number().int().optional(),
  totalCacheReadTokens: z.number().int().optional(),
  totalCostUsd: z.number().optional(),
  estimatedCostUsd: z.number().optional(),
});
export type Run = z.infer<typeof RunSchema>;

export const PostDraftSchema = z.object({
  id: z.string(),
  projectId: z.string(),
  runId: z.string(),
  content: z.string(),
  length: z.number().int().nonnegative().optional(),
  readabilityScore: z.number().optional(),
  hasCta: z.boolean().optional(),
  platform: PlatformSchema.optional(),
  status: z.enum(['pending', 'flagged', 'approved', 'regenerating']).optional(),
  flags: z.array(z.string()).optional(),
  notes: z.string().optional(),
});
export type PostDraft = z.infer<typeof PostDraftSchema>;

export const DeliverableSchema = z.object({
  id: z.string(),
  projectId: z.string(),
  clientId: z.string(),
  format: z.enum(['txt', 'md', 'docx']),
  path: z.string(),
  createdAt: z.string().datetime(),
  status: DeliverableStatusSchema,
  deliveredAt: z.string().datetime().nullish(),
  proofUrl: z.string().url().nullish(),
  proofNotes: z.string().nullish(),
  runId: z.string().nullish(),
  checksum: z.string().nullish(),
  fileSizeBytes: z.number().nullish(),
});
export type Deliverable = z.infer<typeof DeliverableSchema>;

export const PostSummarySchema = z.object({
  id: z.string(),
  templateName: z.string().optional(),
  wordCount: z.number().nullish(),
  readabilityScore: z.number().nullish(),
  status: z.string(),
  flags: z.array(z.string()).nullish(),
  contentPreview: z.string(),
});
export type PostSummary = z.infer<typeof PostSummarySchema>;

// Full post with complete content (used for editing)
export const PostSchema = PostSummarySchema.extend({
  content: z.string(),
});
export type Post = z.infer<typeof PostSchema>;

export const QASummarySchema = z.object({
  avgReadability: z.number().nullish(),
  avgWordCount: z.number().nullish(),
  totalPosts: z.number(),
  flaggedCount: z.number(),
  approvedCount: z.number(),
  ctaPercentage: z.number().nullish(),
  commonFlags: z.array(z.string()),
});
export type QASummary = z.infer<typeof QASummarySchema>;

export const ResearchResultSummarySchema = z.object({
  id: z.string(),
  userId: z.string(),
  clientId: z.string(),
  projectId: z.string().optional().nullable(),
  toolName: z.string(),
  toolLabel: z.string().optional().nullable(),
  toolPrice: z.number().optional().nullable(),
  actualCostUsd: z.number().optional().nullable(),
  summary: z.string().optional().nullable(),
  status: z.string(),
  errorMessage: z.string().optional().nullable(),
  durationSeconds: z.number().optional().nullable(),
  createdAt: z.string().datetime(),
});
export type ResearchResultSummary = z.infer<typeof ResearchResultSummarySchema>;

export const DeliverableDetailsSchema = DeliverableSchema.extend({
  filePreview: z.string().nullish(),
  filePreviewTruncated: z.boolean(),
  posts: z.array(PostSummarySchema),
  qaSummary: QASummarySchema.nullish(),
  fileModifiedAt: z.string().datetime().nullish(),
  researchResults: z.array(ResearchResultSummarySchema).optional().default([]),
});
export type DeliverableDetails = z.infer<typeof DeliverableDetailsSchema>;

export const AuditEntrySchema = z.object({
  id: z.string(),
  actor: z.string(),
  action: z.string(),
  targetType: z.enum(['project', 'run', 'deliverable', 'post', 'client']),
  targetId: z.string(),
  timestamp: z.string().datetime(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});
export type AuditEntry = z.infer<typeof AuditEntrySchema>;

export const MarkDeliveredSchema = z.object({
  deliveredAt: z.string().datetime(),
  proofUrl: z.string().url().optional(),
  proofNotes: z.string().optional(),
});
export type MarkDeliveredInput = z.infer<typeof MarkDeliveredSchema>;

export const GenerateAllSchema = z.object({
  projectId: z.string(),
  clientId: z.string(),
  isBatch: z.boolean().default(true),
  templateQuantities: z.record(z.string(), z.number()).optional(),
  customTopics: z.array(z.string()).optional(),  // NEW: topic override for generation
  targetPlatform: z.string().optional(),  // NEW: target platform for platform-specific generation
});
export type GenerateAllInput = z.infer<typeof GenerateAllSchema>;

export const RegenerateSchema = z.object({
  projectId: z.string(),
  postIds: z.array(z.string()),
  reason: z.string().optional(),
});
export type RegenerateInput = z.infer<typeof RegenerateSchema>;

// Export target platforms
export const ExportTargetSchema = z.enum([
  // Social Media
  'linkedin-posts',
  'linkedin-articles',
  'twitter',
  'twitter-threads',
  'facebook',
  'instagram',
  // Publishing Platforms
  'substack',
  'medium',
  'wordpress',
  'ghost',
  // Productivity
  'notion',
  // Standard Formats
  'docx',
  'markdown',
  'txt',
]);
export type ExportTarget = z.infer<typeof ExportTargetSchema>;

// Export file formats
export const ExportFormatSchema = z.enum(['txt', 'md', 'docx', 'html', 'json', 'wxr']);
export type ExportFormat = z.infer<typeof ExportFormatSchema>;

export const ExportSchema = z.object({
  projectId: z.string(),
  clientId: z.string(),
  format: ExportFormatSchema,
  target: ExportTargetSchema.optional(),
  includeAuditLog: z.boolean().default(false),
  includeResearch: z.boolean().default(false),
});
export type ExportInput = z.infer<typeof ExportSchema>;

export const ClientBriefSchema = z.object({
  companyName: z.string().min(1, 'Company name is required'),
  businessDescription: z
    .string()
    .min(70, 'Business description must be at least 70 characters (required for research tools)'),
  idealCustomer: z
    .string()
    .min(20, 'Target audience description must be at least 20 characters (required for research tools)'),
  mainProblemSolved: z.string().optional(),
  tonePreference: z.string().default('professional'),
  platforms: z.array(PlatformSchema).optional(),
  customerPainPoints: z.array(z.string()).optional(),
  customerQuestions: z.array(z.string()).optional(),
  industry: z.string().optional(),
  keywords: z.array(z.string()).optional(),
  competitors: z.array(z.string()).optional(),
  location: z.string().optional(),
});
export type ClientBrief = z.infer<typeof ClientBriefSchema>;

export const ResearchResultSchema = z.object({
  id: z.string(),
  userId: z.string(),
  clientId: z.string(),
  projectId: z.string().optional().nullable(),
  toolName: z.string(),
  toolLabel: z.string().optional().nullable(),
  toolPrice: z.number().optional().nullable(),
  actualCostUsd: z.number().optional().nullable(),
  isCachedResult: z.boolean().optional().nullable(),
  params: z.record(z.string(), z.any()).optional().nullable(),
  outputs: z.record(z.string(), z.string()),
  data: z.record(z.string(), z.unknown()).optional().nullable(),
  status: z.string(),
  errorMessage: z.string().optional().nullable(),
  durationSeconds: z.number().optional().nullable(),
  createdAt: z.string().datetime(),
});
export type ResearchResult = z.infer<typeof ResearchResultSchema>;
