import { Check, Clock } from 'lucide-react';
import { cn } from '../../lib/utils';

export const StatusTracker = ({ currentStep = 1 }) => {
  const steps = [
    { id: 1, name: 'Submitted', description: 'Resume received' },
    { id: 2, name: 'Screening', description: 'AI profile evaluation' },
    { id: 3, name: 'Interview', description: 'Technical & HR rounds' },
    { id: 4, name: 'Offer', description: 'Final negotiation' },
    { id: 5, name: 'Hired', description: 'Welcome to the team!' },
  ];

  return (
    <div className="w-full py-6">
      <nav aria-label="Progress">
        <ol role="list" className="overflow-hidden">
          {steps.map((step, stepIdx) => (
            <li key={step.name} className={cn("relative", stepIdx !== steps.length - 1 ? "pb-10" : "")}>
              {stepIdx !== steps.length - 1 ? (
                <div
                  className="absolute left-4 top-4 -ml-px mt-0.5 h-full w-0.5 bg-gray-200"
                  aria-hidden="true"
                />
              ) : null}
              {stepIdx < currentStep - 1 ? (
                // Completed Step
                <div className="relative flex items-start group">
                  <span className="h-9 flex items-center">
                    <span className="relative z-10 w-8 h-8 flex items-center justify-center bg-blue-600 rounded-full">
                      <Check className="w-5 h-5 text-white" aria-hidden="true" />
                    </span>
                  </span>
                  <span className="ml-4 min-w-0 flex flex-col">
                    <span className="text-sm font-semibold tracking-wide text-blue-600 uppercase">
                      {step.name}
                    </span>
                    <span className="text-sm text-gray-500">{step.description}</span>
                  </span>
                </div>
              ) : stepIdx === currentStep - 1 ? (
                // Current Step
                <div className="relative flex items-start flex-1" aria-current="step">
                  <span className="h-9 flex items-center" aria-hidden="true">
                    <span className="relative z-10 w-8 h-8 flex items-center justify-center bg-white border-2 border-blue-600 rounded-full">
                      <span className="h-2.5 w-2.5 bg-blue-600 rounded-full" />
                    </span>
                  </span>
                  <span className="ml-4 min-w-0 flex flex-col">
                    <span className="text-sm font-semibold text-gray-900 uppercase">
                      {step.name}
                    </span>
                    <span className="text-sm text-gray-500">{step.description}</span>
                  </span>
                </div>
              ) : (
                // Upcoming Step
                <div className="relative flex items-start group">
                  <span className="h-9 flex items-center" aria-hidden="true">
                    <span className="relative z-10 w-8 h-8 flex items-center justify-center bg-white border-2 border-gray-300 rounded-full">
                      <Clock className="w-4 h-4 text-gray-400" />
                    </span>
                  </span>
                  <span className="ml-4 min-w-0 flex flex-col">
                    <span className="text-sm font-semibold text-gray-500 uppercase">
                      {step.name}
                    </span>
                    <span className="text-sm text-gray-400">{step.description}</span>
                  </span>
                </div>
              )}
            </li>
          ))}
        </ol>
      </nav>
    </div>
  );
};

export default StatusTracker;
