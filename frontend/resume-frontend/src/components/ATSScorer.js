import { useState } from "react";

const API_BASE_URL = "http://localhost:8000";

// ── Tiny SVG icon helper (matches App.js pattern) ─────────────────────────────
const Icon = ({ d, size = "h-4 w-4", className = "" }) => (
  <svg className={`${size} ${className}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d={d} />
  </svg>
);

const ICONS = {
  score:  "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  check:  "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
  alert:  "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  tag:    "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z",
  bulb:   "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  star:   "M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z",
  x:      "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z",
  arrow:  "M13 7l5 5m0 0l-5 5m5-5H6",
};

// ── Score ring ────────────────────────────────────────────────────────────────
const ScoreRing = ({ score, label, size = 80, color = "#6366f1" }) => {
  const r = (size - 10) / 2;
  const circ = 2 * Math.PI * r;
  const filled = (score / 100) * circ;
  const scoreColor =
    score >= 75 ? "#22c55e" : score >= 50 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="currentColor" strokeWidth={6}
          className="text-gray-200 dark:text-gray-700" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={scoreColor} strokeWidth={6}
          strokeDasharray={`${filled} ${circ - filled}`}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dasharray 0.8s ease" }} />
        <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle"
          fontSize={size < 70 ? 13 : 18} fontWeight="700"
          fill={scoreColor}>
          {score}
        </text>
      </svg>
      <span className="text-xs text-gray-500 dark:text-gray-400 text-center leading-tight">{label}</span>
    </div>
  );
};

// ── Verdict badge ─────────────────────────────────────────────────────────────
const VerdictBadge = ({ verdict }) => {
  const map = {
    Excellent:   "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-700",
    Good:        "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-700",
    "Needs Work":"bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-700",
    Poor:        "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-700",
  };
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${map[verdict] || map["Needs Work"]}`}>
      {verdict}
    </span>
  );
};

// ── Section feedback card ─────────────────────────────────────────────────────
const SectionCard = ({ title, content, icon }) => (
  <div className="p-4 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg">
    <div className="flex items-center gap-2 mb-2">
      <Icon d={icon} size="h-3.5 w-3.5" className="text-indigo-500" />
      <p className="text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wide">{title}</p>
    </div>
    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{content}</p>
  </div>
);

// ── Main Component ─────────────────────────────────────────────────────────────
export default function ATSScorer({ resumeText }) {
  const [targetRole, setTargetRole] = useState("");
  const [loading, setLoading]       = useState(false);
  const [result, setResult]         = useState(null);
  const [error, setError]           = useState(null);

  const inputCls = "w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all";

  const runScorer = async () => {
    if (!resumeText?.trim()) { setError("Please upload your resume first."); return; }
    if (!targetRole.trim())  { setError("Please enter a target role."); return; }
    setError(null); setLoading(true); setResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/ats/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText, target_role: targetRole.trim() }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
      setResult(data.result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">

      {/* ── Input card ── */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-7 h-7 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center">
            <Icon d={ICONS.score} size="h-4 w-4" className="text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h2 className="text-base font-medium text-gray-900 dark:text-white">ATS Resume Scorer</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">Analyze your resume against a target role</p>
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-3 mb-4">
            <Icon d={ICONS.alert} size="h-4 w-4" className="text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}

        <div className="flex gap-3">
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">
              Target Role <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={targetRole}
              onChange={e => setTargetRole(e.target.value)}
              onKeyDown={e => e.key === "Enter" && runScorer()}
              placeholder="e.g. Software Engineer, Data Scientist, Product Manager"
              className={inputCls}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={runScorer}
              disabled={loading || !resumeText}
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg disabled:opacity-40 transition-colors flex items-center gap-2 whitespace-nowrap"
            >
              {loading ? (
                <><div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Analyzing...</>
              ) : (
                <><Icon d={ICONS.score} size="h-4 w-4" />Score Resume</>
              )}
            </button>
          </div>
        </div>

        {!resumeText && (
          <p className="text-xs text-amber-600 dark:text-amber-400 mt-3 flex items-center gap-1">
            <Icon d={ICONS.alert} size="h-3.5 w-3.5" />
            Upload your resume from the sidebar first
          </p>
        )}
      </div>

      {/* ── Loading skeleton ── */}
      {loading && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-8">
          <div className="flex flex-col items-center gap-4 py-4">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600" />
            <div className="text-center">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Analyzing resume…</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Checking keywords, structure, and impact statements</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Results ── */}
      {result && !loading && (
        <>
          {/* Score overview */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
            <div className="flex items-start justify-between mb-6 flex-wrap gap-4">
              <div>
                <h3 className="text-base font-medium text-gray-900 dark:text-white mb-1">Score Overview</h3>
                <div className="flex items-center gap-2">
                  <VerdictBadge verdict={result.ats_verdict} />
                  <span className="text-xs text-gray-500 dark:text-gray-400">{result.verdict_reason}</span>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-8 justify-center md:justify-start">
              <ScoreRing score={result.overall_score}  label="Overall ATS Score" size={90} />
              <ScoreRing score={result.keyword_score}  label="Keyword Match"     size={90} />
              <ScoreRing score={result.format_score}   label="Format Score"      size={90} />
              <ScoreRing score={result.bullet_quality?.score ?? 0} label="Bullet Quality" size={90} />
            </div>
          </div>

          {/* Keywords */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Missing */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Icon d={ICONS.x} size="h-4 w-4" className="text-red-500" />
                <h3 className="text-sm font-medium text-gray-900 dark:text-white">Missing Keywords</h3>
                <span className="ml-auto text-xs bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 px-2 py-0.5 rounded-full">
                  {result.missing_keywords?.length ?? 0}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {result.missing_keywords?.map((kw, i) => (
                  <span key={i} className="text-xs bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 px-2.5 py-1 rounded-full">
                    {kw}
                  </span>
                ))}
                {!result.missing_keywords?.length && (
                  <p className="text-xs text-gray-400">No critical keywords missing</p>
                )}
              </div>
            </div>

            {/* Found */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Icon d={ICONS.check} size="h-4 w-4" className="text-green-500" />
                <h3 className="text-sm font-medium text-gray-900 dark:text-white">Found Keywords</h3>
                <span className="ml-auto text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-2 py-0.5 rounded-full">
                  {result.found_keywords?.length ?? 0}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {result.found_keywords?.slice(0, 12).map((kw, i) => (
                  <span key={i} className="text-xs bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 text-green-700 dark:text-green-300 px-2.5 py-1 rounded-full">
                    {kw}
                  </span>
                ))}
                {!result.found_keywords?.length && (
                  <p className="text-xs text-gray-400">No matching keywords detected</p>
                )}
              </div>
            </div>
          </div>

          {/* Section feedback */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Section-wise Feedback</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <SectionCard title="Experience"  content={result.section_feedback?.experience}  icon={ICONS.score} />
              <SectionCard title="Skills"      content={result.section_feedback?.skills}      icon={ICONS.tag} />
              <SectionCard title="Education"   content={result.section_feedback?.education}   icon={ICONS.star} />
              <SectionCard title="Summary"     content={result.section_feedback?.summary}     icon={ICONS.bulb} />
              <SectionCard title="Formatting"  content={result.section_feedback?.formatting}  icon={ICONS.alert} />
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
        </>
      )}
    </div>
  );
}