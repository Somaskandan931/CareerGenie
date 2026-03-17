import React, { useState } from "react";

const API_BASE_URL = "http://localhost:8000";

const QUICK_ROLES = [
  "Machine Learning Engineer", "Full Stack Developer", "Data Scientist",
  "DevOps Engineer", "EV Technician", "Embedded Systems Engineer",
  "Product Manager", "Cloud Architect",
];

// ─── Icons ────────────────────────────────────────────────────────────────────
const TrendUpIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  </svg>
);
const TrendDownIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
  </svg>
);
const TrendFlatIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
  </svg>
);
const SearchIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

// ─── Sparkline (tiny SVG line chart) ─────────────────────────────────────────
const Sparkline = ({ data, color = "#6366f1" }) => {
  if (!data || data.length < 2) {
    return <div className="h-8 flex items-center text-xs text-gray-400">No trend data</div>;
  }
  const w = 120, h = 32, pad = 2;
  const max = Math.max(...data, 1);
  const pts = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (w - pad * 2);
    const y = h - pad - (v / max) * (h - pad * 2);
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

// ─── Direction badge ──────────────────────────────────────────────────────────
const DirectionBadge = ({ direction }) => {
  const cfg = {
    rising: { icon: <TrendUpIcon />, cls: "text-green-700 bg-green-100 border-green-200", label: "Rising" },
    falling: { icon: <TrendDownIcon />, cls: "text-red-700 bg-red-100 border-red-200", label: "Falling" },
    stable: { icon: <TrendFlatIcon />, cls: "text-gray-700 bg-gray-100 border-gray-200", label: "Stable" },
    unknown: { icon: <TrendFlatIcon />, cls: "text-gray-500 bg-gray-50 border-gray-200", label: "No data" },
  }[direction] || { icon: <TrendFlatIcon />, cls: "text-gray-500 bg-gray-50 border-gray-200", label: direction };
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border ${cfg.cls}`}>
      {cfg.icon}{cfg.label}
    </span>
  );
};

// ─── Trend card ───────────────────────────────────────────────────────────────
const TrendCard = ({ keyword, data, isRole = false }) => {
  const sparkColors = { rising: "#22c55e", falling: "#ef4444", stable: "#6366f1", unknown: "#9ca3af" };
  return (
    <div className={`bg-white rounded-xl border p-4 ${isRole ? "border-indigo-200 bg-indigo-50" : "border-gray-200"}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <p className={`font-semibold text-sm truncate ${isRole ? "text-indigo-900" : "text-gray-800"}`}>
            {isRole && "🎯 "}{keyword}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-500">Avg: <strong>{data.avg}</strong>/100</span>
            <span className="text-xs text-gray-500">Peak: <strong>{data.peak}</strong></span>
          </div>
        </div>
        <DirectionBadge direction={data.direction} />
      </div>
      <Sparkline data={data.sparkline} color={sparkColors[data.direction] || "#6366f1"} />
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
const MarketInsights = ({ resumeSkills = [] }) => {
  const [role, setRole] = useState("");
  const [skillInput, setSkillInput] = useState("");
  const [location, setLocation] = useState("India");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const fetchInsights = async (overrideRole) => {
    const targetRole = (overrideRole || role).trim();
    if (!targetRole) { setError("Enter a role to analyse."); return; }
    setLoading(true);
    setError(null);
    setData(null);

    // Build skills list — from input field or from resume skills
    const skills = skillInput.trim()
      ? skillInput.split(",").map(s => s.trim()).filter(Boolean)
      : resumeSkills.slice(0, 8);

    try {
      const res = await fetch(`${API_BASE_URL}/insights/market`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: targetRole, skills, location }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      setData(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const trendEntries = data ? Object.entries(data.trend_data) : [];
  const roleEntry = trendEntries[0];
  const skillEntries = trendEntries.slice(1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-7 text-white">
        <h2 className="text-2xl font-black mb-1">📈 Market Insights</h2>
        <p className="text-indigo-200 text-sm">
          Real Google Trends data + AI analysis for any role or skill in {location}
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Target Role <span className="text-red-500">*</span>
            </label>
            <input type="text" value={role} onChange={e => setRole(e.target.value)}
              placeholder="e.g. Machine Learning Engineer"
              onKeyDown={e => e.key === "Enter" && fetchInsights()}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-400 focus:border-transparent" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Location</label>
            <select value={location} onChange={e => setLocation(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-400 bg-white">
              {["India", "Tamil Nadu", "Bangalore", "Chennai", "Mumbai", "Hyderabad"].map(l => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Skills to Track
              <span className="ml-1 font-normal text-gray-400">
                (comma-separated — leave blank to use your resume skills)
              </span>
            </label>
            <input type="text" value={skillInput} onChange={e => setSkillInput(e.target.value)}
              placeholder="e.g. Python, TensorFlow, Docker, Kubernetes"
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-400 focus:border-transparent" />
          </div>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          <button onClick={() => fetchInsights()} disabled={loading || !role.trim()}
            className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-7 py-2.5 rounded-xl font-semibold text-sm disabled:opacity-50 hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md flex items-center gap-2">
            {loading
              ? <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />Analysing...</>
              : <><SearchIcon />Get Market Insights</>}
          </button>
          <span className="text-xs text-gray-400">or try:</span>
          {QUICK_ROLES.slice(0, 4).map(r => (
            <button key={r} onClick={() => { setRole(r); fetchInsights(r); }}
              className="text-xs bg-gray-100 hover:bg-indigo-50 hover:text-indigo-700 text-gray-600 border border-gray-200 hover:border-indigo-300 px-3 py-1.5 rounded-full transition-colors">
              {r}
            </button>
          ))}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-2 text-sm text-red-800">
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {data && (
        <>
          {/* Role trend + hot skills summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {roleEntry && (
              <div className="md:col-span-1">
                <TrendCard keyword={roleEntry[0]} data={roleEntry[1]} isRole />
              </div>
            )}
            <div className="md:col-span-2 bg-white rounded-xl border border-gray-200 p-5">
              <p className="text-sm font-bold text-gray-800 mb-3">🔥 Hot Skills Right Now</p>
              {data.hot_skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {data.hot_skills.map((s, i) => (
                    <span key={i} className="text-sm bg-green-100 text-green-800 border border-green-200 px-3 py-1 rounded-full font-medium">
                      📈 {s}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">No clearly rising skills detected in this period.</p>
              )}
              <p className="text-xs text-gray-400 mt-3">{data.timeframe}</p>
            </div>
          </div>

          {/* Skill trend cards */}
          {skillEntries.length > 0 && (
            <div>
              <h3 className="font-bold text-gray-900 mb-3">📊 Skill Trend Breakdown</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {skillEntries.map(([kw, d]) => (
                  <TrendCard key={kw} keyword={kw} data={d} />
                ))}
              </div>
            </div>
          )}

          {/* AI Analysis */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              🤖 AI Market Analysis
              <span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                Powered by Groq
              </span>
            </h3>
            <div className="prose prose-sm max-w-none text-gray-700">
              {data.analysis.split('\n').map((line, i) => {
                if (line.startsWith('- ') || line.startsWith('• ')) {
                  return (
                    <div key={i} className="flex items-start gap-2 mb-1">
                      <span className="text-indigo-500 mt-0.5 flex-shrink-0">→</span>
                      <span>{line.replace(/^[-•]\s*/, '')}</span>
                    </div>
                  );
                }
                return line.trim()
                  ? <p key={i} className="mb-3">{line}</p>
                  : null;
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default MarketInsights;