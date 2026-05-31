import React, { useState } from "react";

// ─── Icons ────────────────────────────────────────────────────────────────────

const CheckIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
  </svg>
);

const ClockIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const BookIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const TrophyIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
  </svg>
);

const ChevronIcon = ({ open }) => (
  <svg className={`w-5 h-5 transition-transform duration-200 ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
);

// ✅ FIX: The original file had `// const LinkIcon = () => (` (commented-out opening)
// but the closing `);` was left un-commented, causing "Unexpected token" at line 39.
// Removed the entire dead block. ExternalLinkIcon is the only icon needed here.
const ExternalLinkIcon = () => (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
  </svg>
);

// ─── Resource type badge (dark theme) ─────────────────────────────────────────

const RESOURCE_COLORS = {
  course:   "bg-purple-500/15 text-purple-400 border-purple-500/25",
  book:     "bg-amber-500/15 text-amber-400 border-amber-500/25",
  docs:     "bg-sky-500/15 text-sky-400 border-sky-500/25",
  video:    "bg-red-500/15 text-red-400 border-red-500/25",
  practice: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25",
  github:   "bg-white/8 text-slate-400 border-white/10",
  tutorial: "bg-blue-500/15 text-blue-400 border-blue-500/25",
};

const ResourceBadge = ({ type }) => (
  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${RESOURCE_COLORS[type?.toLowerCase()] || "bg-white/8 text-slate-500 border-white/10"}`}>
    {type || "resource"}
  </span>
);

// ─── Week card (dark theme) ───────────────────────────────────────────────────

const WeekCard = ({ task, completed, onToggle }) => {
  const [open, setOpen] = useState(false);

  const isValidUrl = (string) => {
    try { new URL(string); return true; } catch (_) { return false; }
  };

  return (
    <div className={`rounded-xl border-2 transition-all duration-200 ${
      completed
        ? "border-emerald-500/40 bg-emerald-500/5"
        : "border-white/8 hover:border-violet-500/30"
    }`} style={!completed ? { background: "rgba(255,255,255,0.02)" } : undefined}>

      <div className="flex items-center gap-3 p-4 cursor-pointer" onClick={() => setOpen(o => !o)}>
        <button
          onClick={(e) => { e.stopPropagation(); onToggle(); }}
          className={`flex-shrink-0 w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all ${
            completed ? "bg-emerald-500 border-emerald-500 text-white" : "border-white/20 hover:border-emerald-500/50"
          }`}
        >
          {completed && <CheckIcon />}
        </button>

        <span className={`flex-shrink-0 text-xs font-bold px-2.5 py-1 rounded-full ${
          completed ? "bg-emerald-500/20 text-emerald-300" : "bg-violet-500/15 text-violet-300"
        }`}>
          Week {task.week}
        </span>

        <div className="flex-1 min-w-0">
          <p className={`font-semibold text-sm truncate ${completed ? "text-slate-500 line-through" : "text-white"}`}>
            {task.topic}
          </p>
          <p className="text-xs text-slate-500 truncate">{task.milestone}</p>
        </div>

        <div className="flex-shrink-0 flex items-center gap-1 text-slate-600 text-xs">
          <ClockIcon />
          {task.hours_per_week}h/wk
        </div>

        <ChevronIcon open={open} />
      </div>

      {open && (
        <div className="border-t border-white/5 p-4 space-y-4">
          <p className="text-sm text-slate-300 leading-relaxed">{task.description}</p>

          {task.resources?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <BookIcon /> Resources
              </p>
              <div className="space-y-2">
                {task.resources.map((r, i) => {
                  const hasValidUrl = r.url && isValidUrl(r.url);
                  return (
                    <div key={i} className="flex flex-wrap items-center gap-2 p-2 rounded-lg border border-white/5"
                      style={{ background: "rgba(255,255,255,0.03)" }}>
                      <ResourceBadge type={r.type} />
                      {hasValidUrl ? (
                        <a href={r.url} target="_blank" rel="noopener noreferrer"
                          className="text-sm text-violet-400 hover:text-violet-300 hover:underline flex items-center gap-1 flex-1">
                          {r.title}<ExternalLinkIcon />
                        </a>
                      ) : (
                        <span className="text-sm text-slate-300 flex-1">
                          {r.title}
                          {!r.url && <span className="ml-2 text-xs text-slate-600">(Search on Coursera/Udemy)</span>}
                        </span>
                      )}
                      {r.duration && (
                        <span className="text-xs text-slate-600 bg-white/5 px-2 py-1 rounded-full">{r.duration}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="flex items-start gap-2 rounded-xl p-3 border border-amber-500/20"
            style={{ background: "rgba(245,158,11,0.07)" }}>
            <TrophyIcon />
            <div>
              <p className="text-xs font-semibold text-amber-400">Week Milestone</p>
              <p className="text-sm text-amber-300">{task.milestone}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Phase section (dark theme) ───────────────────────────────────────────────

const PhaseSection = ({ phase, completedWeeks, onToggleWeek }) => {
  const [open, setOpen] = useState(true);
  const totalWeeks     = phase.weekly_tasks?.length || 0;
  const completedCount = phase.weekly_tasks?.filter(t => completedWeeks.has(t.week)).length || 0;
  const pct            = totalWeeks > 0 ? Math.round((completedCount / totalWeeks) * 100) : 0;

  const PHASE_GRADIENTS = [
    "from-indigo-500 to-purple-500",
    "from-sky-500 to-cyan-500",
    "from-emerald-500 to-teal-500",
    "from-orange-500 to-amber-500",
  ];
  const gradient = PHASE_GRADIENTS[(phase.phase_number - 1) % PHASE_GRADIENTS.length];

  return (
    <div className="rounded-2xl border border-white/8 overflow-hidden">
      <div
        className={`bg-gradient-to-r ${gradient} text-white p-5 cursor-pointer flex items-center justify-between`}
        onClick={() => setOpen(o => !o)}
      >
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-white/20 text-xs font-bold px-2 py-0.5 rounded-full">
              Phase {phase.phase_number}
            </span>
            <span className="text-sm opacity-80">Weeks {phase.weeks}</span>
          </div>
          <h3 className="text-lg font-bold">{phase.phase_title}</h3>
          <p className="text-sm opacity-80 mt-0.5">{phase.focus}</p>
        </div>
        <div className="text-right flex flex-col items-end gap-2">
          <span className="text-2xl font-black">{pct}%</span>
          <ChevronIcon open={open} />
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-white/5">
        <div
          className={`h-full bg-gradient-to-r ${gradient} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {open && (
        <div className="p-4 space-y-3" style={{ background: "rgba(255,255,255,0.02)" }}>
          {phase.weekly_tasks?.map(task => (
            <WeekCard
              key={task.week}
              task={task}
              completed={completedWeeks.has(task.week)}
              onToggle={() => onToggleWeek(task.week)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Main component ───────────────────────────────────────────────────────────

const RoadmapView = ({ roadmap, loading = false }) => {
  const [completedWeeks, setCompletedWeeks] = useState(new Set());

  const toggleWeek = (week) => {
    setCompletedWeeks(prev => {
      const next = new Set(prev);
      next.has(week) ? next.delete(week) : next.add(week);
      return next;
    });
  };

  // ── Loading skeleton (dark) ──
  if (loading) {
    return (
      <div className="rounded-2xl border border-white/8 p-8" style={{ background: "rgba(255,255,255,0.03)" }}>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-white/5 rounded w-2/3" />
          <div className="h-4 bg-white/5 rounded w-full" />
          <div className="h-4 bg-white/5 rounded w-5/6" />
          <div className="grid grid-cols-3 gap-4 mt-6">
            {[0, 1, 2].map(i => (
              <div key={i} className="h-20 bg-white/5 rounded-xl" />
            ))}
          </div>
          <div className="h-40 bg-white/5 rounded-xl mt-4" />
        </div>
        <p className="text-center text-slate-500 text-sm mt-4">Generating your personalised roadmap…</p>
      </div>
    );
  }

  // ── Empty state (dark) ──
  if (!roadmap) {
    return (
      <div className="rounded-2xl border border-white/8 p-10 text-center"
        style={{ background: "rgba(255,255,255,0.03)" }}>
        <div className="text-5xl mb-4">🗺️</div>
        <h3 className="text-sm font-semibold text-white mb-1">No Roadmap Yet</h3>
        <p className="text-xs text-slate-500">Generate a roadmap to get your personalised learning plan.</p>
      </div>
    );
  }

  // ── Corrupt / incomplete data guard ──
  const isValid = roadmap.title && Array.isArray(roadmap.phases) && roadmap.phases.length > 0;

  if (!isValid) {
    return (
      <div className="rounded-2xl border border-amber-500/25 p-10 text-center"
        style={{ background: "rgba(245,158,11,0.06)" }}>
        <div className="text-4xl mb-4">⚠️</div>
        <h3 className="text-sm font-semibold text-amber-400 mb-2">Roadmap data is incomplete</h3>
        <p className="text-xs text-slate-500">
          The AI returned an incomplete response. Please try generating the roadmap again.
        </p>
      </div>
    );
  }

  const totalWeeks     = roadmap.phases?.flatMap(p => p.weekly_tasks || []).length || 0;
  const completedCount = completedWeeks.size;
  const overallPct     = totalWeeks > 0 ? Math.round((completedCount / totalWeeks) * 100) : 0;

  return (
    <div className="space-y-5">
      {/* Header card */}
      <div className="rounded-2xl p-7 text-white"
        style={{
          background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%)",
          boxShadow: "0 8px 32px rgba(124,58,237,0.3)",
        }}>
        <p className="text-indigo-200 text-xs font-medium uppercase tracking-widest mb-1">Your Learning Roadmap</p>
        <h2 className="text-2xl font-black mb-2">{roadmap.title}</h2>
        <p className="text-indigo-100 text-sm leading-relaxed mb-5 opacity-90">{roadmap.summary}</p>

        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "Duration",  value: `${roadmap.duration_weeks}w` },
            { label: "Est. Hours", value: `${roadmap.total_hours_estimated}h` },
            { label: "Completed", value: `${completedCount}/${totalWeeks}` },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white/15 rounded-xl p-3 text-center backdrop-blur-sm">
              <p className="text-xl font-black">{value}</p>
              <p className="text-xs text-indigo-200 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        <div className="mt-4">
          <div className="flex justify-between text-xs text-indigo-200 mb-1">
            <span>Overall Progress</span><span>{overallPct}%</span>
          </div>
          <div className="h-2 bg-white/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-white rounded-full transition-all duration-500"
              style={{ width: `${overallPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Phases */}
      {roadmap.phases?.map(phase => (
        <PhaseSection
          key={phase.phase_number}
          phase={phase}
          completedWeeks={completedWeeks}
          onToggleWeek={toggleWeek}
        />
      ))}

      {/* Final milestone */}
      {roadmap.final_milestone && (
        <div className="rounded-2xl p-5 flex items-start gap-4 border border-amber-500/20"
          style={{ background: "rgba(245,158,11,0.07)" }}>
          <div className="text-3xl">🏆</div>
          <div>
            <p className="font-bold text-amber-400 text-sm">Final Milestone</p>
            <p className="text-amber-300 text-sm mt-1">{roadmap.final_milestone}</p>
          </div>
        </div>
      )}

      {/* Tips */}
      {roadmap.tips?.length > 0 && (
        <div className="rounded-2xl border border-white/8 p-5"
          style={{ background: "rgba(255,255,255,0.03)" }}>
          <h3 className="font-semibold text-white text-sm mb-3 flex items-center gap-2">
            💡 Pro Tips
          </h3>
          <ul className="space-y-2">
            {roadmap.tips.map((tip, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-violet-500/20 text-violet-400 text-xs flex items-center justify-center font-bold mt-0.5">
                  {i + 1}
                </span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default RoadmapView;