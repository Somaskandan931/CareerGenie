import { useState, useEffect, useCallback, createContext } from "react";
import JobSearch from './components/JobSearch';
import JobMatches from './components/JobMatches';
import RoadmapView from './components/Roadmapview';
import ProjectSuggestions from './components/ProjectSuggestions';
import JobCoachChat from './components/JobCoachChat';
import MarketInsights from './components/MarketInsights';
import InterviewCoach from './components/InterviewCoach';
import ProgressDashboard from './components/ProgressDashboard';
import ResumeRewriter from './components/ResumeRewriter';
import MentorSearch from './components/MentorSearch';
import ResumeAnalyzer from './components/ResumeAnalyzer';
import HomePage from './components/HomePage';
import JobPost from './components/JobPost';

export const DarkModeContext = createContext({ dark: true, toggle: () => {} });

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const getOrCreateUserId = () => {
  let id = localStorage.getItem("cg-user-id");
  if (!id) { id = "user_" + Math.random().toString(36).slice(2, 10); localStorage.setItem("cg-user-id", id); }
  return id;
};
const USER_ID = getOrCreateUserId();

// ── Icon helper ───────────────────────────────────────────────────────────────
const Ico = ({ d, className = "w-4 h-4" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);

const ICONS = {
  home:      "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
  jobs:      "M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
  progress:  "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  learning:  "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7",
  interview: "M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z",
  coach:     "M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z",
  insights:  "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6",
  ats:       "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4",
  upload:    "M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12",
  mentor:    "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z",
  rewrite:   "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
  employer:  "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
  check:     "M5 13l4 4L19 7",
  alert:     "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  doc:       "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  bulb:      "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  ext:       "M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14",
  map:       "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7",
  sun:       "M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z",
  moon:      "M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z",
};

// ── Career Advice card (shown after job match) ────────────────────────────────
const CareerAdvice = ({ advice }) => {
  if (!advice) return null;
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 mb-6 space-y-5">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-xl bg-amber-500/20 flex items-center justify-center">
          <Ico d={ICONS.bulb} className="w-4 h-4 text-amber-400" />
        </div>
        <h3 className="text-sm font-semibold text-white">Career Guidance</h3>
      </div>
      {advice.current_assessment && (
        <p className="text-sm text-slate-300 leading-relaxed border-l-2 border-violet-500 pl-4">{advice.current_assessment}</p>
      )}
      {advice.skill_gaps?.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-widest">Skill Gaps</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {advice.skill_gaps.map((g, i) => (
              <div key={i} className="flex items-center justify-between px-3 py-2 rounded-xl bg-red-500/10 border border-red-500/20">
                <span className="text-sm text-slate-200">{g.skill}</span>
                <span className="text-xs text-red-400 font-medium">{g.importance}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {advice.action_plan?.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-widest">Action Plan</p>
          {advice.action_plan.map((a, i) => (
            <div key={i} className="flex items-start gap-3 text-sm text-slate-300">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-violet-600/60 text-white flex items-center justify-center text-xs font-bold mt-0.5">{i+1}</span>
              <span>{a}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Learning path tab ─────────────────────────────────────────────────────────
const LearningPathTab = ({ resumeText, careerAdvice, onImported }) => {
  const [targetRole, setTargetRole] = useState("");
  const [skillGaps, setSkillGaps]   = useState("");
  const [duration, setDuration]     = useState(12);
  const [difficulty, setDifficulty] = useState("intermediate");
  const [roadmap, setRoadmap]       = useState(null);
  const [projects, setProjects]     = useState([]);
  const [loadingR, setLoadingR]     = useState(false);
  const [loadingP, setLoadingP]     = useState(false);
  const [importing, setImporting]   = useState(false);
  const [importOk, setImportOk]     = useState(null);
  const [error, setError]           = useState(null);

  useEffect(() => {
    if (careerAdvice?.skill_gaps?.length && !skillGaps)
      setSkillGaps(careerAdvice.skill_gaps.map(g => g.skill).join(", "));
  }, [careerAdvice, skillGaps]);

  const gaps = () => skillGaps.split(",").map(s => s.trim()).filter(Boolean);

  const genRoadmap = async (retry = 0) => {
    if (!targetRole.trim()) { setError("Enter a target role."); return; }
    setError(null); setLoadingR(true); setRoadmap(null);
    try {
      const r = await fetch(`${API_BASE}/roadmap/generate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText || "", target_role: targetRole.trim(), skill_gaps: gaps(), duration_weeks: duration }),
      });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
      const data = await r.json();
      if (!data.roadmap) {
        if (retry < 2) { setError(`Retrying…(${retry+1}/2)`); setLoadingR(false); setTimeout(() => genRoadmap(retry+1), 1500); return; }
        throw new Error("Roadmap generation failed — try again.");
      }
      setRoadmap(data.roadmap);
    } catch (e) { setError(e.message); } finally { setLoadingR(false); }
  };

  const genProjects = async () => {
    if (!targetRole.trim()) { setError("Enter a target role."); return; }
    setError(null); setLoadingP(true); setProjects([]);
    try {
      const r = await fetch(`${API_BASE}/projects/suggest`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText || "", target_role: targetRole.trim(), skill_gaps: gaps(), difficulty, num_projects: 5 }),
      });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
      setProjects((await r.json()).projects || []);
    } catch (e) { setError(e.message); } finally { setLoadingP(false); }
  };

  const importProgress = async () => {
    if (!roadmap && !projects.length) return;
    setImporting(true); setImportOk(null);
    try {
      const ops = [];
      if (roadmap) ops.push(fetch(`${API_BASE}/progress/roadmap/import`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ user_id: USER_ID, roadmap }),
      }));
      if (projects.length) ops.push(fetch(`${API_BASE}/progress/projects/import`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ user_id: USER_ID, projects }),
      }));
      await Promise.all(ops);
      setImportOk("Imported to Progress Dashboard ✓");
      if (onImported) onImported(roadmap, projects);
    } catch { setImportOk("Import failed — check backend."); }
    finally { setImporting(false); }
  };

  const inp = "w-full px-4 py-2.5 text-sm rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none transition";

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-xl bg-violet-500/20 flex items-center justify-center">
            <Ico d={ICONS.map} className="w-4 h-4 text-violet-400" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Learning Path Generator</h2>
            <p className="text-xs text-slate-400">Personalised roadmap + project suggestions</p>
          </div>
        </div>
        {error && <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4 text-sm text-red-400"><Ico d={ICONS.alert} className="w-4 h-4 flex-shrink-0 mt-0.5" />{error}</div>}
        {importOk && <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 mb-4 text-sm text-emerald-400">{importOk}</div>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Target Role <span className="text-red-400">*</span></label>
            <input value={targetRole} onChange={e => setTargetRole(e.target.value)} placeholder="e.g. ML Engineer, Full Stack Developer" className={inp} />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Skill Gaps <span className="text-slate-500 font-normal">(auto-filled from career advice)</span></label>
            <input value={skillGaps} onChange={e => setSkillGaps(e.target.value)} placeholder="e.g. PyTorch, Kubernetes, Docker" className={inp} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Duration</label>
            <select value={duration} onChange={e => setDuration(Number(e.target.value))} className={inp + " cursor-pointer"}>
              {[4,8,12,16,24].map(w => <option key={w} value={w}>{w} weeks</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Project Difficulty</label>
            <select value={difficulty} onChange={e => setDifficulty(e.target.value)} className={inp + " cursor-pointer"}>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
        </div>
        <div className="flex flex-wrap gap-3 pt-4 border-t border-white/5">
          <button onClick={() => { genRoadmap(0); genProjects(); }} disabled={loadingR || loadingP || !targetRole.trim()}
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold px-5 py-2.5 rounded-xl disabled:opacity-40 transition-all">
            {(loadingR || loadingP) ? <><span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Generating…</> : "Generate Both"}
          </button>
          <button onClick={() => genRoadmap(0)} disabled={loadingR || !targetRole.trim()}
            className="text-sm text-violet-300 border border-violet-500/40 px-4 py-2.5 rounded-xl hover:bg-violet-500/10 disabled:opacity-40 transition">
            {loadingR ? "…" : "Roadmap only"}
          </button>
          <button onClick={genProjects} disabled={loadingP || !targetRole.trim()}
            className="text-sm text-cyan-300 border border-cyan-500/40 px-4 py-2.5 rounded-xl hover:bg-cyan-500/10 disabled:opacity-40 transition">
            {loadingP ? "…" : "Projects only"}
          </button>
        </div>
        {(roadmap || projects.length > 0) && (
          <div className="mt-4 pt-4 border-t border-white/5">
            <button onClick={importProgress} disabled={importing}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold px-5 py-2.5 rounded-xl disabled:opacity-40 transition-all">
              {importing ? <><span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Importing…</> : "→ Import to Progress Dashboard"}
            </button>
          </div>
        )}
      </div>
      {(roadmap || loadingR) && <RoadmapView roadmap={roadmap} loading={loadingR} />}
      {(projects.length > 0 || loadingP) && <ProjectSuggestions projects={projects} loading={loadingP} />}
    </div>
  );
};

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab]                       = useState("home");
  const [resumeText, setResumeText]         = useState("");
  const [uploading, setUploading]           = useState(false);
  const [uploadError, setUploadError]       = useState(null);
  const [jobQuery, setJobQuery]             = useState("");
  const [jobLocation, setJobLocation]       = useState("India");
  const [filters, setFilters]               = useState({});
  const [careerAdvice, setCareerAdvice]     = useState(null);
  const [skillComparison, setSkillComparison] = useState(null);
  const [backendConfig, setBackendConfig]   = useState(null);
  const [dark, setDark]                     = useState(true); // dark by default
  const [importedRoadmap, setImportedRoadmap]   = useState(null);
  const [importedProjects, setImportedProjects] = useState([]);
  const [importKey, setImportKey]               = useState(0);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("cg-theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    fetch(`${API_BASE}/config`).then(r => r.json()).then(setBackendConfig).catch(() => null);
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true); setUploadError(null);
    const fd = new FormData(); fd.append("file", file);
    try {
      // Use the alias URL that our fixed main.py exposes
      const r = await fetch(`${API_BASE}/upload-resume/parse`, { method: "POST", body: fd });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
      const data = await r.json();
      setResumeText(data.resume_text);
    } catch (e) { setUploadError(e.message); setResumeText(""); }
    finally { setUploading(false); if (e.target) e.target.value = ""; }
  };

  const handleSetCareerAdvice = useCallback(a => setCareerAdvice(a), []);

  const resumeSkills = skillComparison?.resume_skills?.map(s => s.skill) || [];

  const NAV_SECTIONS = [
    {
      label: "Main",
      items: [
        { key: "home",      label: "Home",            icon: ICONS.home },
        { key: "jobs",      label: "Job Matches",     icon: ICONS.jobs },
        { key: "progress",  label: "Progress",        icon: ICONS.progress },
        { key: "learning",  label: "Learning Path",   icon: ICONS.learning, badge: careerAdvice?.skill_gaps?.length || null },
        { key: "interview", label: "Interview Prep",  icon: ICONS.interview },
      ],
    },
    {
      label: "Resume",
      items: [
        { key: "analyzer",  label: "ATS Analyzer",   icon: ICONS.ats },
        { key: "rewriter",  label: "Rewriter",       icon: ICONS.rewrite },
        { key: "employer",  label: "Post a Job",     icon: ICONS.employer },
      ],
    },
    {
      label: "AI Tools",
      items: [
        { key: "coach",     label: "Career Coach",   icon: ICONS.coach },
        { key: "mentors",   label: "Expert Mentors", icon: ICONS.mentor },
        { key: "insights",  label: "Market Insights",icon: ICONS.insights },
      ],
    },
  ];

  const PAGE_TITLES = {
    home:"Career Genie",jobs:"Job Matches",progress:"Progress Dashboard",
    learning:"Learning Path",interview:"Interview Coach",analyzer:"ATS Analyzer",
    rewriter:"Resume Rewriter",coach:"Career Coach",mentors:"Expert Mentors",
    insights:"Market Insights",employer:"Post a Job",
  };

  const showUploadPrompt = !["progress","mentors","home","employer"].includes(tab);

  const NavItem = ({ item }) => (
    <button onClick={() => setTab(item.key)}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
        tab === item.key
          ? "bg-violet-600/20 text-violet-300 border border-violet-500/30 font-medium"
          : "text-slate-400 hover:text-white hover:bg-white/5"
      }`}>
      <Ico d={item.icon} className="w-4 h-4 flex-shrink-0" />
      <span className="truncate">{item.label}</span>
      {item.badge ? (
        <span className="ml-auto bg-violet-600 text-white text-xs font-bold px-1.5 py-0.5 rounded-full leading-none">{item.badge}</span>
      ) : null}
    </button>
  );

  return (
    <DarkModeContext.Provider value={{ dark, toggle: () => setDark(d => !d) }}>
      {/* Google Fonts */}
      <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet" />
      <style>{`
        * { font-family: 'DM Sans', sans-serif; }
        h1, h2, h3, .syne { font-family: 'Syne', sans-serif; }
        :root { color-scheme: dark; }
        body { background: #080c14; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.3); border-radius: 2px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(139,92,246,0.5); }
        .bg-base { background: #080c14; }
        .bg-surface { background: rgba(255,255,255,0.04); }
        .bg-surface-2 { background: rgba(255,255,255,0.07); }
        .border-subtle { border-color: rgba(255,255,255,0.07); }
      `}</style>

      <div className="flex h-screen overflow-hidden bg-base">

        {/* ── Sidebar ── */}
        <aside className="w-56 flex-shrink-0 flex flex-col border-r border-subtle"
          style={{ background: "rgba(8,12,20,0.95)", backdropFilter: "blur(20px)" }}>

          {/* Brand */}
          <div className="px-4 py-5 border-b border-subtle">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)" }}>
                <span className="text-white text-xs font-black syne">G</span>
              </div>
              <div>
                <p className="text-sm font-bold text-white syne leading-none">Career Genie</p>
                <p className="text-xs text-slate-500 mt-0.5">AI Career OS</p>
              </div>
            </div>
          </div>

          {/* Nav */}
          <nav className="flex-1 px-2 py-4 overflow-y-auto space-y-5">
            {NAV_SECTIONS.map(sec => (
              <div key={sec.label}>
                <p className="text-xs font-semibold text-slate-600 uppercase tracking-widest px-3 mb-1.5">{sec.label}</p>
                <div className="space-y-0.5">{sec.items.map(item => <NavItem key={item.key} item={item} />)}</div>
              </div>
            ))}
          </nav>

          {/* Resume status */}
          <div className="p-2 border-t border-subtle">
            {resumeText ? (
              <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                  <Ico d={ICONS.check} className="w-3 h-3 text-emerald-400" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-emerald-400">Resume loaded</p>
                  <p className="text-xs text-emerald-600">{(resumeText.length/1000).toFixed(1)}k chars</p>
                </div>
              </div>
            ) : (
              <label className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl border border-dashed border-white/10 cursor-pointer hover:border-violet-500/40 hover:bg-violet-500/5 transition-all group">
                <Ico d={ICONS.upload} className="w-4 h-4 text-slate-500 group-hover:text-violet-400 transition-colors" />
                <span className="text-xs text-slate-500 group-hover:text-slate-300 transition-colors">
                  {uploading ? "Uploading…" : "Upload resume"}
                </span>
                <input type="file" accept=".pdf,.doc,.docx" onChange={handleFileUpload} disabled={uploading} className="hidden" />
              </label>
            )}
            {uploadError && <p className="text-xs text-red-400 px-2 mt-1.5 truncate">{uploadError}</p>}
          </div>
        </aside>

        {/* ── Content ── */}
        <div className="flex-1 flex flex-col overflow-hidden">

          {/* Topbar */}
          <header className="h-13 flex-shrink-0 flex items-center justify-between px-6 py-3 border-b border-subtle"
            style={{ background: "rgba(8,12,20,0.8)", backdropFilter: "blur(20px)" }}>
            <h1 className="text-sm font-bold text-white syne">{PAGE_TITLES[tab]}</h1>
            <div className="flex items-center gap-3">
              {backendConfig && (!backendConfig.groq_key_present && !backendConfig.ollama_available) && (
                <span className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-lg">
                  ⚠ No LLM available
                </span>
              )}
              <button onClick={() => setDark(d => !d)}
                className="w-8 h-8 rounded-lg border border-white/10 flex items-center justify-center text-slate-400 hover:text-white hover:border-white/20 transition-all">
                <Ico d={dark ? ICONS.sun : ICONS.moon} className="w-3.5 h-3.5" />
              </button>
            </div>
          </header>

          {/* Scroll area */}
          <main className="flex-1 overflow-y-auto" style={{ background: "#080c14" }}>
            <div className="max-w-5xl mx-auto px-6 py-6 space-y-6">

              {/* Resume upload prompt */}
              {showUploadPrompt && !resumeText && (
                <div className="rounded-2xl border border-dashed border-white/10 bg-white/3 p-8 text-center">
                  <div className="w-12 h-12 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center mx-auto mb-4">
                    <Ico d={ICONS.doc} className="w-6 h-6 text-violet-400" />
                  </div>
                  <h2 className="text-sm font-semibold text-white mb-1 syne">Upload your resume to get started</h2>
                  <p className="text-xs text-slate-500 mb-5">PDF or DOCX · Max 10 MB · Needed for personalised AI analysis</p>
                  <label className="inline-flex items-center gap-2 px-5 py-2.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold rounded-xl cursor-pointer transition-all">
                    <Ico d={ICONS.upload} className="w-4 h-4" />
                    {uploading ? "Uploading…" : "Choose File"}
                    <input type="file" accept=".pdf,.doc,.docx" onChange={handleFileUpload} disabled={uploading} className="hidden" />
                  </label>
                  {uploading && <div className="mt-4 animate-spin rounded-full h-6 w-6 border-b-2 border-violet-500 mx-auto" />}
                  {uploadError && <p className="mt-3 text-xs text-red-400">{uploadError}</p>}
                </div>
              )}

              {/* ── Pages ── */}
              {tab === "home" && (
                <HomePage resumeText={resumeText} careerAdvice={careerAdvice} onNavigate={setTab} />
              )}

              {tab === "jobs" && (
                <>
                  <JobSearch setJobQuery={setJobQuery} setJobLocation={setJobLocation} setFilters={setFilters} />
                  <JobMatches
                    jobQuery={jobQuery} jobLocation={jobLocation} resumeText={resumeText}
                    filters={filters} setCareerAdvice={handleSetCareerAdvice}
                    setSkillComparison={setSkillComparison} userId={USER_ID}
                  />
                  <CareerAdvice advice={careerAdvice} />
                  {careerAdvice && (
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                      {careerAdvice.skill_gaps?.length > 0 && (
                        <button onClick={() => setTab("learning")} className="text-left p-4 rounded-2xl border border-white/10 bg-white/5 hover:border-violet-500/40 hover:bg-violet-500/5 transition-all">
                          <p className="text-xs text-slate-400 mb-1">Skill gaps</p>
                          <p className="text-2xl font-bold text-violet-400 syne">{careerAdvice.skill_gaps.length}</p>
                          <p className="text-xs text-slate-500 mt-1">Generate roadmap →</p>
                        </button>
                      )}
                      {[
                        { key:"progress", label:"Progress", sub:"Track your journey", color:"emerald" },
                        { key:"coach",    label:"Career Coach", sub:"Chat with Genie",  color:"amber" },
                        { key:"interview",label:"Mock Interview", sub:"Practice now",    color:"cyan" },
                      ].map(({ key, label, sub, color }) => (
                        <button key={key} onClick={() => setTab(key)} className={`text-left p-4 rounded-2xl border border-white/10 bg-white/5 hover:border-${color}-500/40 hover:bg-${color}-500/5 transition-all`}>
                          <p className="text-xs text-slate-400 mb-1">{label}</p>
                          <p className="text-sm font-semibold text-white">{sub}</p>
                          <p className="text-xs text-slate-500 mt-1">→</p>
                        </button>
                      ))}
                    </div>
                  )}
                </>
              )}

              {tab === "learning" && (
                <LearningPathTab resumeText={resumeText} careerAdvice={careerAdvice}
                  onImported={(rm, prj) => { setImportedRoadmap(rm); setImportedProjects(prj); setImportKey(k => k+1); }} />
              )}

              {tab === "progress" && (
                <ProgressDashboard key={importKey} importedRoadmap={importedRoadmap} importedProjects={importedProjects} />
              )}

              {tab === "coach" && (
                <div className="space-y-4">
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                    <h2 className="text-base font-semibold text-white syne mb-1">Career Coach & Counsellor</h2>
                    <p className="text-sm text-slate-400">Ask Genie anything about your career.{resumeText && " Resume loaded for personalised advice."}</p>
                  </div>
                  <JobCoachChat resumeText={resumeText} userId={USER_ID} />
                </div>
              )}

              {tab === "mentors"   && <MentorSearch userId={USER_ID} userSkills={resumeSkills} />}
              {tab === "insights"  && <MarketInsights resumeSkills={resumeSkills} />}
              {tab === "interview" && <InterviewCoach resumeText={resumeText} />}
              {tab === "analyzer"  && <ResumeAnalyzer resumeText={resumeText} />}
              {tab === "rewriter"  && <ResumeRewriter resumeText={resumeText} />}
              {tab === "employer"  && <JobPost />}

            </div>
          </main>

          {/* Footer */}
          <div className="h-8 flex-shrink-0 flex items-center justify-center border-t border-subtle"
            style={{ background: "rgba(8,12,20,0.8)" }}>
            <p className="text-xs text-slate-600">Career Genie · AI-powered career intelligence</p>
          </div>
        </div>
      </div>
    </DarkModeContext.Provider>
  );
}