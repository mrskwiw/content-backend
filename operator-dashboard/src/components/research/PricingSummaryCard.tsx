import React from 'react';
import { CheckCircle2, Sparkles, TrendingDown } from 'lucide-react';
import { PricingPreview } from '../../api/research';

interface PricingSummaryCardProps {
  pricing: PricingPreview;
  selectedCount: number;
}

export function PricingSummaryCard({ pricing, selectedCount }: PricingSummaryCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-6">
      {/* Metrics Grid */}
      <div className="grid grid-cols-4 gap-4 mb-4">
        <PriceMetric
          label="Selected"
          value={`${selectedCount} tool${selectedCount !== 1 ? 's' : ''}`}
          icon={null}
        />
        <PriceMetric
          label="Base Price"
          value={`$${pricing.baseCost.toFixed(2)}`}
          icon={null}
        />
        {pricing.discount > 0 && (
          <PriceMetric
            label="Discount"
            value={`-$${pricing.discount.toFixed(2)}`}
            color="emerald"
            icon={<TrendingDown className="h-4 w-4" />}
          />
        )}
        <PriceMetric
          label="Total"
          value={`$${pricing.finalCost.toFixed(2)}`}
          emphasized
          icon={null}
        />
      </div>

      {/* Bundle Applied */}
      {pricing.bundleApplied && pricing.bundleName && (
        <div className="flex items-center gap-2 text-sm mb-3 p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          <span className="text-emerald-700 dark:text-emerald-300 font-medium">
            {pricing.bundleName} applied - Save {pricing.savingsPercent}%!
          </span>
        </div>
      )}

      {/* Next Bundle Suggestion */}
      {pricing.nextBundleSuggestion && (
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-start gap-3">
            <Sparkles className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
                Add {pricing.nextBundleSuggestion.missingTools.length} more tool
                {pricing.nextBundleSuggestion.missingTools.length !== 1 ? 's' : ''} → Save $
                {pricing.nextBundleSuggestion.potentialSavings.toFixed(2)}
              </p>
              <p className="text-xs text-blue-700 dark:text-blue-300 mb-2">
                Complete {pricing.nextBundleSuggestion.bundleName} for $
                {pricing.nextBundleSuggestion.additionalCost.toFixed(2)} more
              </p>
              <div className="flex flex-wrap gap-1">
                {pricing.nextBundleSuggestion.missingToolNames.map((toolName, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded"
                  >
                    {toolName}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface PriceMetricProps {
  label: string;
  value: string;
  color?: 'emerald' | 'blue' | 'gray';
  emphasized?: boolean;
  icon?: React.ReactNode;
}

function PriceMetric({ label, value, color = 'gray', emphasized = false, icon }: PriceMetricProps) {
  const colorClasses = {
    emerald: 'text-emerald-600 dark:text-emerald-400',
    blue: 'text-blue-600 dark:text-blue-400',
    gray: 'text-gray-900 dark:text-gray-100',
  };

  return (
    <div className={`${emphasized ? 'bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3' : ''}`}>
      <div className="text-xs text-gray-500 dark:text-gray-400 mb-1 flex items-center gap-1">
        {icon}
        {label}
      </div>
      <div className={`text-lg font-bold ${colorClasses[color]}`}>{value}</div>
    </div>
  );
}
