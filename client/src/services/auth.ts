import { request } from './api-client';
import { CurrentUserResponseData, LoginResponseData } from '@/types/api';

export interface LoginPayload {
  email: string;
  password: string;
}

export const authService = {
  login: async (credentials: LoginPayload): Promise<LoginResponseData> => {
    return request<LoginResponseData>('auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  getCurrentUser: async (): Promise<CurrentUserResponseData> => {
    return request<CurrentUserResponseData>('auth/me', {
      method: 'GET',
    });
  },

  logout: async (): Promise<{ message: string }> => {
    return request<{ message: string }>('auth/logout', {
      method: 'POST',
    });
  },
};
