/**
 * Loader.jsx — Stage-aware animated loading spinner.
 */

const STAGE_MESSAGES = {
  1: { title: "Parsing job description…", subtitle: "Extracting skills and requirements" },
  2: { title: "Searching candidate pool…", subtitle: "Encoding JD & running FAISS similarity search" },
  3: { title: "Engaging top candidates…", subtitle: "Simulating outreach conversations" },
  4: { title: "Computing final rankings…", subtitle: "Blending Match Score + Interest Score" },
};

const DEFAULT_MSG = { title: "Analyzing candidates…", subtitle: "Processing your request" };

export default function Loader({ stage = 0 }) {
  const msg = STAGE_MESSAGES[stage] || DEFAULT_MSG;

  return (
    <div id="loader-container" className="flex flex-col items-center justify-center py-16 gap-6">
      {/* Outer ring */}
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-2 border-brand-500/20" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-brand-400 animate-spin" />
        {/* Inner dot */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-brand-400 animate-pulse" />
        </div>
      </div>

      <div className="text-center space-y-1.5">
        <p className="text-text-primary font-medium text-sm tracking-wide">
          {msg.title}
        </p>
        <p className="text-text-muted text-xs">
          {msg.subtitle}
        </p>
      </div>
    </div>
  );
}
