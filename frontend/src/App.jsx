/**
 * App.jsx — Root application component.
 *
 * Orchestrates the full talent scouting pipeline:
 * JD input → pipeline stages → results with dual scoring + conversations.
 */

import { useState, useEffect, useRef } from "react";
import JobInput from "./components/JobInput";
import Loader from "./components/Loader";
import PipelineSteps from "./components/PipelineSteps";
import ResultsList from "./components/ResultsList";
import { runPipeline } from "./api";

export default function App() {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pipelineStage, setPipelineStage] = useState(0);
  const resultsRef = useRef(null);

  const handleSubmit = async (jobDescription) => {
    setIsLoading(true);
    setError(null);
    setResults(null);
    setPipelineStage(1);

    // Simulate stage progression for UX feedback
    const stageTimers = [];
    stageTimers.push(setTimeout(() => setPipelineStage(2), 800));
    stageTimers.push(setTimeout(() => setPipelineStage(3), 2000));
    stageTimers.push(setTimeout(() => setPipelineStage(4), 3500));

    try {
      const res = await runPipeline(jobDescription);
      // Clear timers and jump to complete
      stageTimers.forEach(clearTimeout);
      setPipelineStage(5); // all complete
      setResults(res.data);
    } catch (err) {
      stageTimers.forEach(clearTimeout);
      setPipelineStage(0);
      const message =
        err.response?.data?.detail ||
        err.message ||
        "Something went wrong. Please try again.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-scroll to results when they appear
  useEffect(() => {
    if (results && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 300);
    }
  }, [results]);

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header className="w-full border-b border-white/[0.04] bg-surface/60 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-4xl mx-auto px-5 py-4 flex items-center gap-3">
          {/* Logo mark */}
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-600/20">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-text-primary">
              AI Talent Scout
            </h1>
            <p className="text-[11px] text-text-muted leading-none">
              Discover · Engage · Rank
            </p>
          </div>
        </div>
      </header>

      {/* ── Main content ────────────────────────────────────────────────── */}
      <main className="flex-1 w-full max-w-4xl mx-auto px-5 py-10 space-y-10">
        {/* Hero section */}
        <section className="text-center space-y-3 animate-fade-up">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Scout, engage &{" "}
            <span className="bg-gradient-to-r from-brand-400 to-brand-300 bg-clip-text text-transparent">
              rank talent
            </span>
          </h2>
          <p className="text-text-muted text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
            Paste a job description and our AI agent will discover matching candidates,
            simulate outreach conversations to gauge interest, and deliver a ranked shortlist
            scored on <span className="text-text-secondary font-medium">Match</span> and{" "}
            <span className="text-text-secondary font-medium">Interest</span>.
          </p>
        </section>

        {/* Job input */}
        <section
          className="animate-fade-up"
          style={{ animationDelay: "100ms" }}
        >
          <JobInput onSubmit={handleSubmit} isLoading={isLoading} />
        </section>

        {/* Pipeline steps — show during loading or after results */}
        {(pipelineStage > 0) && (
          <PipelineSteps
            currentStep={pipelineStage}
            isComplete={pipelineStage >= 5}
          />
        )}

        {/* Loading */}
        {isLoading && <Loader stage={pipelineStage} />}

        {/* Error */}
        {error && (
          <div
            id="error-message"
            className="animate-fade-up rounded-xl border border-red-500/20 bg-red-500/5 px-5 py-4 flex items-start gap-3"
          >
            <svg className="w-5 h-5 text-red-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-red-400">Pipeline failed</p>
              <p className="text-sm text-red-400/70 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        <div ref={resultsRef}>
          {results && <ResultsList data={results} />}
        </div>
      </main>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="w-full border-t border-white/[0.04] mt-auto">
        <div className="max-w-4xl mx-auto px-5 py-5 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-text-muted">
          <span>AI Talent Scout v2.0</span>
          <span>
            Powered by{" "}
            <span className="text-text-secondary font-medium">
              sentence-transformers
            </span>{" "}
            +{" "}
            <span className="text-text-secondary font-medium">FAISS</span>
            {" "} + {" "}
            <span className="text-text-secondary font-medium">Outreach Simulation</span>
          </span>
        </div>
      </footer>
    </div>
  );
}
