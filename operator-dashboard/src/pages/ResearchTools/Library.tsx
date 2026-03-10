import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { researchApi, costsApi } from '../../api';
import { ToolCard } from '../../components/research/ToolCard';
import { PricingSummaryCard } from '../../components/research/PricingSummaryCard';
import { Search, Filter } from 'lucide-react';

export default function ResearchToolsLibrary() {
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch available tools
  const { data: tools = [], isLoading: toolsLoading } = useQuery({
    queryKey: ['research-tools'],
    queryFn: () => researchApi.listTools()
  });

  // Real-time pricing preview with bundle detection
  const { data: pricing } = useQuery({
    queryKey: ['pricing-preview', selectedTools],
    queryFn: () => researchApi.getPricingPreview(selectedTools),
    enabled: selectedTools.length > 0
  });

  // Filter tools by category and search
  const filteredTools = tools.filter(tool => {
    const matchesCategory = categoryFilter === 'all' || tool.category === categoryFilter;
    const matchesSearch = !searchQuery ||
      tool.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (tool.description || '').toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  // Get unique categories
  const categories = ['all', ...new Set(tools.map(t => t.category).filter(Boolean))];

  const handleToggleTool = (toolId: string) => {
    setSelectedTools(prev =>
      prev.includes(toolId)
        ? prev.filter(id => id !== toolId)
        : [...prev, toolId]
    );
  };

  const handleClearSelection = () => {
    setSelectedTools([]);
  };

  if (toolsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Research Tools Library
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Select tools to enhance your content strategy with AI-powered research
          </p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white dark:bg-neutral-900 rounded-lg border border-gray-200 dark:border-neutral-700 p-4">
        <div className="flex gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <div className="flex gap-2">
              {categories.map(category => (
                <button
                  key={category}
                  onClick={() => setCategoryFilter(category)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    categoryFilter === category
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-700'
                  }`}
                >
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Summary */}
      {selectedTools.length > 0 && pricing && (
        <PricingSummaryCard
          pricing={pricing}
          selectedCount={selectedTools.length}
        />
      )}

      {/* Tool Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTools.map(tool => (
          <ToolCard
            key={tool.name}
            tool={tool}
            isSelected={selectedTools.includes(tool.name)}
            onToggle={() => handleToggleTool(tool.name)}
          />
        ))}
      </div>

      {/* Empty State */}
      {filteredTools.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            No tools found matching your filters.
          </p>
        </div>
      )}

      {/* Action Bar */}
      {selectedTools.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-neutral-900 border-t border-gray-200 dark:border-neutral-700 p-4 shadow-lg">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {selectedTools.length} tool{selectedTools.length !== 1 ? 's' : ''} selected
              {pricing && (
                <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
                  • ${pricing.finalCost.toFixed(2)}
                </span>
              )}
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleClearSelection}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-800 rounded-lg transition-colors"
              >
                Clear Selection
              </button>
              <button
                className="px-6 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                Add to Project
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
