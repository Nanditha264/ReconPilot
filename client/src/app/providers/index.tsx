import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '../query-client';
import { AuthProvider } from './auth-provider';
import { DemoProvider } from './demo-provider';

interface AppProvidersProps {
  children: React.ReactNode;
}

export const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <DemoProvider>{children}</DemoProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};
