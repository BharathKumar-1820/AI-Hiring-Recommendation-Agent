/**
 * JobInput.jsx — Job description textarea + submit button.
 */

import { useState } from "react";

const PLACEHOLDER = `e.g. We are hiring a Senior ML Engineer with expertise in Python, PyTorch, NLP and transformer models. The candidate should have experience deploying models to production with Docker and Kubernetes, and be comfortable working with large datasets using Pandas and SQL.`;

export default function JobInput({ onSubmit, isLoading }) {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || trimmed.length < 20) return;
    onSubmit(trimmed);
  };

  const charCount = text.trim().length;
  const isValid = charCount >= 20;

  return (
    <form
      id="job-input-form"
      onSubmit={handleSubmit}
      className="w-full space-y-4"
    >
      {/* Label row */}
      <div className="flex items-end justify-between">
        <label
          htmlFor="job-description"
          className="text-sm font-medium text-text-secondary"
        >
          Job Description
        </label>
        <span
          className={`text-xs tabular-nums transition-colors ${
            charCount > 0 && !isValid ? "text-danger" : "text-text-muted"
          }`}
        >
          {charCount > 0 && `${charCount} chars`}
          {charCount > 0 && !isValid && " (min 20)"}
        </span>
      </div>

      {/* Textarea */}
      <div className="relative group">
        <textarea
          id="job-description"
          rows={6}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={PLACEHOLDER}
          disabled={isLoading}
          className="
            w-full rounded-xl bg-surface-card border border-white/[0.06]
            px-5 py-4 text-sm leading-relaxed text-text-primary
            placeholder:text-text-muted/60
            resize-y min-h-[140px] max-h-[400px]
            transition-all duration-200
            focus:outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/30
            hover:border-white/10
            disabled:opacity-50 disabled:cursor-not-allowed
          "
        />
        {/* Subtle glow on focus */}
        <div className="
          absolute -inset-px rounded-xl opacity-0 group-focus-within:opacity-100
          bg-gradient-to-r from-brand-500/10 via-transparent to-brand-500/10
          pointer-events-none transition-opacity duration-300 -z-10 blur-sm
        " />
      </div>

      {/* Submit button */}
      <button
        id="submit-button"
        type="submit"
        disabled={!isValid || isLoading}
        className="
          relative w-full sm:w-auto px-8 py-3 rounded-xl
          bg-gradient-to-r from-brand-600 to-brand-500
          text-white text-sm font-semibold tracking-wide
          shadow-lg shadow-brand-600/20
          transition-all duration-200
          hover:shadow-xl hover:shadow-brand-600/30 hover:brightness-110
          active:scale-[0.98]
          disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:shadow-lg disabled:hover:brightness-100
          cursor-pointer
        "
      >
        {/* Shimmer overlay */}
        {!isLoading && isValid && (
          <span className="absolute inset-0 rounded-xl overflow-hidden">
            <span className="absolute inset-0 animate-shimmer" />
          </span>
        )}

        <span className="relative flex items-center justify-center gap-2">
          {isLoading ? (
            <>
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Processing…
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              Find Candidates
            </>
          )}
        </span>
      </button>
    </form>
  );
}
