import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useDemo } from '@/hooks/use-demo';
import { WALKTHROUGH_STEPS } from '@/app/providers/demo-context-definition';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Compass,
  ArrowRight,
  ArrowLeft,
  X,
  CheckCircle2,
  ExternalLink,
  Lightbulb,
  Sparkles,
} from 'lucide-react';

export const WalkthroughModal: React.FC = () => {
  const {
    isWalkthroughActive,
    currentStepIndex,
    currentStep,
    nextStep,
    prevStep,
    stopWalkthrough,
    goToStep,
  } = useDemo();
  const navigate = useNavigate();

  if (!isWalkthroughActive || !currentStep) {
    return null;
  }

  const handleNavigateToRoute = () => {
    navigate(currentStep.route);
  };

  const isLastStep = currentStepIndex === WALKTHROUGH_STEPS.length - 1;

  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-lg w-full px-4 animate-in fade-in slide-in-from-bottom-5 duration-300">
      <Card className="bg-white border-2 border-brand-primary/40 shadow-2xl overflow-hidden rounded-xl">
        {/* Header bar */}
        <div className="bg-gradient-to-r from-brand-primary/10 via-finance-50 to-brand-primary/5 px-4 py-3 border-b border-finance-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-brand-primary text-white rounded-lg shadow-xs">
              <Compass className="w-4 h-4 animate-spin-slow" />
            </div>
            <div>
              <div className="text-xs font-bold text-finance-900 flex items-center gap-1.5">
                <span>Judge Walkthrough Guide</span>
                <Badge variant="info" size="sm" className="font-mono text-[10px] py-0">
                  Step {currentStepIndex + 1} of {WALKTHROUGH_STEPS.length}
                </Badge>
              </div>
              <p className="text-[11px] text-finance-500 font-medium">
                End-to-end guided financial workflow
              </p>
            </div>
          </div>

          <button
            onClick={stopWalkthrough}
            className="p-1 text-finance-400 hover:text-finance-700 rounded hover:bg-finance-100 transition-colors"
            title="Dismiss Walkthrough"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content body */}
        <div className="p-4 space-y-3">
          <div>
            <h4 className="text-sm font-bold text-finance-900 flex items-center gap-1.5">
              <span>{currentStep.title}</span>
            </h4>
            <p className="text-xs text-finance-600 mt-1 leading-relaxed">
              {currentStep.description}
            </p>
          </div>

          <div className="p-2.5 rounded-lg bg-finance-50 border border-finance-200 text-xs space-y-1.5">
            <div className="font-semibold text-finance-800 flex items-center gap-1.5 text-[11px] uppercase tracking-wide">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Evaluation Objective
            </div>
            <p className="text-finance-700 text-xs pl-5">
              {currentStep.objective}
            </p>
          </div>

          <div className="p-2.5 rounded-lg bg-amber-50/80 border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
            <Lightbulb className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-[11px] leading-relaxed">
              <span className="font-semibold">Presenter Tip: </span>
              {currentStep.tip}
            </div>
          </div>

          {/* Quick jump step dots */}
          <div className="flex items-center justify-center gap-1.5 pt-1">
            {WALKTHROUGH_STEPS.map((step, idx) => (
              <button
                key={step.id}
                onClick={() => goToStep(idx)}
                className={`w-2.5 h-2.5 rounded-full transition-all ${
                  idx === currentStepIndex
                    ? 'bg-brand-primary scale-125'
                    : idx < currentStepIndex
                    ? 'bg-emerald-500'
                    : 'bg-finance-200 hover:bg-finance-300'
                }`}
                title={step.title}
              />
            ))}
          </div>
        </div>

        {/* Footer controls */}
        <div className="px-4 py-3 bg-finance-50 border-t border-finance-200 flex items-center justify-between gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleNavigateToRoute}
            className="text-xs gap-1 py-1 h-8"
          >
            <span>Open Feature</span>
            <ExternalLink className="w-3 h-3 text-finance-400" />
          </Button>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={prevStep}
              disabled={currentStepIndex === 0}
              className="text-xs gap-1 py-1 h-8"
            >
              <ArrowLeft className="w-3 h-3" />
              <span>Back</span>
            </Button>

            <Button
              size="sm"
              variant="primary"
              onClick={nextStep}
              className="text-xs gap-1 py-1 h-8 bg-brand-primary text-white"
            >
              <span>{isLastStep ? 'Finish Tour' : 'Next Step'}</span>
              {!isLastStep ? <ArrowRight className="w-3 h-3" /> : <Sparkles className="w-3 h-3" />}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};
