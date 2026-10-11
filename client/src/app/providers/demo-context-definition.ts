import { createContext } from 'react';

export interface WalkthroughStep {
  id: number;
  title: string;
  route: string;
  description: string;
  objective: string;
  tip: string;
}

export const WALKTHROUGH_STEPS: WalkthroughStep[] = [
  {
    id: 1,
    title: '1. Reconciliation Health & Ingestion',
    route: '/dashboard',
    description: 'Monitor multi-source financial ingestion, match ratios, and high-level health distributions across payments and settlement batches.',
    objective: 'Demonstrate deterministic financial matching, batch processing, and live data health.',
    tip: 'Observe that currency exposure is strictly separated (INR vs USD). No currency cross-addition is performed.',
  },
  {
    id: 2,
    title: '2. Financial Discrepancies & Scenarios',
    route: '/exceptions',
    description: 'Inspect live reconciliation exceptions categorized by deterministic discrepancy rules (e.g., amount mismatch, fee drift, missing settlement).',
    objective: 'Demonstrate deterministic exception detection with real expected vs actual settlement calculations.',
    tip: 'Use the Demo Scenario Selector to jump directly into a representative verified scenario.',
  },
  {
    id: 3,
    title: '3. Evidence Dossier & Provenance',
    route: '/exceptions',
    description: 'Inspect the correlated evidence dossier containing gateway payment records, processor settlement items, fee schedules, and conflict detection.',
    objective: 'Show how ReconPilot grounds financial investigations in verifiable database audit trails.',
    tip: 'Notice evidence strength ratings (Confirmed, Corroborated, Conflicting) derived from source data.',
  },
  {
    id: 4,
    title: '4. AI Root Cause Investigation',
    route: '/exceptions',
    description: 'Review schema-constrained AI root-cause diagnostics, evaluating hypotheses, citing verified evidence IDs, and acknowledging limitations.',
    objective: 'Demonstrate how assistive AI diagnoses complex variances without performing financial mutations.',
    tip: 'Review the provider badge (Live Gemini vs Mock) and policy safeguards requiring human review.',
  },
  {
    id: 5,
    title: '5. Human Approval & Dual-Control Governance',
    route: '/exceptions',
    description: 'Demonstrate proposal submission, reviewer separation of duties (proposer cannot approve), and immutable audit history.',
    objective: 'Highlight enterprise governance: human approval records decisions without modifying financial source ledgers.',
    tip: 'Notice the lock badge when a user attempts to approve their own proposed resolution.',
  },
  {
    id: 6,
    title: '6. Command Center & Operations Queue',
    route: '/dashboard',
    description: 'Return to the Finance Operations Command Center to review executive KPIs, 14-day trends, and pending approvals.',
    objective: 'Show how finance leads maintain end-to-end operational visibility over multi-currency exceptions.',
    tip: 'Observe how the operations queue reflects real-time resolution status and age metrics.',
  },
];

export interface DemoContextType {
  isDemoMode: boolean;
  toggleDemoMode: () => void;
  isWalkthroughActive: boolean;
  currentStepIndex: number;
  startWalkthrough: () => void;
  stopWalkthrough: () => void;
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (index: number) => void;
  currentStep: WalkthroughStep | null;
  selectedScenarioExceptionId: string | null;
  setSelectedScenarioExceptionId: (id: string | null) => void;
}

export const DemoContext = createContext<DemoContextType | undefined>(undefined);
