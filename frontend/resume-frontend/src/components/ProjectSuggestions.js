import React, { useState } from "react";

const GithubIcon = () => (
  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
  </svg>
);

const ChevronIcon = ({ open }) => (
  <svg className={`w-4 h-4 transition-transform duration-200 ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
);

const CheckIcon = () => (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
  </svg>
);

const DIFFICULTY = {
  beginner:     { stars: 1, label: "Beginner",     color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", dot: "bg-emerald-400" },
  intermediate: { stars: 2, label: "Intermediate", color: "text-amber-400 bg-amber-500/10 border-amber-500/20",       dot: "bg-amber-400" },
  advanced:     { stars: 3, label: "Advanced",     color: "text-red-400 bg-red-500/10 border-red-500/20",             dot: "bg-red-400" },
};

const DifficultyBadge = ({ level }) => {
  const cfg = DIFFICULTY[level?.toLowerCase()] || DIFFICULTY.intermediate;
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${cfg.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
};

const CARD_ACCENT_COLORS = [
  "from-violet-500 to-purple-600",
  "from-blue-500 to-indigo-600",
  "from-teal-500 to-emerald-600",
  "from-amber-500 to-orange-600",
  "from-pink-500 to-rose-600",
];

const ProjectCard = ({ project, index, saved, onToggleSave }) => {
  const [expanded, setExpanded] = useState(false);
  const accentGradient = CARD_ACCENT_COLORS[index % CARD_ACCENT_COLORS.length];

  return (
    <div className="rounded-2xl border border-white/8 overflow-hidden transition-all hover:border-white/15"
      style={{ background: "rgba(255,255,255,0.03)" }}>
      {/* Gradient top accent */}
      <div className={`h-1 bg-gradient-to-r ${accentGradient}`} />

      <div className="p-5">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <DifficultyBadge level={project.difficulty} />
              {project.estimated_weeks && (
                <span className="text-xs text-slate-500">
                  {project.estimated_weeks}w · {project.hours_per_week}h/wk
                </span>
              )}
            </div>
            <h3 className="text-base font-semibold text-white leading-snug">{project.title}</h3>
            <p className="text-xs text-slate-400 mt-0.5">{project.tagline}</p>
          </div>
          <button
            onClick={() => onToggleSave(project.id)}
            className={`flex-shrink-0 p-2 rounded-xl border-2 transition-all ${
              saved
                ? "bg-violet-600 border-violet-600 text-white"
                : "border-white/10 text-slate-500 hover:border-violet-500/40 hover:text-violet-400"
            }`}
            title={saved ? "Remove from portfolio" : "Save to portfolio"}>
            <CheckIcon />
          </button>
        </div>

        {/* Tech stack */}
        {project.tech_stack && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {project.tech_stack.map((t, i) => (
              <span key={i} className="bg-white/5 border border-white/8 text-slate-400 text-xs px-2.5 py-1 rounded-full">{t}</span>
            ))}
          </div>
        )}

        {/* Impact statement */}
        {project.impact_statement && (
          <div className="mt-4 rounded-xl p-3 border border-violet-500/15"
            style={{ background: "rgba(124,58,237,0.08)" }}>
            <p className="text-xs font-semibold text-violet-300 mb-0.5">💼 Why recruiters love this</p>
            <p className="text-xs text-slate-300">{project.impact_statement}</p>
          </div>
        )}
      </div>

      {/* Expand toggle */}
      <button
        className="w-full flex items-center justify-between px-5 py-3 border-t border-white/5 text-sm text-slate-400 hover:text-slate-200 hover:bg-white/3 transition-colors"
        onClick={() => setExpanded(o => !o)}>
        <span className="font-medium">{expanded ? "Show less" : "View details"}</span>
        <ChevronIcon open={expanded} />
      </button>

      {expanded && (
        <div className="px-5 pb-5 pt-3 border-t border-white/5 space-y-4">
          {project.description && (
            <p className="text-sm text-slate-300 leading-relaxed">{project.description}</p>
          )}

          {project.key_features?.length > 0 && (
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Key Features to Build</p>
              <ul className="space-y-1">
                {project.key_features.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                    <span className="flex-shrink-0 mt-0.5 w-4 h-4 rounded-full bg-violet-500/20 text-violet-400 text-xs flex items-center justify-center font-bold">{i+1}</span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {project.learning_outcomes?.length > 0 && (
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">What You'll Learn</p>
              <div className="flex flex-wrap gap-2">
                {project.learning_outcomes.map((o, i) => (
                  <span key={i} className="text-xs bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded-full">✓ {o}</span>
                ))}
              </div>
            </div>
          )}

          {project.skills_from_gaps?.length > 0 && (
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Addresses Your Skill Gaps</p>
              <div className="flex flex-wrap gap-2">
                {project.skills_from_gaps.map((s, i) => (
                  <span key={i} className="text-xs bg-amber-500/10 border border-amber-500/20 text-amber-300 px-2.5 py-1 rounded-full font-medium">⚡ {s}</span>
                ))}
              </div>
            </div>
          )}

          {project.bonus_extensions?.length > 0 && (
            <div className="rounded-xl p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">🚀 Bonus Extensions</p>
              <ul className="space-y-1">
                {project.bonus_extensions.map((e, i) => (
                  <li key={i} className="text-xs text-slate-400">→ {e}</li>
                ))}
              </ul>
            </div>
          )}

          {project.github_template && (
            <a href={project.github_template} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 bg-white/5 border border-white/8 hover:bg-white/8 px-4 py-2 rounded-xl transition-colors">
              <GithubIcon /> Browse related repos
            </a>
          )}
        </div>
      )}
    </div>
  );
};

const ProjectSuggestions = ({ projects = [], loading = false }) => {
  const [savedProjects, setSavedProjects] = useState(new Set());
  const [filter, setFilter] = useState("all");

  const toggleSave = (id) => {
    setSavedProjects(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const filteredProjects = filter === "saved"
    ? projects.filter(p => savedProjects.has(p.id))
    : filter === "all"
    ? projects
    : projects.filter(p => p.difficulty?.toLowerCase() === filter);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[0,1,2,3].map(i => (
            <div key={i} className="rounded-2xl border border-white/8 p-5 space-y-3 animate-pulse"
              style={{ background: "rgba(255,255,255,0.03)" }}>
              <div className="h-4 bg-white/5 rounded w-1/3" />
              <div className="h-5 bg-white/8 rounded w-3/4" />
              <div className="h-4 bg-white/5 rounded w-full" />
              <div className="flex gap-2">
                <div className="h-6 w-16 bg-white/5 rounded-full" />
                <div className="h-6 w-20 bg-white/5 rounded-full" />
              </div>
            </div>
          ))}
        </div>
        <p className="text-center text-slate-500 text-sm">Crafting project ideas for you…</p>
      </div>
    );
  }

  if (!projects || projects.length === 0) {
    return (
      <div className="rounded-2xl border border-white/8 p-10 text-center"
        style={{ background: "rgba(255,255,255,0.03)" }}>
        <div className="text-4xl mb-4">🛠️</div>
        <h3 className="text-sm font-semibold text-white mb-1">No Projects Yet</h3>
        <p className="text-xs text-slate-500">Generate a roadmap to get personalized project suggestions.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white">🛠️ Project Suggestions</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {projects.length} projects · tailored to your skill gaps
            {savedProjects.size > 0 && ` · ${savedProjects.size} saved`}
          </p>
        </div>
        <div className="flex gap-1 p-1 rounded-xl border border-white/8" style={{ background: "rgba(255,255,255,0.03)" }}>
          {[
            { key: "all",          label: "All" },
            { key: "beginner",     label: "Beginner" },
            { key: "intermediate", label: "Intermediate" },
            { key: "advanced",     label: "Advanced" },
            { key: "saved",        label: `Saved (${savedProjects.size})` },
          ].map(({ key, label }) => (
            <button key={key} onClick={() => setFilter(key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filter === key
                  ? "bg-violet-600/20 border border-violet-500/30 text-violet-300"
                  : "text-slate-500 hover:text-slate-300"
              }`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {savedProjects.size > 0 && (
        <div className="rounded-2xl p-5 flex items-center justify-between gap-4 flex-wrap"
          style={{ background: "linear-gradient(135deg, rgba(124,58,237,0.15), rgba(37,99,235,0.1))", border: "1px solid rgba(124,58,237,0.2)" }}>
          <div>
            <p className="font-semibold text-white text-sm">🎯 Portfolio in Progress</p>
            <p className="text-slate-400 text-xs mt-0.5">
              {savedProjects.size} project{savedProjects.size !== 1 ? "s" : ""} saved. Complete them to build a standout portfolio.
            </p>
          </div>
          <button onClick={() => setFilter("saved")}
            className="flex-shrink-0 bg-white/10 hover:bg-white/15 text-white font-medium px-4 py-2 rounded-xl text-xs transition">
            View Saved
          </button>
        </div>
      )}

      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredProjects.map((project, i) => (
            <ProjectCard key={project.id || i} project={project} index={i}
              saved={savedProjects.has(project.id)} onToggleSave={toggleSave} />
          ))}
        </div>
      ) : (
        <div className="text-center py-10 text-slate-600">
          <p className="text-3xl mb-3">🔍</p>
          <p className="text-sm">No projects match this filter.</p>
        </div>
      )}
    </div>
  );
};

export default ProjectSuggestions;