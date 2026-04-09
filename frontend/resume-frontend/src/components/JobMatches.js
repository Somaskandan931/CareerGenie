import React, { useEffect, useState, useCallback, useRef } from "react";

const API_BASE_URL = 'http://localhost:8000';

// ─── Icons ─────────────────────────────────────────────────────────────────────
const Star = ({ filled = false }) => (
  <svg className={`h-4 w-4 ${filled ? 'text-yellow-400' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
  </svg>
);

const Briefcase = ({ size = "h-6 w-6" }) => (
  <svg className={size} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6" />
  </svg>
);

const SearchIcon = ({ size = "h-5 w-5" }) => (
  <svg className={size} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const AlertCircle = () => (
  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ExternalLink = () => (
  <svg className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
  </svg>
);

const ThumbUp = () => (
  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
  </svg>
);

const ThumbDown = () => (
  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
  </svg>
);

const BookmarkIcon = () => (
  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
  </svg>
);

// ─── Confidence badge ──────────────────────────────────────────────────────────
const ConfidenceBadge = ({ confidence }) => {
  if (!confidence) return null;
  const tier = confidence.confidence_tier;
  const score = confidence.confidence_score;
  const cfg = {
    high:       { cls: "bg-green-50 border-green-200 text-green-700",  label: "High confidence" },
    medium:     { cls: "bg-yellow-50 border-yellow-200 text-yellow-700", label: "Medium confidence" },
    low:        { cls: "bg-orange-50 border-orange-200 text-orange-700", label: "Low confidence" },
    unreliable: { cls: "bg-red-50 border-red-200 text-red-700",        label: "Unreliable — verify" },
  }[tier] || { cls: "bg-gray-50 border-gray-200 text-gray-600", label: "Unknown" };

  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border font-medium ${cfg.cls}`}>
      {cfg.label} · {Math.round(score * 100)}%
    </span>
  );
};

// ─── LTR rank badge ────────────────────────────────────────────────────────────
const LTRBadge = ({ ltrRank, ltrScore, personalised }) => {
  if (!ltrRank || !personalised) return null;
  return (
    <span className="inline-flex items-center gap-1 text-xs bg-indigo-50 border border-indigo-200 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
      ✦ Ranked #{ltrRank} for you
    </span>
  );
};

// ─── Helper: record feedback signal ───────────────────────────────────────────
const recordFeedback = async (userId, signalType, itemId, metadata = {}) => {
  if (!userId) return;
  try {
    await fetch(`${API_BASE_URL}/feedback/record`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, signal_type: signalType, item_id: itemId, metadata }),
    });
  } catch (_) { /* non-blocking */ }
};

// ─── Helper: record LTR preference pair ───────────────────────────────────────
const recordPreference = async (userId, winner, loser, userProfile = {}) => {
  if (!userId || !winner || !loser) return;
  try {
    await fetch(`${API_BASE_URL}/ranking/preference`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, winner, loser, context: { user_profile: userProfile } }),
    });
  } catch (_) { /* non-blocking */ }
};

