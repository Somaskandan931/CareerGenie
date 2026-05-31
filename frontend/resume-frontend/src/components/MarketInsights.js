import React, { useState } from "react";
import API_BASE_URL from '../config';

const QUICK_ROLES = [
  "Machine Learning Engineer", "Full Stack Developer", "Data Scientist",
  "DevOps Engineer", "EV Technician", "Embedded Systems Engineer",
  "Product Manager", "Cloud Architect",
];

const Ico = ({ d, className = "w-4 h-4" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const I = {
  up:     "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6",
  down:   "M13 17h8m0 0V9m0 8l-8-8-4 4-6-6",
  flat:   "M5 12h14",
  search: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
  chart:  "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  alert:  "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
};

const TREND_CFG = {
  rising:  { icon: I.up,   color: "#10b981", bg: "bg-emerald-500/10 border-emerald-500/20", text: "text-emerald-400", label: "Rising" },
  falling: { icon: I.down, color: "#ef4444", bg: "bg-red-500/10 border-red-500/20",         text: "text-red-400",     label: "Falling" },
  stable:  { icon: I.flat, color: "#6366f1", bg: "bg-indigo-500/10 border-indigo-500/20",   text: "text-indigo-400",  label: "Stable" },
  unknown: { icon: I.flat, color: "#64748b", bg: "bg-white/5 border-white/10",              text: "text-slate-500",   label: "No data" },
};

const Sparkline = ({ data, color }) => {
  if (!data || data.length < 2) return <div className="h-8 text-xs text-slate-600 flex items-center">No trend data</div>;
  const w = 100, h = 28, pad = 2;
  const max = Math.max(...data, 1);
  const pts = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (w - pad * 2);
    const y = h - pad - (v / max) * (h - pad * 2);
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

const TrendCard = ({ keyword, data, isRole = false }) => {
  const cfg = TREND_CFG[data.direction] || TREND_CFG.unknown;
  return (
    <div className={`rounded-2xl border p-4 ${isRole ? "border-violet-500/20 bg-violet-500/5" : "border-white/8 bg-white/3"}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0 pr-2">
          <p className={`font-semibold text-sm truncate ${isRole ? "text-violet-300" : "text-slate-200"}`}>
            {isRole ? "🎯 " : ""}{keyword}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-slate-600">Avg: <span className="text-slate-400 font-medium">{data.avg}</span>/100</span>
            <span className="text-xs text-slate-600">Peak: <span className="text-slate-400 font-medium">{data.peak}</span></span>
          </div>
        </div>
        <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border ${cfg.bg} ${cfg.text} flex-shrink-0`}>
          <Ico d={cfg.icon} className="w-3 h-3" />{cfg.label}
        </span>
      </div>
      <Sparkline data={data.monthly_trend} color={cfg.color} />
    </div>
  );
};

export default function MarketInsights({ resumeSkills = [] }) {
  const [role, setRole]       = useState("");
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const fetch_ = async (roleQuery = role) => {
    if (!roleQuery.trim()) { setError("Enter a role to analyze."); return; }
    setError(null); setLoading(true); setData(null);
    try {
      const res = await fetch(`${API_BASE_URL}/insights/market`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: roleQuery.trim(), skills: resumeSkills }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      setData(await res.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const inp = "w-full px-4 py-2.5 text-sm rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none transition";

  return (
    <div className="space-y-5">
      {/* Input card */}
      <div className="rounded-2xl border border-white/10 bg-white/3 p-5">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/15 flex items-center justify-center">
            <Ico d={I.chart} className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Market Insights</h2>
            <p className="text-xs text-slate-500">Real-time demand trends for roles & skills</p>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4 text-sm text-red-400">
            <Ico d={I.alert} className="w-4 h-4 flex-shrink-0" />{error}
          </div>
        )}

        <div className="flex gap-2 mb-4">
          <input value={role} onChange={e => setRole(e.target.value)}
            onKeyDown={e => e.key === "Enter" && fetch_()}
            placeholder="e.g. ML Engineer, Full Stack Developer"
            className={inp + " flex-1"} />
          <button onClick={() => fetch_()} disabled={loading}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold px-5 py-2.5 rounded-xl disabled:opacity-40 transition-all">
            {loading
              ? <><span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Analyzing…</>
              : <><Ico d={I.search} className="w-4 h-4" />Analyze</>}
          </button>
        </div>

        <div className="flex flex-wrap gap-1.5">
          <p className="text-xs text-slate-600 w-full mb-1 uppercase tracking-widest font-medium">Quick roles</p>
          {QUICK_ROLES.map((r, i) => (
            <button key={i} onClick={() => { setRole(r); fetch_(r); }}
              className="text-xs border border-white/10 text-slate-400 hover:border-emerald-500/30 hover:text-emerald-300 px-3 py-1.5 rounded-full transition-all">
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {loading && (
        <div className="rounded-2xl border border-white/8 p-10 text-center bg-white/2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mx-auto mb-3" />
          <p className="text-sm text-slate-400">Analyzing market trends…</p>
        </div>
      )}

      {data && (
        <div className="space-y-4">
          {/* Role header */}
          {data.role_insight && (
            <TrendCard keyword={data.role_insight.keyword} data={data.role_insight} isRole />
          )}

          {/* Summary */}
          {data.summary && (
            <div className="rounded-2xl border border-white/8 bg-white/3 p-5">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-widest mb-2">Market Summary</p>
              <p className="text-sm text-slate-300 leading-relaxed">{data.summary}</p>
              {data.salary_range && (
                <div className="mt-3 flex items-center gap-2">
                  <span className="text-xs text-slate-500">Salary range:</span>
                  <span className="text-sm font-bold text-emerald-400">{data.salary_range}</span>
                </div>
              )}
            </div>
          )}

          {/* Skill trends */}
          {data.skill_trends?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-widest mb-3">Skill Demand Trends</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {data.skill_trends.map((t, i) => (
                  <TrendCard key={i} keyword={t.keyword} data={t} />
                ))}
              </div>
            </div>
          )}

          {/* Top skills */}
          {data.top_skills?.length > 0 && (
            <div className="rounded-2xl border border-white/8 bg-white/3 p-5">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-widest mb-3">Top In-Demand Skills</p>
              <div className="flex flex-wrap gap-2">
                {data.top_skills.map((s, i) => (
                  <span key={i} className="text-xs bg-violet-500/10 border border-violet-500/20 text-violet-300 px-3 py-1.5 rounded-full font-medium">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}