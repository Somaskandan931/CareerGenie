import React, { useState } from "react";

const API_BASE_URL = "http://localhost:8000";

// ─── Mock sample profiles for demo ───────────────────────────────────────────
const SAMPLE_PROFILES = [
  { id: "S001", name: "Arjun Kumar",     target_role: "EV Technician",              text: "ITI pass in electrician trade. Basic knowledge of battery systems and high voltage safety. Familiar with EV charging and some BMS concepts. Completed 6-month apprenticeship at TATA Motors Chennai." },
  { id: "S002", name: "Priya Lakshmi",   target_role: "CNC Operator",               text: "Diploma in Mechanical Engineering. Proficient in CNC machine operation, G-code and M-code programming. Experience with FANUC CNC controller. Knowledge of quality inspection and 5S lean manufacturing." },
  { id: "S003", name: "Ravi Shankar",    target_role: "EV Technician",              text: "ITI electrician 2nd year. Basic electrical knowledge. No EV-specific training yet. Interested in electric vehicles." },
  { id: "S004", name: "Meena Devi",      target_role: "Automation / PLC Engineer",  text: "Diploma in EEE. Completed PLC programming course with Siemens S7-300. Experience in SCADA systems and HMI. Familiar with industrial automation and robotic systems at Hyundai plant." },
  { id: "S005", name: "Karthik Raja",    target_role: "Battery Pack Assembler",     text: "10th pass. Completed welding course — MIG and spot welding certified. Basic safety training. No EV background but willing to learn battery assembly." },
  { id: "S006", name: "Divya S",         target_role: "Quality Inspector (Automotive)", text: "Diploma in Production Engineering. Knowledge of quality control, IATF 16949 standards, FMEA, SPC and PPAP documentation. Used CMM equipment. 5S and Kaizen practitioner." },
  { id: "S007", name: "Suresh M",        target_role: "EV Technician",              text: "ITI fitter trade. Completed Naan Mudhalvan EV module. Trained in BMS, EV charging infrastructure, and HV safety protocols. Hands-on with battery management systems at TNSDC lab." },
  { id: "S008", name: "Anitha R",        target_role: "Automation / PLC Engineer",  text: "B.E. in Instrumentation. Good knowledge of PLC, hydraulics and pneumatics. Some exposure to IoT and Industry 4.0 concepts. Intern at L&T Chennai for 6 months." },
  { id: "S009", name: "Venkat P",        target_role: "CNC Operator",               text: "ITI turner. Basic lathe operation. No CNC training yet. Interested in machining." },
  { id: "S010", name: "Kavitha N",       target_role: "Embedded Systems Engineer",  text: "B.E. CSE. Proficient in Embedded C and microcontroller programming (STM32, Arduino). Knowledge of CAN bus protocols and automotive communication. Project on BMS firmware at college." },
];

// ─── Icons ────────────────────────────────────────────────────────────────────
const ChartIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);
const UsersIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);
const AlertIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);
const CheckIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

// ─── NSQF Badge ───────────────────────────────────────────────────────────────
const NSQF_COLORS = {
  1: "bg-gray-100 text-gray-700 border-gray-300",
  2: "bg-blue-50 text-blue-700 border-blue-300",
  3: "bg-cyan-50 text-cyan-700 border-cyan-300",
  4: "bg-green-50 text-green-700 border-green-300",
  5: "bg-yellow-50 text-yellow-700 border-yellow-300",
  6: "bg-orange-50 text-orange-700 border-orange-300",
  7: "bg-red-50 text-red-700 border-red-300",
};

