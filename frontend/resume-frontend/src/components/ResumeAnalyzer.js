import { useState } from "react";
import API_BASE_URL from '../config';

const Ico = ({ d, className = "w-4 h-4" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const I = {
  score:  "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  check:  "M5 13l4 4L19 7",
  alert:  "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  tag:    "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z",
  bulb:   "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  user:   "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
  jd:     "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
  flag:   "M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9",
  money:  "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  note:   "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
  stage:  "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4",
  q:      "M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
};

const inp = "w-full px-4 py-2.5 text-sm rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none transition";

// ── Score ring ─────────────────────────────────────────────────────────────────
const ScoreRing = ({ score, label, size = 88 }) => {
  const r = (size - 12) / 2;
  const circ = 2 * Math.PI * r;
  const v = score ?? 0;
  const color = v >= 75 ? "#10b981" : v >= 50 ? "#f59e0b" : "#ef4444";
  return (
    <div className="flex flex-col items-center gap-1.5">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={7} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={7}
          strokeDasharray={`${(v/100)*circ} ${circ-(v/100)*circ}`} strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`} style={{ transition: "stroke-dasharray 0.8s ease" }} />
        <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" fontSize="18" fontWeight="700" fill={color}>{score ?? "—"}</text>
      </svg>
      <span className="text-xs text-slate-400 text-center leading-tight">{label}</span>
    </div>
  );
};

const VerdictBadge = ({ verdict }) => {
  const map = {
    Excellent:    "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    Good:         "bg-blue-500/15 text-blue-400 border-blue-500/30",
    "Needs Work": "bg-amber-500/15 text-amber-400 border-amber-500/30",
    Poor:         "bg-red-500/15 text-red-400 border-red-500/30",
  };
  return <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${map[verdict] || map["Needs Work"]}`}>{verdict}</span>;
};

const ATSPanel = ({ result }) => (
  <div className="space-y-5 pt-1">
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
      <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
        <div>
          <VerdictBadge verdict={result.ats_verdict} />
          <p className="text-xs text-slate-400 mt-2">{result.verdict_reason}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-8 justify-center">
        <ScoreRing score={result.overall_score} label="Overall ATS" />
        <ScoreRing score={result.keyword_score}  label="Keywords" />
        <ScoreRing score={result.format_score}   label="Format" />
        <ScoreRing score={result.bullet_quality?.score} label="Bullets" />
      </div>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
        <div className="flex items-center gap-2 mb-3">
          <Ico d={I.alert} className="w-4 h-4 text-red-400" />
          <h3 className="text-sm font-semibold text-white">Missing Keywords</h3>
          <span className="ml-auto text-xs bg-red-500/15 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-full">{result.missing_keywords?.length ?? 0}</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {result.missing_keywords?.map((kw, i) => (
            <span key={i} className="text-xs bg-red-500/10 border border-red-500/20 text-red-300 px-2.5 py-1 rounded-full">{kw}</span>
          ))}
          {!result.missing_keywords?.length && <p className="text-xs text-slate-500">None missing ✓</p>}
        </div>
      </div>
      <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
        <div className="flex items-center gap-2 mb-3">
          <Ico d={I.check} className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white">Found Keywords</h3>
          <span className="ml-auto text-xs bg-emerald-500/15 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full">{result.found_keywords?.length ?? 0}</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {result.found_keywords?.slice(0,12).map((kw, i) => (
            <span key={i} className="text-xs bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded-full">{kw}</span>
          ))}
          {!result.found_keywords?.length && <p className="text-xs text-slate-500">No keywords detected yet</p>}
        </div>
      </div>
    </div>

    {result.improvements?.length > 0 && (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Ico d={I.bulb} className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-white">Improvement Suggestions</h3>
        </div>
        <div className="space-y-2">
          {result.improvements.map((tip, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-amber-500/5 border border-amber-500/10">
              <span className="flex-shrink-0 w-5 h-5 bg-amber-500/20 text-amber-400 rounded-full flex items-center justify-center text-xs font-bold">{i+1}</span>
              <p className="text-sm text-slate-300">{tip}</p>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
);

const VERDICT_CFG = {
  "Strong Yes":{ bg:"bg-emerald-500/10",text:"text-emerald-400",border:"border-emerald-500/30",dot:"bg-emerald-400" },
  "Yes":        { bg:"bg-teal-500/10",  text:"text-teal-400",  border:"border-teal-500/30",  dot:"bg-teal-400" },
  "Maybe":      { bg:"bg-amber-500/10", text:"text-amber-400", border:"border-amber-500/30", dot:"bg-amber-400" },
  "No":         { bg:"bg-orange-500/10",text:"text-orange-400",border:"border-orange-500/30",dot:"bg-orange-400" },
  "Strong No":  { bg:"bg-red-500/10",   text:"text-red-400",   border:"border-red-500/30",   dot:"bg-red-400" },
};
const DIM = { technical_fit:"Technical Fit",experience_relevance:"Experience",culture_fit:"Culture Fit",growth_potential:"Growth",communication_clarity:"Communication" };
const COMPANY_TYPES = [
  { value:"startup",    label:"🚀 Startup" },
  { value:"mid-size",   label:"🏢 Mid-size" },
  { value:"enterprise", label:"🏦 Enterprise" },
  { value:"faang",      label:"⭐ FAANG" },
];
const FOCUS_AREAS = ["general","technical","behavioural","compensation"];

const DimBar = ({ label, score }) => {
  const color = score>=8?"#10b981":score>=6?"#14b8a6":score>=4?"#f59e0b":"#ef4444";
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-slate-400">{label}</span>
        <span className="text-xs font-bold" style={{color}}>{score}/10</span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width:`${(score/10)*100}%`, background:color }} />
      </div>
    </div>
  );
};

const normalisePanel = (raw) => {
  if (!raw || typeof raw !== "object") return null;
  const valid = new Set(["Strong Yes","Yes","Maybe","No","Strong No"]);
  const dimRaw = raw.dimension_scores && typeof raw.dimension_scores==="object" ? raw.dimension_scores : {};
  const dimension_scores = {
    technical_fit: Number(dimRaw.technical_fit)||5, experience_relevance:Number(dimRaw.experience_relevance)||5,
    culture_fit:   Number(dimRaw.culture_fit)||5,   growth_potential:    Number(dimRaw.growth_potential)||5,
    communication_clarity:Number(dimRaw.communication_clarity)||5,
  };
  return {
    hire_verdict: valid.has(raw.hire_verdict)?raw.hire_verdict:"Maybe",
    verdict_summary: raw.verdict_summary||"Reviewed by AI recruiter.",
    verdict_confidence: Number(raw.verdict_confidence)||60,
    dimension_scores,
    green_flags:   Array.isArray(raw.green_flags)?raw.green_flags:[],
    red_flags:     Array.isArray(raw.red_flags)?raw.red_flags:[],
    questions_to_ask: Array.isArray(raw.questions_to_ask)
      ? raw.questions_to_ask.map(q=>typeof q==="string"?{question:q,type:"behavioural",reason:""}:q).filter(q=>q?.question) : [],
    salary_bracket_inr: raw.salary_bracket_inr||null,
    suggested_interview_rounds: Array.isArray(raw.suggested_interview_rounds)?raw.suggested_interview_rounds:[],
    recruiter_notes: raw.recruiter_notes||null,
  };
};

const HRPanel = ({ panel:rawPanel, companyType, focusArea, setCompanyType, setFocusArea, onRun, loading }) => {
  const panel  = normalisePanel(rawPanel);
  const vc     = VERDICT_CFG[panel?.hire_verdict] || VERDICT_CFG["Maybe"];
  if (!panel) return (
    <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6 text-center">
      <p className="text-sm text-amber-400 mb-3">HR panel data unavailable — try re-running.</p>
      <button onClick={onRun} disabled={loading}
        className="bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold px-4 py-2 rounded-xl disabled:opacity-40 transition">
        {loading ? "Running…" : "Re-run Recruiter"}
      </button>
    </div>
  );
  return (
    <div className="space-y-5 pt-1">
      {/* Settings */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Recruiter Settings</p>
        <div className="flex flex-wrap gap-2 mb-3">
          {COMPANY_TYPES.map(c => (
            <button key={c.value} onClick={()=>setCompanyType(c.value)}
              className={`text-xs px-3 py-1.5 rounded-xl border font-medium transition ${companyType===c.value?"border-violet-500/50 bg-violet-500/15 text-violet-300":"border-white/10 text-slate-400 hover:border-white/20"}`}>
              {c.label}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2 mb-4">
          {FOCUS_AREAS.map(f => (
            <button key={f} onClick={()=>setFocusArea(f)}
              className={`text-xs px-3 py-1.5 rounded-full border font-medium capitalize transition ${focusArea===f?"border-violet-500/50 bg-violet-500/15 text-violet-300":"border-white/10 text-slate-400 hover:border-white/20"}`}>
              {f}
            </button>
          ))}
        </div>
        <button onClick={onRun} disabled={loading}
          className="flex items-center gap-1.5 bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold px-4 py-2 rounded-xl disabled:opacity-40 transition">
          {loading ? <><span className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"/>Running…</> : <><Ico d={I.user} className="w-3.5 h-3.5"/>Re-run</>}
        </button>
      </div>

      {/* Verdict hero */}
      <div className={`rounded-2xl border p-6 ${vc.bg} ${vc.border}`}>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${vc.dot} flex-shrink-0 mt-1`} />
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <span className={`text-2xl font-black ${vc.text}`}>{panel.hire_verdict}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${vc.border} ${vc.text} font-medium`}>{panel.verdict_confidence}% confidence</span>
              </div>
              <p className={`text-sm mt-1 ${vc.text} opacity-80`}>{panel.verdict_summary}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Dimension bars */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h3 className="text-sm font-semibold text-white mb-4">Dimension Scores</h3>
        <div className="space-y-3">
          {Object.entries(panel.dimension_scores).map(([k,v])=><DimBar key={k} label={DIM[k]||k} score={v} />)}
        </div>
      </div>

      {/* Flags */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {panel.green_flags.length>0 && (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
            <div className="flex items-center gap-2 mb-3">
              <Ico d={I.check} className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-white">Green Flags</h3>
            </div>
            <div className="space-y-2">
              {panel.green_flags.map((f,i)=>(
                <div key={i} className="flex items-start gap-2 p-2.5 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                  <span className="text-emerald-400 text-xs mt-0.5 flex-shrink-0">✓</span>
                  <p className="text-xs text-slate-300">{f}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        {panel.red_flags.length>0 && (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
            <div className="flex items-center gap-2 mb-3">
              <Ico d={I.flag} className="w-4 h-4 text-red-400" />
              <h3 className="text-sm font-semibold text-white">Red Flags</h3>
            </div>
            <div className="space-y-2">
              {panel.red_flags.map((f,i)=>(
                <div key={i} className="flex items-start gap-2 p-2.5 rounded-xl bg-red-500/5 border border-red-500/10">
                  <Ico d={I.alert} className="w-3.5 h-3.5 text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-slate-300">{f}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {panel.questions_to_ask.length>0 && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Recruiter Questions</h3>
          <div className="space-y-2">
            {panel.questions_to_ask.map((item, i) => {
              const typeColors = {technical:"bg-blue-500/15 text-blue-400",behavioural:"bg-violet-500/15 text-violet-400",situational:"bg-teal-500/15 text-teal-400"};
              return (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl border border-white/5 bg-white/3">
                  <span className="flex-shrink-0 w-5 h-5 bg-white/10 text-slate-400 rounded-full flex items-center justify-center text-xs font-bold">{i+1}</span>
                  <div className="flex-1">
                    <p className="text-sm text-slate-200">{item.question}</p>
                    <span className={`mt-1.5 inline-flex text-xs px-2 py-0.5 rounded-full font-medium ${typeColors[item.type]||"bg-white/10 text-slate-400"}`}>{item.type}</span>
                    {item.reason && <p className="text-xs text-slate-500 mt-1 italic">{item.reason}</p>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {(panel.salary_bracket_inr || panel.suggested_interview_rounds.length>0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {panel.salary_bracket_inr && (
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <Ico d={I.money} className="w-4 h-4 text-emerald-400 mb-2" />
              <p className="text-xl font-black text-emerald-400">{panel.salary_bracket_inr}</p>
              <p className="text-xs text-slate-500 mt-0.5">Estimated salary bracket</p>
            </div>
          )}
          {panel.suggested_interview_rounds.length>0 && (
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <Ico d={I.stage} className="w-4 h-4 text-violet-400 mb-2" />
              <div className="flex flex-wrap gap-2 mt-2">
                {panel.suggested_interview_rounds.map((r,i)=>(
                  <div key={i} className="flex items-center gap-1.5 bg-violet-500/10 border border-violet-500/20 px-3 py-1.5 rounded-full">
                    <span className="w-4 h-4 bg-violet-600/60 text-white rounded-full text-xs flex items-center justify-center font-medium">{i+1}</span>
                    <span className="text-xs text-violet-300">{r}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {panel.recruiter_notes && (
        <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-5">
          <div className="flex items-center gap-2 mb-2">
            <Ico d={I.note} className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-white">Recruiter's Internal Notes</h3>
            <span className="text-xs text-amber-400 bg-amber-500/15 px-2 py-0.5 rounded-full border border-amber-500/20">candid</span>
          </div>
          <p className="text-sm text-slate-300 italic">"{panel.recruiter_notes}"</p>
        </div>
      )}
    </div>
  );
};

export default function ResumeAnalyzer({ resumeText }) {
  const [targetRole,    setTargetRole]    = useState("");
  const [jobDescription,setJobDescription]= useState("");
  const [showJD,        setShowJD]        = useState(false);
  const [companyType,   setCompanyType]   = useState("startup");
  const [focusArea,     setFocusArea]     = useState("general");
  const [atsResult,     setAtsResult]     = useState(null);
  const [hrPanel,       setHrPanel]       = useState(null);
  const [atsLoading,    setAtsLoading]    = useState(false);
  const [hrLoading,     setHrLoading]     = useState(false);
  const [atsError,      setAtsError]      = useState(null);
  const [hrError,       setHrError]       = useState(null);
  const [activeResult,  setActiveResult]  = useState(null);

  const validate = () => {
    if (!resumeText?.trim()) return "Upload your resume first.";
    if (!targetRole.trim())  return "Enter a target role.";
    return null;
  };

  const runATS = async () => {
    const err = validate(); if (err) { setAtsError(err); return; }
    setAtsError(null); setAtsLoading(true); setAtsResult(null);
    try {
      // /ats/score is the alias exposed in main.py → /resume/ats/score
      const r = await fetch(`${API_BASE_URL}/ats/score`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ resume_text:resumeText, target_role:targetRole.trim(), job_description:jobDescription.trim()||null }),
      });
      if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail||`HTTP ${r.status}`);
      const data = await r.json();
      setAtsResult(data.result); setActiveResult("ats");
    } catch(e) { setAtsError(e.message); } finally { setAtsLoading(false); }
  };

  const runHR = async () => {
    const err = validate(); if (err) { setHrError(err); return; }
    setHrError(null); setHrLoading(true); setHrPanel(null);
    try {
      const r = await fetch(`${API_BASE_URL}/interview/hr-panel`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ resume_text:resumeText, target_role:targetRole.trim(), company_type:companyType, focus_area:focusArea }),
      });
      if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail||`HTTP ${r.status}`);
      const data = await r.json();
      setHrPanel(data.panel); setActiveResult("hr");
    } catch(e) { setHrError(e.message); } finally { setHrLoading(false); }
  };

  const runBoth = async () => {
    const err = validate(); if (err) { setAtsError(err); setHrError(err); return; }
    setAtsError(null); setHrError(null); setAtsLoading(true); setHrLoading(true);
    setAtsResult(null); setHrPanel(null);
    try {
      const r = await fetch(`${API_BASE_URL}/resume/analyze`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ resume_text:resumeText, target_role:targetRole.trim(), job_description:jobDescription.trim()||null, company_type:companyType, focus_area:focusArea }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail||`HTTP ${r.status}`);
      if (data.ats_result) { setAtsResult(data.ats_result); setActiveResult("ats"); } else if (data.ats_error) setAtsError(data.ats_error);
      if (data.hr_panel) { setHrPanel(data.hr_panel); if (!data.ats_result) setActiveResult("hr"); } else if (data.hr_error) setHrError(data.hr_error);
    } catch(e) { setAtsError(e.message); setHrError(e.message); }
    finally { setAtsLoading(false); setHrLoading(false); }
  };

  const hasAny = atsResult || hrPanel;
  const isLoading = atsLoading || hrLoading;

  return (
    <div className="space-y-5">
      {/* Input card */}
      <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-xl bg-violet-500/20 flex items-center justify-center">
            <Ico d={I.score} className="w-4 h-4 text-violet-400" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Resume Analyzer</h2>
            <p className="text-xs text-slate-400">ATS scoring + AI HR recruiter simulation</p>
          </div>
        </div>

        {atsError && <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-3 text-sm text-red-400"><Ico d={I.alert} className="w-4 h-4 flex-shrink-0 mt-0.5"/><span><b>ATS:</b> {atsError}</span></div>}
        {hrError  && <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4 text-sm text-red-400"><Ico d={I.alert} className="w-4 h-4 flex-shrink-0 mt-0.5"/><span><b>HR:</b> {hrError}</span></div>}

        <div className="mb-4">
          <label className="block text-xs font-medium text-slate-400 mb-1.5">Target Role <span className="text-red-400">*</span></label>
          <input value={targetRole} onChange={e=>setTargetRole(e.target.value)} onKeyDown={e=>e.key==="Enter"&&runATS()}
            placeholder="e.g. Software Engineer, Data Scientist" className={inp} />
        </div>

        <div className="mb-5">
          <button onClick={()=>setShowJD(v=>!v)}
            className={`flex items-center gap-2 text-sm px-4 py-2 rounded-xl border transition ${showJD?"bg-violet-500/10 border-violet-500/30 text-violet-300":"border-white/10 text-slate-400 hover:border-white/20"}`}>
            <Ico d={I.jd} className="w-4 h-4" />
            {showJD ? "Hide Job Description" : "Paste Job Description (improves accuracy)"}
            {jobDescription.trim()&&!showJD&&<span className="text-xs bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">JD loaded</span>}
          </button>
          {showJD && (
            <textarea value={jobDescription} onChange={e=>setJobDescription(e.target.value)} rows={5}
              placeholder="Paste the full job description here…"
              className={inp + " mt-3 resize-none font-mono text-xs"} />
          )}
        </div>

        {!resumeText && <p className="text-xs text-amber-400 mb-4 flex items-center gap-1"><Ico d={I.alert} className="w-3.5 h-3.5"/>Upload your resume first</p>}

        <div className="flex flex-wrap gap-2.5">
          <button onClick={runATS} disabled={isLoading||!resumeText}
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold px-5 py-2.5 rounded-xl disabled:opacity-40 transition">
            {atsLoading?<><span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white"/>Scoring…</>:<><Ico d={I.score} className="w-4 h-4"/>ATS Score</>}
          </button>
          <button onClick={runHR} disabled={isLoading||!resumeText}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-5 py-2.5 rounded-xl disabled:opacity-40 transition">
            {hrLoading?<><span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white"/>Simulating…</>:<><Ico d={I.user} className="w-4 h-4"/>HR Recruiter</>}
          </button>
          <button onClick={runBoth} disabled={isLoading||!resumeText}
            className="bg-white/10 hover:bg-white/15 text-white text-sm font-semibold px-5 py-2.5 rounded-xl disabled:opacity-40 transition border border-white/10">
            {isLoading?"Running both…":"Run Both"}
          </button>
          {hasAny&&!isLoading&&(
            <button onClick={()=>{setAtsResult(null);setHrPanel(null);setActiveResult(null);}}
              className="text-sm text-slate-400 border border-white/10 px-4 py-2.5 rounded-xl hover:bg-white/5 transition">Clear</button>
          )}
        </div>
      </div>

      {/* Loading */}
      {isLoading&&!hasAny&&(
        <div className="rounded-2xl border border-white/10 bg-white/5 p-12 text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-violet-500 mx-auto mb-4" />
          <p className="text-sm text-slate-400">{atsLoading&&hrLoading?"Running ATS + HR in parallel…":atsLoading?"Analyzing resume…":"Simulating HR recruiter…"}</p>
        </div>
      )}

      {/* Results */}
      {hasAny&&(
        <div>
          {atsResult&&hrPanel&&(
            <div className="flex gap-1 mb-3 p-1 bg-white/5 border border-white/10 rounded-2xl">
              {[{key:"ats",label:"ATS Score",score:atsResult.overall_score},{key:"hr",label:"HR Recruiter",score:null}].map(({key,label,score})=>(
                <button key={key} onClick={()=>setActiveResult(key)}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-xl text-sm font-medium transition ${activeResult===key?"bg-white/10 text-white shadow-sm":"text-slate-400 hover:text-white"}`}>
                  {label}
                  {score!=null&&<span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${score>=75?"bg-emerald-500/20 text-emerald-400":score>=50?"bg-amber-500/20 text-amber-400":"bg-red-500/20 text-red-400"}`}>{score}</span>}
                  {key==="hr"&&hrPanel?.hire_verdict&&<span className="text-xs bg-violet-500/20 text-violet-400 px-1.5 py-0.5 rounded-full font-bold">{hrPanel.hire_verdict}</span>}
                </button>
              ))}
            </div>
          )}
          {activeResult==="ats"&&atsResult&&<ATSPanel result={atsResult} />}
          {activeResult==="hr"&&hrPanel&&(
            <HRPanel panel={hrPanel} companyType={companyType} focusArea={focusArea}
              setCompanyType={setCompanyType} setFocusArea={setFocusArea} onRun={runHR} loading={hrLoading} />
          )}
        </div>
      )}
    </div>
  );
}