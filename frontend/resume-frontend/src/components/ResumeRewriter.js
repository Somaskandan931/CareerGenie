import { useState } from "react";

import API_BASE_URL from '../config';

const Icon = ({ d, size = "h-4 w-4", className = "" }) => (
  <svg className={`${size} ${className}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d={d} />
  </svg>
);

const ICONS = {
  pen:    "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
  check:  "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
  alert:  "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  copy:   "M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3",
  arrow:  "M13 7l5 5m0 0l-5 5m5-5H6",
  spark:  "M13 10V3L4 14h7v7l9-11h-7z",
  doc:    "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  stats:  "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  eye:    "M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z",
};

// ── Stat chip ─────────────────────────────────────────────────────────────────
const StatChip = ({ label, before, after, good }) => {
  const improved = after > before;
  const color = good
    ? improved ? "text-green-600 dark:text-green-400" : "text-gray-500 dark:text-gray-400"
    : improved ? "text-gray-500 dark:text-gray-400"   : "text-green-600 dark:text-green-400";

  return (
    <div className="flex flex-col items-center p-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg">
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <div className="flex items-center gap-1.5">
        <span className="text-sm text-gray-400 dark:text-gray-500 line-through">{before}</span>
        <Icon d={ICONS.arrow} size="h-3 w-3" className="text-gray-400" />
        <span className={`text-sm font-semibold ${color}`}>{after}</span>
      </div>
    </div>
  );
};

// ── Before / After comparison card ───────────────────────────────────────────
const ComparisonCard = ({ item, index }) => (
  <div className="border border-gray-200 dark:border-gray-600 rounded-xl overflow-hidden">
    <div className="px-4 py-2 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-600 flex items-center justify-between">
      <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
        {item.section}
      </span>
      <span className="text-xs bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-2 py-0.5 rounded-full">
        #{index + 1}
      </span>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gray-200 dark:divide-gray-600">
      {/* Before */}
      <div className="p-4">
        <p className="text-xs font-medium text-red-500 mb-2 flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-400 inline-block" /> Before
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{item.before}</p>
      </div>
      {/* After */}
      <div className="p-4 bg-green-50/50 dark:bg-green-900/10">
        <p className="text-xs font-medium text-green-600 dark:text-green-400 mb-2 flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-400 inline-block" /> After
        </p>
        <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed font-medium">{item.after}</p>
      </div>
    </div>
    {/* Improvement note */}
    {item.improvement && (
      <div className="px-4 py-2.5 bg-indigo-50 dark:bg-indigo-900/20 border-t border-indigo-100 dark:border-indigo-800">
        <p className="text-xs text-indigo-700 dark:text-indigo-300">
          <span className="font-semibold">Why it's better: </span>{item.improvement}
        </p>
      </div>
    )}
  </div>
);

// ── Main Component ────────────────────────────────────────────────────────────
export default function ResumeRewriter({ resumeText }) {
  const [targetRole,  setTargetRole]  = useState("");
  const [tone,        setTone]        = useState("professional");
  const [loading,     setLoading]     = useState(false);
  const [result,      setResult]      = useState(null);
  const [error,       setError]       = useState(null);
  const [activeTab,   setActiveTab]   = useState("rewritten"); // "rewritten" | "comparison" | "changes"
  const [copied,      setCopied]      = useState(false);

  const inputCls = "w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all";

  const runRewriter = async () => {
    if (!resumeText?.trim()) { setError("Please upload your resume first."); return; }
    if (!targetRole.trim())  { setError("Please enter a target role."); return; }
    setError(null); setLoading(true); setResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/resume/rewrite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText,
          target_role: targetRole.trim(),
          tone,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
      setResult(data.result);
      setActiveTab("rewritten");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    if (!result?.rewritten_resume) return;
    await navigator.clipboard.writeText(result.rewritten_resume);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const TAB_STYLE = (active) =>
    `px-4 py-2 text-sm font-medium rounded-lg transition-all ${
      active
        ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
        : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
    }`;

  const changes = result?.changes_summary;

  return (
    <div className="space-y-6">

      {/* ── Input card ── */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-7 h-7 rounded-lg bg-purple-100 dark:bg-purple-900/40 flex items-center justify-center">
            <Icon d={ICONS.pen} size="h-4 w-4" className="text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h2 className="text-base font-medium text-gray-900 dark:text-white">Resume Rewriter</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">ATS-optimized · Impact-driven · Professional</p>
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-3 mb-4">
            <Icon d={ICONS.alert} size="h-4 w-4" className="text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          {/* Target role */}
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">
              Target Role <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={targetRole}
              onChange={e => setTargetRole(e.target.value)}
              onKeyDown={e => e.key === "Enter" && runRewriter()}
              placeholder="e.g. Software Engineer, Data Scientist, Product Manager"
              className={inputCls}
            />
          </div>
          {/* Tone */}
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">Tone</label>
            <select value={tone} onChange={e => setTone(e.target.value)} className={inputCls}>
              <option value="professional">Professional</option>
              <option value="confident">Confident & Bold</option>
              <option value="technical">Technical & Precise</option>
              <option value="concise">Concise & Direct</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-700">
          <p className="text-xs text-gray-400 dark:text-gray-500">
            {resumeText ? `Resume loaded · ${(resumeText.length / 1000).toFixed(1)}k chars` : "No resume uploaded"}
          </p>
          <button
            onClick={runRewriter}
            disabled={loading || !resumeText}
            className="bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg disabled:opacity-40 transition-colors flex items-center gap-2"
          >
            {loading ? (
              <><div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Rewriting...</>
            ) : (
              <><Icon d={ICONS.spark} size="h-4 w-4" />Rewrite Resume</>
            )}
          </button>
        </div>

        {!resumeText && (
          <p className="text-xs text-amber-600 dark:text-amber-400 mt-2 flex items-center gap-1">
            <Icon d={ICONS.alert} size="h-3.5 w-3.5" />
            Upload your resume from the sidebar first
          </p>
        )}
      </div>

      {/* ── Loading ── */}
      {loading && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-8">
          <div className="flex flex-col items-center gap-4 py-4">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600" />
            <div className="text-center">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Rewriting your resume…</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Adding impact statements, metrics & ATS keywords</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Results ── */}
      {result && !loading && (
        <>
          {/* Changes summary stats */}
          {changes && (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <Icon d={ICONS.stats} size="h-4 w-4" className="text-purple-500" />
                <h3 className="text-sm font-medium text-gray-900 dark:text-white">What Changed</h3>
                {changes.summary_added && (
                  <span className="ml-auto text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-700 px-2 py-0.5 rounded-full">
                    ✓ Summary added
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <StatChip label="Word Count"    before={changes.word_count?.before}   after={changes.word_count?.after}   good={false} />
                <StatChip label="Action Verbs"  before={changes.action_verbs?.before} after={changes.action_verbs?.after} good={true}  />
                <StatChip label="Metrics"       before={changes.metrics_added?.before} after={changes.metrics_added?.after} good={true} />
                <StatChip label="Bullet Points" before={changes.bullet_count?.before} after={changes.bullet_count?.after} good={true}  />
              </div>

              {changes.improvements_made?.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {changes.improvements_made.map((imp, i) => (
                    <span key={i} className="text-xs bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700 text-purple-700 dark:text-purple-300 px-2.5 py-1 rounded-full">
                      ✓ {imp}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab switcher */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
            <div className="flex items-center gap-1 p-2 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-600">
              <button onClick={() => setActiveTab("rewritten")}  className={TAB_STYLE(activeTab === "rewritten")}>
                <span className="flex items-center gap-1.5"><Icon d={ICONS.doc}  size="h-3.5 w-3.5" />Rewritten Resume</span>
              </button>
              <button onClick={() => setActiveTab("comparison")} className={TAB_STYLE(activeTab === "comparison")}>
                <span className="flex items-center gap-1.5"><Icon d={ICONS.eye}  size="h-3.5 w-3.5" />Before / After</span>
              </button>
            </div>

            <div className="p-6">

              {/* ── Rewritten resume tab ── */}
              {activeTab === "rewritten" && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Optimized for <span className="font-medium text-gray-700 dark:text-gray-300">{result.target_role}</span>
                      {" · "}<span className="capitalize">{result.tone}</span> tone
                    </p>
                    <button
                      onClick={copyToClipboard}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-all"
                    >
                      <Icon d={copied ? ICONS.check : ICONS.copy} size="h-3.5 w-3.5"
                        className={copied ? "text-green-500" : ""} />
                      {copied ? "Copied!" : "Copy text"}
                    </button>
                  </div>
                  <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 leading-relaxed font-mono bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4 max-h-[600px] overflow-y-auto">
                    {result.rewritten_resume}
                  </pre>
                </div>
              )}

              {/* ── Before / After tab ── */}
              {activeTab === "comparison" && (
                <div className="space-y-4">
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Showing {result.before_after?.length ?? 0} key improvements made to your resume
                  </p>
                  {result.before_after?.map((item, i) => (
                    <ComparisonCard key={i} item={item} index={i} />
                  ))}
                  {!result.before_after?.length && (
                    <p className="text-sm text-gray-400 text-center py-6">No comparisons available</p>
                  )}
                </div>
              )}

            </div>
          </div>
        </>
      )}
    </div>
  );
}