const NSQFBadge = ({ level }) => (
  <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${NSQF_COLORS[level] || NSQF_COLORS[1]}`}>
    NSQF {level}
  </span>
);

// ─── Horizontal bar ───────────────────────────────────────────────────────────
const HBar = ({ label, count, total, color = "bg-red-500", sublabel = "" }) => {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs text-gray-600 mb-0.5">
        <span className="font-medium truncate max-w-xs">{label}</span>
        <span className="ml-2 font-bold flex-shrink-0">{count} ({pct}%)</span>
      </div>
      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      {sublabel && <p className="text-xs text-gray-400 mt-0.5">{sublabel}</p>}
    </div>
  );
};

// ─── Stat card ────────────────────────────────────────────────────────────────
const StatCard = ({ label, value, sub, gradient }) => (
  <div className={`rounded-2xl p-5 text-white ${gradient}`}>
    <p className="text-sm opacity-80 mb-1">{label}</p>
    <p className="text-3xl font-black">{value}</p>
    {sub && <p className="text-xs opacity-70 mt-1">{sub}</p>}
  </div>
);

// ─── Individual student row ───────────────────────────────────────────────────
const StudentRow = ({ result }) => {
  const [open, setOpen] = useState(false);
  const ra = result.role_analysis;
  const matchPct = ra?.overall_match_pct ?? null;
  const matchColor = matchPct === null ? "text-gray-400"
    : matchPct >= 70 ? "text-green-600"
    : matchPct >= 40 ? "text-yellow-600"
    : "text-red-600";

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden mb-2">
      <div
        className="flex items-center gap-3 px-4 py-3 bg-white hover:bg-gray-50 cursor-pointer"
        onClick={() => setOpen(o => !o)}
      >
        <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
          {result.name.charAt(0)}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900 text-sm">{result.name}</p>
          <p className="text-xs text-gray-500">{ra?.role ?? "No role specified"} · {ra?.cluster ?? ""}</p>
        </div>
        <NSQFBadge level={result.peak_nsqf} />
        <div className="text-right flex-shrink-0">
          {matchPct !== null ? (
            <p className={`text-sm font-bold ${matchColor}`}>{matchPct}% ready</p>
          ) : (
            <p className="text-xs text-gray-400">—</p>
          )}
          <p className="text-xs text-gray-400">{result.skills_found} skills</p>
        </div>
        <svg className={`w-4 h-4 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {open && ra && (
        <div className="px-4 pb-4 pt-2 bg-gray-50 border-t border-gray-100 space-y-3">
          {/* NSQF Gap */}
          {ra.nsqf_gap > 0 && (
            <div className="flex items-center gap-2 text-xs bg-orange-50 border border-orange-200 rounded-lg px-3 py-2">
              <AlertIcon />
              <span className="text-orange-800">
                NSQF gap: currently <strong>{ra.nsqf_current_label}</strong>, needs <strong>{ra.nsqf_target_label}</strong>
              </span>
            </div>
          )}
          {ra.nsqf_gap === 0 && (
            <div className="flex items-center gap-2 text-xs bg-green-50 border border-green-200 rounded-lg px-3 py-2">
              <CheckIcon />
              <span className="text-green-800">NSQF level meets role requirement ({ra.nsqf_target_label})</span>
            </div>
          )}

          {/* Matched skills */}
          {ra.matched_required.length > 0 && (
            <div>
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">✅ Has Required Skills</p>
              <div className="flex flex-wrap gap-1">
                {ra.matched_required.map((s, i) => (
                  <span key={i} className="text-xs bg-green-100 text-green-800 border border-green-200 px-2 py-0.5 rounded-full">{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Gaps */}
          {ra.skill_gaps.length > 0 && (
            <div>
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">⚠️ Skill Gaps & Training</p>
              <div className="space-y-1.5">
                {ra.skill_gaps.map((g, i) => (
                  <div key={i} className={`rounded-lg px-3 py-2 text-xs ${g.gap_severity === "critical" ? "bg-red-50 border border-red-200" : "bg-orange-50 border border-orange-200"}`}>
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="font-semibold text-gray-800">{g.skill}</span>
                      <NSQFBadge level={g.nsqf_level_needed} />
                    </div>
                    <p className="text-gray-600">Train at: {g.training_recommendations.slice(0, 2).join(" · ")}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Main Dashboard ───────────────────────────────────────────────────────────
const TNAnalyticsDashboard = () => {
  const [institutionName, setInstitutionName] = useState("Government ITI Chennai – Auto & EV Batch 2025");
  const [profilesJson, setProfilesJson] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState("overview"); // overview | students | gaps

  const runDemoAnalysis = async () => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await fetch(`${API_BASE_URL}/tn/batch-analytics`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          institution_name: institutionName,
          profiles: SAMPLE_PROFILES,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      setData(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const runCustomAnalysis = async () => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      let profiles;
      try {
        profiles = JSON.parse(profilesJson);
        if (!Array.isArray(profiles)) throw new Error("JSON must be an array");
      } catch {
        throw new Error("Invalid JSON. Must be an array of {id, name, text, target_role?}");
      }
      const res = await fetch(`${API_BASE_URL}/tn/batch-analytics`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          institution_name: institutionName,
          profiles
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      setData(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const summary = data?.cohort_summary;
  const individuals = data?.individual_results || [];

  // NSQF distribution bar data
  const nsqfDist = summary?.nsqf_distribution || {};
  const nsqfTotal = Object.values(nsqfDist).reduce((a, b) => a + b, 0);
  const nsqfColors = ["bg-gray-400","bg-blue-400","bg-cyan-400","bg-green-500","bg-yellow-500","bg-orange-500","bg-red-500"];

  // Readiness buckets from individual results
  const readinessBuckets = { high: 0, medium: 0, low: 0, unassigned: 0 };
  individuals.forEach(r => {
    const pct = r.role_analysis?.overall_match_pct;
    if (pct == null) readinessBuckets.unassigned++;
    else if (pct >= 70) readinessBuckets.high++;
    else if (pct >= 40) readinessBuckets.medium++;
    else readinessBuckets.low++;
  });

  return (
    <div className="bg-gray-50 min-h-screen p-6">
      {/* ── Header ── */}
      <div className="max-w-6xl mx-auto">
        <div className="bg-gradient-to-r from-orange-600 via-red-600 to-pink-600 rounded-2xl p-8 text-white mb-8 shadow-xl">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-3xl">🏭</span>
                <div>
                  <h1 className="text-2xl font-black">TN AUTO SkillBridge</h1>
                  <p className="text-red-200 text-sm">Workforce Analytics · Tamil Nadu Automotive & EV Ecosystem</p>
                </div>
              </div>
              <p className="text-red-100 text-sm max-w-xl">
                Institutional dashboard for training officers · ITI / Polytechnic cohort analysis ·
                NSQF-mapped skill gap reports · Naan Mudhalvan aligned
              </p>
            </div>
            <div className="flex flex-wrap gap-2 text-xs">
              {["TN AUTO Skills", "Naan Mudhalvan", "TNSDC", "NSQF Aligned"].map(tag => (
                <span key={tag} className="bg-white/20 backdrop-blur px-3 py-1 rounded-full font-medium">{tag}</span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Input Panel ── */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <UsersIcon /> Batch Profile Analysis
          </h2>

          <div className="mb-4">
            <label className="block text-sm font-semibold text-gray-700 mb-1">Institution / Batch Name</label>
            <input
              type="text"
              value={institutionName}
              onChange={e => setInstitutionName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-400 text-sm"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Custom Profiles JSON
              <span className="ml-2 font-normal text-gray-400 text-xs">
                (optional — leave blank to run a demo with 10 sample ITI/polytechnic profiles)
              </span>
            </label>
            <textarea
              rows={5}
              value={profilesJson}
              onChange={e => setProfilesJson(e.target.value)}
              placeholder={`[\n  {"id":"S001","name":"Arjun K","target_role":"EV Technician","text":"ITI electrician. BMS training. HV safety certified..."},\n  ...\n]`}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 text-xs font-mono focus:ring-2 focus:ring-orange-400"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4 text-sm text-red-800 flex items-start gap-2">
              <AlertIcon />{error}
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            <button
              onClick={profilesJson.trim() ? runCustomAnalysis : runDemoAnalysis}
              disabled={loading}
              className="bg-gradient-to-r from-orange-600 to-red-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-orange-700 hover:to-red-700 disabled:opacity-50 transition-all shadow-md flex items-center gap-2"
            >
              {loading ? (
                <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />Analyzing...</>
              ) : (
                <><ChartIcon />{profilesJson.trim() ? "Analyze Batch" : "Run Demo (10 Students)"}</>
              )}
            </button>
            {data && (
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
                  const a = document.createElement("a");
                  a.href = URL.createObjectURL(blob);
                  a.download = `${institutionName.replace(/\s+/g, "_")}_skill_report.json`;
                  a.click();
                }}
                className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors text-sm"
              >
                ⬇ Download Report
              </button>
            )}
          </div>
        </div>

        {/* ── Results ── */}
        {data && (
          <>
            {/* Stat cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard label="Students Analyzed" value={data.total_profiles}
                sub={data.institution} gradient="bg-gradient-to-br from-indigo-600 to-purple-600" />
              <StatCard label="Avg Skills / Student" value={summary.avg_skills_per_person}
                sub="TN automotive skills" gradient="bg-gradient-to-br from-blue-500 to-cyan-500" />
              <StatCard label="Job-Ready (≥70%)" value={readinessBuckets.high}
                sub={`${Math.round(readinessBuckets.high / data.total_profiles * 100)}% of cohort`}
                gradient="bg-gradient-to-br from-green-500 to-emerald-600" />
              <StatCard label="Need Upskilling" value={readinessBuckets.low + readinessBuckets.medium}
                sub="Below 70% role readiness"
                gradient="bg-gradient-to-br from-orange-500 to-red-500" />
            </div>

            {/* Readiness funnel */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {[
                { label: "Job-Ready (≥70%)", count: readinessBuckets.high, color: "bg-green-500", badge: "bg-green-100 text-green-800" },
                { label: "Needs Short Course (40–69%)", count: readinessBuckets.medium, color: "bg-yellow-400", badge: "bg-yellow-100 text-yellow-800" },
                { label: "Needs Full Training (<40%)", count: readinessBuckets.low, color: "bg-red-500", badge: "bg-red-100 text-red-800" },
              ].map(b => (
                <div key={b.label} className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-gray-700 font-medium">{b.label}</p>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${b.badge}`}>{b.count}</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full">
                    <div className={`h-full ${b.color} rounded-full`}
                      style={{ width: `${Math.round(b.count / data.total_profiles * 100)}%` }} />
                  </div>
                  <p className="text-xs text-gray-400 mt-1">{Math.round(b.count / data.total_profiles * 100)}% of batch</p>
                </div>
              ))}
            </div>

            {/* Tabs */}
            <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-6 w-fit">
              {[
                { key: "overview", label: "📊 Overview" },
                { key: "gaps", label: "⚠️ Skill Gaps" },
                { key: "students", label: "👤 Per Student" },
              ].map(t => (
                <button key={t.key} onClick={() => setActiveTab(t.key)}
                  className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${activeTab === t.key ? "bg-white shadow text-gray-900" : "text-gray-500 hover:text-gray-700"}`}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* ── Overview tab ── */}
            {activeTab === "overview" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* NSQF Distribution */}
                <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                  <h3 className="font-bold text-gray-900 mb-4">🎓 NSQF Level Distribution</h3>
                  {[1,2,3,4,5,6,7].map(lvl => (
                    nsqfDist[lvl] > 0 && (
                      <HBar key={lvl}
                        label={`NSQF ${lvl} — ${["","Basic awareness","Semi-skilled","Skilled (ITI)","Technician","Diploma Tech","Jr. Engineer","Sr. Engineer"][lvl]}`}
                        count={nsqfDist[lvl]} total={nsqfTotal}
                        color={nsqfColors[lvl - 1]}
                      />
                    )
                  ))}
                </div>

                {/* Role Readiness */}
                {Object.keys(summary.avg_role_readiness).length > 0 && (
                  <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                    <h3 className="font-bold text-gray-900 mb-4">🏭 Avg Role Readiness by Target Role</h3>
                    {Object.entries(summary.avg_role_readiness).map(([role, pct]) => (
                      <HBar key={role} label={role} count={pct} total={100}
                        color={pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-yellow-400" : "bg-red-500"}
                        sublabel={`${pct}% average readiness`} />
                    ))}
                  </div>
                )}

                {/* Top skills present */}
                <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                  <h3 className="font-bold text-gray-900 mb-4">✅ Top Skills Present in Cohort</h3>
                  {summary.top_skills_present.map((s, i) => (
                    <HBar key={i} label={s.skill} count={s.count} total={data.total_profiles}
                      color="bg-indigo-500" />
                  ))}
                  {summary.top_skills_present.length === 0 && (
                    <p className="text-sm text-gray-400">No skills detected across profiles.</p>
                  )}
                </div>

                {/* Recommended courses */}
                <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                  <h3 className="font-bold text-gray-900 mb-4">📚 Recommended Courses to Run</h3>
                  <p className="text-xs text-gray-500 mb-3">
                    Based on most common gaps across this batch:
                  </p>
                  {summary.top_skill_gaps.slice(0, 6).map((g, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <div>
                        <p className="text-sm font-medium text-gray-800">{g.skill}</p>
                        <p className="text-xs text-red-600">{g.count} students missing ({g.pct}%)</p>
                      </div>
                      <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-bold">Priority {i + 1}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── Gaps tab ── */}
            {activeTab === "gaps" && (
              <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                <h3 className="font-bold text-gray-900 mb-2">⚠️ Cohort Skill Gap Heatmap</h3>
                <p className="text-sm text-gray-500 mb-5">
                  Skills missing across the batch, sorted by frequency. Use this to plan training programs.
                </p>
                <div className="space-y-3">
                  {summary.top_skill_gaps.map((g, i) => (
                    <div key={i} className="flex items-center gap-4">
                      <div className="w-6 text-center text-xs font-bold text-gray-400">{i + 1}</div>
                      <div className="flex-1">
                        <div className="flex justify-between text-sm mb-0.5">
                          <span className="font-semibold text-gray-800">{g.skill}</span>
                          <span className={`font-bold ${g.pct >= 70 ? "text-red-600" : g.pct >= 40 ? "text-orange-500" : "text-yellow-600"}`}>
                            {g.count}/{data.total_profiles} ({g.pct}%)
                          </span>
                        </div>
                        <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${g.pct >= 70 ? "bg-red-500" : g.pct >= 40 ? "bg-orange-400" : "bg-yellow-400"}`}
                            style={{ width: `${g.pct}%` }}
                          />
                        </div>
                      </div>
                      <span className={`flex-shrink-0 text-xs font-bold px-2 py-1 rounded-full ${
                        g.pct >= 70 ? "bg-red-100 text-red-700" :
                        g.pct >= 40 ? "bg-orange-100 text-orange-700" :
                        "bg-yellow-100 text-yellow-700"
                      }`}>
                        {g.pct >= 70 ? "Critical" : g.pct >= 40 ? "High" : "Moderate"}
                      </span>
                    </div>
                  ))}
                </div>

                {summary.top_skill_gaps.length === 0 && (
                  <p className="text-gray-400 text-sm">No gaps detected — all students have all required skills!</p>
                )}

                {/* Action box */}
                {summary.top_skill_gaps.length > 0 && (
                  <div className="mt-8 bg-orange-50 border border-orange-200 rounded-xl p-5">
                    <h4 className="font-bold text-orange-900 mb-2">💡 Recommended Training Action Plan</h4>
                    <ol className="space-y-1 text-sm text-orange-800">
                      {summary.top_skill_gaps.slice(0, 3).map((g, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="font-bold flex-shrink-0">{i + 1}.</span>
                          Run a short-course on <strong>{g.skill}</strong> — impacts {g.count} students ({g.pct}% of batch)
                        </li>
                      ))}
                      <li className="flex items-start gap-2">
                        <span className="font-bold flex-shrink-0">{Math.min(4, summary.top_skill_gaps.length + 1)}.</span>
                        Contact TNSDC / Naan Mudhalvan for module availability and scheduling.
                      </li>
                    </ol>
                  </div>
                )}
              </div>
            )}

            {/* ── Per-student tab ── */}
            {activeTab === "students" && (
              <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
                <h3 className="font-bold text-gray-900 mb-4">👤 Individual Student Breakdown</h3>
                <p className="text-xs text-gray-500 mb-4">
                  Click on a student to see their skill gaps, NSQF readiness, and training recommendations.
                </p>
                {individuals.map((r, i) => (
                  <StudentRow key={i} result={r} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TNAnalyticsDashboard;