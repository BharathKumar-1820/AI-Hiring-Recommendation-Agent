/**
 * CandidateCard.jsx — Candidate result card with dual scoring (Match + Interest).
 */

import { useState } from "react";
import ConversationPanel from "./ConversationPanel";

/* ── Score colour helpers ─────────────────────────────────────────────────── */

function scoreColor(score) {
  if (score >= 80) return { bar: "bg-emerald-500", text: "text-emerald-400", glow: "shadow-emerald-500/20" };
  if (score >= 65) return { bar: "bg-amber-400",   text: "text-amber-400",   glow: "shadow-amber-400/20"  };
  if (score >= 50) return { bar: "bg-orange-400",  text: "text-orange-400",  glow: "shadow-orange-400/20" };
  return              { bar: "bg-red-400",     text: "text-red-400",     glow: "shadow-red-400/20"    };
}

function scoreLabel(score) {
  if (score >= 80) return "Excellent";
  if (score >= 65) return "Strong";
  if (score >= 50) return "Moderate";
  return "Weak";
}

/* ── Badge component ──────────────────────────────────────────────────────── */

function SkillBadge({ skill, variant = "matched" }) {
  const styles =
    variant === "matched"
      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
      : "bg-red-500/10 text-red-400 border-red-500/20";

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border ${styles}`}>
      {variant === "matched" ? (
        <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
        </svg>
      ) : (
        <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      )}
      {skill}
    </span>
  );
}

/* ── Mini Score Pill ──────────────────────────────────────────────────────── */

function MiniScore({ label, value, colorClass }) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className={`text-lg font-extrabold tabular-nums ${colorClass}`}>
        {value}
      </span>
      <span className="text-[9px] font-medium text-text-muted uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}

/* ── Main Card ────────────────────────────────────────────────────────────── */

export default function CandidateCard({ candidate, rank, isTop }) {
  const [showConversation, setShowConversation] = useState(false);

  const { bar, text, glow } = scoreColor(candidate.final_score);
  const label = scoreLabel(candidate.final_score);

  // Determine if this is a pipeline result (has interest data) or legacy match
  const hasPipeline = candidate.interest_score !== undefined;

  return (
    <div
      id={`candidate-card-${candidate.id}`}
      className={`
        relative rounded-2xl border transition-all duration-300
        bg-surface-card hover:bg-surface-elevated
        ${isTop
          ? "border-brand-500/30 shadow-lg animate-pulse-glow"
          : "border-white/[0.06] shadow-md shadow-black/20 hover:border-white/10 hover:shadow-lg"
        }
      `}
      style={{ animationDelay: `${rank * 100}ms` }}
    >
      {/* Top-candidate ribbon */}
      {isTop && (
        <div className="absolute -top-px left-6 right-6 h-[2px] bg-gradient-to-r from-transparent via-brand-400 to-transparent rounded-full" />
      )}

      <div className="p-6 space-y-5">
        {/* ── Header row ──────────────────────────────────────────────────── */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4 min-w-0">
            {/* Avatar circle */}
            <div className={`
              shrink-0 w-12 h-12 rounded-full flex items-center justify-center
              text-base font-bold
              ${isTop
                ? "bg-gradient-to-br from-brand-500 to-brand-700 text-white"
                : "bg-surface-hover text-text-secondary"
              }
            `}>
              {candidate.name.split(" ").map(n => n[0]).join("")}
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-base font-semibold text-text-primary truncate">
                  {candidate.name}
                </h3>
                {isTop && (
                  <span className="shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-brand-500/15 text-brand-300 border border-brand-500/20">
                    Top Pick
                  </span>
                )}
              </div>
              <p className="text-sm text-text-muted truncate">
                {candidate.role} · {candidate.experience} yrs exp
              </p>
            </div>
          </div>

          {/* Score pills — dual display */}
          <div className="shrink-0 flex items-center gap-3">
            {hasPipeline && (
              <>
                <MiniScore
                  label="Match"
                  value={candidate.match_score}
                  colorClass={scoreColor(candidate.match_score).text}
                />
                <MiniScore
                  label="Interest"
                  value={candidate.interest_score}
                  colorClass={scoreColor(candidate.interest_score).text}
                />
                <div className="w-px h-10 bg-white/[0.06]" />
              </>
            )}
            <div className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl bg-surface-hover shadow-sm ${glow}`}>
              <span className={`text-2xl font-extrabold tabular-nums ${text}`}>
                {hasPipeline ? candidate.final_score : candidate.score}
              </span>
              <span className="text-[10px] font-medium text-text-muted uppercase tracking-wider">
                {hasPipeline ? "Final" : label}
              </span>
            </div>
          </div>
        </div>

        {/* ── Final score bar ─────────────────────────────────────────────── */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span>{hasPipeline ? "Final Score (60% Match + 40% Interest)" : "Composite Score"}</span>
            <span className="tabular-nums">{hasPipeline ? candidate.final_score : candidate.score}/100</span>
          </div>
          <div className="h-2 rounded-full bg-surface-hover overflow-hidden">
            <div
              className={`h-full rounded-full ${bar} animate-score-fill`}
              style={{ width: `${hasPipeline ? candidate.final_score : candidate.score}%` }}
            />
          </div>
          <div className="flex gap-4 text-[11px] text-text-muted">
            <span>Similarity: <span className="text-text-secondary font-medium">{(candidate.similarity_score * 100).toFixed(1)}%</span></span>
            <span>Skill overlap: <span className="text-text-secondary font-medium">{(candidate.skill_overlap_score * 100).toFixed(1)}%</span></span>
          </div>
        </div>

        {/* ── Skills ──────────────────────────────────────────────────────── */}
        {candidate.matched_skills.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-text-muted uppercase tracking-wider">
              Matched Skills
            </p>
            <div className="flex flex-wrap gap-1.5">
              {candidate.matched_skills.map((s) => (
                <SkillBadge key={s} skill={s} variant="matched" />
              ))}
            </div>
          </div>
        )}

        {candidate.missing_skills.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-text-muted uppercase tracking-wider">
              Missing Skills
            </p>
            <div className="flex flex-wrap gap-1.5">
              {candidate.missing_skills.map((s) => (
                <SkillBadge key={s} skill={s} variant="missing" />
              ))}
            </div>
          </div>
        )}

        {/* ── Explanation ─────────────────────────────────────────────────── */}
        <div className="pt-1 border-t border-white/[0.04]">
          <p className="text-sm leading-relaxed text-text-secondary">
            {hasPipeline ? candidate.match_reason : candidate.reason}
          </p>
        </div>

        {/* ── Conversation toggle ─────────────────────────────────────────── */}
        {hasPipeline && (
          <div>
            <button
              id={`conversation-toggle-${candidate.id}`}
              onClick={() => setShowConversation(!showConversation)}
              className="
                flex items-center gap-2 px-4 py-2.5 rounded-xl
                bg-surface-hover hover:bg-surface-elevated
                border border-white/[0.06] hover:border-white/10
                text-xs font-medium text-text-secondary hover:text-text-primary
                transition-all duration-200 cursor-pointer
              "
            >
              <svg
                className={`w-4 h-4 transition-transform duration-200 ${showConversation ? "rotate-180" : ""}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
              </svg>
              {showConversation ? "Hide Conversation" : "View Outreach Conversation"}
              <span className="ml-auto px-2 py-0.5 rounded-md text-[10px] font-bold bg-brand-500/10 text-brand-300">
                Interest: {candidate.interest_score}/100
              </span>
            </button>

            {showConversation && (
              <ConversationPanel
                conversation={candidate.conversation}
                interestBreakdown={candidate.interest_breakdown}
                outreachSummary={candidate.outreach_summary}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
