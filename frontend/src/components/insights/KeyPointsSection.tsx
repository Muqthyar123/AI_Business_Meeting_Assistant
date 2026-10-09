import React from 'react';
import { CheckCircle2, Tag, Layers } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';

interface KeyPointsSectionProps {
  keyPoints: string[];
  topics: string[];
}

export const KeyPointsSection: React.FC<KeyPointsSectionProps> = ({ keyPoints, topics }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Key Discussion Points */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-brand-primary" />
            <CardTitle>Key Discussion Points</CardTitle>
          </div>
          <CardDescription>Core substantive topics evaluated during the call</CardDescription>
        </CardHeader>
        <CardContent>
          {keyPoints.length === 0 ? (
            <p className="text-xs text-content-secondary">No key points extracted yet.</p>
          ) : (
            <ul className="space-y-3">
              {keyPoints.map((point, index) => (
                <li
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-xl bg-surface-secondary/40 dark:bg-surface-darkSecondary/30 border border-edge-light dark:border-edge-dark text-sm leading-relaxed"
                >
                  <span className="w-5 h-5 rounded-full bg-brand-light dark:bg-brand-primary/20 text-brand-primary dark:text-brand-secondary flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                    {index + 1}
                  </span>
                  <span className="text-content-primary dark:text-content-darkPrimary">
                    {point}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Topics & Tags */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Tag className="w-4 h-4 text-brand-secondary" />
            <CardTitle>Topics & Tags</CardTitle>
          </div>
          <CardDescription>Primary thematic clusters</CardDescription>
        </CardHeader>
        <CardContent>
          {topics.length === 0 ? (
            <p className="text-xs text-content-secondary">No topics tagged yet.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {topics.map((topic, i) => (
                <span
                  key={i}
                  className="px-3 py-1.5 rounded-xl bg-brand-light dark:bg-brand-primary/15 text-brand-primary dark:text-brand-secondary border border-brand-primary/20 text-xs font-medium"
                >
                  #{topic}
                </span>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
