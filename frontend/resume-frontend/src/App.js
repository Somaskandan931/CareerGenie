import { useState, useEffect, createContext } from "react";

import JobSearch from './components/JobSearch';
import JobMatches from './components/JobMatches';
import SkillAssessmentDashboard from './components/SkillAssessmentDashboard';
import RoadmapView from './components/Roadmapview';
import ProjectSuggestions from './components/ProjectSuggestions';
import TNAnalyticsDashboard from './components/TNAnalyticsDashboard';
import JobCoachChat from './components/JobCoachChat';
import MarketInsights from './components/MarketInsights';
import InterviewCoach from './components/InterviewCoach';
import ProgressDashboard from './components/ProgressDashboard';
import ATSScorer from './components/ATSScorer';
import ResumeRewriter from './components/ResumeRewriter';
import MentorSearch from './components/MentorSearch';

export const DarkModeContext = createContext({ dark: false, toggle: () => {} });

const API_BASE_URL = 'http://localhost:8000';

// Stable user ID persisted to localStorage so feedback + LTR data accumulates
// across sessions. In a real auth system this would come from your auth provider.
const getOrCreateUserId = () => {
  let id = localStorage.getItem("cg-user-id");
  if (!id) {
    id = "user_" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem("cg-user-id", id);
  }
  return id;
};
const USER_ID = getOrCreateUserId();

const Icon = ({ d, size = "h-4 w-4", className = "" }) => (
  <svg className={`${size} ${className}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d={d} />
  </svg>
);

const icons = {
  jobs:        "M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
  progress:    "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  learning:    "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7",
  interview:   "M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z",
  coach:       "M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z",
  insights:    "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6",
  institution: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4",
  ats:         "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4",
  upload:      "M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12",
  check:       "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
  alert:       "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  doc:         "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  bulb:        "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  book:        "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
  ext:         "M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14",
  map:         "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7",
  globe:       "M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  pen:         "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
  debate:      "M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z",
};

// ─── Confidence badge (inline) ────────────────────────────────────────────────
const ConfidencePill = ({ tier, score }) => {
  if (!tier) return null;
  const cfg = {
    high:       "bg-green-50 border-green-200 text-green-700",
    medium:     "bg-yellow-50 border-yellow-200 text-yellow-700",
    low:        "bg-orange-50 border-orange-200 text-orange-700",
    unreliable: "bg-red-50 border-red-200 text-red-700",
  }[tier] || "bg-gray-50 border-gray-200 text-gray-600";
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${cfg}`}>
      {tier} · {Math.round((score || 0) * 100)}%
    </span>
  );
};

