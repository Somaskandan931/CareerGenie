import React, { useEffect, useState, useCallback, useRef } from "react";
import API_BASE_URL from '../config';

const Ico = ({ d, className = "w-4 h-4" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const I = {
  brief:   "M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
  ext:     "M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14",
  check:   "M5 13l4 4L19 7",
  alert:   "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  thumb_u: "M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5",
  thumb_d: "M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5",
  save:    "M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z",
  search:  "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
  refresh: "M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15",
};

// ── Fixed feedback endpoints (use /progress/ prefix) ────────────────────────
const recordFeedback = async (userId, signalType, itemId, metadata = {}) => {
  if (!userId) return;
  try {
    await fetch(`${API_BASE_URL}/progress/feedback/record`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, signal_type: signalType, item_id: itemId, metadata }),
    });
  } catch (_) {}
};

const recordPreference = async (userId, winner, loser) => {
  if (!userId || !winner || !loser) return;
  try {
    await fetch(`${API_BASE_URL}/progress/ranking/preference`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, winner, loser, context: {} }),
    });
  } catch (_) {}
};

const ScoreArc = ({ score }) => {
  const color = score >= 80 ? "#10b981" : score >= 65 ? "#f59e0b" : score >= 50 ? "#f97316" : "#ef4444";
  const label = score >= 80 ? "Excellent" : score >= 65 ? "Good" : score >= 50 ? "Fair" : "Low";
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-16 h-16">
        <svg viewBox="0 0 56 56" className="w-full h-full -rotate-90">
          <circle cx="28" cy="28" r="22" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="5" />
          <circle cx="28" cy="28" r="22" fill="none" stroke={color} strokeWidth="5"
            strokeDasharray={`${(score / 100) * 138} 138`} strokeLinecap="round"
            style={{ transition: "stroke-dasharray 0.8s ease" }} />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-black" style={{ color }}>{score}%</span>
        </div>
      </div>
      <span className="text-xs font-medium" style={{ color }}>{label}</span>
    </div>
  );
};

