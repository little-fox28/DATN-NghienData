import React from 'react';
import { User, Wallet, FileText, Award } from 'lucide-react';

interface StepWizardProps {
  currentStep: number;
  onStepClick: (step: number) => void;
}

export const StepWizard: React.FC<StepWizardProps> = ({ currentStep, onStepClick }) => {
  const steps = [
    { number: 1, title: 'Nhân khẩu học', icon: User },
    { number: 2, title: 'Tài chính & Việc làm', icon: Wallet },
    { number: 3, title: 'Nhu cầu Khoản vay', icon: FileText },
    { number: 4, title: 'Kết quả Chấm điểm AI', icon: Award },
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
