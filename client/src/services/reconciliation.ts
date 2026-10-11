import { request } from './api-client';
import {
  ExceptionEvidenceResponse,
  ExceptionSummary,
  FinancialEvidenceSummary,
  IngestionSummary,
  InvestigationResponse,
  PaginatedResponse,
  ProposalResponse,
  ReconciliationResultItem,
  ReconciliationRun,
  ResolutionHistoryItem,
  ResolutionSummaryResponse,
  CreateProposalPayload,
  DecisionPayload,
  ResolveExceptionPayload,
  ReopenExceptionPayload,
  TransactionSummary,
} from '@/types/api';

export const reconciliationService = {
  triggerRun: async (params: {
    run_type?: string;
    tolerance?: string;
    settlement_delay_days?: number;
  }): Promise<ReconciliationRun> => {
    return request<ReconciliationRun>('reconciliation/runs', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  listRuns: async (page = 1, pageSize = 20): Promise<PaginatedResponse<ReconciliationRun>> => {
    return request<PaginatedResponse<ReconciliationRun>>(
      `reconciliation/runs?page=${page}&page_size=${pageSize}`
    );
  },

  getRunDetails: async (runId: string): Promise<ReconciliationRun> => {
    return request<ReconciliationRun>(`reconciliation/runs/${runId}`);
  },

  getRunResults: async (
    runId: string,
    page = 1,
    pageSize = 20
  ): Promise<PaginatedResponse<ReconciliationResultItem>> => {
    return request<PaginatedResponse<ReconciliationResultItem>>(
      `reconciliation/runs/${runId}/results?page=${page}&page_size=${pageSize}`
    );
  },
};

export const transactionService = {
  listTransactions: async (
    page = 1,
    pageSize = 20,
    search?: string
  ): Promise<PaginatedResponse<TransactionSummary>> => {
    const searchParam = search ? `&search=${encodeURIComponent(search)}` : '';
    return request<PaginatedResponse<TransactionSummary>>(
      `transactions?page=${page}&page_size=${pageSize}${searchParam}`
    );
  },
};

export const exceptionService = {
  listExceptions: async (
    page = 1,
    pageSize = 20,
    search?: string
  ): Promise<PaginatedResponse<ExceptionSummary>> => {
    const searchParam = search ? `&search=${encodeURIComponent(search)}` : '';
    return request<PaginatedResponse<ExceptionSummary>>(
      `exceptions?page=${page}&page_size=${pageSize}${searchParam}`
    );
  },

  getExceptionDetails: async (
    exceptionId: string
  ): Promise<{ exception: ExceptionSummary; reconciliation_result: ReconciliationResultItem | null }> => {
    return request<{ exception: ExceptionSummary; reconciliation_result: ReconciliationResultItem | null }>(
      `exceptions/${exceptionId}`
    );
  },

  getExceptionEvidence: async (
    exceptionId: string
  ): Promise<ExceptionEvidenceResponse> => {
    return request<ExceptionEvidenceResponse>(`exceptions/${exceptionId}/evidence`);
  },

  getExceptionEvidenceSummary: async (
    exceptionId: string
  ): Promise<FinancialEvidenceSummary> => {
    return request<FinancialEvidenceSummary>(`exceptions/${exceptionId}/evidence/summary`);
  },

  startInvestigation: async (
    exceptionId: string,
    options?: { force_refresh?: boolean; notes?: string }
  ): Promise<InvestigationResponse> => {
    return request<InvestigationResponse>(`exceptions/${exceptionId}/investigations`, {
      method: 'POST',
      body: JSON.stringify(options || {}),
    });
  },

  getLatestInvestigation: async (
    exceptionId: string
  ): Promise<InvestigationResponse | null> => {
    try {
      return await request<InvestigationResponse>(`exceptions/${exceptionId}/investigations/latest`);
    } catch {
      return null;
    }
  },
};

export const ingestionService = {
  ingestDemoData: async (): Promise<IngestionSummary> => {
    return request<IngestionSummary>('ingestion/demo', {
      method: 'POST',
    });
  },
};

export const resolutionService = {
  getResolutionSummary: async (exceptionId: string): Promise<ResolutionSummaryResponse> => {
    return request<ResolutionSummaryResponse>(`exceptions/${exceptionId}/resolution`);
  },

  getResolutionHistory: async (exceptionId: string): Promise<ResolutionHistoryItem[]> => {
    return request<ResolutionHistoryItem[]>(`exceptions/${exceptionId}/resolution/history`);
  },

  createProposal: async (
    exceptionId: string,
    payload: CreateProposalPayload
  ): Promise<ProposalResponse> => {
    return request<ProposalResponse>(`exceptions/${exceptionId}/resolution/proposals`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  submitProposal: async (
    exceptionId: string,
    proposalId: string
  ): Promise<ProposalResponse> => {
    return request<ProposalResponse>(
      `exceptions/${exceptionId}/resolution/proposals/${proposalId}/submit`,
      {
        method: 'POST',
      }
    );
  },

  approveProposal: async (
    exceptionId: string,
    proposalId: string,
    payload: DecisionPayload
  ): Promise<ProposalResponse> => {
    return request<ProposalResponse>(
      `exceptions/${exceptionId}/resolution/proposals/${proposalId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },

  rejectProposal: async (
    exceptionId: string,
    proposalId: string,
    payload: DecisionPayload
  ): Promise<ProposalResponse> => {
    return request<ProposalResponse>(
      `exceptions/${exceptionId}/resolution/proposals/${proposalId}/reject`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  },

  resolveException: async (
    exceptionId: string,
    payload: ResolveExceptionPayload
  ): Promise<ResolutionSummaryResponse> => {
    return request<ResolutionSummaryResponse>(`exceptions/${exceptionId}/resolution/resolve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  reopenException: async (
    exceptionId: string,
    payload: ReopenExceptionPayload
  ): Promise<ResolutionSummaryResponse> => {
    return request<ResolutionSummaryResponse>(`exceptions/${exceptionId}/resolution/reopen`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
