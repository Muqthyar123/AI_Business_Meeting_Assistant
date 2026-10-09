import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { DashboardPage } from '../pages/DashboardPage';
import { MeetingsPage } from '../pages/MeetingsPage';
import { NewMeetingPage } from '../pages/NewMeetingPage';
import { MeetingDetailPage } from '../pages/MeetingDetailPage';
import { InsightsPage } from '../pages/InsightsPage';
import { DecisionsPage } from '../pages/DecisionsPage';
import { ActionItemsPage } from '../pages/ActionItemsPage';
import { FollowUpsPage } from '../pages/FollowUpsPage';
import { HistoryPage } from '../pages/HistoryPage';
import { ReportsPage } from '../pages/ReportsPage';
import { SettingsPage } from '../pages/SettingsPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'meetings',
        element: <MeetingsPage />,
      },
      {
        path: 'meetings/new',
        element: <NewMeetingPage />,
      },
      {
        path: 'transcribe',
        element: <NewMeetingPage />,
      },
      {
        path: 'meetings/:meetingId',
        element: <MeetingDetailPage />,
      },
      {
        path: 'meetings/:meetingId/transcript',
        element: <MeetingDetailPage />,
      },
      {
        path: 'meetings/:meetingId/insights',
        element: <MeetingDetailPage />,
      },
      {
        path: 'insights',
        element: <InsightsPage />,
      },
      {
        path: 'decisions',
        element: <DecisionsPage />,
      },
      {
        path: 'decisions/:decisionId',
        element: <DecisionsPage />,
      },
      {
        path: 'action-items',
        element: <ActionItemsPage />,
      },
      {
        path: 'action-items/:taskId',
        element: <ActionItemsPage />,
      },
      {
        path: 'follow-ups',
        element: <FollowUpsPage />,
      },
      {
        path: 'follow-ups/:planId',
        element: <FollowUpsPage />,
      },
      {
        path: 'history',
        element: <HistoryPage />,
      },
      {
        path: 'reports',
        element: <ReportsPage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);
