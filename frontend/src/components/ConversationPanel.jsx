/**
 * ConversationPanel.jsx — Chat-style display of the simulated outreach conversation.
 */

export default function ConversationPanel({ conversation, interestBreakdown, outreachSummary }) {
  if (!conversation || conversation.length === 0) return null;

  const dims = [
    { label: "Enthusiasm",     value: interestBreakdown.enthusiasm,     color: "bg-violet-500" },
    { label: "Availability",   value: interestBreakdown.availability,   color: "bg-sky-500" },
    { label: "Role Alignment", value: interestBreakdown.role_alignment, color: "bg-amber-400" },
    { label: "Engagement",     value: interestBreakdown.engagement,     color: "bg-emerald-500" },
  ];

  return (
    <div className="mt-4 space-y-4 animate-fade-up">
      {/* ── Summary banner ──────────────────────────────────────────────── */}
      <div className="px-4 py-3 rounded-lg bg-brand-500/5 border border-brand-500/10">
        <p className="text-xs text-text-secondary leading-relaxed">
          <span className="font-medium text-brand-300">Agent Summary: </span>
          {outreachSummary}
        </p>
      </div>

      {/* ── Chat messages ───────────────────────────────────────────────── */}
      <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
        {conversation.map((msg, idx) => {
          const isAgent = msg.role === "agent";
          return (
            <div
              key={idx}
              className={`flex ${isAgent ? "justify-start" : "justify-end"}`}
            >
              <div
                className={`
                  max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed
                  ${isAgent
                    ? "bg-brand-500/10 border border-brand-500/15 text-text-primary rounded-bl-md"
                    : "bg-surface-hover border border-white/[0.06] text-text-secondary rounded-br-md"
                  }
                `}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider ${
                      isAgent ? "text-brand-400" : "text-text-muted"
                    }`}
                  >
                    {isAgent ? "🤖 AI Recruiter" : "👤 Candidate"}
                  </span>
                  <span className="text-[10px] text-text-muted/60">
                    {new Date(msg.timestamp).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
                <p>{msg.content}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Interest breakdown bars ─────────────────────────────────────── */}
      <div className="pt-3 border-t border-white/[0.04] space-y-2.5">
        <p className="text-xs font-medium text-text-muted uppercase tracking-wider">
          Interest Breakdown
        </p>
        <div className="grid grid-cols-2 gap-x-6 gap-y-2.5">
          {dims.map((dim) => (
            <div key={dim.label} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-text-muted">{dim.label}</span>
                <span className="text-text-secondary font-medium tabular-nums">
                  {dim.value}/100
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-surface-hover overflow-hidden">
                <div
                  className={`h-full rounded-full ${dim.color} animate-score-fill`}
                  style={{ width: `${dim.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
