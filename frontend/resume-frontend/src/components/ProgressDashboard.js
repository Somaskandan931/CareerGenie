import React, { useState, useEffect, useCallback } from "react";

import API_BASE_URL from '../config';
const USER_ID = "default_user";

const Icon = ({ d, size = "h-4 w-4", className = "" }) => (
  <svg className={`${size} ${className}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d={d} />
  </svg>
);
const CheckIcon = ({ className = "h-3 w-3" }) => <Icon className={className} d="M5 13l4 4L19 7" />;
const PlusIcon  = () => <Icon d="M12 4v16m8-8H4" />;
const TrashIcon = () => <Icon d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />;
const ChevronIcon = ({ open }) => (
  <svg className={`h-4 w-4 transition-transform duration-200 ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M19 9l-7 7-7-7" />
  </svg>
);
const ExternalIcon = () => <Icon d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />;

const PIPELINE_STAGES = [
  "Applied","OA / Assignment","Technical Round 1","Technical Round 2",
  "System Design","HR Round","Offer","Rejected","Withdrawn",
];
const STAGE_STYLE = {
  "Applied":"bg-blue-50 text-blue-700 border-blue-200",
  "OA / Assignment":"bg-violet-50 text-violet-700 border-violet-200",
  "Technical Round 1":"bg-amber-50 text-amber-700 border-amber-200",
  "Technical Round 2":"bg-amber-50 text-amber-700 border-amber-200",
  "System Design":"bg-pink-50 text-pink-700 border-pink-200",
  "HR Round":"bg-teal-50 text-teal-700 border-teal-200",
  "Offer":"bg-green-50 text-green-700 border-green-200",
  "Rejected":"bg-red-50 text-red-700 border-red-200",
  "Withdrawn":"bg-gray-100 text-gray-500 border-gray-200",
};
const FUNNEL_COLOR = {
  "Applied":"#3B82F6","OA / Assignment":"#8B5CF6","Technical Round 1":"#F59E0B",
  "Technical Round 2":"#F59E0B","System Design":"#EC4899","HR Round":"#14B8A6",
  "Offer":"#22C55E","Rejected":"#EF4444","Withdrawn":"#9CA3AF",
};
const PROJECT_STATUS_COLORS = {
  "Not Started":"bg-gray-100 text-gray-600 border-gray-200",
  "In Progress":"bg-blue-50 text-blue-700 border-blue-200",
  "Testing":"bg-amber-50 text-amber-700 border-amber-200",
  "Deployed":"bg-teal-50 text-teal-700 border-teal-200",
  "Completed":"bg-green-50 text-green-700 border-green-200",
};
const PROJECT_BAR_COLOR = {
  "Not Started":"#9CA3AF","In Progress":"#3B82F6","Testing":"#F59E0B",
  "Deployed":"#14B8A6","Completed":"#22C55E",
};
const TOPIC_COLORS = [
  "#3B82F6","#8B5CF6","#14B8A6","#F59E0B","#EF4444","#22C55E",
  "#EC4899","#6366F1","#0EA5E9","#A78BFA","#34D399","#FB923C",
];

const Card = ({ children, className = "" }) => (
  <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl ${className}`}>
    {children}
  </div>
);

const StatCard = ({ label, value, sub, valueColor = "" }) => (
  <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</p>
    <p className={`text-2xl font-medium ${valueColor || "text-gray-900 dark:text-white"}`}>{value}</p>
    {sub && <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{sub}</p>}
  </div>
);

const ProgressBar = ({ pct, color = "#3B82F6", height = "h-1.5" }) => (
  <div className={`bg-gray-100 dark:bg-gray-700 rounded-full ${height} overflow-hidden`}>
    <div className="h-full rounded-full transition-all duration-500"
      style={{ width: `${Math.min(100, Math.max(0, pct))}%`, background: color }} />
  </div>
);

const SubTabs = ({ tabs, active, onChange }) => (
  <div className="flex gap-0.5 bg-gray-100 dark:bg-gray-700 p-1 rounded-xl mb-5 overflow-x-auto">
    {tabs.map(t => (
      <button key={t.key} onClick={() => onChange(t.key)}
        className={`px-4 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
          active === t.key
            ? "bg-white dark:bg-gray-800 shadow text-gray-900 dark:text-white"
            : "text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
        }`}>
        {t.label}
      </button>
    ))}
  </div>
);

const ActivityHeatmap = ({ activityLog = [] }) => {
  const today = new Date();
  const cells = [];
  for (let i = 181; i >= 0; i--) {
    const d = new Date(today); d.setDate(d.getDate() - i);
    const iso = d.toISOString().split("T")[0];
    const entries = activityLog.filter(e => e.date === iso);
    const count = entries.reduce((s, e) => s + e.count, 0);
    const types = [...new Set(entries.map(e => e.type))];
    cells.push({ date: iso, count, types });
  }
  const getColor = (count, types) => {
    if (!count) return null;
    const t = types[0];
    if (t === "dsa")                return count >= 5 ? "#1D9E75" : count >= 3 ? "#5DCAA5" : "#9FE1CB";
    if (t === "roadmap")            return count >= 3 ? "#2563EB" : "#93C5FD";
    if (t === "project")            return "#8B5CF6";
    if (t?.startsWith("interview")) return "#F59E0B";
    return count >= 5 ? "#1D9E75" : count >= 2 ? "#5DCAA5" : "#9FE1CB";
  };
  const weeks = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));
  return (
    <div>
      <div className="flex gap-1.5 overflow-x-auto pb-1">
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-1 flex-shrink-0">
            {week.map((cell, di) => (
              <div key={di}
                title={`${cell.date}: ${cell.count} activities${cell.types.length ? " (" + cell.types.join(", ") + ")" : ""}`}
                style={{ background: getColor(cell.count, cell.types) || undefined }}
                className={`w-3.5 h-3.5 rounded-sm cursor-default ${!getColor(cell.count, cell.types) ? "bg-gray-200 dark:bg-gray-700" : ""}`} />
            ))}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-4 mt-3 flex-wrap">
        {[["#93C5FD","Roadmap"],["#5DCAA5","DSA"],["#8B5CF6","Projects"],["#F59E0B","Interviews"]].map(([color,label]) => (
          <span key={label} className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500">
            <span className="w-3 h-3 rounded-sm inline-block flex-shrink-0" style={{background:color}} />{label}
          </span>
        ))}
      </div>
    </div>
  );
};

const DSABarChart = ({ dsaData }) => {
  const topics = Object.entries(dsaData || {}).slice(0, 8);
  if (!topics.length) return <p className="text-sm text-gray-400 dark:text-gray-500 py-4">No DSA data yet.</p>;
  return (
    <div className="space-y-2.5">
      {topics.map(([topic, data], i) => {
        const pct = data.total ? Math.round((data.solved / data.total) * 100) : 0;
        return (
          <div key={topic} className="flex items-center gap-3">
            <p className="text-xs text-gray-500 dark:text-gray-400 w-32 flex-shrink-0 truncate">{topic}</p>
            <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
              <div className="h-full rounded-full transition-all duration-500"
                style={{ width: `${pct}%`, background: TOPIC_COLORS[i % TOPIC_COLORS.length] }} />
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500 w-14 text-right flex-shrink-0">{data.solved}/{data.total}</p>
          </div>
        );
      })}
    </div>
  );
};

const FunnelChart = ({ funnel = {}, total = 0 }) => {
  const stages = PIPELINE_STAGES.filter(s => (funnel[s] || 0) > 0);
  if (!stages.length) return <p className="text-sm text-gray-400 dark:text-gray-500 py-4">No applications yet.</p>;
  return (
    <div className="space-y-2">
      {stages.map(stage => {
        const count = funnel[stage] || 0;
        const pct = total ? Math.round((count / total) * 100) : 0;
        const color = FUNNEL_COLOR[stage] || "#6B7280";
        return (
          <div key={stage} className="flex items-center gap-3">
            <p className="text-xs text-gray-500 dark:text-gray-400 w-28 flex-shrink-0 truncate">{stage}</p>
            <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-sm h-5 overflow-hidden">
              <div className="h-full flex items-center px-2 transition-all duration-500"
                style={{ width: `${Math.max(pct, 8)}%`, background: `${color}22`, borderLeft: `2px solid ${color}` }}>
                <span className="text-xs font-medium" style={{ color }}>{count}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

const RoadmapPanel = ({ roadmapData, onTaskToggle }) => {
  const [openWeeks, setOpenWeeks] = useState(new Set());
  const weeks = Object.entries(roadmapData || {});
  if (!weeks.length) return (
    <Card className="p-10 text-center">
      <p className="text-3xl mb-3">🗺️</p>
      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">No roadmap imported yet</p>
      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Go to the Learning tab, generate a roadmap, and it will appear here automatically</p>
    </Card>
  );
  const allTasks = weeks.flatMap(([, t]) => t);
  const done = allTasks.filter(t => t.done).length;
  const pct = allTasks.length ? Math.round((done / allTasks.length) * 100) : 0;
  return (
    <div className="space-y-4">
      <Card className="p-5">
        <div className="flex items-end justify-between mb-3">
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">Overall progress</p>
            <p className="text-2xl font-medium text-gray-900 dark:text-white">{pct}%</p>
          </div>
          <p className="text-sm text-gray-400 dark:text-gray-500">{done} / {allTasks.length} tasks</p>
        </div>
        <ProgressBar pct={pct} color="#6366F1" height="h-2" />
      </Card>
      <div className="space-y-2">
        {weeks.map(([weekKey, tasks]) => {
          const wd = tasks.filter(t => t.done).length;
          const wp = tasks.length ? Math.round((wd / tasks.length) * 100) : 0;
          const isOpen = openWeeks.has(weekKey);
          return (
            <Card key={weekKey} className={`overflow-hidden ${wp === 100 ? "border-green-200 dark:border-green-800" : ""}`}>
              <button className="w-full flex items-center gap-3 px-4 py-3 text-left"
                onClick={() => { const n = new Set(openWeeks); n.has(weekKey) ? n.delete(weekKey) : n.add(weekKey); setOpenWeeks(n); }}>
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 ${wp === 100 ? "bg-green-500 text-white" : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"}`}>
                  {wp === 100 ? <CheckIcon className="h-3.5 w-3.5" /> : <span>{wp}%</span>}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{weekKey}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">{tasks[0]?.phase} · {wd}/{tasks.length} done</p>
                </div>
                <div className="w-20"><ProgressBar pct={wp} color={wp === 100 ? "#22C55E" : "#6366F1"} /></div>
                <ChevronIcon open={isOpen} />
              </button>
              {isOpen && (
                <div className="border-t border-gray-100 dark:border-gray-700 px-4 pb-3 pt-2 space-y-1">
                  {tasks.map(task => (
                    <div key={task.id} className="flex items-start gap-3 py-2">
                      <button onClick={() => onTaskToggle(weekKey, task.id, !task.done)}
                        className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all ${task.done ? "bg-green-500 border-green-500 text-white" : "border-gray-300 dark:border-gray-500 hover:border-green-400"}`}>
                        {task.done && <CheckIcon className="h-2.5 w-2.5" />}
                      </button>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm ${task.done ? "line-through text-gray-400 dark:text-gray-500" : "text-gray-800 dark:text-gray-200"}`}>{task.topic}</p>
                        {task.milestone && <p className="text-xs text-amber-600 dark:text-amber-400 mt-0.5">{task.milestone}</p>}
                      </div>
                      <span className="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0">{task.hours}h/wk</span>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
};

const ProjectsPanel = ({ projects, onUpdateProject }) => {
  if (!projects?.length) return (
    <Card className="p-10 text-center">
      <p className="text-3xl mb-3">🛠️</p>
      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">No projects tracked yet</p>
      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Generate projects in the Learning tab — they sync here automatically</p>
    </Card>
  );
  const sorted = [...projects].sort((a, b) =>
    ["In Progress","Testing","Deployed","Not Started","Completed"].indexOf(a.status) -
    ["In Progress","Testing","Deployed","Not Started","Completed"].indexOf(b.status)
  );
  return (
    <div className="space-y-3">
      {sorted.map(proj => (
        <Card key={proj.id} className="p-5">
          <div className="flex items-start justify-between gap-4 mb-3">
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white">{proj.title}</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{proj.tagline}</p>
            </div>
            <select value={proj.status} onChange={e => onUpdateProject(proj.id, { status: e.target.value })}
              className={`text-xs border rounded-lg px-2 py-1 cursor-pointer outline-none flex-shrink-0 ${PROJECT_STATUS_COLORS[proj.status] || "bg-gray-100 text-gray-600 border-gray-200"}`}>
              {Object.keys(PROJECT_STATUS_COLORS).map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          {proj.tech_stack?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {proj.tech_stack.map((t, i) => <span key={i} className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded-md">{t}</span>)}
            </div>
          )}
          <div className="mb-1">
            <div className="flex justify-between text-xs text-gray-400 dark:text-gray-500 mb-1">
              <span>Progress</span><span>{proj.progress_pct}%</span>
            </div>
            <ProgressBar pct={proj.progress_pct} color={PROJECT_BAR_COLOR[proj.status] || "#9CA3AF"} height="h-2" />
          </div>
          <input type="range" min="0" max="100" value={proj.progress_pct}
            onChange={e => onUpdateProject(proj.id, { progress_pct: Number(e.target.value) })}
            className="w-full accent-indigo-600 cursor-pointer mt-1.5" />
          <div className="flex gap-2 mt-3">
            <input type="text" placeholder="GitHub URL" value={proj.github_url || ""}
              onChange={e => onUpdateProject(proj.id, { github_url: e.target.value })}
              className="flex-1 text-xs border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 focus:ring-1 focus:ring-indigo-300 outline-none" />
            <input type="text" placeholder="Live URL" value={proj.live_url || ""}
              onChange={e => onUpdateProject(proj.id, { live_url: e.target.value })}
              className="flex-1 text-xs border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 focus:ring-1 focus:ring-indigo-300 outline-none" />
            {proj.github_url && (
              <a href={proj.github_url} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex-shrink-0">
                View <ExternalIcon />
              </a>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
};

const DSAPanel = ({ dsaData, onBulkUpdate }) => {
  const topics = Object.entries(dsaData || {});
  const totalSolved = topics.reduce((s, [, v]) => s + v.solved, 0);
  const totalAll    = topics.reduce((s, [, v]) => s + v.total, 0);
  const pct = totalAll ? Math.round((totalSolved / totalAll) * 100) : 0;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <StatCard label="Solved" value={totalSolved} valueColor="text-teal-600 dark:text-teal-400" />
        <StatCard label="Total" value={totalAll} />
        <StatCard label="Completion" value={`${pct}%`} sub={`${totalAll - totalSolved} remaining`} />
      </div>
      <Card className="overflow-hidden">
        <div className="grid grid-cols-12 gap-2 px-5 py-2.5 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
          <span className="col-span-4 text-xs font-medium text-gray-500 dark:text-gray-400">Topic</span>
          <span className="col-span-4 text-xs font-medium text-gray-500 dark:text-gray-400">Progress</span>
          <span className="col-span-2 text-center text-xs font-medium text-gray-500 dark:text-gray-400">Solved</span>
          <span className="col-span-2 text-center text-xs font-medium text-gray-500 dark:text-gray-400">Update</span>
        </div>
        {topics.map(([topic, data], i) => {
          const tp = data.total ? Math.round((data.solved / data.total) * 100) : 0;
          return (
            <div key={topic} className="grid grid-cols-12 gap-2 items-center px-5 py-3 border-b border-gray-50 dark:border-gray-700 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
              <div className="col-span-4 min-w-0">
                <p className="text-sm text-gray-700 dark:text-gray-300 truncate">{topic}</p>
              </div>
              <div className="col-span-4">
                <ProgressBar pct={tp} color={TOPIC_COLORS[i % TOPIC_COLORS.length]} height="h-2" />
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{tp}%</p>
              </div>
              <div className="col-span-2 text-center">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{data.solved}</span>
                <span className="text-xs text-gray-400 dark:text-gray-500">/{data.total}</span>
              </div>
              <div className="col-span-2 text-center">
                <input type="number" min={0} max={data.total} value={data.solved}
                  onChange={e => onBulkUpdate(topic, Math.max(0, Math.min(data.total, Number(e.target.value))))}
                  className="w-14 text-center text-xs border border-gray-200 dark:border-gray-600 rounded-lg px-2 py-1.5 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 focus:ring-1 focus:ring-teal-400 outline-none" />
              </div>
            </div>
          );
        })}
      </Card>
    </div>
  );
};

const InterviewPipelinePanel = ({ interviews, analytics, onAdd, onUpdateStage, onDelete }) => {
  const [company, setCompany] = useState("");
  const [role, setRole]       = useState("");
  const [source, setSource]   = useState("LinkedIn");
  const funnel = analytics?.funnel || {};
  const total  = analytics?.total_applications || 0;
  const handleAdd = () => {
    if (!company.trim() || !role.trim()) return;
    onAdd(company, role, source);
    setCompany(""); setRole("");
  };
  const inputCls = "w-full text-sm border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-1 focus:ring-indigo-300 outline-none placeholder-gray-400 dark:placeholder-gray-500";
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total applied" value={analytics?.total_applications || 0} />
        <StatCard label="Offers" value={analytics?.offers || 0} valueColor="text-green-600 dark:text-green-400" sub={`${analytics?.offer_rate || 0}% offer rate`} />
        <StatCard label="Tech conversion" value={`${analytics?.technical_conversion_rate || 0}%`} sub="reached tech rounds" />
        <StatCard label="Active" value={analytics?.active || 0} sub={`${analytics?.rejections || 0} rejections`} />
      </div>
      {Object.values(funnel).some(v => v > 0) && (
        <Card className="p-5">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-4">Interview funnel</p>
          <FunnelChart funnel={funnel} total={total} />
        </Card>
      )}
      <Card className="p-4">
        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-3">Log a new application</p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Company</label>
            <input value={company} onChange={e => setCompany(e.target.value)} placeholder="e.g. Zoho"
              onKeyDown={e => e.key === "Enter" && handleAdd()} className={inputCls} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Role</label>
            <input value={role} onChange={e => setRole(e.target.value)} placeholder="e.g. SDE-1"
              onKeyDown={e => e.key === "Enter" && handleAdd()} className={inputCls} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Source</label>
            <select value={source} onChange={e => setSource(e.target.value)} className={inputCls}>
              {["LinkedIn","Referral","Company Website","Naukri","Indeed","Other"].map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <button onClick={handleAdd} disabled={!company.trim() || !role.trim()}
            className="flex items-center justify-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-40 transition-colors">
            <PlusIcon /> Add
          </button>
        </div>
      </Card>
      {!interviews?.length && (
        <div className="text-center py-8 text-gray-400 dark:text-gray-500">
          <p className="text-sm">No applications logged yet. Add your first one above.</p>
        </div>
      )}
      <div className="space-y-2">
        {(interviews || []).map(iv => (
          <Card key={iv.id} className="px-4 py-3 flex items-center gap-4">
            <div className="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-indigo-700 dark:text-indigo-300 text-xs font-medium flex-shrink-0">
              {iv.company.slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{iv.company}</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 truncate">{iv.role} · {iv.source} · {iv.applied_date}</p>
            </div>
            <select value={iv.current_stage} onChange={e => onUpdateStage(iv.id, e.target.value)}
              className={`text-xs border rounded-lg px-2 py-1 cursor-pointer outline-none flex-shrink-0 ${STAGE_STYLE[iv.current_stage] || "bg-gray-100 text-gray-600 border-gray-200"}`}>
              {PIPELINE_STAGES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <button onClick={() => onDelete(iv.id)} className="text-gray-300 dark:text-gray-600 hover:text-red-400 transition-colors flex-shrink-0">
              <TrashIcon />
            </button>
          </Card>
        ))}
      </div>
    </div>
  );
};

const ProgressDashboard = ({ importedRoadmap = null, importedProjects = [] }) => {
  const [activeTab, setActiveTab] = useState("overview");
  const [summary, setSummary]     = useState(null);
  const [fullState, setFullState] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading]     = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [sRes, fRes, aRes] = await Promise.all([
        fetch(`${API_BASE_URL}/progress/${USER_ID}/summary`),
        fetch(`${API_BASE_URL}/progress/${USER_ID}/full`),
        fetch(`${API_BASE_URL}/progress/${USER_ID}/interviews/analytics`),
      ]);
      if (sRes.ok) {
        const sData = await sRes.json();
        setSummary(sData.summary);
      }
      if (fRes.ok) {
        const fData = await fRes.json();
        setFullState(fData);
      }
      if (aRes.ok) {
        const aData = await aRes.json();
        setAnalytics(aData.analytics);
      }
    } catch {
      setSummary(null);
      setFullState(null);
      setAnalytics(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  useEffect(() => {
    if (!importedRoadmap) return;
    fetch(`${API_BASE_URL}/progress/roadmap/import`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: USER_ID, roadmap: importedRoadmap }),
    }).then(() => fetchData()).catch(() => {});
  }, [importedRoadmap, fetchData]);

  useEffect(() => {
    if (!importedProjects?.length) return;
    fetch(`${API_BASE_URL}/progress/projects/import`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: USER_ID, projects: importedProjects }),
    }).then(() => fetchData()).catch(() => {});
  }, [importedProjects, fetchData]);

  const handleTaskToggle = async (weekKey, taskId, done) => {
    if (fullState) {
      const ns = JSON.parse(JSON.stringify(fullState));
      const t = ns.roadmap[weekKey]?.find(t => t.id === taskId);
      if (t) {
        t.done = done;
        setFullState(ns);
      }
    }
    try {
      await fetch(`${API_BASE_URL}/progress/roadmap/task/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: USER_ID,
          week_key: weekKey,
          task_id: taskId,
          done
        })
      });
      fetchData();
    } catch {}
  };
  const handleProjectUpdate = async (projectId, updates) => {
    if (fullState) {
      const ns = JSON.parse(JSON.stringify(fullState));
      const p = ns.projects?.find(p => p.id === projectId);
      if (p) {
        Object.assign(p, updates);
        setFullState(ns);
      }
    }
    try {
      await fetch(`${API_BASE_URL}/progress/projects/update`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: USER_ID,
          project_id: projectId,
          updates
        })
      });
      fetchData();
    } catch {}
  };
  const handleDSABulkUpdate = async (topic, solvedCount) => {
    if (fullState) {
      const ns = JSON.parse(JSON.stringify(fullState));
      if (ns.dsa?.[topic]) {
        ns.dsa[topic].solved = solvedCount;
        setFullState(ns);
      }
    }
    try {
      await fetch(`${API_BASE_URL}/progress/dsa/bulk-update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: USER_ID,
          topic,
          solved_count: solvedCount
        })
      });
      fetchData();
    } catch {}
  };
  const handleAddInterview    = async (company, role, source) => {
    try {
      await fetch(`${API_BASE_URL}/progress/interviews/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: USER_ID,
          company,
          role,
          source
        })
      });
      fetchData();
    } catch {}
  };
  const handleUpdateStage     = async (interviewId, newStage) => {
    if (fullState) {
      const ns = JSON.parse(JSON.stringify(fullState));
      const iv = ns.interviews?.find(i => i.id === interviewId);
      if (iv) {
        iv.current_stage = newStage;
        setFullState(ns);
      }
    }
    try {
      await fetch(`${API_BASE_URL}/progress/interviews/stage`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: USER_ID,
          interview_id: interviewId,
          new_stage: newStage,
          notes: ""
        })
      });
      fetchData();
    } catch {}
  };
  const handleDeleteInterview = async (interviewId) => {
    try {
      await fetch(`${API_BASE_URL}/progress/interviews/${USER_ID}/${interviewId}`, {
        method: "DELETE"
      });
      fetchData();
    } catch {}
  };

  const rm = summary?.roadmap; const dsa = summary?.dsa;
  const iv = summary?.interviews; const proj = summary?.projects;

  const tabs = [
    { key: "overview",   label: "Overview" },
    { key: "roadmap",    label: `Roadmap ${rm ? rm.pct + "%" : ""}` },
    { key: "projects",   label: `Projects ${proj ? "(" + proj.total + ")" : ""}` },
    { key: "dsa",        label: `DSA ${dsa ? dsa.solved + "/" + dsa.total : ""}` },
    { key: "interviews", label: `Interviews ${iv ? "(" + iv.total_applied + ")" : ""}` },
  ];

  if (loading) return (
    <div className="flex items-center justify-center py-24">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
    </div>
  );

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Roadmap" value={`${rm?.pct ?? 0}%`} sub={`${rm?.completed_tasks ?? 0}/${rm?.total_tasks ?? 0} tasks`} valueColor="text-indigo-600 dark:text-indigo-400" />
        <StatCard label="DSA solved" value={dsa?.solved ?? 0} sub={`of ${dsa?.total ?? 0} total`} />
        <StatCard label="Projects" value={proj?.total ?? 0} sub={`${proj?.by_status?.Completed ?? 0} completed`} />
        <StatCard label="Offers" value={iv?.offers ?? 0} sub={`${iv?.offer_rate ?? 0}% offer rate`} valueColor="text-green-600 dark:text-green-400" />
      </div>

      <Card className="p-5">
        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-4">Activity — last 6 months</p>
        <ActivityHeatmap activityLog={fullState?.activity_log || []} />
      </Card>

      <SubTabs tabs={tabs} active={activeTab} onChange={setActiveTab} />

      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-gray-800 dark:text-white">Roadmap progress</p>
              <button onClick={() => setActiveTab("roadmap")} className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">View all →</button>
            </div>
            <ProgressBar pct={rm?.pct || 0} color="#6366F1" height="h-2" />
            <div className="flex justify-between mt-2 text-xs text-gray-400 dark:text-gray-500">
              <span>{rm?.completed_tasks || 0} / {rm?.total_tasks || 0} tasks</span>
              <span className="font-medium text-indigo-600 dark:text-indigo-400">{rm?.pct || 0}%</span>
            </div>
          </Card>
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-gray-800 dark:text-white">DSA problems</p>
              <button onClick={() => setActiveTab("dsa")} className="text-xs text-teal-600 dark:text-teal-400 hover:underline">View all →</button>
            </div>
            <DSABarChart dsaData={Object.fromEntries(Object.entries(fullState?.dsa || {}).slice(0, 6))} />
          </Card>
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-gray-800 dark:text-white">Projects</p>
              <button onClick={() => setActiveTab("projects")} className="text-xs text-violet-600 dark:text-violet-400 hover:underline">View all →</button>
            </div>
            {proj?.by_status && Object.keys(proj.by_status).length > 0 ? (
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(proj.by_status).map(([status, count]) => (
                  <div key={status} className={`rounded-lg px-2 py-2.5 text-center border text-xs ${PROJECT_STATUS_COLORS[status]}`}>
                    <p className="text-lg font-medium">{count}</p>
                    <p className="leading-tight mt-0.5">{status}</p>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-gray-400 dark:text-gray-500">No projects yet</p>}
          </Card>
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-gray-800 dark:text-white">Interview tracker</p>
              <button onClick={() => setActiveTab("interviews")} className="text-xs text-amber-600 dark:text-amber-400 hover:underline">View all →</button>
            </div>
            <FunnelChart funnel={iv?.funnel || {}} total={iv?.total_applied || 0} />
          </Card>
        </div>
      )}
      {activeTab === "roadmap"    && <RoadmapPanel roadmapData={fullState?.roadmap || {}} onTaskToggle={handleTaskToggle} />}
      {activeTab === "projects"   && <ProjectsPanel projects={fullState?.projects || []} onUpdateProject={handleProjectUpdate} />}
      {activeTab === "dsa"        && <DSAPanel dsaData={fullState?.dsa || {}} onBulkUpdate={handleDSABulkUpdate} />}
      {activeTab === "interviews" && (
        <InterviewPipelinePanel
          interviews={fullState?.interviews || []}
          analytics={analytics}
          onAdd={handleAddInterview}
          onUpdateStage={handleUpdateStage}
          onDelete={handleDeleteInterview}
        />
      )}
    </div>
  );
};

export default ProgressDashboard;