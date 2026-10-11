import { useContext } from 'react';
import { DemoContext, DemoContextType } from '@/app/providers/demo-context-definition';

export function useDemo(): DemoContextType {
  const context = useContext(DemoContext);
  if (!context) {
    throw new Error('useDemo must be used within a DemoProvider');
  }
  return context;
}
