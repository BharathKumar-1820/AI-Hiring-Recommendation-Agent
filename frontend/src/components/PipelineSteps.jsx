/**
 * PipelineSteps.jsx — Horizontal step indicator for the 4 pipeline stages.
 */

const STEPS = [
  { id: 1, label: "Parse JD",         icon: "📝" },
  { id: 2, label: "Match Candidates",  icon: "🔍" },
  { id: 3, label: "Engage & Assess",   icon: "💬" },
  { id: 4, label: "Rank & Output",     icon: "🏆" },
];

export default function PipelineSteps({ currentStep = 0, isComplete = false }) {
  return (
    <div id="pipeline-steps" className="w-full animate-fade-up">
      <div className="flex items-center justify-between gap-1 sm:gap-2">
        {STEPS.map((step, idx) => {
          const isActive = !isComplete && currentStep === step.id;
          const isDone = isComplete || currentStep > step.id;

          return (
            <div key={step.id} className="flex items-center flex-1 last:flex-none">
              {/* Step circle + label */}
              <div className="flex flex-col items-center gap-1.5 min-w-0">
                <div
                  className={`
                    relative w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center
                    text-base sm:text-lg transition-all duration-500
                    ${isDone
                      ? "bg-emerald-500/15 border-2 border-emerald-500/40"
                      : isActive
                        ? "bg-brand-500/15 border-2 border-brand-400/60 animate-pulse"
                        : "bg-surface-hover border-2 border-white/[0.06]"
                    }
                  `}
                >
                  {isDone ? (
                    <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  ) : (
                    <span>{step.icon}</span>
                  )}
                </div>
                <span
                  className={`text-[10px] sm:text-xs font-medium text-center leading-tight transition-colors ${
                    isDone
                      ? "text-emerald-400"
                      : isActive
                        ? "text-brand-300"
                        : "text-text-muted"
                  }`}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector line (not after last step) */}
              {idx < STEPS.length - 1 && (
                <div className="flex-1 mx-1 sm:mx-2 mt-[-18px]">
                  <div className="h-0.5 rounded-full bg-surface-hover overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        isDone ? "bg-emerald-500/50 w-full" : "w-0"
                      }`}
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
