import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { useData } from '../../context/DataContext';

export const DashboardCharts: React.FC = () => {
  const { actionItems } = useData();

  // Action item status distribution based on actual live items
  const statusCounts = {
    'To Do': actionItems.filter((a) => a.status === 'To Do').length,
    'In Progress': actionItems.filter((a) => a.status === 'In Progress').length,
    'Completed': actionItems.filter((a) => a.status === 'Completed').length,
    'Blocked': actionItems.filter((a) => a.status === 'Blocked').length,
  };

  const actionStatusData = [
    { name: 'To Do', value: statusCounts['To Do'] || 0, color: '#94A3B8' },
    { name: 'In Progress', value: statusCounts['In Progress'] || 0, color: '#6558E8' },
    { name: 'Completed', value: statusCounts['Completed'] || 0, color: '#10B981' },
    { name: 'Blocked', value: statusCounts['Blocked'] || 0, color: '#EF4444' },
  ].filter((item) => item.value > 0);

  // If there are no tasks yet, show a placeholder entry
  const displayData =
    actionStatusData.length > 0
      ? actionStatusData
      : [{ name: 'No Active Tasks', value: 1, color: '#CBD5E1' }];

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Task Status Breakdown</CardTitle>
          <CardDescription>Real-time execution health across all action items</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="h-64 flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={displayData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={75}
              paddingAngle={4}
              dataKey="value"
            >
              {displayData.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(25, 28, 50, 0.95)',
                borderColor: '#2A2E54',
                borderRadius: 12,
                color: '#FFFFFF',
                fontSize: 12,
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value) => (
                <span className="text-xs text-content-secondary dark:text-content-darkSecondary">
                  {value}
                </span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