const JobCard = ({ job, index, userId, allJobs, onSignal }) => {
  const [signal, setSignal]       = useState(null);
  const [applyDone, setApplyDone] = useState(false);

  const displayScore = job.personalised && job.ltr_score != null
    ? Math.round(job.ltr_score * 100)
    : Math.round(job.match_score || 0);

  const handleApply = () => {
    if (!applyDone) {
      setApplyDone(true);
      recordFeedback(userId, "apply_click", job.job_id || `job_${index}`, { role: job.title, company: job.company });
      const loser = allJobs[index + 1];
      if (loser) recordPreference(userId, job, loser);
      if (onSignal) onSignal(job, "apply_click");
    }
  };

  const handleRate = (type) => {
    if (signal) return;
    setSignal(type);
    const sig = type === "up" ? "rate_match_up" : "rate_match_down";
    recordFeedback(userId, sig, job.job_id || `job_${index}`, { role: job.title, company: job.company });
    if (type === "up" && allJobs[index + 1]) recordPreference(userId, job, allJobs[index + 1]);
    if (type === "down" && index > 0)         recordPreference(userId, allJobs[index - 1], job);
    if (onSignal) onSignal(job, sig);
  };

  const handleSave = () => {
    if (signal === "save") return;
    setSignal("save");
    recordFeedback(userId, "save_job", job.job_id || `job_${index}`, { role: job.title, company: job.company });
    if (onSignal) onSignal(job, "save_job");
  };

  return (
    <div className="rounded-2xl border border-white/8 p-5 hover:border-violet-500/30 transition-all group"
      style={{ background: "rgba(255,255,255,0.03)" }}>
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h3 className="text-base font-semibold text-white truncate">{job.title}</h3>
            {job.personalised && (
              <span className="text-xs bg-violet-500/15 border border-violet-500/20 text-violet-400 px-2 py-0.5 rounded-full font-medium">
                ✦ Personalised
              </span>
            )}
          </div>
          <p className="text-sm text-slate-300 font-medium mb-1">{job.company}</p>
          <p className="text-xs text-slate-500">📍 {job.location}</p>
        </div>
        <div className="flex-shrink-0">
          <ScoreArc score={displayScore} />
        </div>
      </div>

      {job.explanation && (
        <div className="mb-4 px-4 py-3 rounded-xl border border-violet-500/10"
          style={{ background: "rgba(124,58,237,0.06)" }}>
          <p className="text-xs text-slate-300 leading-relaxed">{job.explanation}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
        {job.matched_skills?.length > 0 && (
          <div>
            <p className="text-xs font-medium text-emerald-400 mb-2 flex items-center gap-1">
              <Ico d={I.check} className="w-3.5 h-3.5" /> Matched ({job.matched_skills.length})
            </p>
            <div className="flex flex-wrap gap-1.5">
              {job.matched_skills.slice(0, 6).map((s, i) => (
                <span key={i} className="text-xs bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded-full">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
        {job.missing_skills?.length > 0 && (
          <div>
            <p className="text-xs font-medium text-amber-400 mb-2 flex items-center gap-1">
              <Ico d={I.alert} className="w-3.5 h-3.5" /> To develop ({job.missing_skills.length})
            </p>
            <div className="flex flex-wrap gap-1.5">
              {job.missing_skills.slice(0, 4).map((s, i) => (
                <span key={i} className="text-xs bg-amber-500/10 border border-amber-500/20 text-amber-300 px-2.5 py-1 rounded-full">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {job.recommendation && (
        <p className="text-xs text-slate-400 italic mb-3 pl-3 border-l border-white/10">{job.recommendation}</p>
      )}

      <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-white/5">
        {job.apply_link ? (
          <a href={job.apply_link} target="_blank" rel="noopener noreferrer" onClick={handleApply}
            className="flex items-center gap-1.5 bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold px-4 py-2 rounded-xl transition-all">
            Apply Now <Ico d={I.ext} className="w-3.5 h-3.5" />
          </a>
        ) : (
          <span className="text-xs text-slate-600 italic">No apply link</span>
        )}

        <div className="flex items-center gap-1.5 ml-auto">
          <span className="text-xs text-slate-600 mr-1">Rate:</span>
          {[
            { type: "up",   icon: I.thumb_u, active: "bg-emerald-500/15 border-emerald-500/30 text-emerald-400", title: "Good match" },
            { type: "down", icon: I.thumb_d, active: "bg-red-500/15 border-red-500/30 text-red-400",     title: "Not a match" },
            { type: "save", icon: I.save,    active: "bg-violet-500/15 border-violet-500/30 text-violet-400", title: "Save job", onClick: handleSave },
          ].map(({ type, icon, active, title, onClick }) => (
            <button key={type}
              onClick={onClick || (() => handleRate(type))}
              disabled={!!signal}
              title={title}
              className={`p-1.5 rounded-lg border transition-all disabled:cursor-default ${
                signal === type ? active : "border-white/10 text-slate-600 hover:border-white/20 hover:text-slate-400"
              }`}>
              <Ico d={icon} className="w-3.5 h-3.5" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

const JobMatches = ({
  jobQuery, jobLocation, resumeText, filters = {},
  setCareerAdvice, setSkillComparison,
  userId = "default_user",
}) => {
  const [jobs, setJobs]       = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const [stats, setStats]     = useState(null);
  const [sigLog, setSigLog]   = useState([]);

  const adviceRef = useRef(setCareerAdvice);
  const skillRef  = useRef(setSkillComparison);
  useEffect(() => { adviceRef.current = setCareerAdvice; }, [setCareerAdvice]);
  useEffect(() => { skillRef.current  = setSkillComparison; }, [setSkillComparison]);

  const match = useCallback(async () => {
    if (!resumeText || !jobQuery) {
      setJobs([]); adviceRef.current?.(null); skillRef.current?.(null); return;
    }
    setLoading(true); setError(null);
    try {
      // ✅ FIXED: was /rag/match-realtime → correct route is /jobs/match
      const res = await fetch(`${API_BASE_URL}/jobs/match`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText, job_query: jobQuery,
          location: jobLocation || "India",
          num_jobs: 50, top_k: 10, user_id: userId,
          min_match_score: filters.minMatchScore || 40,
          experience_level: filters.experienceLevel || null,
          posted_within_days: filters.postedWithinDays || 14,
          exclude_remote: filters.excludeRemote || false,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
      const j = data.matched_jobs || [];
      setJobs(j);
      setStats({ total: data.total_jobs_fetched || 0, personalised: j.some(x => x.personalised) });
      if (data.career_advice)    adviceRef.current?.(data.career_advice);
      if (data.skill_comparison) skillRef.current?.(data.skill_comparison);
    } catch (e) {
      let msg = e.message;
      if (msg.includes("SERPAPI") || msg.includes("API key"))
        msg = "Job search API not configured. Please add SERPAPI_KEY to backend .env";
      setError(msg); setJobs([]); adviceRef.current?.(null); skillRef.current?.(null);
    } finally { setLoading(false); }
  }, [resumeText, jobQuery, jobLocation, filters, userId]);

  useEffect(() => { match(); }, [match]);

  if (!resumeText || !jobQuery) {
    return (
      <div className="rounded-2xl border border-white/8 p-10 text-center"
        style={{ background: "rgba(255,255,255,0.02)" }}>
        <Ico d={!resumeText
          ? "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          : I.search}
          className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <p className="text-sm text-slate-500">
          {!resumeText ? "Upload your resume to see job matches" : "Search for jobs above to see matches"}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header stats */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-white">Job Matches</h2>
          {stats?.personalised && (
            <span className="text-xs bg-violet-500/15 border border-violet-500/20 text-violet-400 px-2.5 py-1 rounded-full">
              ✦ Personalised ranking
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {jobs.length > 0 && (
            <span className="text-xs bg-white/5 border border-white/10 text-slate-400 px-3 py-1.5 rounded-full">
              {jobs.length} match{jobs.length !== 1 ? "es" : ""}{stats?.total ? ` · ${stats.total} analysed` : ""}
            </span>
          )}
          <button onClick={match} disabled={loading}
            className="flex items-center gap-1.5 text-xs border border-white/10 text-slate-400 px-3 py-1.5 rounded-full hover:border-violet-500/30 hover:text-violet-300 transition disabled:opacity-40">
            <Ico d={I.refresh} className="w-3 h-3" /> Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-4 flex items-start gap-3">
          <Ico d={I.alert} className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-red-400">{error}</p>
            <button onClick={match} className="mt-2 text-xs text-red-400 border border-red-500/30 px-3 py-1 rounded-lg hover:bg-red-500/10 transition">
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="rounded-2xl border border-white/8 p-12 text-center"
          style={{ background: "rgba(255,255,255,0.02)" }}>
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-violet-500 mx-auto mb-4" />
          <p className="text-sm text-slate-400">Finding your perfect matches…</p>
          <p className="text-xs text-slate-600 mt-1">Scraping jobs + AI scoring · 10–20 seconds</p>
        </div>
      )}

      {/* Empty */}
      {!loading && jobs.length === 0 && !error && (
        <div className="rounded-2xl border border-white/8 p-10 text-center"
          style={{ background: "rgba(255,255,255,0.02)" }}>
          <Ico d={I.brief} className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <p className="text-sm text-slate-500">No matches found — try adjusting filters or search terms</p>
        </div>
      )}

      {/* Cards */}
      {jobs.map((job, i) => (
        <JobCard key={job.job_id || i} job={job} index={i}
          userId={userId} allJobs={jobs}
          onSignal={(j, s) => setSigLog(prev => [...prev, { job: j.title, signal: s, ts: Date.now() }])} />
      ))}

      {sigLog.length > 0 && (
        <p className="text-xs text-slate-700 text-center pt-2">
          {sigLog.length} feedback signal{sigLog.length !== 1 ? "s" : ""} recorded — rankings improve over time
        </p>
      )}
    </div>
  );
};

export default JobMatches;