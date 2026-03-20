import { X, BookOpen, Calendar, TrendingUp, MessageSquare, Target, Lightbulb, Award, Users } from 'lucide-react';
import { format } from 'date-fns';
import type { Story } from '@/api/stories';

interface StoryDetailsDrawerProps {
  story: Story | null;
  open: boolean;
  onClose: () => void;
}

export function StoryDetailsDrawer({ story, open, onClose }: StoryDetailsDrawerProps) {
  if (!open || !story) return null;

  const formatStoryType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="absolute inset-y-0 right-0 flex max-w-full pl-10">
        <div className="w-screen max-w-2xl">
          <div className="flex h-full flex-col overflow-y-scroll bg-white dark:bg-neutral-900 shadow-xl">
            {/* Header */}
            <div className="border-b border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 px-6 py-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/20">
                    <BookOpen className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                      {story.title || 'Untitled Story'}
                    </h2>
                    <div className="flex items-center gap-2 mt-1">
                      {story.storyType && (
                        <span className="inline-flex items-center rounded-full bg-primary-100 dark:bg-primary-900/20 px-2.5 py-0.5 text-xs font-medium text-primary-800 dark:text-primary-300">
                          {formatStoryType(story.storyType)}
                        </span>
                      )}
                      <span className="text-xs text-neutral-600 dark:text-neutral-400">
                        <Calendar className="inline h-3 w-3 mr-1" />
                        {format(new Date(story.createdAt), 'MMM d, yyyy')}
                      </span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="rounded-lg p-2 text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-600 dark:hover:text-neutral-300"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
              {/* Summary */}
              {story.summary && (
                <div>
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 uppercase tracking-wide mb-2">
                    Summary
                  </h3>
                  <p className="text-sm text-neutral-700 dark:text-neutral-300">
                    {story.summary}
                  </p>
                </div>
              )}

              {/* Emotional Hook */}
              {story.emotionalHook && (
                <div>
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 uppercase tracking-wide mb-2">
                    Key Quote
                  </h3>
                  <div className="rounded-lg bg-neutral-50 dark:bg-neutral-800 p-4 border-l-4 border-primary-500">
                    <MessageSquare className="h-5 w-5 text-primary-600 dark:text-primary-400 mb-2" />
                    <p className="text-base italic text-neutral-900 dark:text-neutral-100">
                      "{story.emotionalHook}"
                    </p>
                  </div>
                </div>
              )}

              {/* Key Metrics */}
              {story.keyMetrics && Object.keys(story.keyMetrics).length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 uppercase tracking-wide mb-3 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    Key Results & Metrics
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(story.keyMetrics).map(([key, value]) => (
                      <div
                        key={key}
                        className="rounded-lg bg-emerald-50 dark:bg-emerald-900/20 p-3 border border-emerald-200 dark:border-emerald-800"
                      >
                        <p className="text-xs text-emerald-700 dark:text-emerald-400 font-medium mb-1">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                        </p>
                        <p className="text-lg font-bold text-emerald-900 dark:text-emerald-100">
                          {String(value)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Full Story Structure */}
              {story.fullStory && (
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 uppercase tracking-wide">
                    Full Story
                  </h3>

                  {/* Customer Background */}
                  {story.fullStory.customer_background && (
                    <StorySection
                      icon={Users}
                      title="Customer Background"
                      data={story.fullStory.customer_background}
                    />
                  )}

                  {/* Challenge */}
                  {story.fullStory.challenge && (
                    <StorySection
                      icon={Target}
                      title="Challenge"
                      data={story.fullStory.challenge}
                    />
                  )}

                  {/* Decision Process */}
                  {story.fullStory.decision_process && (
                    <StorySection
                      icon={Lightbulb}
                      title="Decision Process"
                      data={story.fullStory.decision_process}
                    />
                  )}

                  {/* Implementation */}
                  {story.fullStory.implementation && (
                    <StorySection
                      icon={Award}
                      title="Implementation"
                      data={story.fullStory.implementation}
                    />
                  )}

                  {/* Results */}
                  {story.fullStory.results && (
                    <StorySection
                      icon={TrendingUp}
                      title="Results"
                      data={story.fullStory.results}
                    />
                  )}

                  {/* Testimonials */}
                  {story.fullStory.testimonials && (
                    <StorySection
                      icon={MessageSquare}
                      title="Testimonials"
                      data={story.fullStory.testimonials}
                    />
                  )}

                  {/* Future Plans */}
                  {story.fullStory.future_plans && (
                    <StorySection
                      icon={Calendar}
                      title="Future Plans"
                      data={story.fullStory.future_plans}
                    />
                  )}
                </div>
              )}

              {/* Usage Statistics */}
              <div>
                <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 uppercase tracking-wide mb-3">
                  Usage Statistics
                </h3>
                <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-neutral-600 dark:text-neutral-400">Total Uses</p>
                      <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mt-1">
                        {story.usageCount}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-neutral-600 dark:text-neutral-400">Platforms</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {story.platformsUsed.length > 0 ? (
                          story.platformsUsed.map((platform) => (
                            <span
                              key={platform}
                              className="inline-flex items-center rounded-full bg-primary-100 dark:bg-primary-900/20 px-2 py-0.5 text-xs font-medium text-primary-800 dark:text-primary-300"
                            >
                              {platform}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-neutral-500 dark:text-neutral-400">Not used yet</span>
                        )}
                      </div>
                    </div>
                  </div>
                  {story.source && (
                    <div className="mt-3 pt-3 border-t border-neutral-200 dark:border-neutral-700">
                      <p className="text-xs text-neutral-600 dark:text-neutral-400">Source</p>
                      <p className="text-sm text-neutral-900 dark:text-neutral-100 mt-1">
                        {story.source.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-neutral-200 dark:border-neutral-700 px-6 py-4 bg-neutral-50 dark:bg-neutral-800">
              <div className="flex justify-end gap-3">
                <button
                  onClick={onClose}
                  className="rounded-lg border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-900 px-4 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800"
                >
                  Close
                </button>
                <button className="rounded-lg bg-primary-600 dark:bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 dark:hover:bg-primary-600">
                  Use in Content
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface StorySectionProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  data: Record<string, unknown>;
}

function StorySection({ icon: Icon, title, data }: StorySectionProps) {
  if (!data) return null;

  return (
    <div className="rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4">
      <h4 className="flex items-center gap-2 text-sm font-semibold text-neutral-900 dark:text-neutral-100 mb-3">
        <Icon className="h-4 w-4 text-primary-600 dark:text-primary-400" />
        {title}
      </h4>
      <div className="space-y-2 text-sm text-neutral-700 dark:text-neutral-300">
        {Object.entries(data).map(([key, value]) => {
          if (!value) return null;

          // Format the key
          const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

          // Handle different value types
          if (Array.isArray(value) && value.length > 0) {
            return (
              <div key={key}>
                <p className="text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
                  {formattedKey}
                </p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  {value.map((item, index) => (
                    <li key={index} className="text-sm">
                      {String(item)}
                    </li>
                  ))}
                </ul>
              </div>
            );
          } else if (typeof value === 'string' && value.length > 0) {
            return (
              <div key={key}>
                <p className="text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
                  {formattedKey}
                </p>
                <p className="text-sm">{value}</p>
              </div>
            );
          } else if (typeof value === 'object' && value !== null) {
            return (
              <div key={key}>
                <p className="text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1">
                  {formattedKey}
                </p>
                <pre className="text-xs bg-neutral-50 dark:bg-neutral-800 p-2 rounded overflow-x-auto">
                  {JSON.stringify(value, null, 2)}
                </pre>
              </div>
            );
          }
          return null;
        })}
      </div>
    </div>
  );
}
