import { request } from './api-client';
import { DemoScenariosResponse } from '@/types/api';

export const demoService = {
  getScenarios: async (): Promise<DemoScenariosResponse> => {
    return request<DemoScenariosResponse>('demo/scenarios');
  },
};
