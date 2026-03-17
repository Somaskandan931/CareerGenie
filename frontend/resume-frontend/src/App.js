import { useState, useEffect } from "react";

import JobSearch from './components/JobSearch';
import JobMatches from './components/JobMatches';
import SkillAssessmentDashboard from './components/SkillAssessmentDashboard';
import RoadmapView from './components/Roadmapview';
import ProjectSuggestions from './components/ProjectSuggestions';
import TNAnalyticsDashboard from './components/TNAnalyticsDashboard';
import JobCoachChat from './components/JobCoachChat';
import MarketInsights from './components/MarketInsights';
import InterviewCoach from './components/InterviewCoach';

const API_BASE_URL = 'http://localhost:8000';

// ─── Shared icons ─────────────────────────────────────────────────────────────
const Icon = ({ d, size = "h-4 w-4" }) => (
  <svg className={size} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={d} />
  </svg>
);
const BriefcaseIcon = ({ size }) => <Icon size={size} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6" />;
const MapIcon = ({ size }) => <Icon size={size} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />;
const FactoryIcon = ({ size }) => <Icon size={size} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />;
const BotIcon = ({ size }) => <Icon size={size} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17H3a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-2" />;
const TrendIcon = ({ size }) => <Icon size={size} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />;
const MicIcon = ({ size }) => <Icon size={size} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />;
const AlertIcon = () => <Icon d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />;
const CheckIcon = () => <Icon d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />;
const ExternalLinkIcon = () => <Icon d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />;
const LightBulbIcon = () => <Icon d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />;
const BookIcon = () => <Icon d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />;
const TrendUpIcon = () => <Icon d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />;

