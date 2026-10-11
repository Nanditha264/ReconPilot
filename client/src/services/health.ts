import { request } from './api-client';
import { HealthLivenessData, HealthReadinessData } from '@/types/api';

export const healthApi = {
  getLiveness: (): Promise<HealthLivenessData> => {
    return request<HealthLivenessData>('/health');
  },

  getReadiness: (): Promise<HealthReadinessData> => {
    return request<HealthReadinessData>('/health/ready');
  },
};
