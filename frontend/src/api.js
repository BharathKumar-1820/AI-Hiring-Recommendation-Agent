import axios from "axios";

const API_BASE = import.meta.env.VITE_API_HOST 
  ? `https://${import.meta.env.VITE_API_HOST}` 
  : (import.meta.env.VITE_API_URL || "http://localhost:8000");

const client = axios.create({
  baseURL: API_BASE,
  timeout: 60_000, // pipeline can take longer with outreach simulation
  headers: { "Content-Type": "application/json" },
});

/**
 * POST /pipeline — full talent scouting pipeline (match + engage + rank).
 * @param {string} jobDescription
 * @returns {Promise<import("axios").AxiosResponse>}
 */
export async function runPipeline(jobDescription) {
  return client.post("/pipeline", { job_description: jobDescription });
}

/**
 * POST /match — match-only (backward compatible).
 * @param {string} jobDescription
 * @returns {Promise<import("axios").AxiosResponse>}
 */
export async function matchCandidates(jobDescription) {
  return client.post("/match", { job_description: jobDescription });
}

/**
 * GET /health — liveness probe.
 */
export async function healthCheck() {
  return client.get("/health");
}
