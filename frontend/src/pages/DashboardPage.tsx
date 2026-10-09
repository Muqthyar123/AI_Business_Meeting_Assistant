import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, History, Sparkles, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { KpiGrid } from '../components/dashboard/KpiGrid';
import { RecentMeetingsTable } from '../components/dashboard/RecentMeetingsTable';
import { ActionItemsSummary } from '../components/dashboard/ActionItemsSummary';
import { DecisionsSummary } from '../components/dashboard/DecisionsSummary';
import { DashboardCharts } from '../components/dashboard/DashboardCharts';
import { useData } from '../context/DataContext';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { mode } = useData();

  const formattedDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-brand-navy via-[#1e2246] to-brand-primary text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-radial from-brand-secondary/20 to-transparent pointer-events-none" />

        <div className="relative z-10 space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase tracking-wider font-semibold text-brand-teal/90">
              {formattedDate}
            </span>
            {mode === 'demo' && (
              <span className="text-[10px] bg-amber-500/20 text-amber-300 border border-amber-400/30 px-2 py-0.5 rounded-full font-semibold">
                Demo Workspace
              </span>
            )}
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight">
            Turn your meetings into measurable progress.
          </h1>
          <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
            MeetMind automatically converts spoken discussions into verified decisions, accountable action items, and structured follow-up plans.
          </p>
        </div>

        <div className="relative z-10 flex flex-wrap items-center gap-3 shrink-0">
          <Button
            variant="secondary"
            size="md"
            onClick={() => navigate('/history')}
            leftIcon={<History className="w-4 h-4" />}
            className="bg-white/10 hover:bg-white/20 text-white border-0"
          >
            Meeting History
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={() => navigate('/meetings/new')}
            leftIcon={<Plus className="w-4 h-4" />}
            className="bg-brand-primary hover:bg-brand-hover shadow-lg shadow-brand-primary/40 text-white"
          >
            New Meeting
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <KpiGrid />

      {/* Recent Meetings Table */}
      <RecentMeetingsTable />

      {/* Outcomes & Tasks Breakdown Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <DashboardCharts />
        <DecisionsSummary />
        <ActionItemsSummary />
      </div>
    </div>
  );
};
