/**
 * ResultsList.jsx — Renders the ranked list of candidate cards with summary stats.
 */

import CandidateCard from "./CandidateCard";

export default function ResultsList({ data }) {
  if (!data) return null;

  const { results, total_candidates_evaluated } = data;

  // Determine if pipeline (has final_score) or legacy match
  const isPipeline = results.length > 0 && results[0].final_score !== undefined;

  // Sort by final_score (pipeline) or score (legacy)
  const sorted = [...results].sort((a, b) =>
    isPipeline
      ? b.final_score - a.final_score
      : b.score - a.score
  );

  // Stats
  const bestFinal = sorted.length > 0
    ? (isPipeline ? sorted[0].final_score : sorted[0].score)
    : 0;

  const avgMatch = sorted.length > 0
    ? Math.round(
        sorted.reduce((s, c) => s + (isPipeline ? c.match_score : c.score), 0) / sorted.length
      )
    : 0;

  const avgInterest = isPipeline && sorted.length > 0
    ? Math.round(sorted.reduce((s, c) => s + c.interest_score, 0) / sorted.length)
    : null;

  return (
    <section id="results-section" className="w-full space-y-6">
      {/* ── Summary header ──────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fade-up">
        <div>
          <h2 className="text-lg font-semibold text-text-primary">
            {isPipeline ? "Talent Shortlist" : "Top Matches"}
          </h2>
          <p className="text-sm text-text-muted">
            Showing {sorted.length} of {total_candidates_evaluated} candidates evaluated
            {isPipeline && " · Ranked by Final Score (Match + Interest)"}
          </p>
        </div>

        {/* Quick stats pills */}
        <div className="flex items-center gap-2 flex-wrap">
          {sorted.length > 0 && (
            <>
              <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
                Best: {bestFinal}/100
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-brand-500/10 border border-brand-500/20 text-brand-300 text-xs font-medium">
                Avg Match: {avgMatch}
              </span>
              {avgInterest !== null && (
                <span className="px-3 py-1.5 rounded-lg bg-violet-500/10 border border-violet-500/20 text-violet-300 text-xs font-medium">
                  Avg Interest: {avgInterest}
                </span>
              )}
            </>
          )}
        </div>
      </div>

      {/* ── Cards list ──────────────────────────────────────────────────── */}
      <div className="grid gap-5">
        {sorted.map((candidate, idx) => (
          <div
            key={candidate.id}
            className="animate-fade-up"
            style={{ animationDelay: `${(idx + 1) * 80}ms` }}
          >
            <CandidateCard
              candidate={candidate}
              rank={idx}
              isTop={idx === 0}
            />
          </div>
        ))}
      </div>

      {/* ── Empty state ─────────────────────────────────────────────────── */}
      {sorted.length === 0 && (
        <div className="text-center py-16">
          <p className="text-text-muted text-sm">
            No matching candidates found. Try a different job description.
          </p>
        </div>
      )}
    </section>
  );
}
