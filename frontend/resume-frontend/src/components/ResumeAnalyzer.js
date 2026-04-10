import { useState } from "react";

import API_BASE_URL from '../config';

const Icon = ({ d, size = "h-4 w-4", className = "" }) => (
  <svg className={`${size} ${className}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d={d} />
  </svg>
);

const ICONS = {
  score:    "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  check:    "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
  alert:    "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  tag:      "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z",
  bulb:     "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  star:     "M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z",
  x:        "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z",
  jd:       "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
  user:     "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
  flag:     "M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9",
  money:    "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  stage:    "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4",
  q:        "M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  note:     "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
  brief:    "M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
};

// ─────────────────────────────────────────────────────────────────────────────
// SHARED SUB-COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

const SectionCard = ({ title, content, icon }) => (
  <div className="p-4 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg">
    <div className="flex items-center gap-2 mb-2">
      <Icon d={icon} size="h-3.5 w-3.5" className="text-indigo-500" />
      <p className="text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wide">{title}</p>
    </div>
    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{content}</p>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// ATS SUB-COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

const ScoreRing = ({ score, label, size = 80 }) => {
  const r      = (size - 10) / 2;
  const circ   = 2 * Math.PI * r;
  const filled = ((score ?? 0) / 100) * circ;
  const color  = (score ?? 0) >= 75 ? "#22c55e" : (score ?? 0) >= 50 ? "#f59e0b" : "#ef4444";
  if (score == null) return (
    <div className="flex flex-col items-center gap-1">
      <div style={{ width: size, height: size }} className="flex items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700">
        <span className="text-xs text-gray-400">N/A</span>
      </div>
      <span className="text-xs text-gray-500 dark:text-gray-400 text-center leading-tight">{label}</span>
    </div>
  );
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="currentColor" strokeWidth={6} className="text-gray-200 dark:text-gray-700" />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={6}
          strokeDasharray={`${filled} ${circ - filled}`} strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`} style={{ transition: "stroke-dasharray 0.8s ease" }} />
        <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle"
          fontSize={size < 70 ? 13 : 18} fontWeight="700" fill={color}>{score}</text>
      </svg>
      <span className="text-xs text-gray-500 dark:text-gray-400 text-center leading-tight">{label}</span>
    </div>
  );
};

const ATSVerdictBadge = ({ verdict }) => {
  const map = {
    Excellent:    "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-700",
    Good:         "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-700",
    "Needs Work": "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-700",
    Poor:         "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-700",
  };
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${map[verdict] || map["Needs Work"]}`}>
      {verdict}
    </span>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// HR RECRUITER SUB-COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

const VERDICT_CONFIG = {
  "Strong Yes": { bg: "bg-green-100 dark:bg-green-900/30",  text: "text-green-800 dark:text-green-200",  border: "border-green-300 dark:border-green-600",  dot: "bg-green-500" },
  "Yes":        { bg: "bg-teal-100 dark:bg-teal-900/30",    text: "text-teal-800 dark:text-teal-200",    border: "border-teal-300 dark:border-teal-600",    dot: "bg-teal-500" },
  "Maybe":      { bg: "bg-amber-100 dark:bg-amber-900/30",  text: "text-amber-800 dark:text-amber-200",  border: "border-amber-300 dark:border-amber-600",  dot: "bg-amber-500" },
  "No":         { bg: "bg-orange-100 dark:bg-orange-900/30",text: "text-orange-800 dark:text-orange-200",border: "border-orange-300 dark:border-orange-600",dot: "bg-orange-500" },
  "Strong No":  { bg: "bg-red-100 dark:bg-red-900/30",      text: "text-red-800 dark:text-red-200",      border: "border-red-300 dark:border-red-600",      dot: "bg-red-500" },
};

const DIMENSION_LABELS = {
  technical_fit:         "Technical Fit",
  experience_relevance:  "Experience Relevance",
  culture_fit:           "Culture Fit",
  growth_potential:      "Growth Potential",
  communication_clarity: "Communication Clarity",
};

const COMPANY_TYPES = [
  { value: "startup",    label: "🚀 Startup",       desc: "Hustle, breadth, ownership" },
  { value: "mid-size",   label: "🏢 Mid-size",       desc: "Depth, process, collaboration" },
  { value: "enterprise", label: "🏦 Enterprise",     desc: "Stability, compliance, expertise" },
  { value: "faang",      label: "⭐ FAANG / Tier-1", desc: "CS fundamentals, scale, problem-solving" },
];

const FOCUS_AREAS = [
  { value: "general",      label: "General" },
  { value: "technical",    label: "Technical" },
  { value: "behavioural",  label: "Behavioural" },
  { value: "compensation", label: "Compensation" },
];

const DimensionBar = ({ label, score }) => {
  const color = score >= 8 ? "bg-green-500" : score >= 6 ? "bg-teal-500" : score >= 4 ? "bg-amber-400" : "bg-red-500";
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-gray-600 dark:text-gray-400">{label}</span>
        <span className={`text-xs font-bold ${score >= 7 ? "text-green-600 dark:text-green-400" : score >= 5 ? "text-amber-600 dark:text-amber-400" : "text-red-600 dark:text-red-400"}`}>{score}/10</span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${(score/10)*100}%` }} />
      </div>
    </div>
  );
};

