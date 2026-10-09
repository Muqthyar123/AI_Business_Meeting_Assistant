import React, { useState } from 'react';
import {
  Milestone,
  Plus,
  Sparkles,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { FollowUpPlan } from '../types';
import { FollowUpTimeline } from '../components/follow-ups/FollowUpTimeline';
import { FollowUpFormModal } from '../components/follow-ups/FollowUpFormModal';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { useData } from '../context/DataContext';

export const FollowUpsPage: React.FC = () => {
  const { followUps, meetings, generateFollowUpPlan } = useData();

  const [activeTab, setActiveTab] = useState<'All' | 'Active' | 'Completed' | 'Draft'>('All');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<FollowUpPlan | null>(null);

  const filteredPlans = followUps.filter((p) => {
    if (activeTab === 'All') return true;
    return p.status === activeTab;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-content-primary dark:text-content-darkPrimary flex items-center gap-2.5">
            <Milestone className="w-6 h-6 text-brand-primary" />
            Follow-up Execution Plans
          </h1>
          <p className="text-xs sm:text-sm text-content-secondary dark:text-content-darkSecondary mt-0.5">
            Structured roadmap sequences turning meeting agreements into verified delivery milestones
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          leftIcon={<Plus className="w-3.5 h-3.5" />}
          onClick={() => {
            setEditingPlan(null);
            setIsModalOpen(true);
          }}
        >
          Create Follow-up Plan
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-edge-light dark:border-edge-dark pb-1">
        {(['All', 'Active', 'Completed', 'Draft'] as const).map((tab) => {
          const count =
            tab === 'All'
              ? followUps.length
              : followUps.filter((p) => p.status === tab).length;
          const isActive = activeTab === tab;

          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3.5 py-2 text-xs font-semibold rounded-xl transition-all flex items-center gap-1.5 ${
                isActive
                  ? 'bg-brand-primary text-white shadow-xs'
                  : 'text-content-secondary hover:text-content-primary hover:bg-surface-secondary'
              }`}
            >
              <span>{tab}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  isActive ? 'bg-white/20 text-white' : 'bg-surface-secondary text-content-secondary'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Plans List */}
      {filteredPlans.length === 0 ? (
        <EmptyState
          icon={<Milestone className="w-8 h-8 text-brand-primary" />}
          title="No follow-up plans found"
          description="Transform meeting outcomes into actionable milestone timelines."
          actionLabel="Create Follow-up Plan"
          onAction={() => {
            setEditingPlan(null);
            setIsModalOpen(true);
          }}
        />
      ) : (
        <div className="space-y-6">
          {filteredPlans.map((plan) => (
            <FollowUpTimeline
              key={plan.id}
              plan={plan}
              onEdit={(p) => {
                setEditingPlan(p);
                setIsModalOpen(true);
              }}
            />
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      <FollowUpFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        plan={editingPlan}
      />
    </div>
  );
};
