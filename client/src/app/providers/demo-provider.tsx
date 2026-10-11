import React, { useState, useEffect } from 'react';
import {
  DemoContext,
  WALKTHROUGH_STEPS,
} from './demo-context-definition';

const DEMO_MODE_STORAGE_KEY = 'reconpilot_demo_mode_enabled';
const WALKTHROUGH_STORAGE_KEY = 'reconpilot_walkthrough_active';
const WALKTHROUGH_STEP_KEY = 'reconpilot_walkthrough_step';

export const DemoProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isDemoMode, setIsDemoMode] = useState<boolean>(() => {
    const saved = localStorage.getItem(DEMO_MODE_STORAGE_KEY);
    return saved !== null ? saved === 'true' : true; // Enabled by default for judge experience
  });

  const [isWalkthroughActive, setIsWalkthroughActive] = useState<boolean>(() => {
    return localStorage.getItem(WALKTHROUGH_STORAGE_KEY) === 'true';
  });

  const [currentStepIndex, setCurrentStepIndex] = useState<number>(() => {
    const saved = localStorage.getItem(WALKTHROUGH_STEP_KEY);
    return saved ? parseInt(saved, 10) : 0;
  });

  const [selectedScenarioExceptionId, setSelectedScenarioExceptionId] = useState<string | null>(null);

  useEffect(() => {
    localStorage.setItem(DEMO_MODE_STORAGE_KEY, String(isDemoMode));
  }, [isDemoMode]);

  useEffect(() => {
    localStorage.setItem(WALKTHROUGH_STORAGE_KEY, String(isWalkthroughActive));
  }, [isWalkthroughActive]);

  useEffect(() => {
    localStorage.setItem(WALKTHROUGH_STEP_KEY, String(currentStepIndex));
  }, [currentStepIndex]);

  const toggleDemoMode = () => {
    setIsDemoMode((prev) => !prev);
  };

  const startWalkthrough = () => {
    setIsWalkthroughActive(true);
    setCurrentStepIndex(0);
  };

  const stopWalkthrough = () => {
    setIsWalkthroughActive(false);
  };

  const nextStep = () => {
    if (currentStepIndex < WALKTHROUGH_STEPS.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    } else {
      stopWalkthrough();
    }
  };

  const prevStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const goToStep = (index: number) => {
    if (index >= 0 && index < WALKTHROUGH_STEPS.length) {
      setCurrentStepIndex(index);
    }
  };

  const currentStep = isWalkthroughActive ? WALKTHROUGH_STEPS[currentStepIndex] || null : null;

  return (
    <DemoContext.Provider
      value={{
        isDemoMode,
        toggleDemoMode,
        isWalkthroughActive,
        currentStepIndex,
        startWalkthrough,
        stopWalkthrough,
        nextStep,
        prevStep,
        goToStep,
        currentStep,
        selectedScenarioExceptionId,
        setSelectedScenarioExceptionId,
      }}
    >
      {children}
    </DemoContext.Provider>
  );
};
