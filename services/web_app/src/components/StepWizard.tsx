import { Award, FileText, User, Wallet } from 'lucide-react';
import React from 'react';
import { useTranslation } from 'react-i18next';

interface StepWizardProps {
  currentStep: number;
  onStepClick: (step: number) => void;
}

export const StepWizard: React.FC<StepWizardProps> = ({ currentStep, onStepClick }) => {
  const { t } = useTranslation();

  const steps = [
    { number: 1, title: t('loanApplication.steps.demographics'), icon: User },
    { number: 2, title: t('loanApplication.steps.financial'), icon: Wallet },
    { number: 3, title: t('loanApplication.steps.intent'), icon: FileText },
    { number: 4, title: t('loanApplication.steps.result'), icon: Award },
  ];

  return (
    <div className="wizard-steps">
      {steps.map((step) => {
        const Icon = step.icon;
        const isActive = currentStep === step.number;
        const isCompleted = currentStep > step.number;

        return (
          <div
            key={step.number}
            className={`step-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
            onClick={() => isCompleted && onStepClick(step.number)}
          >
            <div className="step-number">
              <Icon size={18} />
            </div>
            <span className="step-title">{step.title}</span>
          </div>
        );
      })}
    </div>
  );
};
