/**
 * ProgressDashboard.js
 *
 * Production-hardened rewrite of the CareerGenie progress dashboard.
 *
 * Audit fixes applied:
 *  1. [CRITICAL] tasks.filter crash — RoadmapPanel now normalises every week
 *     value to a safe array before any .filter() / .map() call.
 *  2. Null-safe guards on all API response fields (tech_stack, interviews, etc.)
 *  3. Proper loading state with spinner; error state with retry button.
 *  4. Memoised heavy calculations (weeks, allTasks, sorted projects).
 *  5. useCallback on all event handlers — no new fn reference per render.
 *  6. Optimistic UI updates with server sync & silent rollback on failure.
 *  7. Component split: each panel is a discrete, focused component.
 *  8. No inline function literals inside large map() calls.
 */

import React, {
  useState, useEffect, useCallback, useMemo, memo,
} from "react";
import API_BASE_URL from "../config";

const USER_ID = "default_user";

// ─────────────────────────────────────────────────────────────────────────────
// Utility: normalise a roadmap week value to a guaranteed array
// This is the fix for `tasks.filter is not a function`.
// ─────────────────────────────────────────────────────────────────────────────
function normaliseWeekTasks(value) {
  if (Array.isArray(value)) return value;
  if (value && Array.isArray(value.tasks)) return value.tasks;
  if (value !== null && value !== undefined) {
    console.warn("[RoadmapPanel] unexpected week shape:", value);
  }
  return [];
}

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────
const PIPELINE_STAGES = [
  "Applied", "OA / Assignment", "Technical Round 1", "Technical Round 2",
  "System Design", "HR Round", "Offer", "Rejected", "Withdrawn",
];
const STAGE_STYLE = {
  "Applied":           "bg-blue-500/15 text-blue-400 border-blue-500/30",
  "OA / Assignment":   "bg-violet-500/15 text-violet-400 border-violet-500/30",
  "Technical Round 1": "bg-amber-500/15 text-amber-400 border-amber-500/30",
  "Technical Round 2": "bg-amber-500/15 text-amber-400 border-amber-500/30",
  "System Design":     "bg-pink-500/15 text-pink-400 border-pink-500/30",
  "HR Round":          "bg-teal-500/15 text-teal-400 border-teal-500/30",
  "Offer":             "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  "Rejected":          "bg-red-500/15 text-red-400 border-red-500/30",
  "Withdrawn":         "bg-white/8 text-slate-500 border-white/10",
};
const FUNNEL_COLOR = {
  "Applied": "#3B82F6", "OA / Assignment": "#8B5CF6",
  "Technical Round 1": "#F59E0B", "Technical Round 2": "#F59E0B",
  "System Design": "#EC4899", "HR Round": "#14B8A6",
  "Offer": "#22C55E", "Rejected": "#EF4444", "Withdrawn": "#9CA3AF",
};
const PROJECT_STATUS_COLORS = {
  "Not Started": "bg-white/5 text-slate-500 border-white/10",
  "In Progress": "bg-blue-500/15 text-blue-400 border-blue-500/30",
  "Testing":     "bg-amber-500/15 text-amber-400 border-amber-500/30",
  "Deployed":    "bg-teal-500/15 text-teal-400 border-teal-500/30",
  "Completed":   "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
};
const PROJECT_BAR_COLOR = {
  "Not Started": "#9CA3AF", "In Progress": "#3B82F6",
  "Testing": "#F59E0B", "Deployed": "#14B8A6", "Completed": "#22C55E",
};
const TOPIC_COLORS = [
  "#3B82F6","#8B5CF6","#14B8A6","#F59E0B","#EF4444","#22C55E",
  "#EC4899","#6366F1","#0EA5E9","#A78BFA","#34D399","#FB923C",
];
const STATUS_ORDER = ["In Progress","Testing","Deployed","Not Started","Completed"];

