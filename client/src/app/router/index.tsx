import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '@/layouts/app-layout';
import { LoginPage } from '@/features/auth/login-page';
import { ProtectedRoute } from '@/components/layout/protected-route';
import { DashboardPage } from '@/features/dashboard/dashboard-page';
import { ReconciliationPage } from '@/features/reconciliation/reconciliation-page';
import { ReconciliationDetailPage } from '@/features/reconciliation/reconciliation-detail-page';
import { ExceptionsPage } from '@/features/exceptions/exceptions-page';
import { ExceptionDetailPage } from '@/features/exceptions/exception-detail-page';
import { ReviewPage } from '@/features/review/review-page';
import { TransactionsPage } from '@/features/transactions/transactions-page';
import { AnalyticsPage } from '@/features/analytics/analytics-page';
import { AuditPage } from '@/features/audit/audit-page';
import { SettingsPage } from '@/features/settings/settings-page';
import { NotFoundPage } from '@/components/feedback/not-found-page';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'reconciliation',
        element: <ReconciliationPage />,
      },
      {
        path: 'reconciliation/:id',
        element: <ReconciliationDetailPage />,
      },
      {
        path: 'exceptions',
        element: <ExceptionsPage />,
      },
      {
        path: 'exceptions/:id',
        element: <ExceptionDetailPage />,
      },
      {
        path: 'review',
        element: <ReviewPage />,
      },
      {
        path: 'transactions',
        element: <TransactionsPage />,
      },
      {
        path: 'analytics',
        element: <AnalyticsPage />,
      },
      {
        path: 'audit',
        element: <AuditPage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);
