import { useState, useEffect } from "react";
import API_BASE_URL from '../config';

const STATS = [
  { label: "AI-Powered Tools",  value: "12+",  color: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300" },
  { label: "Job Sources",       value: "Live", color: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300" },
  { label: "Agent Systems",     value: "2",    color: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300" },
  { label: "LLM Providers",     value: "4",    color: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300" },
];

const FEATURES = [
  {
    key:   "jobs",
    title: "Job Matching",
    desc:  "RAG-powered semantic job matching against live listings using ChromaDB + embeddings.",
    icon:  "💼",
    badge: "RAG",
    border: "hover:border-indigo-400 dark:hover:border-indigo-500",
  },
  {
    key:   "analyzer",
    title: "Resume Analyzer",
    desc:  "ATS scoring + AI recruiter panel. See exactly how recruiters evaluate your resume.",
    icon:  "📄",
    badge: "ATS",
    border: "hover:border-blue-400 dark:hover:border-blue-500",
  },
  {
    key:   "rewriter",
    title: "Resume Rewriter",
    desc:  "LangChain PromptTemplate + LLMChain rewrite. Action verbs, metrics, ATS-ready.",
    icon:  "✍️",
    badge: "LangChain",
    border: "hover:border-violet-400 dark:hover:border-violet-500",
  },
  {
    key:   "learning",
    title: "Learning Path",
    desc:  "LangGraph deep analysis: parse → gap analysis → roadmap → project suggestions.",
    icon:  "🗺️",
    badge: "LangGraph",
    border: "hover:border-green-400 dark:hover:border-green-500",
  },
  {
    key:   "interview",
    title: "Interview Coach",
    desc:  "Role-specific question generation and AI feedback on your answers in real-time.",
    icon:  "🎤",
    badge: "AI Coach",
    border: "hover:border-red-400 dark:hover:border-red-500",
  },
  {
    key:   "coach",
    title: "Career Debate",
    desc:  "Multi-agent Propose → Critique → Synthesise debate system for career decisions.",
    icon:  "🤖",
    badge: "Agentic AI",
    border: "hover:border-orange-400 dark:hover:border-orange-500",
  },
  {
    key:   "mentors",
    title: "Expert Mentors",
    desc:  "Find and book sessions with industry professionals matched to your skill gaps.",
    icon:  "👥",
    badge: "Mentorship",
    border: "hover:border-teal-400 dark:hover:border-teal-500",
  },
  {
    key:   "employer",
    title: "Post a Job",
    desc:  "Employers: post jobs directly to our live board. Candidates see them immediately.",
    icon:  "📢",
    badge: "Employer",
    border: "hover:border-yellow-400 dark:hover:border-yellow-500",
  },
];

export default function HomePage({ resumeText, careerAdvice, onNavigate }) {
  const [apiStatus,  setApiStatus]  = useState(null);
  const [postedJobs, setPostedJobs] = useState(0);

  useEffect(() => {
    fetch(`${API_BASE_URL}/config`)
      .then(r => r.json()).then(setApiStatus).catch(() => null);
    fetch(`${API_BASE_URL}/jobs/posted`)
      .then(r => r.json()).then(d => setPostedJobs(d.total || 0)).catch(() => null);
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">

      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-700 rounded-full text-xs text-indigo-700 dark:text-indigo-300 font-medium mb-4">
          <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse" />
          {apiStatus ? "All systems operational" : "Connecting to backend..."}
        </div>

        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Career Genie AI
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xl mx-auto">
          RAG · LangChain · LangGraph · Multi-Agent Debate · Live Job Matching · ATS Scoring
        </p>

        {!resumeText ? (
          <div className="mt-5 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl text-sm text-amber-700 dark:text-amber-300">
            👆 Upload your resume from the sidebar to unlock all personalised features
          </div>
        ) : (
          <div className="mt-5 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl text-sm text-green-700 dark:text-green-300">
            ✅ Resume loaded — all {FEATURES.length} tools are ready for you
          </div>
        )}
      </div>

      {/* ── Stats ────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
        {STATS.map((s, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 text-center">
            <p className={`text-xl font-bold mb-1 px-2 py-0.5 rounded-lg inline-block ${s.color}`}>{s.value}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* ── Employer jobs alert ───────────────────────────────────────────── */}
      {postedJobs > 0 && (
        <div className="mb-5 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-xl text-sm text-yellow-700 dark:text-yellow-300 flex items-center gap-2">
          <span>📢</span>
          <span>
            <strong>{postedJobs}</strong> employer-posted job{postedJobs !== 1 ? "s" : ""} currently live on the board.
          </span>
          <button
            onClick={() => onNavigate("jobs")}
            className="ml-auto text-xs underline opacity-80 hover:opacity-100"
          >
            View all →
          </button>
        </div>
      )}

      {/* ── Skill gap summary ─────────────────────────────────────────────── */}
      {careerAdvice?.skill_gaps?.length > 0 && (
        <div className="mb-5 p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700 rounded-xl">
          <p className="text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">
            📊 {careerAdvice.skill_gaps.length} skill gaps identified for your profile
          </p>
          <div className="flex flex-wrap gap-2">
            {careerAdvice.skill_gaps.slice(0, 6).map((g, i) => (
              <span
                key={i}
                className="text-xs bg-white dark:bg-gray-800 border border-purple-200 dark:border-purple-700 text-purple-700 dark:text-purple-300 px-2 py-1 rounded-lg"
              >
                {g.skill}
              </span>
            ))}
          </div>
          <button
            onClick={() => onNavigate("learning")}
            className="mt-3 text-xs text-purple-600 dark:text-purple-400 underline"
          >
            Generate your learning path →
          </button>
        </div>
      )}

      {/* ── Feature cards ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {FEATURES.map(f => (
          <button
            key={f.key}
            onClick={() => onNavigate(f.key)}
            className={`text-left p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:shadow-md transition-all duration-150 ${f.border}`}
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl flex-shrink-0">{f.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{f.title}</p>
                  <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-300 px-1.5 py-0.5 rounded font-mono flex-shrink-0">
                    {f.badge}
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">{f.desc}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* ── Tech stack footer ─────────────────────────────────────────────── */}
      <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-center text-gray-400 dark:text-gray-600">
          Powered by ChromaDB · LangChain · LangGraph · FastAPI · Ollama / Groq / Anthropic / Gemini
        </p>
      </div>

    </div>
  );
}