const RecruiterQuestionCard = ({ item, index }) => {
  const [open, setOpen] = useState(false);
  const typeColors = {
    technical:   "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-700",
    behavioural: "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-700",
    situational: "bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 border-teal-200 dark:border-teal-700",
  };
  return (
    <div className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
      <button onClick={() => setOpen(o => !o)}
        className="w-full flex items-start gap-3 p-3 text-left bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 text-xs font-bold flex items-center justify-center mt-0.5">{index + 1}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-800 dark:text-gray-200">{item.question}</p>
          <span className={`mt-1.5 inline-flex text-xs px-2 py-0.5 rounded-full border font-medium ${typeColors[item.type] || typeColors.situational}`}>{item.type}</span>
        </div>
        <svg className={`w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5 transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && item.reason && (
        <div className="px-3 pb-3 pt-0 bg-gray-50 dark:bg-gray-700/50">
          <p className="text-xs text-gray-500 dark:text-gray-400 italic">Why ask this: {item.reason}</p>
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// ATS RESULTS PANEL
// ─────────────────────────────────────────────────────────────────────────────

const ATSResults = ({ result }) => (
  <div className="space-y-6 pt-2">
    {/* Score overview */}
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
      <div className="flex items-start justify-between mb-6 flex-wrap gap-4">
        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-1">Score Overview</h3>
          <div className="flex items-center gap-2 flex-wrap">
            <ATSVerdictBadge verdict={result.ats_verdict} />
            <span className="text-xs text-gray-500 dark:text-gray-400">{result.verdict_reason}</span>
          </div>
          {result.jd_match_score != null && (
            <div className="mt-2 inline-flex items-center gap-1.5 bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-700 px-3 py-1 rounded-full">
              <Icon d={ICONS.jd} size="h-3.5 w-3.5" className="text-indigo-600 dark:text-indigo-400" />
              <span className="text-xs font-medium text-indigo-700 dark:text-indigo-300">JD-matched scoring active</span>
            </div>
          )}
        </div>
      </div>
      <div className="flex flex-wrap gap-8 justify-center md:justify-start">
        <ScoreRing score={result.overall_score}              label="Overall ATS"    size={90} />
        <ScoreRing score={result.keyword_score}              label="Keyword Match"  size={90} />
        <ScoreRing score={result.format_score}               label="Format Score"   size={90} />
        <ScoreRing score={result.bullet_quality?.score ?? 0} label="Bullet Quality" size={90} />
        {result.jd_match_score != null && (
          <ScoreRing score={result.jd_match_score} label="JD Match" size={90} />
        )}
      </div>
    </div>

    {/* JD-specific gaps */}
    {result.jd_specific_gaps?.length > 0 && (
      <div className="bg-white dark:bg-gray-800 border border-amber-200 dark:border-amber-700 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Icon d={ICONS.jd} size="h-4 w-4" className="text-amber-600 dark:text-amber-400" />
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">JD Requirements Not Addressed</h3>
          <span className="ml-auto text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 px-2 py-0.5 rounded-full">{result.jd_specific_gaps.length} gaps</span>
        </div>
        <div className="space-y-2">
          {result.jd_specific_gaps.map((gap, i) => (
            <div key={i} className="flex items-start gap-2 p-2.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800 rounded-lg">
              <Icon d={ICONS.alert} size="h-3.5 w-3.5" className="text-amber-500 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-amber-800 dark:text-amber-200">{gap}</p>
            </div>
          ))}
        </div>
      </div>
    )}

    {/* Keywords */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Icon d={ICONS.x} size="h-4 w-4" className="text-red-500" />
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">Missing Keywords</h3>
          <span className="ml-auto text-xs bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 px-2 py-0.5 rounded-full">{result.missing_keywords?.length ?? 0}</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {result.missing_keywords?.map((kw, i) => (
            <span key={i} className="text-xs bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 px-2.5 py-1 rounded-full">{kw}</span>
          ))}
          {!result.missing_keywords?.length && <p className="text-xs text-gray-400">No critical keywords missing</p>}
        </div>
      </div>
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Icon d={ICONS.check} size="h-4 w-4" className="text-green-500" />
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">Found Keywords</h3>
          <span className="ml-auto text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-2 py-0.5 rounded-full">{result.found_keywords?.length ?? 0}</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {result.found_keywords?.slice(0, 12).map((kw, i) => (
            <span key={i} className="text-xs bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 text-green-700 dark:text-green-300 px-2.5 py-1 rounded-full">{kw}</span>
          ))}
          {!result.found_keywords?.length && <p className="text-xs text-gray-400">No matching keywords detected</p>}
        </div>
      </div>
    </div>

    {/* Section feedback */}
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
      <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Section-wise Feedback</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <SectionCard title="Experience" content={result.section_feedback?.experience} icon={ICONS.score} />
        <SectionCard title="Skills"     content={result.section_feedback?.skills}     icon={ICONS.tag} />
        <SectionCard title="Education"  content={result.section_feedback?.education}  icon={ICONS.star} />
        <SectionCard title="Summary"    content={result.section_feedback?.summary}    icon={ICONS.bulb} />
        <SectionCard title="Formatting" content={result.section_feedback?.formatting} icon={ICONS.alert} />
      </div>
    </div>

    {/* Bullet quality */}
    {result.bullet_quality && (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Bullet Point Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {result.bullet_quality.issues?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Issues found</p>
              <div className="space-y-2">
                {result.bullet_quality.issues.map((issue, i) => (
                  <div key={i} className="flex items-start gap-2 p-2.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800 rounded-lg">
                    <Icon d={ICONS.alert} size="h-3.5 w-3.5" className="text-amber-500 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-amber-800 dark:text-amber-200">{issue}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {result.bullet_quality.good_examples?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Strong bullets ✓</p>
              <div className="space-y-2">
                {result.bullet_quality.good_examples.map((ex, i) => (
                  <div key={i} className="flex items-start gap-2 p-2.5 bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800 rounded-lg">
                    <Icon d={ICONS.check} size="h-3.5 w-3.5" className="text-green-500 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-green-800 dark:text-green-200">{ex}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )}

    {/* Improvements */}
    {result.improvements?.length > 0 && (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-7 h-7 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center">
            <Icon d={ICONS.bulb} size="h-4 w-4" className="text-indigo-600 dark:text-indigo-400" />
          </div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">Improvement Suggestions</h3>
        </div>
        <div className="space-y-2">
          {result.improvements.map((tip, i) => (
            <div key={i} className="flex items-start gap-3 p-3 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 rounded-lg">
              <span className="flex-shrink-0 w-5 h-5 bg-indigo-600 text-white rounded-full flex items-center justify-center text-xs font-medium">{i + 1}</span>
              <p className="text-sm text-indigo-800 dark:text-indigo-200">{tip}</p>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// HR RECRUITER RESULTS PANEL
// ─────────────────────────────────────────────────────────────────────────────

// Normalise whatever the backend returns into the exact shape HRResults needs.
// Guards against missing keys, wrong types, or partial responses.
const normalisePanel = (raw) => {
  if (!raw || typeof raw !== "object") return null;

  const validVerdicts = new Set(["Strong Yes", "Yes", "Maybe", "No", "Strong No"]);

  const dimRaw = raw.dimension_scores && typeof raw.dimension_scores === "object"
    ? raw.dimension_scores : {};
  const dimension_scores = {
    technical_fit:         Number(dimRaw.technical_fit)         || 5,
    experience_relevance:  Number(dimRaw.experience_relevance)  || 5,
    culture_fit:           Number(dimRaw.culture_fit)           || 5,
    growth_potential:      Number(dimRaw.growth_potential)      || 5,
    communication_clarity: Number(dimRaw.communication_clarity) || 5,
  };

  const normaliseQ = (q) => {
    if (typeof q === "string") return { question: q, type: "behavioural", reason: "" };
    if (q && typeof q === "object" && q.question)
      return { question: String(q.question), type: q.type || "behavioural", reason: q.reason || "" };
    return null;
  };

  return {
    hire_verdict:               validVerdicts.has(raw.hire_verdict) ? raw.hire_verdict : "Maybe",
    verdict_summary:            raw.verdict_summary    || "Resume reviewed by AI recruiter.",
    verdict_confidence:         Number(raw.verdict_confidence) || 60,
    dimension_scores,
    green_flags:                Array.isArray(raw.green_flags)  ? raw.green_flags  : [],
    red_flags:                  Array.isArray(raw.red_flags)    ? raw.red_flags    : [],
    questions_to_ask:           Array.isArray(raw.questions_to_ask)
                                  ? raw.questions_to_ask.map(normaliseQ).filter(Boolean) : [],
    salary_bracket_inr:         raw.salary_bracket_inr         || null,
    suggested_interview_rounds: Array.isArray(raw.suggested_interview_rounds)
                                  ? raw.suggested_interview_rounds : [],
    recruiter_notes:            raw.recruiter_notes            || null,
  };
};

const HRResults = ({ panel: rawPanel, companyType, focusArea, setCompanyType, setFocusArea, onRun, loading }) => {
  const panel    = normalisePanel(rawPanel);
  const verdict  = panel?.hire_verdict;
  const vStyle   = VERDICT_CONFIG[verdict] || VERDICT_CONFIG["Maybe"];
  const avgScore = panel
    ? (Object.values(panel.dimension_scores).reduce((a, v) => a + v, 0) /
       Math.max(Object.keys(panel.dimension_scores).length, 1)).toFixed(1)
    : null;

  // Safety net — if normalisation still yields nothing renderable, show a helpful message
  if (!panel) return (
    <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-6 text-center">
      <p className="text-sm text-amber-700 dark:text-amber-300 font-medium mb-1">HR panel data unavailable</p>
      <p className="text-xs text-amber-600 dark:text-amber-400">The recruiter analysis returned an unexpected response. Try re-running.</p>
      <button onClick={onRun} disabled={loading}
        className="mt-3 bg-violet-600 hover:bg-violet-700 text-white text-xs font-medium px-4 py-2 rounded-lg disabled:opacity-40 transition-colors">
        {loading ? "Running…" : "Re-run Recruiter"}
      </button>
    </div>
  );

  return (
    <div className="space-y-6 pt-2">
      {/* Recruiter config — always visible so user can re-run with different settings */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Recruiter Settings</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
          {COMPANY_TYPES.map(c => (
            <button key={c.value} onClick={() => setCompanyType(c.value)}
              className={`text-left px-3 py-2.5 rounded-lg border text-xs transition-colors ${
                companyType === c.value
                  ? "bg-violet-50 dark:bg-violet-900/30 border-violet-400 dark:border-violet-500 text-violet-800 dark:text-violet-200"
                  : "border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-violet-300 dark:hover:border-violet-600"
              }`}>
              <span className="block font-medium mb-0.5">{c.label}</span>
              <span className="text-gray-400 dark:text-gray-500 font-normal">{c.desc}</span>
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2 mb-4">
          {FOCUS_AREAS.map(f => (
            <button key={f.value} onClick={() => setFocusArea(f.value)}
              className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${
                focusArea === f.value
                  ? "bg-violet-100 dark:bg-violet-900/40 border-violet-400 dark:border-violet-500 text-violet-800 dark:text-violet-200"
                  : "border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-violet-300"
              }`}>
              {f.label}
            </button>
          ))}
        </div>
        <button onClick={onRun} disabled={loading}
          className="bg-violet-600 hover:bg-violet-700 text-white text-xs font-medium px-4 py-2 rounded-lg disabled:opacity-40 transition-colors flex items-center gap-1.5">
          {loading
            ? <><div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white" />Re-running…</>
            : <><Icon d={ICONS.user} size="h-3.5 w-3.5" />Re-run Recruiter</>}
        </button>
      </div>

      {/* Verdict hero */}
      <div className={`${vStyle.bg} border ${vStyle.border} rounded-xl p-6`}>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${vStyle.dot} flex-shrink-0 mt-1`} />
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`text-2xl font-black ${vStyle.text}`}>{verdict}</span>
                {panel.verdict_confidence != null && (
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${vStyle.border} ${vStyle.text} font-medium`}>
                    {panel.verdict_confidence}% confidence
                  </span>
                )}
              </div>
              <p className={`text-sm mt-1 ${vStyle.text} opacity-90`}>{panel.verdict_summary}</p>
            </div>
          </div>
          {avgScore && (
            <div className="text-right">
              <p className={`text-3xl font-black ${vStyle.text}`}>{avgScore}</p>
              <p className={`text-xs ${vStyle.text} opacity-70`}>avg dimension score</p>
            </div>
          )}
        </div>
      </div>

      {/* Dimension scores */}
      {panel.dimension_scores && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Icon d={ICONS.brief} size="h-4 w-4" className="text-violet-500" />
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">Dimension Scores</h3>
          </div>
          <div className="space-y-3">
            {Object.entries(panel.dimension_scores).map(([key, val]) => (
              <DimensionBar key={key} label={DIMENSION_LABELS[key] || key.replace(/_/g, " ")} score={val} />
            ))}
          </div>
        </div>
      )}

      {/* Flags */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {panel.green_flags?.length > 0 && (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Icon d={ICONS.check} size="h-4 w-4" className="text-green-500" />
              <h3 className="text-sm font-medium text-gray-900 dark:text-white">Green Flags</h3>
              <span className="ml-auto text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-2 py-0.5 rounded-full">{panel.green_flags.length}</span>
            </div>
            <div className="space-y-2">
              {panel.green_flags.map((f, i) => (
                <div key={i} className="flex items-start gap-2 p-2.5 bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800 rounded-lg">
                  <span className="text-green-500 flex-shrink-0 mt-0.5 text-xs">✓</span>
                  <p className="text-xs text-green-800 dark:text-green-200">{f}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        {panel.red_flags?.length > 0 && (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Icon d={ICONS.flag} size="h-4 w-4" className="text-red-500" />
              <h3 className="text-sm font-medium text-gray-900 dark:text-white">Red Flags</h3>
              <span className="ml-auto text-xs bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 px-2 py-0.5 rounded-full">{panel.red_flags.length}</span>
            </div>
            <div className="space-y-2">
              {panel.red_flags.map((f, i) => (
                <div key={i} className="flex items-start gap-2 p-2.5 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 rounded-lg">
                  <Icon d={ICONS.alert} size="h-3.5 w-3.5" className="text-red-500 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-red-800 dark:text-red-200">{f}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Recruiter questions */}
      {panel.questions_to_ask?.length > 0 && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Icon d={ICONS.q} size="h-4 w-4" className="text-violet-500" />
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">Questions the Recruiter Would Ask</h3>
            <span className="ml-auto text-xs text-gray-400">tap to see why</span>
          </div>
          <div className="space-y-2">
            {panel.questions_to_ask.map((item, i) => <RecruiterQuestionCard key={i} item={item} index={i} />)}
          </div>
        </div>
      )}

      {/* Salary + rounds */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {panel.salary_bracket_inr && (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-2">
              <Icon d={ICONS.money} size="h-4 w-4" className="text-emerald-500" />
              <h3 className="text-sm font-medium text-gray-900 dark:text-white">Estimated Salary Bracket</h3>
            </div>
            <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400">{panel.salary_bracket_inr}</p>
            <p className="text-xs text-gray-400 mt-1">Based on profile strength and market rate</p>
          </div>
        )}
        {panel.suggested_interview_rounds?.length > 0 && (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Icon d={ICONS.stage} size="h-4 w-4" className="text-indigo-500" />
              <h3 className="text-sm font-medium text-gray-900 dark:text-white">Suggested Interview Rounds</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {panel.suggested_interview_rounds.map((r, i) => (
                <div key={i} className="flex items-center gap-1.5 bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-700 px-3 py-1.5 rounded-full">
                  <span className="w-4 h-4 bg-indigo-600 text-white rounded-full text-xs flex items-center justify-center font-medium">{i + 1}</span>
                  <span className="text-xs text-indigo-700 dark:text-indigo-300">{r}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Recruiter notes */}
      {panel.recruiter_notes && (
        <div className="bg-white dark:bg-gray-800 border border-amber-200 dark:border-amber-700 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <Icon d={ICONS.note} size="h-4 w-4" className="text-amber-600 dark:text-amber-400" />
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">Recruiter's Internal Notes</h3>
            <span className="ml-2 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/30 px-2 py-0.5 rounded-full border border-amber-200 dark:border-amber-700">candid</span>
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed italic">"{panel.recruiter_notes}"</p>
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export default function ResumeAnalyzer({ resumeText }) {
  // Shared inputs
  const [targetRole,      setTargetRole]      = useState("");
  const [jobDescription,  setJobDescription]  = useState("");
  const [showJD,          setShowJD]          = useState(false);

  // HR-only inputs
  const [companyType, setCompanyType] = useState("startup");
  const [focusArea,   setFocusArea]   = useState("general");

  // Results
  const [atsResult,   setAtsResult]   = useState(null);
  const [hrPanel,     setHrPanel]     = useState(null);

  // Loading / error per tab
  const [atsLoading,  setAtsLoading]  = useState(false);
  const [hrLoading,   setHrLoading]   = useState(false);
  const [atsError,    setAtsError]    = useState(null);
  const [hrError,     setHrError]     = useState(null);

  // Active result tab — only switches after a run
  const [activeResult, setActiveResult] = useState(null); // "ats" | "hr" | null

  const inputCls = "w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all";

  const validateShared = () => {
    if (!resumeText?.trim()) return "Please upload your resume first.";
    if (!targetRole.trim())  return "Please enter a target role.";
    return null;
  };

  const runATS = async () => {
    const err = validateShared();
    if (err) { setAtsError(err); return; }
    setAtsError(null); setAtsLoading(true); setAtsResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/ats/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText,
          target_role: targetRole.trim(),
          job_description: jobDescription.trim() || null,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
      setAtsResult(data.result);
      setActiveResult("ats");
    } catch (e) {
      setAtsError(e.message);
    } finally {
      setAtsLoading(false);
    }
  };

  const runHR = async () => {
    const err = validateShared();
    if (err) { setHrError(err); return; }
    setHrError(null); setHrLoading(true); setHrPanel(null);
    try {
      const res = await fetch(`${API_BASE_URL}/interview/hr-panel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText,
          target_role: targetRole.trim(),
          company_type: companyType,
          focus_area: focusArea,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
      setHrPanel(data.panel);
      setActiveResult("hr");
    } catch (e) {
      setHrError(e.message);
    } finally {
      setHrLoading(false);
    }
  };

  const runBoth = async () => {
    const err = validateShared();
    if (err) { setAtsError(err); setHrError(err); return; }
    setAtsError(null); setHrError(null);
    setAtsLoading(true); setHrLoading(true);
    setAtsResult(null); setHrPanel(null);

    try {
      // Single request — backend runs both analyses in parallel with ThreadPoolExecutor
      const res = await fetch(`${API_BASE_URL}/resume/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText,
          target_role: targetRole.trim(),
          job_description: jobDescription.trim() || null,
          company_type: companyType,
          focus_area: focusArea,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

      if (data.ats_result) { setAtsResult(data.ats_result); }
      else if (data.ats_error) { setAtsError(data.ats_error); }

      if (data.hr_panel) { setHrPanel(data.hr_panel); }
      else if (data.hr_error) { setHrError(data.hr_error); }

      // Switch to whichever result is available
      if (data.ats_result) setActiveResult("ats");
      else if (data.hr_panel) setActiveResult("hr");
    } catch (e) {
      setAtsError(e.message);
      setHrError(e.message);
    } finally {
      setAtsLoading(false);
      setHrLoading(false);
    }
  };

  const hasAny    = atsResult || hrPanel;
  const isLoading = atsLoading || hrLoading;

  return (
    <div className="space-y-6">

      {/* ── Shared input card ── */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
        {/* Header */}
        <div className="flex items-center gap-2 mb-5">
          <div className="w-7 h-7 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center">
            <Icon d={ICONS.score} size="h-4 w-4" className="text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h2 className="text-base font-medium text-gray-900 dark:text-white">Resume Analyzer</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">ATS scoring + AI HR recruiter simulation — one shared input</p>
          </div>
        </div>

        {/* Per-tab errors */}
        {atsError && (
          <div className="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-3 mb-3">
            <Icon d={ICONS.alert} size="h-4 w-4" className="text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 dark:text-red-300"><span className="font-semibold">ATS Error:</span> {atsError}</p>
          </div>
        )}
        {hrError && (
          <div className="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-3 mb-4">
            <Icon d={ICONS.alert} size="h-4 w-4" className="text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 dark:text-red-300"><span className="font-semibold">HR Error:</span> {hrError}</p>
          </div>
        )}

        {/* Target role */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">
            Target Role <span className="text-red-500">*</span>
          </label>
          <input type="text" value={targetRole} onChange={e => setTargetRole(e.target.value)}
            onKeyDown={e => e.key === "Enter" && runATS()}
            placeholder="e.g. Software Engineer, Data Scientist, Product Manager"
            className={inputCls} />
        </div>

        {/* JD toggle */}
        <div className="mb-4">
          <button onClick={() => setShowJD(v => !v)}
            className={`flex items-center gap-2 text-sm px-4 py-2 rounded-lg border transition-colors ${
              showJD
                ? "bg-indigo-50 dark:bg-indigo-900/30 border-indigo-300 dark:border-indigo-600 text-indigo-700 dark:text-indigo-300"
                : "border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-indigo-300 dark:hover:border-indigo-600"
            }`}>
            <Icon d={ICONS.jd} size="h-4 w-4" />
            {showJD ? "Hide Job Description" : "Paste Job Description (improves ATS & recruiter accuracy)"}
            {jobDescription.trim() && !showJD && (
              <span className="ml-1 text-xs bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 px-1.5 py-0.5 rounded">JD loaded</span>
            )}
          </button>
        </div>

        {showJD && (
          <div className="mb-5">
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">
              Job Description
              <span className="ml-1 font-normal text-gray-400">— used by both ATS scorer and HR recruiter</span>
            </label>
            <textarea value={jobDescription} onChange={e => setJobDescription(e.target.value)} rows={6}
              placeholder="Paste the full job description here…"
              className={`${inputCls} resize-none font-mono text-xs`} />
            {jobDescription.trim() && (
              <p className="text-xs text-green-600 dark:text-green-400 mt-1.5 flex items-center gap-1">
                <Icon d={ICONS.check} size="h-3.5 w-3.5" />
                {jobDescription.trim().split(/\s+/).length} words loaded
              </p>
            )}
          </div>
        )}

        {!resumeText && (
          <p className="text-xs text-amber-600 dark:text-amber-400 mb-4 flex items-center gap-1">
            <Icon d={ICONS.alert} size="h-3.5 w-3.5" />Upload your resume from the sidebar first
          </p>
        )}

        {/* Action buttons */}
        <div className="flex flex-wrap gap-2">
          <button onClick={runATS} disabled={isLoading || !resumeText}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg disabled:opacity-40 transition-colors flex items-center gap-2">
            {atsLoading
              ? <><div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Scoring…</>
              : <><Icon d={ICONS.score} size="h-4 w-4" />{jobDescription.trim() ? "ATS Score vs JD" : "ATS Score"}</>}
          </button>
          <button onClick={runHR} disabled={isLoading || !resumeText}
            className="bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg disabled:opacity-40 transition-colors flex items-center gap-2">
            {hrLoading
              ? <><div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Simulating…</>
              : <><Icon d={ICONS.user} size="h-4 w-4" />HR Recruiter</>}
          </button>
          <button onClick={runBoth} disabled={isLoading || !resumeText}
            className="bg-gray-800 hover:bg-gray-900 dark:bg-gray-100 dark:hover:bg-white dark:text-gray-900 text-white text-sm font-medium px-5 py-2.5 rounded-lg disabled:opacity-40 transition-colors flex items-center gap-2">
            {isLoading
              ? <><div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-current" />Running both…</>
              : "Run Both"}
          </button>
          {hasAny && !isLoading && (
            <button onClick={() => { setAtsResult(null); setHrPanel(null); setActiveResult(null); }}
              className="text-sm text-gray-500 dark:text-gray-400 border border-gray-300 dark:border-gray-600 px-4 py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              Clear
            </button>
          )}
        </div>
      </div>

      {/* ── Loading state ── */}
      {isLoading && !hasAny && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-10">
          <div className="flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600" />
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {atsLoading && hrLoading ? "Running ATS scorer & HR recruiter in parallel…"
                : atsLoading ? "Analyzing resume…"
                : "Simulating HR recruiter…"}
            </p>
          </div>
        </div>
      )}

      {/* ── Results area with tab switcher ── */}
      {hasAny && (
        <div>
          {/* Tab bar — only shown when both results exist */}
          {atsResult && hrPanel && (
            <div className="flex gap-1 mb-1 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-1">
              <button onClick={() => setActiveResult("ats")}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  activeResult === "ats"
                    ? "bg-white dark:bg-gray-700 text-indigo-700 dark:text-indigo-300 shadow-sm"
                    : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                }`}>
                <Icon d={ICONS.score} size="h-4 w-4" />
                ATS Score
                {atsResult && (
                  <span className={`text-xs px-1.5 py-0.5 rounded-full font-semibold ${
                    atsResult.overall_score >= 75 ? "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300"
                    : atsResult.overall_score >= 50 ? "bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300"
                    : "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300"
                  }`}>{atsResult.overall_score}</span>
                )}
              </button>
              <button onClick={() => setActiveResult("hr")}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  activeResult === "hr"
                    ? "bg-white dark:bg-gray-700 text-violet-700 dark:text-violet-300 shadow-sm"
                    : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                }`}>
                <Icon d={ICONS.user} size="h-4 w-4" />
                HR Recruiter
                {hrPanel && (
                  <span className={`text-xs px-1.5 py-0.5 rounded-full font-semibold ${
                    ["Strong Yes","Yes"].includes(hrPanel.hire_verdict) ? "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300"
                    : hrPanel.hire_verdict === "Maybe" ? "bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300"
                    : "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300"
                  }`}>{hrPanel.hire_verdict}</span>
                )}
              </button>
            </div>
          )}

          {/* Loading overlay on tabs while second result comes in */}
          {isLoading && hasAny && (
            <div className="flex items-center gap-2 py-3 px-4 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-700 rounded-xl mb-1">
              <div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-indigo-600" />
              <p className="text-xs text-indigo-700 dark:text-indigo-300">
                {atsLoading ? "ATS scoring in progress…" : "HR recruiter simulation in progress…"}
              </p>
            </div>
          )}

          {/* Tab content */}
          {activeResult === "ats" && atsResult && <ATSResults result={atsResult} />}
          {activeResult === "hr"  && hrPanel   && (
            <HRResults
              panel={hrPanel}
              companyType={companyType}
              focusArea={focusArea}
              setCompanyType={setCompanyType}
              setFocusArea={setFocusArea}
              onRun={runHR}
              loading={hrLoading}
            />
          )}
        </div>
      )}
    </div>
  );
}