// ─── Job card ─────────────────────────────────────────────────────────────────
const JobCard = ({ job, index, userId, allJobs, onSignal }) => {
  const [signalSent, setSignalSent]     = useState(null); // "up" | "down" | "save"
  const [applyClicked, setApplyClicked] = useState(false);

  const handleApply = () => {
    if (!applyClicked) {
      setApplyClicked(true);
      recordFeedback(userId, "apply_click", job.job_id || `job_${index}`, {
        role: job.title, company: job.company,
        component_contributions: job.component_contributions || {},
      });
      // Record as winner vs the next job in the list (pairwise LTR signal)
      const loser = allJobs[index + 1];
      if (loser) recordPreference(userId, job, loser);
      if (onSignal) onSignal(job, "apply_click");
    }
  };

  const handleRate = (type) => {
    if (signalSent) return;
    const signal = type === "up" ? "rate_match_up" : "rate_match_down";
    setSignalSent(type);
    recordFeedback(userId, signal, job.job_id || `job_${index}`, {
      role: job.title, company: job.company,
      component_contributions: job.component_contributions || {},
    });
    // Up-vote = winner vs next job; down-vote = loser vs previous job
    if (type === "up" && allJobs[index + 1]) {
      recordPreference(userId, job, allJobs[index + 1]);
    }
    if (type === "down" && index > 0) {
      recordPreference(userId, allJobs[index - 1], job);
    }
    if (onSignal) onSignal(job, signal);
  };

  const handleSave = () => {
    if (signalSent === "save") return;
    setSignalSent("save");
    recordFeedback(userId, "save_job", job.job_id || `job_${index}`, {
      role: job.title, company: job.company,
    });
    if (onSignal) onSignal(job, "save_job");
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100 border-green-300';
    if (score >= 65) return 'text-yellow-600 bg-yellow-100 border-yellow-300';
    if (score >= 50) return 'text-orange-600 bg-orange-100 border-orange-300';
    return 'text-red-600 bg-red-100 border-red-300';
  };

  const getScoreStars = (score) => {
    const stars = Math.round(score / 20);
    return Array.from({ length: 5 }, (_, i) => <Star key={i} filled={i < stars} />);
  };

  // Use LTR score if available, else match_score
  const displayScore = job.personalised && job.ltr_score != null
    ? Math.round(job.ltr_score * 100)
    : Math.round(job.match_score || 0);

  return (
    <div className="border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 rounded-xl p-6 hover:shadow-xl hover:border-blue-300 dark:hover:border-blue-600 transition-all">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-start gap-2 flex-wrap mb-1">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">{job.title}</h3>
            <LTRBadge ltrRank={job.ltr_rank} ltrScore={job.ltr_score} personalised={job.personalised} />
          </div>
          <p className="text-lg text-gray-700 dark:text-gray-300 font-medium mb-1">{job.company}</p>
          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
            <span>📍 {job.location}</span>
            {job._confidence && <ConfidenceBadge confidence={job._confidence} />}
          </div>
        </div>

        <div className="mt-4 sm:mt-0 sm:ml-6 text-center">
          <div className={`inline-flex items-center px-4 py-2 rounded-full text-lg font-bold border-2 ${getScoreColor(displayScore)}`}>
            {displayScore}% {job.personalised ? "Match ✦" : "Match"}
          </div>
          <div className="flex items-center justify-center mt-2 gap-1">
            {getScoreStars(displayScore)}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 font-medium">{job.recommendation}</p>
        </div>
      </div>

      {(job.explanation || (job.matched_skills?.length > 0 || job.missing_skills?.length > 0)) && (
        <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-700">
          {job.explanation ? (
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{job.explanation}</p>
          ) : (
            <p className="text-sm text-gray-400 dark:text-gray-500 italic">
              AI explanation unavailable — matched {job.matched_skills?.length || 0} skill{job.matched_skills?.length !== 1 ? "s" : ""} from your resume.
            </p>
          )}
        </div>
      )}

      {job.matched_skills?.length > 0 && (
        <div className="mb-4">
          <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">✓ Matching Skills ({job.matched_skills.length}):</p>
          <div className="flex flex-wrap gap-2">
            {job.matched_skills.map((skill, idx) => (
              <span key={idx} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-medium border border-green-300">
                ✓ {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {job.missing_skills?.length > 0 && (
        <div className="mb-4">
          <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">⚠ Skills to Develop ({job.missing_skills.length}):</p>
          <div className="flex flex-wrap gap-2">
            {job.missing_skills.map((skill, idx) => (
              <span key={idx} className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-xs font-medium border border-orange-300">
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
        {job.apply_link && (
          <a
            href={job.apply_link}
            target="_blank"
            rel="noopener noreferrer"
            onClick={handleApply}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium inline-flex items-center"
          >
            Apply Now
            <ExternalLink />
          </a>
        )}

        {/* Feedback buttons */}
        <div className="flex items-center gap-1 ml-auto">
          <span className="text-xs text-gray-400 dark:text-gray-500 mr-1">Rate this match:</span>
          <button
            onClick={() => handleRate("up")}
            disabled={!!signalSent}
            title="Good match"
            className={`p-2 rounded-lg border transition-colors text-sm ${
              signalSent === "up"
                ? "bg-green-100 border-green-300 text-green-700"
                : "border-gray-200 dark:border-gray-600 text-gray-400 hover:border-green-300 hover:text-green-600 dark:text-gray-500"
            } disabled:cursor-default`}
          >
            <ThumbUp />
          </button>
          <button
            onClick={() => handleRate("down")}
            disabled={!!signalSent}
            title="Not a good match"
            className={`p-2 rounded-lg border transition-colors text-sm ${
              signalSent === "down"
                ? "bg-red-100 border-red-300 text-red-700"
                : "border-gray-200 dark:border-gray-600 text-gray-400 hover:border-red-300 hover:text-red-600 dark:text-gray-500"
            } disabled:cursor-default`}
          >
            <ThumbDown />
          </button>
          <button
            onClick={handleSave}
            disabled={signalSent === "save"}
            title="Save job"
            className={`p-2 rounded-lg border transition-colors text-sm ${
              signalSent === "save"
                ? "bg-indigo-100 border-indigo-300 text-indigo-700"
                : "border-gray-200 dark:border-gray-600 text-gray-400 hover:border-indigo-300 hover:text-indigo-600 dark:text-gray-500"
            } disabled:cursor-default`}
          >
            <BookmarkIcon />
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Main Component ────────────────────────────────────────────────────────────
const JobMatches = ({
  jobQuery, jobLocation, resumeText, filters = {},
  setCareerAdvice, setSkillComparison,
  userId = "default_user",
}) => {
  const [matchedJobs, setMatchedJobs]   = useState([]);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState(null);
  const [stats, setStats]               = useState(null);
  const [signalLog, setSignalLog]       = useState([]); // light audit log for the session
  const prevJobsRef                      = useRef([]);

  // Stable refs for parent callbacks — prevents them from being useCallback deps
  // and causing an infinite re-render loop when the parent re-renders after
  // setCareerAdvice is called from inside the effect.
  const setCareerAdviceRef    = useRef(setCareerAdvice);
  const setSkillComparisonRef = useRef(setSkillComparison);
  useEffect(() => { setCareerAdviceRef.current    = setCareerAdvice;    }, [setCareerAdvice]);
  useEffect(() => { setSkillComparisonRef.current = setSkillComparison; }, [setSkillComparison]);

  // Emit scroll_past when user skips a job (i.e. it was in the list but not clicked)
  const handleSignal = (job, signalType) => {
    setSignalLog(prev => [...prev, { job: job.title, signal: signalType, ts: Date.now() }]);
  };

  const matchJobs = useCallback(async () => {
    if (!resumeText || !jobQuery) {
      setMatchedJobs([]);
      setCareerAdviceRef.current?.(null);
      setSkillComparisonRef.current?.(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/rag/match-realtime`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_text: resumeText,
          job_query: jobQuery,
          location: jobLocation || "India",
          num_jobs: 50,
          top_k: 10,
          user_id: userId,                                  // enables adaptive scoring + LTR
          min_match_score: filters.minMatchScore || 40,
          experience_level: filters.experienceLevel || null,
          posted_within_days: filters.postedWithinDays || 14,
          exclude_remote: filters.excludeRemote || false,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      const jobs  = data.matched_jobs || [];
      setMatchedJobs(jobs);
      prevJobsRef.current = jobs;

      setStats({
        total_fetched: data.total_jobs_fetched || 0,
        total_indexed: data.total_jobs_indexed || 0,
        search_query:  data.search_query || '',
        personalised:  jobs.some(j => j.personalised),
      });

      // Use refs — calling these directly would cause parent re-render → new
      // function references → matchJobs recreated → useEffect fires again (loop)
      if (data.career_advice)    setCareerAdviceRef.current?.(data.career_advice);
      if (data.skill_comparison) setSkillComparisonRef.current?.(data.skill_comparison);

    } catch (err) {
      let msg = err.message;
      if (msg.includes('SERPAPI_KEY') || msg.includes('API key'))
        msg = 'Job search API not configured. Please add SERPAPI_KEY to your backend .env file.';
      else if (msg.includes('500'))
        msg = 'Server error. Please check backend logs and ensure all API keys are configured.';
      setError(msg);
      setMatchedJobs([]);
      setCareerAdviceRef.current?.(null);
      setSkillComparisonRef.current?.(null);
    } finally {
      setLoading(false);
    }
  // setCareerAdvice / setSkillComparison intentionally excluded — they are
  // accessed via stable refs above to prevent an infinite render loop.
  }, [resumeText, jobQuery, jobLocation, filters, userId]);

  useEffect(() => { matchJobs(); }, [matchJobs]);

  if (!resumeText) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mb-8">
        <div className="flex items-center mb-6">
          <Star filled />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white ml-3">Job Matches</h2>
        </div>
        <div className="text-center py-16">
          <svg className="h-16 w-16 text-gray-300 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-gray-500 dark:text-gray-400 mt-4 text-lg">Upload your resume first to see job matches</p>
        </div>
      </div>
    );
  }

  if (!jobQuery) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mb-8">
        <div className="flex items-center mb-6">
          <Star filled />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white ml-3">Job Matches</h2>
        </div>
        <div className="text-center py-16">
          <SearchIcon size="h-16 w-16 text-gray-300 mx-auto" />
          <p className="text-gray-500 dark:text-gray-400 mt-4 text-lg">Search for jobs to see matches</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mb-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Star filled />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Job Matches</h2>
          {stats?.personalised && (
            <span className="text-xs bg-indigo-100 border border-indigo-200 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
              ✦ Personalised ranking
            </span>
          )}
        </div>
        {matchedJobs.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium">
              {matchedJobs.length} {matchedJobs.length === 1 ? 'match' : 'matches'}
            </span>
            {stats && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                ({stats.total_fetched} jobs analyzed)
              </span>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-4 mb-4">
          <div className="flex items-start">
            <AlertCircle />
            <div className="flex-1 ml-2">
              <span className="text-red-800 dark:text-red-300 font-medium block">Error</span>
              <p className="text-red-700 dark:text-red-400 mt-1 text-sm">{error}</p>
              <button onClick={matchJobs} className="mt-2 px-3 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200 text-sm font-medium">
                Try Again
              </button>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center p-12">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300 font-medium">Finding your perfect job matches...</p>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-2">This may take 10-20 seconds...</p>
        </div>
      )}

      {!loading && matchedJobs.length === 0 && !error && (
        <div className="text-center py-16">
          <Briefcase size="h-16 w-16 text-gray-300 mx-auto" />
          <p className="text-gray-500 dark:text-gray-400 mt-4 text-lg">No job matches found</p>
          <p className="text-gray-400 mt-2 text-sm">Try adjusting your filters or search terms</p>
        </div>
      )}

      <div className="space-y-6">
        {matchedJobs.map((job, index) => (
          <JobCard
            key={job.job_id || index}
            job={job}
            index={index}
            userId={userId}
            allJobs={matchedJobs}
            onSignal={handleSignal}
          />
        ))}
      </div>

      {/* Session signal log — collapsed summary */}
      {signalLog.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-100 dark:border-gray-700">
          <p className="text-xs text-gray-400 dark:text-gray-500">
            {signalLog.length} feedback signal{signalLog.length !== 1 ? "s" : ""} recorded this session — your rankings will improve over time.
          </p>
        </div>
      )}
    </div>
  );
};

export default JobMatches;