import { useState, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/api/projects';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Building2, User, Target, Info } from 'lucide-react';
import type { Project } from '@/types/domain';

// ---------------------------------------------------------------------------
// Pricing constants (mirrors src/config/pricing.py — keep in sync)
// ---------------------------------------------------------------------------

const PRICE_PER_POST = 40;
const RESEARCH_PRICE_PER_POST = 15;

interface ToolDef {
  id: string;
  name: string;
  price: number;
  group: 'foundation' | 'seo' | 'advanced';
  implemented: boolean;
}

const TOOLS: ToolDef[] = [
  // Foundation group
  { id: 'voice_analysis',            name: 'Voice Analysis',            price: 400, group: 'foundation', implemented: true },
  { id: 'brand_archetype',           name: 'Brand Archetype',           price: 300, group: 'foundation', implemented: true },
  { id: 'audience_research',         name: 'Audience Research',         price: 500, group: 'foundation', implemented: true },
  { id: 'icp_workshop',              name: 'ICP Workshop',              price: 600, group: 'foundation', implemented: true },
  // SEO group
  { id: 'seo_keyword_research',      name: 'SEO Keyword Research',      price: 400, group: 'seo',        implemented: true },
  { id: 'competitive_analysis',      name: 'Competitive Analysis',      price: 500, group: 'seo',        implemented: true },
  { id: 'content_gap_analysis',      name: 'Content Gap Analysis',      price: 500, group: 'seo',        implemented: true },
  // Advanced group (not yet implemented)
  { id: 'content_audit',             name: 'Content Audit',             price: 400, group: 'advanced',   implemented: false },
  { id: 'platform_strategy',         name: 'Platform Strategy',         price: 300, group: 'advanced',   implemented: false },
  { id: 'content_calendar_strategy', name: 'Content Calendar Strategy', price: 300, group: 'advanced',   implemented: false },
  { id: 'story_mining_interview',    name: 'Story Mining Interview',    price: 500, group: 'advanced',   implemented: false },
  { id: 'market_trends',             name: 'Market Trends',             price: 400, group: 'advanced',   implemented: false },
];

const FOUNDATION_IDS = new Set(['voice_analysis', 'brand_archetype', 'audience_research', 'icp_workshop']);
const SEO_IDS        = new Set(['seo_keyword_research', 'competitive_analysis', 'content_gap_analysis']);
const ALL_TOOL_IDS   = new Set(TOOLS.map(t => t.id));

interface BundleResult {
  toolsCost: number;
  discountAmount: number;
  appliedBundles: string[];
}

/**
 * Client-side bundle detection — mirrors calculate_tools_cost() in pricing.py.
 * Priority: Ultimate > Complete Strategy > (Foundation + SEO independently).
 */
function calculateToolsCost(selectedIds: Set<string>): BundleResult {
  if (selectedIds.size === 0) {
    return { toolsCost: 0, discountAmount: 0, appliedBundles: [] };
  }

  const alaCarteTotal = TOOLS
    .filter(t => selectedIds.has(t.id))
    .reduce((sum, t) => sum + t.price, 0);

  const appliedBundles: string[] = [];
  let bundledIds = new Set<string>();
  let bundlePrice = 0;

  const hasAllTools      = [...ALL_TOOL_IDS].every(id => selectedIds.has(id));
  const hasAllStrategy   = [...FOUNDATION_IDS, ...SEO_IDS].every(id => selectedIds.has(id));
  const hasAllFoundation = [...FOUNDATION_IDS].every(id => selectedIds.has(id));
  const hasAllSeo        = [...SEO_IDS].every(id => selectedIds.has(id));

  if (hasAllTools) {
    bundlePrice = 4500;
    bundledIds = new Set(ALL_TOOL_IDS);
    appliedBundles.push('Ultimate Pack');
  } else if (hasAllStrategy) {
    bundlePrice = 2400;
    bundledIds = new Set([...FOUNDATION_IDS, ...SEO_IDS]);
    appliedBundles.push('Complete Strategy');
  } else {
    if (hasAllFoundation) {
      bundlePrice += 1500;
      FOUNDATION_IDS.forEach(id => bundledIds.add(id));
      appliedBundles.push('Foundation Pack');
    }
    if (hasAllSeo) {
      bundlePrice += 1300;
      SEO_IDS.forEach(id => bundledIds.add(id));
      appliedBundles.push('SEO Pack');
    }
  }

  // A la carte cost for tools not covered by a bundle
  const unbundledCost = TOOLS
    .filter(t => selectedIds.has(t.id) && !bundledIds.has(t.id))
    .reduce((sum, t) => sum + t.price, 0);

  const toolsCost = bundlePrice + unbundledCost;
  const discountAmount = alaCarteTotal - toolsCost;

  return { toolsCost, discountAmount, appliedBundles };
}

// ---------------------------------------------------------------------------
// Component types
// ---------------------------------------------------------------------------

interface FormData {
  name: string;
  clientId: string;
  clientName: string;
  numPosts: number;
  researchAddon: boolean;
  selectedTools: Set<string>;
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (project: Project) => void;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface GroupCheckboxProps {
  tool: ToolDef;
  checked: boolean;
  onChange: (id: string, checked: boolean) => void;
}

function ToolCheckbox({ tool, checked, onChange }: GroupCheckboxProps) {
  return (
    <label
      className={`flex items-center gap-2 cursor-pointer rounded px-2 py-1 transition-colors
        ${tool.implemented ? 'hover:bg-slate-50' : 'opacity-60 cursor-not-allowed'}`}
      title={tool.implemented ? undefined : 'Not yet available — coming soon'}
    >
      <input
        type="checkbox"
        checked={checked}
        disabled={!tool.implemented}
        onChange={e => onChange(tool.id, e.target.checked)}
        className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50"
      />
      <span className="flex-1 text-sm text-slate-700">{tool.name}</span>
      <span className="text-xs text-slate-500">${tool.price.toLocaleString()}</span>
      {!tool.implemented && (
        <span
          className="inline-flex items-center gap-1 rounded bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-700"
          title="Not yet available — coming soon"
        >
          <Info className="h-3 w-3" />
          Soon
        </span>
      )}
    </label>
  );
}

// ---------------------------------------------------------------------------
// Main dialog
// ---------------------------------------------------------------------------

export function NewProjectDialog({ open, onOpenChange, onSuccess }: Props) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<FormData>({
    name: '',
    clientId: '',
    clientName: '',
    numPosts: 30,
    researchAddon: false,
    selectedTools: new Set(),
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // ---- live price calculation ----
  const pricing = useMemo(() => {
    const postsCost        = formData.numPosts * PRICE_PER_POST;
    const researchAddonCost = formData.researchAddon
      ? formData.numPosts * RESEARCH_PRICE_PER_POST
      : 0;
    const { toolsCost, discountAmount, appliedBundles } = calculateToolsCost(formData.selectedTools);
    const totalPrice = postsCost + researchAddonCost + toolsCost;

    return { postsCost, researchAddonCost, toolsCost, discountAmount, appliedBundles, totalPrice };
  }, [formData.numPosts, formData.researchAddon, formData.selectedTools]);

  // ---- bundle badge detection ----
  const foundationAllChecked = [...FOUNDATION_IDS].every(id => formData.selectedTools.has(id));
  const seoAllChecked        = [...SEO_IDS].every(id => formData.selectedTools.has(id));

  // ---- a la carte total for strikethrough ----
  const alaCarteToolsTotal = TOOLS
    .filter(t => formData.selectedTools.has(t.id))
    .reduce((sum, t) => sum + t.price, 0);
  const hasDiscount = pricing.discountAmount > 0;

  // ---- mutation ----
  const createMutation = useMutation({
    mutationFn: (data: FormData) =>
      projectsApi.create({
        name: data.name,
        clientId: data.clientId,
        templates: [],
        platforms: [],
        tone: 'professional',
        numPosts: data.numPosts,
        pricePerPost: PRICE_PER_POST,
        researchPricePerPost: data.researchAddon ? RESEARCH_PRICE_PER_POST : 0,
        postsCost: pricing.postsCost,
        researchAddonCost: pricing.researchAddonCost,
        toolsCost: pricing.toolsCost,
        discountAmount: pricing.discountAmount,
        selectedTools: [...data.selectedTools],
        totalPrice: pricing.totalPrice,
      }),
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      onSuccess?.(project);
      handleClose();
    },
  });

  // ---- helpers ----
  const toggleTool = (id: string, checked: boolean) => {
    setFormData(prev => {
      const next = new Set(prev.selectedTools);
      if (checked) next.add(id); else next.delete(id);
      return { ...prev, selectedTools: next };
    });
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = 'Project name is required';
    if (!formData.clientId.trim()) newErrors.clientId = 'Client ID is required';
    if (!formData.clientName.trim()) newErrors.clientName = 'Client name is required';
    if (formData.numPosts < 1 || formData.numPosts > 100)
      newErrors.numPosts = 'Post count must be between 1 and 100';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) createMutation.mutate(formData);
  };

  const handleClose = () => {
    setFormData({
      name: '',
      clientId: '',
      clientName: '',
      numPosts: 30,
      researchAddon: false,
      selectedTools: new Set(),
    });
    setErrors({});
    onOpenChange(false);
  };

  // ---- tool groups ----
  const foundationTools = TOOLS.filter(t => t.group === 'foundation');
  const seoTools        = TOOLS.filter(t => t.group === 'seo');
  const advancedTools   = TOOLS.filter(t => t.group === 'advanced');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[560px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
          <DialogDescription>
            Configure posts and optional research tools. Pricing updates live as you make selections.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* ---- Project Name ---- */}
          <div>
            <label className="mb-1 flex items-center gap-2 text-sm font-medium text-slate-800">
              <Building2 className="h-4 w-4" />
              Project Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              placeholder="March 2026 Campaign"
              className={`w-full rounded-md border px-3 py-2 text-sm ${
                errors.name ? 'border-rose-500' : 'border-slate-200'
              }`}
            />
            {errors.name && <p className="mt-1 text-xs text-rose-600">{errors.name}</p>}
          </div>

          {/* ---- Client ID ---- */}
          <div>
            <label className="mb-1 flex items-center gap-2 text-sm font-medium text-slate-800">
              <User className="h-4 w-4" />
              Client ID
            </label>
            <input
              type="text"
              value={formData.clientId}
              onChange={e => setFormData({ ...formData, clientId: e.target.value })}
              placeholder="acme-corp"
              className={`w-full rounded-md border px-3 py-2 text-sm ${
                errors.clientId ? 'border-rose-500' : 'border-slate-200'
              }`}
            />
            {errors.clientId && <p className="mt-1 text-xs text-rose-600">{errors.clientId}</p>}
            <p className="mt-1 text-xs text-slate-500">Lowercase, hyphenated identifier</p>
          </div>

          {/* ---- Client Name ---- */}
          <div>
            <label className="mb-1 flex items-center gap-2 text-sm font-medium text-slate-800">
              <Target className="h-4 w-4" />
              Client Name
            </label>
            <input
              type="text"
              value={formData.clientName}
              onChange={e => setFormData({ ...formData, clientName: e.target.value })}
              placeholder="Acme Corp"
              className={`w-full rounded-md border px-3 py-2 text-sm ${
                errors.clientName ? 'border-rose-500' : 'border-slate-200'
              }`}
            />
            {errors.clientName && <p className="mt-1 text-xs text-rose-600">{errors.clientName}</p>}
          </div>

          {/* ---- Section A: Post Generation ---- */}
          <div className="rounded-lg border border-slate-200 p-4 space-y-3">
            <h3 className="text-sm font-semibold text-slate-800">Post Generation</h3>

            <div className="flex items-center gap-3">
              <label className="text-sm text-slate-700 whitespace-nowrap">Number of posts</label>
              <input
                type="number"
                min={1}
                max={100}
                value={formData.numPosts}
                onChange={e =>
                  setFormData({ ...formData, numPosts: Math.max(1, Math.min(100, parseInt(e.target.value) || 1)) })
                }
                className={`w-20 rounded-md border px-3 py-1.5 text-sm text-center ${
                  errors.numPosts ? 'border-rose-500' : 'border-slate-200'
                }`}
              />
              <span className="text-xs text-slate-500">× ${PRICE_PER_POST}/post</span>
            </div>
            {errors.numPosts && <p className="text-xs text-rose-600">{errors.numPosts}</p>}

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.researchAddon}
                onChange={e => setFormData({ ...formData, researchAddon: e.target.checked })}
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-slate-700">
                Topic research add-on{' '}
                <span className="text-slate-500">(+${RESEARCH_PRICE_PER_POST}/post)</span>
              </span>
            </label>
          </div>

          {/* ---- Section B: Research Tools ---- */}
          <div className="rounded-lg border border-slate-200 p-4 space-y-4">
            <h3 className="text-sm font-semibold text-slate-800">Research Tools</h3>

            {/* Foundation group */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Foundation
                </span>
                {foundationAllChecked && (
                  <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">
                    Foundation Pack — saves $300
                  </span>
                )}
              </div>
              <div className="space-y-1">
                {foundationTools.map(tool => (
                  <ToolCheckbox
                    key={tool.id}
                    tool={tool}
                    checked={formData.selectedTools.has(tool.id)}
                    onChange={toggleTool}
                  />
                ))}
              </div>
            </div>

            {/* SEO group */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  SEO
                </span>
                {seoAllChecked && !foundationAllChecked && (
                  <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">
                    SEO Pack — saves $100
                  </span>
                )}
                {seoAllChecked && foundationAllChecked && (
                  <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700">
                    Complete Strategy — saves $800
                  </span>
                )}
              </div>
              <div className="space-y-1">
                {seoTools.map(tool => (
                  <ToolCheckbox
                    key={tool.id}
                    tool={tool}
                    checked={formData.selectedTools.has(tool.id)}
                    onChange={toggleTool}
                  />
                ))}
              </div>
            </div>

            {/* Advanced group */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Advanced
                </span>
                <span className="text-xs text-slate-400 italic">a la carte only</span>
              </div>
              <div className="space-y-1">
                {advancedTools.map(tool => (
                  <ToolCheckbox
                    key={tool.id}
                    tool={tool}
                    checked={formData.selectedTools.has(tool.id)}
                    onChange={toggleTool}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* ---- Section C: Price Breakdown ---- */}
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2 text-sm">
            <h3 className="font-semibold text-slate-800 mb-2">Price Breakdown</h3>

            <div className="flex justify-between text-slate-700">
              <span>Post Generation ({formData.numPosts} posts)</span>
              <span className="font-medium">${pricing.postsCost.toLocaleString()}</span>
            </div>

            {pricing.researchAddonCost > 0 && (
              <div className="flex justify-between text-slate-700">
                <span>Topic Research Add-on</span>
                <span className="font-medium">${pricing.researchAddonCost.toLocaleString()}</span>
              </div>
            )}

            {formData.selectedTools.size > 0 && (
              <div className="flex justify-between text-slate-700">
                <span>Research Tools</span>
                <span className="font-medium">
                  {hasDiscount && (
                    <span className="mr-2 text-xs text-slate-400 line-through">
                      ${alaCarteToolsTotal.toLocaleString()}
                    </span>
                  )}
                  ${pricing.toolsCost.toLocaleString()}
                </span>
              </div>
            )}

            {hasDiscount && (
              <div className="flex justify-between text-green-700 font-medium">
                <span>Bundle Discount</span>
                <span>−${pricing.discountAmount.toLocaleString()}</span>
              </div>
            )}

            <div className="border-t border-slate-200 pt-2 flex justify-between font-semibold text-slate-900">
              <span>Total</span>
              <span>${pricing.totalPrice.toLocaleString()}</span>
            </div>

            {pricing.appliedBundles.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1">
                {pricing.appliedBundles.map(name => (
                  <span
                    key={name}
                    className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700"
                  >
                    {name}
                  </span>
                ))}
              </div>
            )}
          </div>

          {createMutation.isError && (
            <p className="text-sm text-rose-600">
              Failed to create project. Please check your inputs and try again.
            </p>
          )}

          <DialogFooter>
            <button
              type="button"
              onClick={handleClose}
              className="rounded-md border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Project'}
            </button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