// ─── Career Advice ────────────────────────────────────────────────────────────
const CareerAdvice = ({ careerAdvice }) => {
  if (!careerAdvice) return null;
  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      <div className="flex items-center mb-6">
        <div className="bg-purple-600 p-2 rounded-lg mr-3"><LightBulbIcon /></div>
        <h2 className="text-2xl font-bold text-gray-900">Career Guidance</h2>
      </div>
      {careerAdvice.current_assessment && (
        <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
          <h3 className="font-semibold text-blue-900 mb-2">📊 Current Assessment</h3>
          <p className="text-blue-800 text-sm">{careerAdvice.current_assessment}</p>
        </div>
      )}
      {careerAdvice.skill_gaps?.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 mb-3">⚠️ Critical Skill Gaps ({careerAdvice.skill_gaps.length})</h3>
          <div className="space-y-2">
            {careerAdvice.skill_gaps.map((gap, i) => (
              <div key={i} className="p-3 bg-red-50 border border-red-200 rounded-lg flex justify-between items-start">
                <div>
                  <p className="font-medium text-red-900">{gap.skill}</p>
                  <p className="text-xs text-red-700 mt-1">Current: {gap.current_level} → Target: {gap.target_level}</p>
                </div>
                <span className="text-xs bg-red-200 text-red-800 px-2 py-1 rounded-full">{gap.importance}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {careerAdvice.learning_path?.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2"><BookIcon />Recommended Resources</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {careerAdvice.learning_path.map((r, i) => (
              <div key={i} className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start justify-between">
                <div className="flex-1">
                  <p className="font-medium text-green-900">{r.title}</p>
                  <div className="flex gap-2 mt-2 text-xs flex-wrap">
                    <span className="bg-green-200 text-green-800 px-2 py-0.5 rounded">{r.type}</span>
                    <span className="bg-gray-200 text-gray-800 px-2 py-0.5 rounded">{r.duration}</span>
                    <span className="bg-blue-200 text-blue-800 px-2 py-0.5 rounded">{r.difficulty}</span>
                  </div>
                </div>
                {r.url && <a href={r.url} target="_blank" rel="noopener noreferrer" className="ml-2 text-green-600"><ExternalLinkIcon /></a>}
              </div>
            ))}
          </div>
        </div>
      )}
      {careerAdvice.action_plan?.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 mb-3">🎯 Action Plan</h3>
          <div className="space-y-2">
            {careerAdvice.action_plan.map((a, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">{i+1}</span>
                <p className="text-sm text-gray-700">{a}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {careerAdvice.market_insights && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h3 className="font-semibold text-yellow-900 mb-2">📈 Market Insights</h3>
          <p className="text-yellow-800 text-sm">{careerAdvice.market_insights}</p>
        </div>
      )}
    </div>
  );
};

// ─── Learning Path Tab ────────────────────────────────────────────────────────
const LearningPathTab = ({ resumeText, careerAdvice }) => {
  const [targetRole, setTargetRole] = useState("");
  const [skillGaps, setSkillGaps] = useState("");
  const [durationWeeks, setDurationWeeks] = useState(12);
  const [difficulty, setDifficulty] = useState("intermediate");
  const [experienceLevel, setExperienceLevel] = useState("");
  const [roadmap, setRoadmap] = useState(null);
  const [projects, setProjects] = useState([]);
  const [loadingRoadmap, setLoadingRoadmap] = useState(false);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (careerAdvice?.skill_gaps?.length > 0 && !skillGaps)
      setSkillGaps(careerAdvice.skill_gaps.map(g => g.skill).join(", "));
  }, [careerAdvice]);

  const parseGaps = () => skillGaps.split(",").map(s => s.trim()).filter(Boolean);

  const genRoadmap = async () => {
    if (!targetRole.trim()) { setError("Enter a target role."); return; }
    setError(null); setLoadingRoadmap(true); setRoadmap(null);
    try {
      const res = await fetch(`${API_BASE_URL}/generate/roadmap`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText || "", target_role: targetRole.trim(),
                               skill_gaps: parseGaps(), duration_weeks: durationWeeks, experience_level: experienceLevel || null }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      setRoadmap((await res.json()).roadmap);
    } catch (e) { setError(e.message); } finally { setLoadingRoadmap(false); }
  };

  const genProjects = async () => {
    if (!targetRole.trim()) { setError("Enter a target role."); return; }
    setError(null); setLoadingProjects(true); setProjects([]);
    try {
      const res = await fetch(`${API_BASE_URL}/generate/projects`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText || "", target_role: targetRole.trim(),
                               skill_gaps: parseGaps(), difficulty, num_projects: 5 }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      setProjects((await res.json()).projects || []);
    } catch (e) { setError(e.message); } finally { setLoadingProjects(false); }
  };

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="flex items-center mb-5">
          <div className="bg-indigo-600 p-2 rounded-lg mr-3"><MapIcon size="h-6 w-6 text-white" /></div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Learning Path Generator</h2>
            <p className="text-sm text-gray-500">Personalised roadmap + project suggestions powered by Groq</p>
          </div>
        </div>
        {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-5 flex items-start gap-2"><AlertIcon /><p className="text-red-800 text-sm">{error}</p></div>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
          <div className="md:col-span-2">
            <label className="block text-sm font-semibold text-gray-700 mb-1">Target Role <span className="text-red-500">*</span></label>
            <input type="text" value={targetRole} onChange={e => setTargetRole(e.target.value)}
              placeholder="e.g. EV Technician, ML Engineer, Full Stack Developer"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Skill Gaps <span className="text-xs font-normal text-gray-400">(auto-filled from career advice)</span>
            </label>
            <input type="text" value={skillGaps} onChange={e => setSkillGaps(e.target.value)}
              placeholder="e.g. PyTorch, Kubernetes, BMS, CAN Bus"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Duration</label>
            <select value={durationWeeks} onChange={e => setDurationWeeks(Number(e.target.value))}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
              {[4,8,12,16,24].map(w => <option key={w} value={w}>{w} weeks</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Experience Level</label>
            <select value={experienceLevel} onChange={e => setExperienceLevel(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
              <option value="">Not specified</option>
              <option value="entry">Entry Level</option>
              <option value="mid">Mid Level</option>
              <option value="senior">Senior Level</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Project Difficulty</label>
            <select value={difficulty} onChange={e => setDifficulty(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <button onClick={() => { genRoadmap(); genProjects(); }} disabled={loadingRoadmap || loadingProjects || !targetRole.trim()}
            className="flex-1 md:flex-none bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-8 rounded-lg font-semibold disabled:opacity-50 hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md">
            {(loadingRoadmap || loadingProjects)
              ? <span className="flex items-center gap-2"><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />Generating...</span>
              : "✨ Generate Roadmap + Projects"}
          </button>
          <button onClick={genRoadmap} disabled={loadingRoadmap || !targetRole.trim()}
            className="px-6 py-3 border-2 border-indigo-300 text-indigo-700 rounded-lg hover:bg-indigo-50 disabled:opacity-50 font-medium">
            {loadingRoadmap ? "..." : "🗺️ Roadmap Only"}
          </button>
          <button onClick={genProjects} disabled={loadingProjects || !targetRole.trim()}
            className="px-6 py-3 border-2 border-purple-300 text-purple-700 rounded-lg hover:bg-purple-50 disabled:opacity-50 font-medium">
            {loadingProjects ? "..." : "🛠️ Projects Only"}
          </button>
        </div>
      </div>
      {(roadmap || loadingRoadmap) && <RoadmapView roadmap={roadmap} loading={loadingRoadmap} />}
      {(projects.length > 0 || loadingProjects) && <ProjectSuggestions projects={projects} loading={loadingProjects} />}
    </div>
  );
};

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  // tabs: "jobs" | "learning" | "coach" | "insights" | "interview" | "institution"
  const [activeTab, setActiveTab] = useState("jobs");
  const [resumeText, setResumeText] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [jobQuery, setJobQuery] = useState("");
  const [jobLocation, setJobLocation] = useState("India");
  const [filters, setFilters] = useState({});
  const [careerAdvice, setCareerAdvice] = useState(null);
  const [skillComparison, setSkillComparison] = useState(null);
  const [backendConfig, setBackendConfig] = useState(null);

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

  const resumeSkills = skillComparison?.resume_skills?.map(s => s.skill) || [];

  const TABS = [
    { key: "jobs",        label: "Job Matches",  icon: <BriefcaseIcon />, activeColor: "text-blue-700" },
    { key: "learning",    label: "Learning",     icon: <MapIcon />,        activeColor: "text-indigo-700",
      badge: careerAdvice?.skill_gaps?.length > 0 ? careerAdvice.skill_gaps.length : null },
    { key: "coach",       label: "Job Coach",    icon: <BotIcon />,        activeColor: "text-orange-700" },
    { key: "insights",    label: "Insights",     icon: <TrendIcon />,      activeColor: "text-purple-700" },
    { key: "interview",   label: "Interview",    icon: <MicIcon />,        activeColor: "text-blue-700" },
    { key: "institution", label: "Institution",  icon: <FactoryIcon />,    activeColor: "text-red-700" },
  ];

  // Resume upload is hidden on institution tab
  const showResume = activeTab !== "institution";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ── Header ── */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-r from-blue-600 to-green-600 p-2 rounded-lg">
                <BriefcaseIcon size="h-7 w-7 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                  Career Genie
                </h1>
                <p className="text-xs text-gray-400 hidden sm:block">TN AUTO SkillBridge · Powered by Groq</p>
              </div>
            </div>

            {/* Tab bar */}
            <div className="flex gap-0.5 bg-gray-100 p-1 rounded-xl overflow-x-auto">
              {TABS.map(tab => (
                <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                    activeTab === tab.key ? `bg-white shadow ${tab.activeColor}` : "text-gray-500 hover:text-gray-800"
                  }`}>
                  {tab.icon}
                  <span className="hidden sm:inline">{tab.label}</span>
                  <span className="sm:hidden">{tab.label.split(" ")[0]}</span>
                  {tab.badge && (
                    <span className="bg-indigo-600 text-white text-xs px-1.5 py-0.5 rounded-full leading-none">
                      {tab.badge}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">

        {/* ── Config warning ── */}
        {backendConfig && (!backendConfig.serpapi_key_present || !backendConfig.anthropic_key_present) && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-5 mb-8 rounded-r-lg">
            <h3 className="font-semibold text-yellow-800 mb-1">⚙️ Configuration Required</h3>
            <p className="text-yellow-700 text-sm mb-2">Add these to <code className="bg-yellow-100 px-1 rounded">backend/.env</code>:</p>
            <div className="bg-yellow-100 p-2 rounded text-xs font-mono text-yellow-900">
              {!backendConfig.serpapi_key_present && <p>SERPAPI_KEY=your_key</p>}
              {!backendConfig.anthropic_key_present && <p>GROQ_API_KEY=your_key</p>}
            </div>
          </div>
        )}

        {/* ── Resume upload (hidden on institution tab) ── */}
        {showResume && (
          <div className="bg-white rounded-xl shadow-lg p-7 mb-8">
            <div className="flex items-center mb-5">
              <div className="bg-blue-600 p-2 rounded-lg mr-3">
                <Icon size="h-6 w-6 text-white" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Your Resume</h2>
            </div>

            {uploadError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 flex items-start gap-2">
                <AlertIcon /><div><p className="text-red-800 font-medium text-sm">Upload Error</p><p className="text-red-700 text-xs mt-0.5">{uploadError}</p></div>
              </div>
            )}

            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-400 transition-colors text-center">
              <Icon size="h-10 w-10 text-gray-400 mx-auto mb-3" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              <label htmlFor="resume-upload" className="cursor-pointer">
                <span className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm">
                  <Icon size="h-4 w-4 text-white" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  {uploading ? "Uploading..." : "Upload Resume (PDF / DOCX)"}
                </span>
                <input id="resume-upload" type="file" accept=".pdf,.doc,.docx"
                  onChange={handleFileUpload} disabled={uploading} className="hidden" />
              </label>
              <p className="mt-2 text-xs text-gray-400">PDF or DOCX • Max 10MB</p>
              {uploading && <div className="mt-3 animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto" />}
            </div>

            {resumeText && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 mt-4 flex items-center gap-2">
                <CheckIcon />
                <div>
                  <span className="text-green-800 font-medium text-sm">Resume ready!</span>
                  <p className="text-green-700 text-xs mt-0.5">{resumeText.length} characters</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ══════════════ JOB MATCHES ══════════════ */}
        {activeTab === "jobs" && (
          <>
            <JobSearch setJobQuery={setJobQuery} setJobLocation={setJobLocation} setFilters={setFilters} />
            <SkillAssessmentDashboard
              resumeSkills={skillComparison?.resume_skills || []}
              jobSkills={skillComparison?.job_skills || []}
              comparison={skillComparison} />
            <JobMatches jobQuery={jobQuery} jobLocation={jobLocation} resumeText={resumeText}
              filters={filters} setCareerAdvice={setCareerAdvice} setSkillComparison={setSkillComparison} />
            <CareerAdvice careerAdvice={careerAdvice} />

            {/* CTAs */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              {careerAdvice?.skill_gaps?.length > 0 && (
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-5 text-white">
                  <p className="font-bold">🎯 {careerAdvice.skill_gaps.length} skill gaps found</p>
                  <p className="text-indigo-200 text-xs mt-1 mb-3">Get a personalised learning roadmap</p>
                  <button onClick={() => setActiveTab("learning")}
                    className="bg-white text-indigo-700 text-sm font-semibold px-4 py-2 rounded-lg hover:bg-indigo-50 transition-colors">
                    Generate Roadmap →
                  </button>
                </div>
              )}
              <div className="bg-gradient-to-r from-orange-500 to-red-600 rounded-xl p-5 text-white">
                <p className="font-bold">💬 Career Coach</p>
                <p className="text-orange-100 text-xs mt-1 mb-3">Get personalised career counselling</p>
                <button onClick={() => setActiveTab("coach")}
                  className="bg-white text-orange-700 text-sm font-semibold px-4 py-2 rounded-lg hover:bg-orange-50 transition-colors">
                  Chat with Genie →
                </button>
              </div>
              <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl p-5 text-white">
                <p className="font-bold">🎤 Interview Prep</p>
                <p className="text-blue-200 text-xs mt-1 mb-3">Practice with AI mock interviews</p>
                <button onClick={() => setActiveTab("interview")}
                  className="bg-white text-blue-700 text-sm font-semibold px-4 py-2 rounded-lg hover:bg-blue-50 transition-colors">
                  Start Practice →
                </button>
              </div>
            </div>
          </>
        )}

        {/* ══════════════ LEARNING PATH ══════════════ */}
        {activeTab === "learning" && (
          <LearningPathTab resumeText={resumeText} careerAdvice={careerAdvice} />
        )}

        {/* ══════════════ JOB COACH ══════════════ */}
        {activeTab === "coach" && (
          <div className="space-y-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <h2 className="text-xl font-bold text-gray-900 mb-1">💬 Career Coach & Counsellor</h2>
              <p className="text-sm text-gray-500">
                Ask Genie anything about your career — resume tips, salary negotiation, role transitions, networking, and more.
                {resumeText && " Your resume is loaded for personalised advice."}
              </p>
            </div>
            <JobCoachChat resumeText={resumeText} />
          </div>
        )}

        {/* ══════════════ MARKET INSIGHTS ══════════════ */}
        {activeTab === "insights" && (
          <MarketInsights resumeSkills={resumeSkills} />
        )}

        {/* ══════════════ INTERVIEW COACH ══════════════ */}
        {activeTab === "interview" && (
          <InterviewCoach resumeText={resumeText} />
        )}

        {/* ══════════════ INSTITUTION ══════════════ */}
        {activeTab === "institution" && (
          <TNAnalyticsDashboard />
        )}

      </main>

      <footer className="bg-gray-900 text-white py-6 mt-16">
        <div className="max-w-6xl mx-auto px-4 text-center space-y-1">
          <p className="text-gray-400 text-sm">© 2025 Career Genie · TN AUTO SkillBridge · v3.0</p>
          <p className="text-gray-600 text-xs">
            Powered by Groq · RAG · ChromaDB · pytrends ·
            Aligned with Naan Mudhalvan · TNSDC · NSQF
          </p>
        </div>
      </footer>
    </div>
  );
}