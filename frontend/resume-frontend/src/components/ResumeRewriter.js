import { useState } from "react";
import API_BASE_URL from '../config';

const Ico = ({ d, className = "w-4 h-4" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const I = {
  pen:   "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
  copy:  "M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3",
  alert: "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  check: "M5 13l4 4L19 7",
  arrow: "M13 7l5 5m0 0l-5 5m5-5H6",
  spark: "M13 10V3L4 14h7v7l9-11h-7z",
  doc:   "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
};

const inp = "w-full px-4 py-2.5 text-sm rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none transition";

const StatChip = ({ label, before, after, good }) => {
  const improved = after > before;
  const color = good
    ? (improved ? "text-emerald-400" : "text-slate-500")
    : (improved ? "text-slate-500" : "text-emerald-400");
  return (
    <div className="flex flex-col items-center p-3 rounded-xl border border-white/8 bg-white/3">
      <p className="text-xs text-slate-600 mb-1">{label}</p>
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-slate-600 line-through">{before}</span>
        <Ico d={I.arrow} className="w-3 h-3 text-slate-600" />
        <span className={`text-xs font-semibold ${color}`}>{after}</span>
      </div>
    </div>
  );
};

const ComparisonCard = ({ item, index }) => (
  <div className="rounded-2xl border border-white/8 overflow-hidden">
    <div className="px-4 py-2.5 border-b border-white/5 flex items-center justify-between"
      style={{ background: "rgba(255,255,255,0.03)" }}>
      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{item.section}</span>
      <span className="text-xs bg-violet-500/15 border border-violet-500/20 text-violet-400 px-2 py-0.5 rounded-full">#{index + 1}</span>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-white/5">
      <div className="p-4">
        <p className="text-xs font-medium text-red-400 mb-2 flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-400 inline-block" /> Before
        </p>
        <p className="text-xs text-slate-500 leading-relaxed">{item.before}</p>
      </div>
      <div className="p-4" style={{ background: "rgba(16,185,129,0.04)" }}>
        <p className="text-xs font-medium text-emerald-400 mb-2 flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" /> After
        </p>
        <p className="text-xs text-slate-200 leading-relaxed font-medium">{item.after}</p>
      </div>
    </div>
    {item.improvement && (
      <div className="px-4 py-2.5 border-t border-violet-500/10" style={{ background: "rgba(124,58,237,0.05)" }}>
        <p className="text-xs text-violet-300">
          <span className="font-semibold">Why it's better: </span>{item.improvement}
        </p>
      </div>
    )}
  </div>
);

const TONES = ["professional", "confident", "concise", "achievement-focused", "technical"];
const TABS  = ["rewritten", "comparison", "changes"];

export default function ResumeRewriter({ resumeText }) {
  const [targetRole, setTargetRole]   = useState("");
  const [tone, setTone]               = useState("professional");
  const [loading, setLoading]         = useState(false);
  const [result, setResult]           = useState(null);
  const [error, setError]             = useState(null);
  const [activeTab, setActiveTab]     = useState("rewritten");
  const [copied, setCopied]           = useState(false);

  const run = async () => {
    if (!resumeText?.trim()) { setError("Upload your resume first."); return; }
    if (!targetRole.trim())  { setError("Enter a target role."); return; }
    setError(null); setLoading(true); setResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/resume/rewrite`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText, target_role: targetRole.trim(), tone }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
      setResult(data.result || data);
      setActiveTab("rewritten");
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const copyText = () => {
    const text = result?.rewritten_resume || result?.resume_text || "";
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); });
  };

  const improvements = result?.improvements || result?.comparison || [];
  const changes      = result?.key_changes  || result?.changes    || [];

  return (
    <div className="space-y-5">
      {/* Input card */}
      <div className="rounded-2xl border border-white/10 bg-white/3 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-xl bg-indigo-500/15 flex items-center justify-center">
            <Ico d={I.pen} className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Resume Rewriter</h2>
            <p className="text-xs text-slate-500">AI-powered rewrite with ATS optimisation</p>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4 text-sm text-red-400">
            <Ico d={I.alert} className="w-4 h-4 flex-shrink-0" />{error}
          </div>
        )}

        <div className="space-y-4 mb-5">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5">Target Role <span className="text-red-400">*</span></label>
            <input value={targetRole} onChange={e => setTargetRole(e.target.value)}
              onKeyDown={e => e.key === "Enter" && run()}
              placeholder="e.g. Senior Software Engineer, Data Scientist"
              className={inp} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5">Writing Tone</label>
            <div className="flex flex-wrap gap-2">
              {TONES.map(t => (
                <button key={t} onClick={() => setTone(t)}
                  className={`text-xs px-3 py-1.5 rounded-xl border font-medium capitalize transition ${
                    tone === t
                      ? "border-indigo-500/50 bg-indigo-500/15 text-indigo-300"
                      : "border-white/10 text-slate-500 hover:border-white/20 hover:text-slate-300"
                  }`}>
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

        {!resumeText && <p className="text-xs text-amber-400 mb-4 flex items-center gap-1"><Ico d={I.alert} className="w-3.5 h-3.5" />Upload your resume first</p>}

        <button onClick={run} disabled={loading || !resumeText}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-6 py-2.5 rounded-xl disabled:opacity-40 transition-all">
          {loading
            ? <><span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Rewriting…</>
            : <><Ico d={I.spark} className="w-4 h-4" />Rewrite Resume</>}
        </button>
      </div>

      {/* Loading */}
      {loading && !result && (
        <div className="rounded-2xl border border-white/8 p-10 text-center bg-white/2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto mb-3" />
          <p className="text-sm text-slate-400">Rewriting with AI…</p>
          <p className="text-xs text-slate-600 mt-1">This takes 15–30 seconds</p>
        </div>
      )}

      {/* Stats */}
      {result?.stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Word Count",   before: result.stats.word_count_before,  after: result.stats.word_count_after,  good: true  },
            { label: "Action Verbs", before: result.stats.action_verbs_before, after: result.stats.action_verbs_after, good: true  },
            { label: "Bullet Points",before: result.stats.bullets_before,      after: result.stats.bullets_after,      good: true  },
            { label: "Filler Words", before: result.stats.filler_words_before, after: result.stats.filler_words_after, good: false },
          ].map((s, i) => s.before !== undefined && <StatChip key={i} {...s} />)}
        </div>
      )}

      {/* Tabs + Content */}
      {result && (
        <div>
          <div className="flex gap-1 mb-3 p-1 bg-white/5 border border-white/10 rounded-2xl">
            {TABS.map(t => (
              <button key={t} onClick={() => setActiveTab(t)}
                className={`flex-1 py-2 px-3 rounded-xl text-xs font-medium capitalize transition ${
                  activeTab === t ? "bg-white/10 text-white" : "text-slate-500 hover:text-slate-300"
                }`}>
                {t === "rewritten" ? "Rewritten Resume" : t === "comparison" ? `Before/After (${improvements.length})` : `Key Changes (${changes.length})`}
              </button>
            ))}
          </div>

          {/* Rewritten */}
          {activeTab === "rewritten" && (
            <div className="rounded-2xl border border-white/8 bg-white/3 p-5">
              <div className="flex items-center justify-between mb-4">
                <p className="text-xs font-medium text-slate-500 uppercase tracking-widest">Rewritten Resume</p>
                <button onClick={copyText}
                  className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-xl border transition ${
                    copied
                      ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                      : "border-white/10 text-slate-400 hover:border-white/20"
                  }`}>
                  <Ico d={copied ? I.check : I.copy} className="w-3.5 h-3.5" />
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
              <pre className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap font-mono">
                {result.rewritten_resume || result.resume_text || "No rewritten text returned."}
              </pre>
            </div>
          )}

          {/* Before/After */}
          {activeTab === "comparison" && improvements.length > 0 && (
            <div className="space-y-3">
              {improvements.map((item, i) => <ComparisonCard key={i} item={item} index={i} />)}
            </div>
          )}
          {activeTab === "comparison" && improvements.length === 0 && (
            <div className="rounded-2xl border border-white/8 p-8 text-center bg-white/2">
              <p className="text-sm text-slate-500">No comparison data available</p>
            </div>
          )}

          {/* Key changes */}
          {activeTab === "changes" && (
            <div className="rounded-2xl border border-white/8 bg-white/3 p-5">
              {changes.length > 0 ? (
                <div className="space-y-2">
                  {changes.map((c, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-xl border border-emerald-500/10 bg-emerald-500/5">
                      <span className="w-5 h-5 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">{i+1}</span>
                      <p className="text-sm text-slate-300">{typeof c === "string" ? c : c.description || c.change || JSON.stringify(c)}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-2">
                  {(result.summary_of_changes || "No change log provided.").split("\n").filter(Boolean).map((line, i) => (
                    <p key={i} className="text-sm text-slate-300">{line}</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}