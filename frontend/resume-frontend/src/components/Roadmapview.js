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

const LinkIcon = () => (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
  </svg>
);

// ─── Resource type badge ───────────────────────────────────────────────────────

const RESOURCE_COLORS = {
  course: "bg-purple-100 text-purple-700 border-purple-200",
  book: "bg-amber-100 text-amber-700 border-amber-200",
  docs: "bg-sky-100 text-sky-700 border-sky-200",
  video: "bg-red-100 text-red-700 border-red-200",
  practice: "bg-emerald-100 text-emerald-700 border-emerald-200",
};

const ResourceBadge = ({ type }) => (
  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${RESOURCE_COLORS[type] || "bg-gray-100 text-gray-600 border-gray-200"}`}>
    {type}
  </span>
);

// ─── Week card ────────────────────────────────────────────────────────────────

const WeekCard = ({ task, completed, onToggle }) => {
  const [open, setOpen] = useState(false);

  return (
    <div className={`rounded-xl border-2 transition-all duration-200 ${completed ? "border-green-300 bg-green-50" : "border-gray-200 bg-white hover:border-indigo-300"}`}>
      {/* Header row */}
      <div className="flex items-center gap-3 p-4 cursor-pointer" onClick={() => setOpen((o) => !o)}>
        {/* Complete toggle */}
        <button
          onClick={(e) => { e.stopPropagation(); onToggle(); }}
          className={`flex-shrink-0 w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all ${completed ? "bg-green-500 border-green-500 text-white" : "border-gray-300 hover:border-green-400"}`}
        >
          {completed && <CheckIcon />}
        </button>

        {/* Week label */}
        <span className={`flex-shrink-0 text-xs font-bold px-2.5 py-1 rounded-full ${completed ? "bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200" : "bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300"}`}>
          Week {task.week}
        </span>

        {/* Topic */}
        <div className="flex-1 min-w-0">
          <p className={`font-semibold text-sm truncate ${completed ? "text-gray-500 line-through" : "text-gray-900 dark:text-white"}`}>
            {task.topic}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{task.milestone}</p>
        </div>

        {/* Hours */}
        <div className="flex-shrink-0 flex items-center gap-1 text-gray-400 dark:text-gray-500 text-xs">
          <ClockIcon />
          {task.hours_per_week}h/wk
        </div>

        <ChevronIcon open={open} />
      </div>

      {/* Expanded content */}
      {open && (
        <div className="border-t border-gray-100 dark:border-gray-700 p-4 space-y-4">
          <p className="text-sm text-gray-700 dark:text-gray-300">{task.description}</p>

          {/* Resources */}
          {task.resources && task.resources.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-1">
                <BookIcon /> Resources
              </p>
              <div className="space-y-2 dark:text-gray-300">
                {task.resources.map((r, i) => (
                  <div key={i} className="flex items-center gap-2 flex-wrap">
                    <ResourceBadge type={r.type} />
                    {r.url ? (
                      <a href={r.url} target="_blank" rel="noopener noreferrer"
                        className="text-sm text-indigo-600 hover:underline flex items-center gap-1">
                        {r.title} <LinkIcon />
                      </a>
                    ) : (
                      <span className="text-sm text-gray-700 dark:text-gray-300">{r.title}</span>
                    )}
                    {r.duration && (
                      <span className="text-xs text-gray-400">· {r.duration}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Milestone */}
          <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3">
            <TrophyIcon />
            <div>
              <p className="text-xs font-semibold text-amber-800">Week Milestone</p>
              <p className="text-sm text-amber-700">{task.milestone}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Phase section ────────────────────────────────────────────────────────────

const PhaseSection = ({ phase, completedWeeks, onToggleWeek }) => {
  const [open, setOpen] = useState(true);
  const totalWeeks = phase.weekly_tasks?.length || 0;
  const completedCount = phase.weekly_tasks?.filter((t) => completedWeeks.has(t.week)).length || 0;
  const pct = totalWeeks > 0 ? Math.round((completedCount / totalWeeks) * 100) : 0;

  const PHASE_COLORS = [
    "from-indigo-500 to-purple-500",
    "from-sky-500 to-cyan-500",
    "from-emerald-500 to-teal-500",
    "from-orange-500 to-amber-500",
  ];
  const gradient = PHASE_COLORS[(phase.phase_number - 1) % PHASE_COLORS.length];

  return (
    <div className="rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
      {/* Phase header */}
      <div
        className={`bg-gradient-to-r ${gradient} text-white p-5 cursor-pointer flex items-center justify-between`}
        onClick={() => setOpen((o) => !o)}
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
      <div className="h-1.5 bg-gray-100 dark:bg-gray-700">
        <div
          className={`h-full bg-gradient-to-r ${gradient} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Weeks */}
      {open && (
        <div className="p-4 space-y-3 bg-white dark:bg-gray-800">
          {phase.weekly_tasks?.map((task) => (
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
    setCompletedWeeks((prev) => {
      const next = new Set(prev);
      next.has(week) ? next.delete(week) : next.add(week);
      return next;
    });
  };

  // ── Loading skeleton ──
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-2/3" />
          <div className="h-4 bg-gray-100 rounded w-full" />
          <div className="h-4 bg-gray-100 rounded w-5/6" />
          <div className="grid grid-cols-3 gap-4 mt-6">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-20 bg-gray-100 rounded-xl" />
            ))}
          </div>
          <div className="h-40 bg-gray-100 rounded-xl mt-4" />
        </div>
        <p className="text-center text-gray-400 text-sm mt-4">Generating your personalized roadmap…</p>
      </div>
    );
  }

  // ── Empty state ──
  if (!roadmap) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-10 text-center">
        <div className="text-5xl mb-4">🗺️</div>
        <h3 className="text-xl font-bold text-gray-800 mb-2">No Roadmap Yet</h3>
        <p className="text-gray-500 text-sm">Match with a job and click "Generate Roadmap" to get your personalized learning plan.</p>
      </div>
    );
  }

  const totalWeeks = roadmap.phases?.flatMap((p) => p.weekly_tasks || []).length || 0;
  const completedCount = completedWeeks.size;
  const overallPct = totalWeeks > 0 ? Math.round((completedCount / totalWeeks) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* ── Header card ── */}
      <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 rounded-2xl p-8 text-white shadow-xl">
        <p className="text-indigo-200 text-sm font-medium uppercase tracking-widest mb-1">Your Learning Roadmap</p>
        <h2 className="text-3xl font-black mb-2">{roadmap.title}</h2>
        <p className="text-indigo-100 text-sm leading-relaxed mb-6">{roadmap.summary}</p>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Duration", value: `${roadmap.duration_weeks} weeks` },
            { label: "Est. Hours", value: `${roadmap.total_hours_estimated}h` },
            { label: "Completed", value: `${completedCount}/${totalWeeks} weeks` },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white/15 rounded-xl p-3 text-center backdrop-blur-sm">
              <p className="text-2xl font-black">{value}</p>
              <p className="text-xs text-indigo-200 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {/* Overall progress */}
        <div className="mt-5">
          <div className="flex justify-between text-xs text-indigo-200 mb-1">
            <span>Overall Progress</span>
            <span>{overallPct}%</span>
          </div>
          <div className="h-2.5 bg-white/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-white rounded-full transition-all duration-500"
              style={{ width: `${overallPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* ── Phases ── */}
      {roadmap.phases?.map((phase) => (
        <PhaseSection
          key={phase.phase_number}
          phase={phase}
          completedWeeks={completedWeeks}
          onToggleWeek={toggleWeek}
        />
      ))}

      {/* ── Final milestone ── */}
      {roadmap.final_milestone && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300 rounded-2xl p-6 flex items-start gap-4">
          <div className="text-3xl">🏆</div>
          <div>
            <p className="font-bold text-amber-900 text-lg">Final Milestone</p>
            <p className="text-amber-800 text-sm mt-1">{roadmap.final_milestone}</p>
          </div>
        </div>
      )}

      {/* ── Tips ── */}
      {roadmap.tips && roadmap.tips.length > 0 && (
        <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-2xl p-6">
          <h3 className="font-bold text-gray-800 dark:text-white mb-3 flex items-center gap-2">
            <span>💡</span> Pro Tips
          </h3>
          <ul className="space-y-2 dark:text-gray-300">
            {roadmap.tips.map((tip, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-indigo-100 text-indigo-600 text-xs flex items-center justify-center font-bold mt-0.5">
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