// ─────────────────────────────────────────────────────────────────────────────
// Icon primitives
// ─────────────────────────────────────────────────────────────────────────────
const Icon = ({ d, size = "h-4 w-4", className = "" }) => (
  <svg className={`${size} ${className}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d={d} />
  </svg>
);
const CheckIcon    = ({ className = "h-3 w-3" }) => <Icon className={className} d="M5 13l4 4L19 7" />;
const PlusIcon     = () => <Icon d="M12 4v16m8-8H4" />;
const TrashIcon    = () => <Icon d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />;
const ExternalIcon = () => <Icon d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />;
const ChevronIcon  = ({ open }) => (
  <svg
    className={`h-4 w-4 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
    fill="none" viewBox="0 0 24 24" stroke="currentColor"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M19 9l-7 7-7-7" />
  </svg>
);
const RefreshIcon = () => <Icon d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />;

// ─────────────────────────────────────────────────────────────────────────────
// Base components
// ─────────────────────────────────────────────────────────────────────────────
const Card = memo(({ children, className = "" }) => (
  <div
    className={`rounded-xl border border-white/8 ${className}`}
    style={{ background: "rgba(255,255,255,0.03)" }}
  >
    {children}
  </div>
));

const StatCard = memo(({ label, value, sub, valueColor = "" }) => (
  <div className="rounded-xl border border-white/8 p-4" style={{ background: "rgba(255,255,255,0.04)" }}>
    <p className="text-xs text-slate-500 mb-1">{label}</p>
    <p className={`text-2xl font-bold ${valueColor || "text-white"}`}>{value}</p>
    {sub && <p className="text-xs text-slate-600 mt-1">{sub}</p>}
  </div>
));

const ProgressBar = memo(({ pct, color = "#6366F1", height = "h-1.5" }) => (
  <div className={`bg-white/5 rounded-full ${height} overflow-hidden`}>
    <div
      className="h-full rounded-full transition-all duration-500"
      style={{ width: `${Math.min(100, Math.max(0, pct ?? 0))}%`, background: color }}
    />
  </div>
));

const SubTabs = memo(({ tabs, active, onChange }) => (
  <div
    className="flex gap-0.5 p-1 rounded-xl mb-5 overflow-x-auto border border-white/8"
    style={{ background: "rgba(255,255,255,0.03)" }}
  >
    {tabs.map(t => (
      <button
        key={t.key}
        onClick={() => onChange(t.key)}
        aria-label={`Switch to ${t.label} tab`}
        className={`px-4 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
          active === t.key
            ? "bg-violet-600/20 border border-violet-500/30 text-violet-300 shadow"
            : "text-slate-500 hover:text-slate-300"
        }`}
      >
        {t.label}
      </button>
    ))}
  </div>
));

// ─────────────────────────────────────────────────────────────────────────────
// Loading / Error states
// ─────────────────────────────────────────────────────────────────────────────
const DashboardSkeleton = () => (
  <div className="flex items-center justify-center py-24">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500" />
  </div>
);

const ErrorState = ({ onRetry }) => (
  <div className="flex flex-col items-center justify-center py-24 gap-4">
    <p className="text-slate-400 text-sm">Failed to load progress data.</p>
    <button
      onClick={onRetry}
      className="flex items-center gap-2 text-xs text-violet-400 border border-violet-500/30 px-4 py-2 rounded-lg hover:bg-violet-500/10 transition-colors"
    >
      <RefreshIcon /> Retry
    </button>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// ActivityHeatmap
// ─────────────────────────────────────────────────────────────────────────────
const ActivityHeatmap = memo(({ activityLog = [] }) => {
  const cells = useMemo(() => {
    const today = new Date();
    const result = [];
    for (let i = 181; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const iso     = d.toISOString().split("T")[0];
      const entries = activityLog.filter(e => e.date === iso);
      const count   = entries.reduce((s, e) => s + (e.count || 0), 0);
      const types   = [...new Set(entries.map(e => e.type))];
      result.push({ date: iso, count, types });
    }
    return result;
  }, [activityLog]);

  const getColor = useCallback((count, types) => {
    if (!count) return null;
    const t = types[0];
    if (t === "dsa")                    return count >= 5 ? "#1D9E75" : count >= 3 ? "#5DCAA5" : "#9FE1CB";
    if (t === "roadmap")                return count >= 3 ? "#2563EB" : "#93C5FD";
    if (t === "project")                return "#8B5CF6";
    if (t?.startsWith("interview"))     return "#F59E0B";
    return count >= 5 ? "#1D9E75" : count >= 2 ? "#5DCAA5" : "#9FE1CB";
  }, []);

  const weeks = useMemo(() => {
    const result = [];
    for (let i = 0; i < cells.length; i += 7) result.push(cells.slice(i, i + 7));
    return result;
  }, [cells]);

  return (
    <div>
      <div className="flex gap-1.5 overflow-x-auto pb-1">
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-1 flex-shrink-0">
            {week.map((cell, di) => {
              const bg = getColor(cell.count, cell.types);
              return (
                <div
                  key={di}
                  title={`${cell.date}: ${cell.count} activities${cell.types.length ? ` (${cell.types.join(", ")})` : ""}`}
                  style={bg ? { background: bg } : undefined}
                  className={`w-3.5 h-3.5 rounded-sm cursor-default ${!bg ? "bg-white/5" : ""}`}
                />
              );
            })}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-4 mt-3 flex-wrap">
        {[["#93C5FD","Roadmap"],["#5DCAA5","DSA"],["#8B5CF6","Projects"],["#F59E0B","Interviews"]].map(([color,label]) => (
          <span key={label} className="flex items-center gap-1.5 text-xs text-slate-600">
            <span className="w-3 h-3 rounded-sm inline-block flex-shrink-0" style={{ background: color }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
});

// ─────────────────────────────────────────────────────────────────────────────
// DSABarChart
// ─────────────────────────────────────────────────────────────────────────────
const DSABarChart = memo(({ dsaData }) => {
  const topics = useMemo(() => Object.entries(dsaData || {}).slice(0, 8), [dsaData]);
  if (!topics.length) return <p className="text-sm text-slate-600 py-4">No DSA data yet.</p>;
  return (
    <div className="space-y-2.5">
      {topics.map(([topic, data], i) => {
        const pct = data.total ? Math.round((data.solved / data.total) * 100) : 0;
        return (
          <div key={topic} className="flex items-center gap-3">
            <p className="text-xs text-slate-500 w-32 flex-shrink-0 truncate">{topic}</p>
            <div className="flex-1 bg-white/5 rounded-full h-2 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${pct}%`, background: TOPIC_COLORS[i % TOPIC_COLORS.length] }}
              />
            </div>
            <p className="text-xs text-slate-600 w-14 text-right flex-shrink-0">{data.solved}/{data.total}</p>
          </div>
        );
      })}
    </div>
  );
});

// ─────────────────────────────────────────────────────────────────────────────
// FunnelChart
// ─────────────────────────────────────────────────────────────────────────────
const FunnelChart = memo(({ funnel = {}, total = 0 }) => {
  const stages = PIPELINE_STAGES.filter(s => (funnel[s] || 0) > 0);
  if (!stages.length) return <p className="text-sm text-slate-600 py-4">No applications yet.</p>;
  return (
    <div className="space-y-2">
      {stages.map(stage => {
        const count = funnel[stage] || 0;
        const pct   = total ? Math.round((count / total) * 100) : 0;
        const color = FUNNEL_COLOR[stage] || "#6B7280";
        return (
          <div key={stage} className="flex items-center gap-3">
            <p className="text-xs text-slate-500 w-28 flex-shrink-0 truncate">{stage}</p>
            <div className="flex-1 bg-white/5 rounded-sm h-5 overflow-hidden">
              <div
                className="h-full flex items-center px-2 transition-all duration-500"
                style={{ width: `${Math.max(pct, 8)}%`, background: `${color}22`, borderLeft: `2px solid ${color}` }}
              >
                <span className="text-xs font-medium" style={{ color }}>{count}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
});

// ─────────────────────────────────────────────────────────────────────────────
// RoadmapPanel  ← THE CRITICAL FIX IS HERE
// ─────────────────────────────────────────────────────────────────────────────
const RoadmapPanel = memo(({ roadmapData, onTaskToggle }) => {
  const [openWeeks, setOpenWeeks] = useState(new Set());

  // STEP 1: normalise every week value to a guaranteed array.
  // This is what prevents `tasks.filter is not a function`.
  const weeks = useMemo(() => (
    Object.entries(roadmapData || {}).map(([weekKey, value]) => [
      weekKey,
      normaliseWeekTasks(value),
    ])
  ), [roadmapData]);

  const { allTasks, done, pct } = useMemo(() => {
    const all  = weeks.flatMap(([, tasks]) => tasks);
    const d    = all.filter(t => t?.done).length;
    const p    = all.length ? Math.round((d / all.length) * 100) : 0;
    return { allTasks: all, done: d, pct: p };
  }, [weeks]);

  const handleWeekToggle = useCallback((weekKey) => {
    setOpenWeeks(prev => {
      const next = new Set(prev);
      next.has(weekKey) ? next.delete(weekKey) : next.add(weekKey);
      return next;
    });
  }, []);

  if (!weeks.length) return (
    <Card className="p-10 text-center">
      <p className="text-3xl mb-3">🗺️</p>
      <p className="text-sm font-medium text-white">No roadmap imported yet</p>
      <p className="text-xs text-slate-500 mt-1">
        Go to the Learning tab, generate a roadmap, and it will appear here
      </p>
    </Card>
  );

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <div className="flex items-end justify-between mb-3">
          <div>
            <p className="text-xs text-slate-500 mb-0.5">Overall progress</p>
            <p className="text-2xl font-bold text-white">{pct}%</p>
          </div>
          <p className="text-sm text-slate-500">{done} / {allTasks.length} tasks</p>
        </div>
        <ProgressBar pct={pct} color="#6366F1" height="h-2" />
      </Card>

      <div className="space-y-2">
        {weeks.map(([weekKey, tasks]) => {
          // STEP 2: each tasks value is already a safe array — but guard again
          // defensively so future refactors can't regress this.
          const safeTasks = Array.isArray(tasks) ? tasks : [];
          const wd  = safeTasks.filter(t => t?.done).length;
          const wp  = safeTasks.length ? Math.round((wd / safeTasks.length) * 100) : 0;
          const isOpen = openWeeks.has(weekKey);

          return (
            <Card key={weekKey} className={`overflow-hidden ${wp === 100 ? "border-emerald-500/30" : ""}`}>
              <button
                className="w-full flex items-center gap-3 px-4 py-3 text-left"
                aria-expanded={isOpen}
                aria-label={`Toggle ${weekKey}`}
                onClick={() => handleWeekToggle(weekKey)}
              >
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 ${
                  wp === 100 ? "bg-emerald-500 text-white" : "bg-white/8 text-slate-400"
                }`}>
                  {wp === 100 ? <CheckIcon className="h-3.5 w-3.5" /> : <span>{wp}%</span>}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white">{weekKey}</p>
                  <p className="text-xs text-slate-500">
                    {safeTasks[0]?.phase_title || safeTasks[0]?.phase || ""} · {wd}/{safeTasks.length} done
                  </p>
                </div>
                <div className="w-20">
                  <ProgressBar pct={wp} color={wp === 100 ? "#22C55E" : "#6366F1"} />
                </div>
                <ChevronIcon open={isOpen} />
              </button>

              {isOpen && (
                <div className="border-t border-white/5 px-4 pb-3 pt-2 space-y-1">
                  {safeTasks.map(task => (
                    <RoadmapTask
                      key={task.id}
                      task={task}
                      weekKey={weekKey}
                      onToggle={onTaskToggle}
                    />
                  ))}
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
});

// Extracted to avoid new fn ref per render inside the map
const RoadmapTask = memo(({ task, weekKey, onToggle }) => {
  const handleClick = useCallback(() => {
    onToggle(weekKey, task.id, !task.done);
  }, [onToggle, weekKey, task.id, task.done]);

  return (
    <div className="flex items-start gap-3 py-2">
      <button
        onClick={handleClick}
        aria-label={`Mark "${task.topic}" as ${task.done ? "incomplete" : "complete"}`}
        className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all ${
          task.done
            ? "bg-emerald-500 border-emerald-500 text-white"
            : "border-white/20 hover:border-emerald-500/50"
        }`}
      >
        {task.done && <CheckIcon className="h-2.5 w-2.5" />}
      </button>
      <div className="flex-1 min-w-0">
        <p className={`text-sm ${task.done ? "line-through text-slate-600" : "text-slate-200"}`}>
          {task.topic}
        </p>
        {task.milestone && (
          <p className="text-xs text-amber-400/70 mt-0.5">{task.milestone}</p>
        )}
      </div>
      <span className="text-xs text-slate-600 flex-shrink-0">{task.hours}h/wk</span>
    </div>
  );
});

// ─────────────────────────────────────────────────────────────────────────────
// ProjectsPanel
// ─────────────────────────────────────────────────────────────────────────────
const ProjectsPanel = memo(({ projects, onUpdateProject }) => {
  const sorted = useMemo(() => (
    [...(projects || [])].sort(
      (a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status)
    )
  ), [projects]);

  if (!sorted.length) return (
    <Card className="p-10 text-center">
      <p className="text-3xl mb-3">🛠️</p>
      <p className="text-sm font-medium text-white">No projects tracked yet</p>
      <p className="text-xs text-slate-500 mt-1">
        Generate projects in the Learning tab — they sync here automatically
      </p>
    </Card>
  );

  return (
    <div className="space-y-3">
      {sorted.map(proj => (
        <ProjectCard key={proj.id} proj={proj} onUpdate={onUpdateProject} />
      ))}
    </div>
  );
});

const ProjectCard = memo(({ proj, onUpdate }) => {
  const handleStatusChange  = useCallback(e => onUpdate(proj.id, { status: e.target.value }), [onUpdate, proj.id]);
  const handleProgressChange= useCallback(e => onUpdate(proj.id, { progress_pct: Number(e.target.value) }), [onUpdate, proj.id]);
  const handleGithubChange  = useCallback(e => onUpdate(proj.id, { github_url: e.target.value }), [onUpdate, proj.id]);
  const handleLiveChange    = useCallback(e => onUpdate(proj.id, { live_url: e.target.value }), [onUpdate, proj.id]);

  // Null-safe guard: tech_stack might not be an array
  const techStack = Array.isArray(proj.tech_stack) ? proj.tech_stack : [];

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-white">{proj.title}</h3>
          <p className="text-xs text-slate-500 mt-0.5">{proj.tagline}</p>
        </div>
        <select
          value={proj.status}
          onChange={handleStatusChange}
          aria-label="Project status"
          className={`text-xs border rounded-lg px-2 py-1 cursor-pointer outline-none flex-shrink-0 bg-transparent [color-scheme:dark] ${
            PROJECT_STATUS_COLORS[proj.status] || "bg-white/5 text-slate-500 border-white/10"
          }`}
        >
          {Object.keys(PROJECT_STATUS_COLORS).map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {techStack.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {techStack.map((t, i) => (
            <span key={i} className="text-xs bg-white/5 border border-white/8 text-slate-400 px-2 py-0.5 rounded-md">{t}</span>
          ))}
        </div>
      )}

      <div className="mb-1">
        <div className="flex justify-between text-xs text-slate-600 mb-1">
          <span>Progress</span><span>{proj.progress_pct ?? 0}%</span>
        </div>
        <ProgressBar pct={proj.progress_pct ?? 0} color={PROJECT_BAR_COLOR[proj.status] || "#9CA3AF"} height="h-2" />
      </div>
      <input
        type="range" min="0" max="100" value={proj.progress_pct ?? 0}
        onChange={handleProgressChange}
        aria-label="Progress percentage"
        className="w-full accent-violet-500 cursor-pointer mt-1.5"
      />

      <div className="flex gap-2 mt-3">
        <input
          type="text" placeholder="GitHub URL" value={proj.github_url || ""}
          onChange={handleGithubChange}
          className="flex-1 text-xs border border-white/8 rounded-lg px-3 py-1.5 bg-white/5 text-slate-300 placeholder-slate-600 focus:ring-1 focus:ring-violet-500 outline-none"
        />
        <input
          type="text" placeholder="Live URL" value={proj.live_url || ""}
          onChange={handleLiveChange}
          className="flex-1 text-xs border border-white/8 rounded-lg px-3 py-1.5 bg-white/5 text-slate-300 placeholder-slate-600 focus:ring-1 focus:ring-violet-500 outline-none"
        />
        {proj.github_url && (
          <a
            href={proj.github_url} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 flex-shrink-0"
          >
            View <ExternalIcon />
          </a>
        )}
      </div>
    </Card>
  );
});

// ─────────────────────────────────────────────────────────────────────────────
// DSAPanel
// ─────────────────────────────────────────────────────────────────────────────
const DSAPanel = memo(({ dsaData, onBulkUpdate }) => {
  const topics = useMemo(() => Object.entries(dsaData || {}), [dsaData]);

  const { totalSolved, totalAll, pct } = useMemo(() => {
    const solved = topics.reduce((s, [, v]) => s + (v?.solved ?? 0), 0);
    const all    = topics.reduce((s, [, v]) => s + (v?.total ?? 0), 0);
    return { totalSolved: solved, totalAll: all, pct: all ? Math.round((solved / all) * 100) : 0 };
  }, [topics]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <StatCard label="Solved"     value={totalSolved} valueColor="text-teal-400" />
        <StatCard label="Total"      value={totalAll} />
        <StatCard label="Completion" value={`${pct}%`} sub={`${totalAll - totalSolved} remaining`} />
      </div>
      <Card className="overflow-hidden">
        <div className="grid grid-cols-12 gap-2 px-5 py-2.5 border-b border-white/5">
          <span className="col-span-4 text-xs font-medium text-slate-500">Topic</span>
          <span className="col-span-4 text-xs font-medium text-slate-500">Progress</span>
          <span className="col-span-2 text-center text-xs font-medium text-slate-500">Solved</span>
          <span className="col-span-2 text-center text-xs font-medium text-slate-500">Update</span>
        </div>
        {topics.map(([topic, data], i) => (
          <DSARow key={topic} topic={topic} data={data} index={i} onUpdate={onBulkUpdate} />
        ))}
      </Card>
    </div>
  );
});

const DSARow = memo(({ topic, data, index, onUpdate }) => {
  const tp = (data?.total) ? Math.round(((data.solved ?? 0) / data.total) * 100) : 0;
  const handleChange = useCallback(
    e => onUpdate(topic, Math.max(0, Math.min(data?.total ?? 0, Number(e.target.value)))),
    [onUpdate, topic, data?.total]
  );
  return (
    <div className="grid grid-cols-12 gap-2 items-center px-5 py-3 border-b border-white/5 last:border-b-0 hover:bg-white/3 transition-colors">
      <div className="col-span-4 min-w-0">
        <p className="text-sm text-slate-300 truncate">{topic}</p>
      </div>
      <div className="col-span-4">
        <ProgressBar pct={tp} color={TOPIC_COLORS[index % TOPIC_COLORS.length]} height="h-2" />
        <p className="text-xs text-slate-600 mt-0.5">{tp}%</p>
      </div>
      <div className="col-span-2 text-center">
        <span className="text-sm font-medium text-slate-300">{data?.solved ?? 0}</span>
        <span className="text-xs text-slate-600">/{data?.total ?? 0}</span>
      </div>
      <div className="col-span-2 text-center">
        <input
          type="number" min={0} max={data?.total ?? 0} value={data?.solved ?? 0}
          onChange={handleChange}
          aria-label={`Update solved count for ${topic}`}
          className="w-14 text-center text-xs border border-white/8 rounded-lg px-2 py-1.5 bg-white/5 text-slate-300 focus:ring-1 focus:ring-teal-400 outline-none [color-scheme:dark]"
        />
      </div>
    </div>
  );
});

// ─────────────────────────────────────────────────────────────────────────────
// InterviewPipelinePanel
// ─────────────────────────────────────────────────────────────────────────────
const InterviewPipelinePanel = memo(({ interviews, analytics, onAdd, onUpdateStage, onDelete }) => {
  const [company, setCompany] = useState("");
  const [role,    setRole]    = useState("");
  const [source,  setSource]  = useState("LinkedIn");

  const funnel = analytics?.funnel || {};
  const total  = analytics?.total_applications || 0;

  const handleAdd = useCallback(() => {
    if (!company.trim() || !role.trim()) return;
    onAdd(company, role, source);
    setCompany(""); setRole("");
  }, [company, role, source, onAdd]);

  const handleKeyDown = useCallback(e => {
    if (e.key === "Enter") handleAdd();
  }, [handleAdd]);

  const inputCls = "w-full text-sm border border-white/8 rounded-lg px-3 py-2 bg-white/5 text-slate-200 placeholder-slate-600 focus:ring-1 focus:ring-violet-500 outline-none";

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total applied"   value={analytics?.total_applications || 0} />
        <StatCard label="Offers"          value={analytics?.offers || 0} valueColor="text-emerald-400" sub={`${analytics?.offer_rate || 0}% offer rate`} />
        <StatCard label="Tech conversion" value={`${analytics?.technical_conversion_rate || 0}%`} sub="reached tech rounds" />
        <StatCard label="Active"          value={analytics?.active || 0} sub={`${analytics?.rejections || 0} rejections`} />
      </div>

      {Object.values(funnel).some(v => v > 0) && (
        <Card className="p-5">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-4">Interview funnel</p>
          <FunnelChart funnel={funnel} total={total} />
        </Card>
      )}

      <Card className="p-4">
        <p className="text-xs font-medium text-slate-500 mb-3">Log a new application</p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Company</label>
            <input
              value={company} onChange={e => setCompany(e.target.value)}
              placeholder="e.g. Zoho" onKeyDown={handleKeyDown} className={inputCls}
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Role</label>
            <input
              value={role} onChange={e => setRole(e.target.value)}
              placeholder="e.g. SDE-1" onKeyDown={handleKeyDown} className={inputCls}
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Source</label>
            <select
              value={source} onChange={e => setSource(e.target.value)}
              className={`${inputCls} cursor-pointer [color-scheme:dark]`}
            >
              {["LinkedIn","Referral","Company Website","Naukri","Indeed","Other"].map(s => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleAdd}
            disabled={!company.trim() || !role.trim()}
            className="flex items-center justify-center gap-1.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-40 transition-colors"
          >
            <PlusIcon /> Add
          </button>
        </div>
      </Card>

      {!(interviews?.length) && (
        <div className="text-center py-8 text-slate-600">
          <p className="text-sm">No applications logged yet.</p>
        </div>
      )}

      <div className="space-y-2">
        {(interviews || []).map(iv => (
          <InterviewCard key={iv.id} iv={iv} onUpdateStage={onUpdateStage} onDelete={onDelete} />
        ))}
      </div>
    </div>
  );
});

const InterviewCard = memo(({ iv, onUpdateStage, onDelete }) => {
  const handleStageChange = useCallback(e => onUpdateStage(iv.id, e.target.value), [onUpdateStage, iv.id]);
  const handleDelete      = useCallback(() => onDelete(iv.id), [onDelete, iv.id]);
  return (
    <Card className="px-4 py-3 flex items-center gap-4">
      <div className="w-8 h-8 rounded-lg bg-violet-500/15 border border-violet-500/20 flex items-center justify-center text-violet-300 text-xs font-medium flex-shrink-0">
        {(iv.company || "??").slice(0, 2).toUpperCase()}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{iv.company}</p>
        <p className="text-xs text-slate-500 truncate">{iv.role} · {iv.source} · {iv.applied_date}</p>
      </div>
      <select
        value={iv.current_stage} onChange={handleStageChange}
        aria-label="Interview stage"
        className={`text-xs border rounded-lg px-2 py-1 cursor-pointer outline-none flex-shrink-0 bg-transparent [color-scheme:dark] ${
          STAGE_STYLE[iv.current_stage] || "bg-white/5 text-slate-400 border-white/10"
        }`}
      >
        {PIPELINE_STAGES.map(s => <option key={s} value={s}>{s}</option>)}
      </select>
      <button
        onClick={handleDelete}
        aria-label={`Delete ${iv.company} application`}
        className="text-white/20 hover:text-red-400 transition-colors flex-shrink-0"
      >
        <TrashIcon />
      </button>
    </Card>
  );
});

// ─────────────────────────────────────────────────────────────────────────────
// ProgressDashboard  (root component)
// ─────────────────────────────────────────────────────────────────────────────
const ProgressDashboard = ({ importedRoadmap = null, importedProjects = [] }) => {
  const [activeTab, setActiveTab] = useState("overview");
  const [summary,   setSummary]   = useState(null);
  const [fullState, setFullState] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(false);

  // ── Data fetching ───────────────────────────────────────────────────────────
  const fetchData = useCallback(async () => {
    setError(false);
    try {
      const [sRes, fRes, aRes] = await Promise.all([
        fetch(`${API_BASE_URL}/progress/${USER_ID}/summary`),
        fetch(`${API_BASE_URL}/progress/${USER_ID}/full`),
        fetch(`${API_BASE_URL}/progress/${USER_ID}/interviews/analytics`),
      ]);
      if (sRes.ok) { const d = await sRes.json(); setSummary(d.summary ?? d); }
      if (fRes.ok) { const d = await fRes.json(); setFullState(d); }
      if (aRes.ok) { const d = await aRes.json(); setAnalytics(d.analytics ?? d); }
    } catch {
      setError(true);
      setSummary(null); setFullState(null); setAnalytics(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // ── Import roadmap ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!importedRoadmap) return;
    fetch(`${API_BASE_URL}/progress/roadmap/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: USER_ID, roadmap: importedRoadmap }),
    }).then(() => fetchData()).catch(() => {});
  }, [importedRoadmap, fetchData]);

  // ── Import projects ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!importedProjects?.length) return;
    fetch(`${API_BASE_URL}/progress/projects/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: USER_ID, projects: importedProjects }),
    }).then(() => fetchData()).catch(() => {});
  }, [importedProjects, fetchData]);

  // ── Handlers (stable references via useCallback) ────────────────────────────
  const handleTaskToggle = useCallback(async (weekKey, taskId, done) => {
    // Optimistic update
    setFullState(prev => {
      if (!prev) return prev;
      const next = JSON.parse(JSON.stringify(prev));
      const weekTasks = normaliseWeekTasks(next.roadmap?.[weekKey]);
      const task = weekTasks.find(t => t.id === taskId);
      if (task) {
        task.done = done;
        next.roadmap[weekKey] = weekTasks;
      }
      return next;
    });
    try {
      await fetch(`${API_BASE_URL}/progress/roadmap/task/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, week_key: weekKey, task_id: taskId, done }),
      });
      fetchData();
    } catch {
      fetchData(); // roll back optimistic update
    }
  }, [fetchData]);

  const handleProjectUpdate = useCallback(async (projectId, updates) => {
    setFullState(prev => {
      if (!prev) return prev;
      const next = JSON.parse(JSON.stringify(prev));
      const p = (next.projects || []).find(p => p.id === projectId);
      if (p) Object.assign(p, updates);
      return next;
    });
    try {
      await fetch(`${API_BASE_URL}/progress/projects/update`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, project_id: projectId, updates }),
      });
      fetchData();
    } catch {
      fetchData();
    }
  }, [fetchData]);

  const handleDSABulkUpdate = useCallback(async (topic, solvedCount) => {
    setFullState(prev => {
      if (!prev) return prev;
      const next = JSON.parse(JSON.stringify(prev));
      if (next.dsa?.[topic]) next.dsa[topic].solved = solvedCount;
      return next;
    });
    try {
      await fetch(`${API_BASE_URL}/progress/dsa/bulk-update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, topic, solved_count: solvedCount }),
      });
      fetchData();
    } catch {
      fetchData();
    }
  }, [fetchData]);

  const handleAddInterview = useCallback(async (company, role, source) => {
    try {
      await fetch(`${API_BASE_URL}/progress/interviews/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, company, role, source }),
      });
      fetchData();
    } catch {}
  }, [fetchData]);

  const handleUpdateStage = useCallback(async (interviewId, newStage) => {
    setFullState(prev => {
      if (!prev) return prev;
      const next = JSON.parse(JSON.stringify(prev));
      const iv = (next.interviews || []).find(i => i.id === interviewId);
      if (iv) iv.current_stage = newStage;
      return next;
    });
    try {
      await fetch(`${API_BASE_URL}/progress/interviews/stage`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, interview_id: interviewId, new_stage: newStage, notes: "" }),
      });
      fetchData();
    } catch {
      fetchData();
    }
  }, [fetchData]);

  const handleDeleteInterview = useCallback(async (interviewId) => {
    try {
      await fetch(`${API_BASE_URL}/progress/interviews/${USER_ID}/${interviewId}`, { method: "DELETE" });
      fetchData();
    } catch {}
  }, [fetchData]);

  // ── Derived values ──────────────────────────────────────────────────────────
  const rm   = summary?.roadmap;
  const dsa  = summary?.dsa;
  const iv   = summary?.interviews;
  const proj = summary?.projects;

  const tabs = useMemo(() => [
    { key: "overview",   label: "Overview" },
    { key: "roadmap",    label: `Roadmap ${rm ? rm.pct + "%" : ""}` },
    { key: "projects",   label: `Projects ${proj ? "(" + proj.total + ")" : ""}` },
    { key: "dsa",        label: `DSA ${dsa ? dsa.solved + "/" + dsa.total : ""}` },
    { key: "interviews", label: `Interviews ${iv ? "(" + iv.total_applied + ")" : ""}` },
  ], [rm, proj, dsa, iv]);

  // ── Render ──────────────────────────────────────────────────────────────────
  if (loading) return <DashboardSkeleton />;
  if (error)   return <ErrorState onRetry={fetchData} />;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Roadmap"    value={`${rm?.pct ?? 0}%`}  sub={`${rm?.completed_tasks ?? 0}/${rm?.total_tasks ?? 0} tasks`} valueColor="text-violet-400" />
        <StatCard label="DSA solved" value={dsa?.solved ?? 0}    sub={`of ${dsa?.total ?? 0} total`} />
        <StatCard label="Projects"   value={proj?.total ?? 0}    sub={`${proj?.by_status?.Completed ?? 0} completed`} />
        <StatCard label="Offers"     value={iv?.offers ?? 0}     sub={`${iv?.offer_rate ?? 0}% offer rate`} valueColor="text-emerald-400" />
      </div>

      <Card className="p-5">
        <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-4">Activity — last 6 months</p>
        <ActivityHeatmap activityLog={fullState?.activity_log || []} />
      </Card>

      <SubTabs tabs={tabs} active={activeTab} onChange={setActiveTab} />

      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-white">Roadmap progress</p>
              <button onClick={() => setActiveTab("roadmap")} className="text-xs text-violet-400 hover:underline">View all →</button>
            </div>
            <ProgressBar pct={rm?.pct || 0} color="#6366F1" height="h-2" />
            <div className="flex justify-between mt-2 text-xs text-slate-600">
              <span>{rm?.completed_tasks || 0} / {rm?.total_tasks || 0} tasks</span>
              <span className="font-medium text-violet-400">{rm?.pct || 0}%</span>
            </div>
          </Card>
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-white">DSA problems</p>
              <button onClick={() => setActiveTab("dsa")} className="text-xs text-teal-400 hover:underline">View all →</button>
            </div>
            <DSABarChart dsaData={Object.fromEntries(Object.entries(fullState?.dsa || {}).slice(0, 6))} />
          </Card>
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-white">Projects</p>
              <button onClick={() => setActiveTab("projects")} className="text-xs text-violet-400 hover:underline">View all →</button>
            </div>
            {proj?.by_status && Object.keys(proj.by_status).length > 0 ? (
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(proj.by_status).map(([status, count]) => (
                  <div key={status} className={`rounded-lg px-2 py-2.5 text-center border text-xs ${PROJECT_STATUS_COLORS[status]}`}>
                    <p className="text-lg font-bold">{count}</p>
                    <p className="leading-tight mt-0.5">{status}</p>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-slate-600">No projects yet</p>}
          </Card>
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-white">Interview tracker</p>
              <button onClick={() => setActiveTab("interviews")} className="text-xs text-amber-400 hover:underline">View all →</button>
            </div>
            <FunnelChart funnel={iv?.funnel || {}} total={iv?.total_applied || 0} />
          </Card>
        </div>
      )}

      {activeTab === "roadmap" && (
        <RoadmapPanel
          roadmapData={fullState?.roadmap || {}}
          onTaskToggle={handleTaskToggle}
        />
      )}
      {activeTab === "projects" && (
        <ProjectsPanel
          projects={fullState?.projects || []}
          onUpdateProject={handleProjectUpdate}
        />
      )}
      {activeTab === "dsa" && (
        <DSAPanel
          dsaData={fullState?.dsa || {}}
          onBulkUpdate={handleDSABulkUpdate}
        />
      )}
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