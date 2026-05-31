import { useState, useEffect } from "react";
import API_BASE_URL from '../config';

const Ico = ({ d, className = "w-4 h-4" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const I = {
  check:  "M5 13l4 4L19 7",
  arrow:  "M13 7l5 5m0 0l-5 5m5-5H6",
  spark:  "M13 10V3L4 14h7v7l9-11h-7z",
  alert:  "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
};

const FEATURES = [
  { key:"jobs",      icon:"💼", title:"Job Matching",      desc:"Match your resume against live job listings ranked by fit.",    badge:"Live",    color:"violet" },
  { key:"analyzer",  icon:"📄", title:"ATS Analyzer",      desc:"Score your resume for ATS compatibility + HR recruiter sim.", badge:"ATS",     color:"blue"   },
  { key:"rewriter",  icon:"✍️",  title:"Resume Rewriter",   desc:"AI-rewrites with stronger verbs, quantified wins, ATS format.",badge:"AI",      color:"indigo" },
  { key:"learning",  icon:"🗺️", title:"Learning Path",     desc:"Week-by-week plan from your skill gaps with real resources.",  badge:"Guided",  color:"emerald"},
  { key:"interview", icon:"🎤", title:"Interview Coach",   desc:"Live camera mock interviews with real-time AI feedback.",      badge:"AI Coach",color:"cyan"   },
  { key:"coach",     icon:"🤖", title:"Career Coach",      desc:"Chat with Genie about salary, transitions, and strategy.",    badge:"Chat",    color:"amber"  },
  { key:"mentors",   icon:"👥", title:"Expert Mentors",    desc:"Book sessions with pros matched to your skill gaps.",          badge:"Book",    color:"teal"   },
  { key:"insights",  icon:"📈", title:"Market Insights",   desc:"Real-time demand trends for roles and skills.",               badge:"Trends",  color:"rose"   },
  { key:"employer",  icon:"📢", title:"Post a Job",        desc:"Employers: post to our live board — candidates see it now.", badge:"Employer",color:"orange" },
];

const COLOR_MAP = {
  violet:  { bg: "bg-violet-500/15",  border: "border-violet-500/20",  text: "text-violet-400",  hover: "hover:border-violet-500/40" },
  blue:    { bg: "bg-blue-500/15",    border: "border-blue-500/20",    text: "text-blue-400",    hover: "hover:border-blue-500/40" },
  indigo:  { bg: "bg-indigo-500/15",  border: "border-indigo-500/20",  text: "text-indigo-400",  hover: "hover:border-indigo-500/40" },
  emerald: { bg: "bg-emerald-500/15", border: "border-emerald-500/20", text: "text-emerald-400", hover: "hover:border-emerald-500/40" },
  cyan:    { bg: "bg-cyan-500/15",    border: "border-cyan-500/20",    text: "text-cyan-400",    hover: "hover:border-cyan-500/40" },
  amber:   { bg: "bg-amber-500/15",   border: "border-amber-500/20",   text: "text-amber-400",   hover: "hover:border-amber-500/40" },
  teal:    { bg: "bg-teal-500/15",    border: "border-teal-500/20",    text: "text-teal-400",    hover: "hover:border-teal-500/40" },
  rose:    { bg: "bg-rose-500/15",    border: "border-rose-500/20",    text: "text-rose-400",    hover: "hover:border-rose-500/40" },
  orange:  { bg: "bg-orange-500/15",  border: "border-orange-500/20",  text: "text-orange-400",  hover: "hover:border-orange-500/40" },
};

export default function HomePage({ resumeText, careerAdvice, onNavigate }) {
  const [apiStatus, setApiStatus] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then(r => r.json())
      .then(d => setApiStatus(d.status === "healthy" ? "online" : "degraded"))
      .catch(() => setApiStatus("offline"));
  }, []);

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="rounded-2xl border border-white/8 p-8 relative overflow-hidden"
        style={{ background: "linear-gradient(135deg, rgba(124,58,237,0.12) 0%, rgba(37,99,235,0.08) 100%)" }}>
        <div className="absolute top-0 right-0 w-64 h-64 opacity-5"
          style={{ background: "radial-gradient(circle, #7c3aed, transparent)", borderRadius: "50%", transform: "translate(30%,-30%)" }} />

        <div className="relative">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
              style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)" }}>🧞</div>
            <div>
              <h1 className="text-2xl font-black text-white" style={{ fontFamily: "'Syne', sans-serif" }}>
                Career Genie AI
              </h1>
              <p className="text-xs text-slate-500">Your AI-powered career intelligence platform</p>
            </div>
            <div className="ml-auto flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${apiStatus === "online" ? "bg-emerald-400" : apiStatus === "offline" ? "bg-red-400" : "bg-amber-400"} animate-pulse`} />
              <span className="text-xs text-slate-500 capitalize">{apiStatus || "connecting…"}</span>
            </div>
          </div>

          <p className="text-sm text-slate-300 leading-relaxed max-w-2xl mb-6">
            From resume parsing to AI mock interviews, job matching, and personalised learning paths —
            everything you need to accelerate your career in one platform.
          </p>

          {resumeText ? (
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <Ico d={I.check} className="w-4 h-4 text-emerald-400" />
                <span className="text-sm text-emerald-400 font-medium">Resume loaded · {(resumeText.length/1000).toFixed(1)}k chars</span>
              </div>
              <button onClick={() => onNavigate("jobs")}
                className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold px-5 py-2 rounded-xl transition-all">
                Find Jobs <Ico d={I.arrow} className="w-4 h-4" />
              </button>
              <button onClick={() => onNavigate("analyzer")}
                className="text-sm text-slate-400 border border-white/10 px-4 py-2 rounded-xl hover:border-white/20 hover:text-white transition">
                Analyze Resume
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <Ico d={I.alert} className="w-4 h-4 text-amber-400" />
                <span className="text-sm text-amber-400 font-medium">Upload your resume from the sidebar to get started</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Career advice snapshot */}
      {careerAdvice && (
        <div className="rounded-2xl border border-violet-500/20 p-5"
          style={{ background: "rgba(124,58,237,0.06)" }}>
          <p className="text-xs font-medium text-violet-400 uppercase tracking-widest mb-3">Your Career Snapshot</p>
          {careerAdvice.current_assessment && (
            <p className="text-sm text-slate-300 leading-relaxed mb-4 border-l-2 border-violet-500 pl-4">
              {careerAdvice.current_assessment}
            </p>
          )}
          {careerAdvice.skill_gaps?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <p className="text-xs text-slate-500 w-full mb-1">Skill gaps to address:</p>
              {careerAdvice.skill_gaps.map((g, i) => (
                <span key={i} className="text-xs bg-red-500/10 border border-red-500/20 text-red-300 px-2.5 py-1 rounded-full">
                  {g.skill || g}
                </span>
              ))}
              <button onClick={() => onNavigate("learning")}
                className="text-xs text-violet-300 border border-violet-500/30 px-3 py-1 rounded-full hover:bg-violet-500/10 transition">
                Generate Learning Path →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Feature grid */}
      <div>
        <p className="text-xs font-medium text-slate-600 uppercase tracking-widest mb-4">All Features</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {FEATURES.map(f => {
            const c = COLOR_MAP[f.color] || COLOR_MAP.violet;
            return (
              <button key={f.key} onClick={() => onNavigate(f.key)}
                className={`text-left p-4 rounded-2xl border border-white/8 bg-white/3 transition-all group ${c.hover}`}>
                <div className="flex items-start justify-between mb-3">
                  <div className={`w-8 h-8 rounded-xl ${c.bg} ${c.border} border flex items-center justify-center text-base`}>
                    {f.icon}
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${c.bg} ${c.border} ${c.text} font-medium`}>
                    {f.badge}
                  </span>
                </div>
                <p className="text-sm font-semibold text-white mb-1 group-hover:text-white">{f.title}</p>
                <p className="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "AI Tools",      value: "12+",  color: "violet" },
          { label: "Job Sources",   value: "Live", color: "emerald" },
          { label: "Agent Systems", value: "2",    color: "blue" },
          { label: "LLM Providers", value: "4+",   color: "amber" },
        ].map(({ label, value, color }) => {
          const c = COLOR_MAP[color] || COLOR_MAP.violet;
          return (
            <div key={label} className={`rounded-2xl border ${c.border} ${c.bg} p-4 text-center`}>
              <p className={`text-2xl font-black ${c.text}`} style={{ fontFamily: "'Syne', sans-serif" }}>{value}</p>
              <p className="text-xs text-slate-500 mt-1">{label}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}