// ─── Career Advice ────────────────────────────────────────────────────────────
const CareerAdvice = ({ careerAdvice }) => {
  if (!careerAdvice) return null;
  const confidence = careerAdvice._confidence;
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 mb-6">
      <div className="flex items-center gap-2 mb-5">
        <div className="w-7 h-7 rounded-lg bg-purple-100 dark:bg-purple-900/40 flex items-center justify-center">
          <Icon d={icons.bulb} size="h-4 w-4" className="text-purple-600 dark:text-purple-400" />
        </div>
        <h2 className="text-base font-medium text-gray-900 dark:text-white">Career Guidance</h2>
        {confidence && (
          <ConfidencePill tier={confidence.confidence_tier} score={confidence.confidence_score} />
        )}
        {careerAdvice.context_used?.personalisation_active && (
          <span className="text-xs bg-indigo-50 border border-indigo-200 text-indigo-700 px-2 py-0.5 rounded-full font-medium">✦ Personalised</span>
        )}
      </div>

      {/* Confidence issues — shown only when low/unreliable */}
      {confidence?.issues?.length > 0 && (
        <div className="mb-4 p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-700 rounded-lg">
          <p className="text-xs font-medium text-orange-700 dark:text-orange-400 mb-1">Confidence warnings</p>
          {confidence.issues.map((issue, i) => (
            <p key={i} className="text-xs text-orange-600 dark:text-orange-300">• {issue}</p>
          ))}
        </div>
      )}

      {careerAdvice.current_assessment && (
        <div className="mb-5 p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded-r-lg">
          <p className="text-xs font-medium text-blue-700 dark:text-blue-400 mb-1">Current Assessment</p>
          <p className="text-sm text-blue-800 dark:text-blue-200">{careerAdvice.current_assessment}</p>
        </div>
      )}
      {careerAdvice.skill_gaps?.length > 0 && (
        <div className="mb-5">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Critical skill gaps ({careerAdvice.skill_gaps.length})</p>
          <div className="space-y-2">
            {careerAdvice.skill_gaps.map((gap, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{gap.skill}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{gap.current_level} → {gap.target_level}</p>
                </div>
                <span className="text-xs bg-red-100 dark:bg-red-800 text-red-700 dark:text-red-200 px-2 py-1 rounded-md">{gap.importance}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {careerAdvice.learning_path?.length > 0 && (
        <div className="mb-5">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Recommended resources</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {careerAdvice.learning_path.map((r, i) => (
              <div key={i} className="flex items-start justify-between p-3 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{r.title}</p>
                  <div className="flex gap-1.5 mt-1.5 flex-wrap">
                    <span className="text-xs bg-white dark:bg-gray-600 border border-gray-200 dark:border-gray-500 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded">{r.type}</span>
                    <span className="text-xs bg-white dark:bg-gray-600 border border-gray-200 dark:border-gray-500 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded">{r.duration}</span>
                    <span className="text-xs bg-white dark:bg-gray-600 border border-gray-200 dark:border-gray-500 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded">{r.difficulty}</span>
                  </div>
                </div>
                {r.url && <a href={r.url} target="_blank" rel="noopener noreferrer" className="ml-2 text-indigo-500 hover:text-indigo-600 flex-shrink-0"><Icon d={icons.ext} size="h-4 w-4" /></a>}
              </div>
            ))}
          </div>
        </div>
      )}
      {careerAdvice.action_plan?.length > 0 && (
        <div className="mb-5">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Action plan</p>
          <div className="space-y-2">
            {careerAdvice.action_plan.map((a, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-100 dark:border-gray-600">
                <span className="flex-shrink-0 w-5 h-5 bg-indigo-600 text-white rounded-full flex items-center justify-center text-xs font-medium">{i + 1}</span>
                <p className="text-sm text-gray-700 dark:text-gray-200">{a}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {careerAdvice.market_insights && (
        <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <p className="text-xs font-medium text-amber-700 dark:text-amber-400 mb-1">Market insights</p>
          <p className="text-sm text-amber-800 dark:text-amber-200">{careerAdvice.market_insights}</p>
        </div>
      )}
    </div>
  );
};

// ─── Debate Synthesis Panel ───────────────────────────────────────────────────
const DebateSynthesis = ({ synthesis }) => {
  const [expanded, setExpanded] = useState(false);
  if (!synthesis?.action_plan && !synthesis?.key_insight) return null;

  const consensus = synthesis.consensus_score;
  const rounds    = synthesis.debate_rounds;
  const consensusColor =
    consensus >= 0.75 ? "text-green-600 bg-green-50 border-green-200" :
    consensus >= 0.5  ? "text-yellow-600 bg-yellow-50 border-yellow-200" :
                        "text-orange-600 bg-orange-50 border-orange-200";

  return (
    <div className="bg-white dark:bg-gray-800 border border-indigo-200 dark:border-indigo-700 rounded-xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center">
            <Icon d={icons.debate} size="h-4 w-4" className="text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h2 className="text-base font-medium text-gray-900 dark:text-white">Agent Consensus · This Week's Plan</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {rounds} debate round{rounds !== 1 ? "s" : ""} · 3 agents · synthesised recommendation
            </p>
          </div>
        </div>
        {consensus != null && (
          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${consensusColor}`}>
            {Math.round(consensus * 100)}% consensus
          </span>
        )}
      </div>

      {synthesis.key_insight && (
        <div className="mb-4 p-3 bg-indigo-50 dark:bg-indigo-900/20 border-l-4 border-indigo-500 rounded-r-lg">
          <p className="text-xs font-medium text-indigo-600 dark:text-indigo-400 mb-1">Key insight</p>
          <p className="text-sm text-indigo-800 dark:text-indigo-200">{synthesis.key_insight}</p>
        </div>
      )}

      {synthesis.action_plan?.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Consensus action plan</p>
          <div className="space-y-2">
            {synthesis.action_plan.map((step, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-100 dark:border-gray-600">
                <span className="flex-shrink-0 w-5 h-5 bg-indigo-600 text-white rounded-full flex items-center justify-center text-xs font-medium">{i + 1}</span>
                <p className="text-sm text-gray-700 dark:text-gray-200">{step}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {synthesis.top_job_recommendation && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg mb-4">
          <p className="text-xs font-medium text-green-700 dark:text-green-400 mb-1">Top job recommendation</p>
          <p className="text-sm text-green-800 dark:text-green-200">{synthesis.top_job_recommendation}</p>
        </div>
      )}

      {synthesis.timeline && (
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">Timeline: {synthesis.timeline}</p>
      )}

      {/* Elements adopted — collapsed by default */}
      {synthesis.elements_adopted_from && (
        <div className="mt-3">
          <button
            onClick={() => setExpanded(e => !e)}
            className="text-xs text-indigo-500 hover:text-indigo-600 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors"
          >
            {expanded ? "Hide" : "Show"} agent perspectives
          </button>
          {expanded && (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
              {Object.entries(synthesis.elements_adopted_from).map(([agent, text]) => (
                <div key={agent} className="p-3 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg">
                  <p className="text-xs font-medium text-gray-600 dark:text-gray-400 capitalize mb-1">{agent}</p>
                  <p className="text-xs text-gray-700 dark:text-gray-300">{text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Learning Path Tab ────────────────────────────────────────────────────────
const LearningPathTab = ({ resumeText, careerAdvice }) => {
  const [targetRole, setTargetRole]           = useState("");
  const [skillGaps, setSkillGaps]             = useState("");
  const [durationWeeks, setDurationWeeks]     = useState(12);
  const [difficulty, setDifficulty]           = useState("intermediate");
  const [experienceLevel, setExperienceLevel] = useState("");
  const [roadmap, setRoadmap]                 = useState(null);
  const [projects, setProjects]               = useState([]);
  const [loadingRoadmap, setLoadingRoadmap]   = useState(false);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [importingProgress, setImportingProgress] = useState(false);
  const [importSuccess, setImportSuccess]     = useState(null);
  const [error, setError]                     = useState(null);

  useEffect(() => {
    if (careerAdvice?.skill_gaps?.length > 0 && !skillGaps)
      setSkillGaps(careerAdvice.skill_gaps.map(g => g.skill).join(", "));
  }, [careerAdvice, skillGaps]);

  const parseGaps = () => skillGaps.split(",").map(s => s.trim()).filter(Boolean);

  const genRoadmap = async (retryCount = 0) => {
    if (!targetRole.trim()) { setError("Enter a target role."); return; }
    setError(null); setLoadingRoadmap(true); setRoadmap(null);
    try {
      const res = await fetch(`${API_BASE_URL}/roadmap/generate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText || "", target_role: targetRole.trim(), skill_gaps: parseGaps(), duration_weeks: durationWeeks, experience_level: experienceLevel || null }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
      if (!data.roadmap) {
        if (retryCount < 2) {
          setError(`Roadmap generation returned empty data — retrying (${retryCount + 1}/2)…`);
          setLoadingRoadmap(false);
          setTimeout(() => genRoadmap(retryCount + 1), 1500);
          return;
        }
        throw new Error("Roadmap generation failed after retries. The AI model may be overloaded — please try again in a moment.");
      }
      setRoadmap(data.roadmap);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoadingRoadmap(false);
    }
  };

  const genProjects = async () => {
    if (!targetRole.trim()) { setError("Enter a target role."); return; }
    setError(null); setLoadingProjects(true); setProjects([]);
    try {
      const res = await fetch(`${API_BASE_URL}/projects/suggest`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText || "", target_role: targetRole.trim(), skill_gaps: parseGaps(), difficulty, num_projects: 5 }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      setProjects((await res.json()).projects || []);
    } catch (e) { setError(e.message); }
    finally { setLoadingProjects(false); }
  };

  const importToProgress = async () => {
    if (!roadmap && projects.length === 0) return;
    setImportingProgress(true); setImportSuccess(null);
    try {
      const ops = [];
      if (roadmap) ops.push(fetch(`${API_BASE_URL}/progress/roadmap/import`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_id: USER_ID, roadmap }) }));
      if (projects.length > 0) ops.push(fetch(`${API_BASE_URL}/progress/projects/import`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_id: USER_ID, projects }) }));
      await Promise.all(ops);
      setImportSuccess(`Imported ${roadmap ? "roadmap" : ""}${roadmap && projects.length ? " + " : ""}${projects.length ? `${projects.length} projects` : ""} into your Progress Dashboard.`);
    } catch { setImportSuccess("Import failed — make sure the backend is running."); }
    finally { setImportingProgress(false); }
  };

  const inputCls = "w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none";

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-7 h-7 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center">
            <Icon d={icons.map} size="h-4 w-4" className="text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h2 className="text-base font-medium text-gray-900 dark:text-white">Learning Path Generator</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">Personalised roadmap + project suggestions</p>
          </div>
        </div>
        {error && (
          <div className="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-3 mb-4">
            <Icon d={icons.alert} size="h-4 w-4" className="text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}
        {importSuccess && (
          <div className="flex items-start gap-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-3 mb-4">
            <Icon d={icons.check} size="h-4 w-4" className="text-green-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-green-700 dark:text-green-300 font-medium">{importSuccess}</p>
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">Target Role <span className="text-red-500">*</span></label>
            <input type="text" value={targetRole} onChange={e => setTargetRole(e.target.value)} placeholder="e.g. EV Technician, ML Engineer, Full Stack Developer" className={inputCls} />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">Skill Gaps <span className="text-xs font-normal text-gray-400">(auto-filled from career advice)</span></label>
            <input type="text" value={skillGaps} onChange={e => setSkillGaps(e.target.value)} placeholder="e.g. PyTorch, Kubernetes, BMS, CAN Bus" className={inputCls} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">Duration</label>
            <select value={durationWeeks} onChange={e => setDurationWeeks(Number(e.target.value))} className={inputCls}>
              {[4, 8, 12, 16, 24].map(w => <option key={w} value={w}>{w} weeks</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">Experience Level</label>
            <select value={experienceLevel} onChange={e => setExperienceLevel(e.target.value)} className={inputCls}>
              <option value="">Not specified</option>
              <option value="entry">Entry Level</option>
              <option value="mid">Mid Level</option>
              <option value="senior">Senior Level</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">Project Difficulty</label>
            <select value={difficulty} onChange={e => setDifficulty(e.target.value)} className={inputCls}>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
        </div>
        <div className="flex flex-wrap gap-2.5 pt-4 border-t border-gray-100 dark:border-gray-700">
          <button onClick={() => { genRoadmap(0); genProjects(); }} disabled={loadingRoadmap || loadingProjects || !targetRole.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg disabled:opacity-40 transition-colors flex items-center gap-2">
            {(loadingRoadmap || loadingProjects) ? <><div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Generating...</> : "Generate Roadmap + Projects"}
          </button>
          <button onClick={() => genRoadmap(0)} disabled={loadingRoadmap || !targetRole.trim()}
            className="text-sm text-indigo-700 dark:text-indigo-300 border border-indigo-300 dark:border-indigo-600 px-4 py-2.5 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/20 disabled:opacity-40 transition-colors">
            {loadingRoadmap ? "..." : "Roadmap only"}
          </button>
          <button onClick={genProjects} disabled={loadingProjects || !targetRole.trim()}
            className="text-sm text-purple-700 dark:text-purple-300 border border-purple-300 dark:border-purple-600 px-4 py-2.5 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 disabled:opacity-40 transition-colors">
            {loadingProjects ? "..." : "Projects only"}
          </button>
        </div>
        {(roadmap || projects.length > 0) && (
          <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
            <button onClick={importToProgress} disabled={importingProgress}
              className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg disabled:opacity-40 transition-colors flex items-center gap-2">
              {importingProgress ? <><div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Importing...</> : "Import to Progress Dashboard"}
            </button>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">Saves roadmap and projects to your dashboard so you can track completion week by week.</p>
          </div>
        )}
      </div>
      {(roadmap || loadingRoadmap) && <RoadmapView roadmap={roadmap} loading={loadingRoadmap} />}
      {(projects.length > 0 || loadingProjects) && <ProjectSuggestions projects={projects} loading={loadingProjects} />}
    </div>
  );
};

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab]             = useState("jobs");
  const [resumeText, setResumeText]           = useState("");
  const [uploading, setUploading]             = useState(false);
  const [uploadError, setUploadError]         = useState(null);
  const [jobQuery, setJobQuery]               = useState("");
  const [jobLocation, setJobLocation]         = useState("India");
  const [filters, setFilters]                 = useState({});
  const [careerAdvice, setCareerAdvice]       = useState(null);
  const [skillComparison, setSkillComparison] = useState(null);
  const [synthesis, setSynthesis]             = useState(null); // debate synthesis result
  const [backendConfig, setBackendConfig]     = useState(null);
  const [dark, setDark]                       = useState(() => localStorage.getItem("cg-theme") === "dark");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("cg-theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/config`).then(r => r.json()).then(setBackendConfig).catch(() => null);
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true); setUploadError(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${API_BASE_URL}/upload-resume/parse`, { method: "POST", body: formData });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      setResumeText((await res.json()).resume_text);
    } catch (e) { setUploadError(e.message); setResumeText(""); }
    finally { setUploading(false); }
  };

  // When career advice arrives, also try to pull debate synthesis if present
  const handleSetCareerAdvice = (advice) => {
    setCareerAdvice(advice);
    if (advice?.synthesis) setSynthesis(advice.synthesis);
    else if (advice?.action_plan) setSynthesis(null);
  };

  const resumeSkills = skillComparison?.resume_skills?.map(s => s.skill) || [];

  const NAV_MAIN = [
    { key: "jobs",      label: "Job Matches",    icon: icons.jobs },
    { key: "progress",  label: "Progress",       icon: icons.progress },
    { key: "learning",  label: "Learning",       icon: icons.learning, badge: careerAdvice?.skill_gaps?.length > 0 ? careerAdvice.skill_gaps.length : null },
    { key: "interview", label: "Interview Prep", icon: icons.interview },
    { key: "ats",       label: "ATS Scorer",     icon: icons.ats },
    { key: "rewriter",  label: "Resume Rewriter", icon: icons.pen },
  ];

  const NAV_AI = [
    { key: "coach",       label: "Job Coach",       icon: icons.coach },
    { key: "mentors",     label: "Expert Mentors",  icon: icons.globe },
    { key: "insights",    label: "Market Insights", icon: icons.insights },
    { key: "institution", label: "Institution",     icon: icons.institution },
  ];

  const PAGE_TITLES = {
    jobs: "Job Matches",
    progress: "Progress Dashboard",
    learning: "Learning Path",
    interview: "Interview Coach",
    ats: "ATS Resume Scorer",
    rewriter: "Resume Rewriter",
    coach: "Job Coach",
    mentors: "Expert Mentors",
    insights: "Market Insights",
    institution: "Institution Analytics"
  };

  const showResume = !["institution", "progress", "mentors"].includes(activeTab);

  const NavItem = ({ item }) => (
    <button onClick={() => setActiveTab(item.key)}
      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all text-left ${
        activeTab === item.key
          ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-medium shadow-sm"
          : "text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-white/70 dark:hover:bg-gray-700/50"
      }`}>
      <Icon d={item.icon} size="h-4 w-4" className="flex-shrink-0 opacity-70" />
      <span className="truncate">{item.label}</span>
      {item.badge && <span className="ml-auto bg-indigo-600 text-white text-xs font-medium px-1.5 py-0.5 rounded-full leading-none">{item.badge}</span>}
    </button>
  );

  return (
    <DarkModeContext.Provider value={{ dark, toggle: () => setDark(d => !d) }}>
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900 overflow-hidden transition-colors duration-200">

      {/* ── Sidebar ── */}
      <aside className="w-52 flex-shrink-0 bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="px-4 py-4 border-b border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium text-gray-900 dark:text-white">Career Genie</p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">TN AUTO SkillBridge</p>
        </div>
        <nav className="flex-1 px-2 py-3 overflow-y-auto space-y-4">
          <div>
            <p className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider px-3 mb-1.5">Main</p>
            <div className="space-y-0.5">{NAV_MAIN.map(item => <NavItem key={item.key} item={item} />)}</div>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider px-3 mb-1.5">AI Tools</p>
            <div className="space-y-0.5">{NAV_AI.map(item => <NavItem key={item.key} item={item} />)}</div>
          </div>
        </nav>
        {/* Resume pill */}
        <div className="px-2 py-3 border-t border-gray-200 dark:border-gray-700 space-y-1.5">
          {resumeText ? (
            <div className="flex items-center gap-2 px-3 py-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <Icon d={icons.check} size="h-3.5 w-3.5" className="text-green-600 dark:text-green-400 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-xs font-medium text-green-700 dark:text-green-400">Resume loaded</p>
                <p className="text-xs text-green-600/70 dark:text-green-500 truncate">{(resumeText.length / 1000).toFixed(1)}k chars</p>
              </div>
            </div>
          ) : (
            <label htmlFor="resume-sidebar" className="flex items-center gap-2 px-3 py-2 border border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors">
              <Icon d={icons.upload} size="h-3.5 w-3.5" className="text-gray-400 flex-shrink-0" />
              <span className="text-xs text-gray-500 dark:text-gray-400">{uploading ? "Uploading..." : "Upload resume"}</span>
              <input id="resume-sidebar" type="file" accept=".pdf,.doc,.docx" onChange={handleFileUpload} disabled={uploading} className="hidden" />
            </label>
          )}
          {uploadError && <p className="text-xs text-red-500 px-1 truncate">{uploadError}</p>}
        </div>
      </aside>

      {/* ── Main area ── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-12 flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
          <h1 className="text-sm font-medium text-gray-900 dark:text-white">{PAGE_TITLES[activeTab]}</h1>
          <div className="flex items-center gap-2">
            {backendConfig && (!backendConfig.serpapi_key_present || !backendConfig.groq_key_present) && (
              <span className="text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 px-2 py-1 rounded-md">
                {!backendConfig.groq_key_present ? "Groq API key missing" : "SerpAPI key missing"}
              </span>
            )}
            <button onClick={() => setDark(d => !d)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 transition-all">
              {dark
                ? <><svg className="w-3.5 h-3.5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" /></svg>Light</>
                : <><svg className="w-3.5 h-3.5 text-indigo-500" fill="currentColor" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" /></svg>Dark</>
              }
            </button>
          </div>
        </header>

        {/* Scrollable content */}
        <main className="flex-1 overflow-y-auto bg-gray-100 dark:bg-gray-900">
          <div className="max-w-5xl mx-auto px-6 py-6">

            {/* Inline resume upload when not yet loaded */}
            {showResume && !resumeText && (
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center">
                    <Icon d={icons.doc} size="h-4 w-4" className="text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h2 className="text-sm font-medium text-gray-900 dark:text-white">Upload your resume to get started</h2>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Needed for job matching and personalised advice</p>
                  </div>
                </div>
                <div className="border-2 border-dashed border-gray-200 dark:border-gray-600 rounded-lg p-6 text-center hover:border-indigo-300 dark:hover:border-indigo-500 transition-colors">
                  <Icon d={icons.upload} size="h-8 w-8" className="text-gray-300 dark:text-gray-500 mx-auto mb-3" />
                  <label htmlFor="resume-main" className="cursor-pointer">
                    <span className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors">
                      {uploading ? "Uploading..." : "Choose file"}
                    </span>
                    <input id="resume-main" type="file" accept=".pdf,.doc,.docx" onChange={handleFileUpload} disabled={uploading} className="hidden" />
                  </label>
                  <p className="mt-2 text-xs text-gray-400 dark:text-gray-500">PDF or DOCX · Max 10 MB</p>
                  {uploading && <div className="mt-3 animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600 mx-auto" />}
                  {uploadError && <p className="mt-2 text-xs text-red-500">{uploadError}</p>}
                </div>
              </div>
            )}

            {/* ══ JOB MATCHES ══ */}
            {activeTab === "jobs" && (
              <>
                <JobSearch setJobQuery={setJobQuery} setJobLocation={setJobLocation} setFilters={setFilters} />
                <SkillAssessmentDashboard resumeSkills={skillComparison?.resume_skills || []} jobSkills={skillComparison?.job_skills || []} comparison={skillComparison} />
                <JobMatches
                  jobQuery={jobQuery}
                  jobLocation={jobLocation}
                  resumeText={resumeText}
                  filters={filters}
                  setCareerAdvice={handleSetCareerAdvice}
                  setSkillComparison={setSkillComparison}
                  userId={USER_ID}
                />
                {/* Debate synthesis shown above career advice if present */}
                <DebateSynthesis synthesis={synthesis} />
                <CareerAdvice careerAdvice={careerAdvice} />
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
                  {careerAdvice?.skill_gaps?.length > 0 && (
                    <button onClick={() => setActiveTab("learning")} className="text-left p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-indigo-300 dark:hover:border-indigo-600 hover:shadow-sm transition-all">
                      <p className="text-xs text-gray-400 dark:text-gray-500 mb-1">Skill gaps found</p>
                      <p className="text-xl font-medium text-indigo-600 dark:text-indigo-400">{careerAdvice.skill_gaps.length}</p>
                      <p className="text-xs text-gray-400 mt-1">Generate roadmap →</p>
                    </button>
                  )}
                  <button onClick={() => setActiveTab("progress")} className="text-left p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-green-300 dark:hover:border-green-600 hover:shadow-sm transition-all">
                    <p className="text-xs text-gray-400 dark:text-gray-500 mb-1">Progress Tracker</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">View Dashboard</p>
                    <p className="text-xs text-gray-400 mt-1">Roadmap, DSA, interviews →</p>
                  </button>
                  <button onClick={() => setActiveTab("coach")} className="text-left p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-orange-300 dark:hover:border-orange-600 hover:shadow-sm transition-all">
                    <p className="text-xs text-gray-400 dark:text-gray-500 mb-1">Career Coach</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Chat with Genie</p>
                    <p className="text-xs text-gray-400 mt-1">Salary, transitions →</p>
                  </button>
                  <button onClick={() => setActiveTab("interview")} className="text-left p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-sm transition-all">
                    <p className="text-xs text-gray-400 dark:text-gray-500 mb-1">Interview Prep</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Mock Interview</p>
                    <p className="text-xs text-gray-400 mt-1">AI interviewer →</p>
                  </button>
                </div>
              </>
            )}

            {activeTab === "learning"    && <LearningPathTab resumeText={resumeText} careerAdvice={careerAdvice} />}
            {activeTab === "progress"    && <ProgressDashboard />}
            {activeTab === "coach"       && (
              <div className="space-y-4">
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
                  <h2 className="text-base font-medium text-gray-900 dark:text-white mb-1">Career Coach & Counsellor</h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Ask Genie anything about your career.{resumeText && " Resume loaded for personalised advice."}</p>
                </div>
                <JobCoachChat resumeText={resumeText} userId={USER_ID} />
              </div>
            )}
            {activeTab === "mentors"     && (
              <div className="space-y-4">
                <MentorSearch userId={USER_ID} userSkills={resumeSkills} />
              </div>
            )}
            {activeTab === "insights"    && <MarketInsights resumeSkills={resumeSkills} />}
            {activeTab === "interview"   && <InterviewCoach resumeText={resumeText} />}
            {activeTab === "ats"         && <ATSScorer resumeText={resumeText} />}
            {activeTab === "rewriter"    && <ResumeRewriter resumeText={resumeText} />}
            {activeTab === "institution" && <TNAnalyticsDashboard />}

          </div>
        </main>

        <footer className="h-8 flex-shrink-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex items-center justify-center">
          <p className="text-xs text-gray-400 dark:text-gray-500">Career Genie v4.0 · Groq · RAG · ChromaDB · LTR · Agent Debate · Naan Mudhalvan · TNSDC · NSQF · Expert Mentors · ATS Scorer · Resume Rewriter</p>
        </footer>
      </div>
    </div>
    </DarkModeContext.Provider>
  );
}