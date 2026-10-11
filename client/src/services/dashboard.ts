import { request } from './api-client';
import {
  DashboardOverviewResponse,
  DashboardTrendsResponse,
  OperationsQueueResponse,
  PendingApprovalItem,
  ReconciliationHealthResponse,
} from '@/types/api';

export interface OperationsQueueFilterParams {
  page?: number;
  pageSize?: number;
  status?: string;
  exceptionType?: string;
  currency?: string;
  minImpact?: number;
  maxImpact?: number;
  search?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export const dashboardService = {
  getOverview: async (): Promise<DashboardOverviewResponse> => {
    return request<DashboardOverviewResponse>('dashboard/overview');
  },

  getReconciliationHealth: async (): Promise<ReconciliationHealthResponse> => {
    return request<ReconciliationHealthResponse>('dashboard/reconciliation-health');
  },

  getExceptionTrends: async (): Promise<DashboardTrendsResponse> => {
    return request<DashboardTrendsResponse>('dashboard/exception-trends');
  },

  getPendingApprovals: async (): Promise<PendingApprovalItem[]> => {
    return request<PendingApprovalItem[]>('dashboard/pending-approvals');
  },

  getOperationsQueue: async (
    params: OperationsQueueFilterParams = {}
  ): Promise<OperationsQueueResponse> => {
    const query = new URLSearchParams();
    if (params.page) query.set('page', String(params.page));
    if (params.pageSize) query.set('page_size', String(params.pageSize));
    if (params.status) query.set('status', params.status);
    if (params.exceptionType) query.set('exception_type', params.exceptionType);
    if (params.currency) query.set('currency', params.currency);
    if (params.minImpact !== undefined) query.set('min_impact', String(params.minImpact));
    if (params.maxImpact !== undefined) query.set('max_impact', String(params.maxImpact));
    if (params.search) query.set('search', params.search);
    if (params.sortBy) query.set('sort_by', params.sortBy);
    if (params.sortOrder) query.set('sort_order', params.sortOrder);

    const queryString = query.toString();
    const endpoint = queryString ? `dashboard/operations-queue?${queryString}` : 'dashboard/operations-queue';
    return request<OperationsQueueResponse>(endpoint);
  },
};
