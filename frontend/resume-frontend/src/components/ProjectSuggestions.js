import React, { useState } from "react";

// ─── Icons ────────────────────────────────────────────────────────────────────

const GithubIcon = () => (
  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
  </svg>
);

const ClockIcon = () => (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const StarIcon = ({ filled }) => (
  <svg className={`w-4 h-4 ${filled ? "text-amber-400" : "text-gray-200"}`} fill="currentColor" viewBox="0 0 20 20">
    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
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

// ─── Difficulty config ────────────────────────────────────────────────────────

const DIFFICULTY = {
  beginner: {
    stars: 1,
    label: "Beginner",
    color: "text-emerald-600 bg-emerald-50 border-emerald-200",
    dot: "bg-emerald-500",
  },
  intermediate: {
    stars: 2,
    label: "Intermediate",
    color: "text-amber-600 bg-amber-50 border-amber-200",
    dot: "bg-amber-500",
  },
  advanced: {
    stars: 3,
    label: "Advanced",
    color: "text-red-600 bg-red-50 border-red-200",
    dot: "bg-red-500",
  },
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

const DifficultyStars = ({ level }) => {
  const cfg = DIFFICULTY[level?.toLowerCase()] || DIFFICULTY.intermediate;
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3].map((i) => (
        <StarIcon key={i} filled={i <= cfg.stars} />
      ))}
    </div>
  );
};

// ─── Project card ─────────────────────────────────────────────────────────────

const CARD_ACCENTS = [
  "border-t-indigo-500",
  "border-t-purple-500",
  "border-t-sky-500",
  "border-t-emerald-500",
  "border-t-orange-500",
];

const ProjectCard = ({ project, index, saved, onToggleSave }) => {
  const [expanded, setExpanded] = useState(false);
  const accent = CARD_ACCENTS[index % CARD_ACCENTS.length];

  return (
    <div className={`bg-white rounded-2xl border-2 border-gray-100 border-t-4 ${accent} shadow-sm hover:shadow-lg transition-all duration-200 overflow-hidden`}>
      {/* Card header */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <DifficultyBadge level={project.difficulty} />
              <span className="flex items-center gap-1 text-xs text-gray-400">
                <ClockIcon />
                {project.estimated_weeks}w · {project.hours_per_week}h/wk
              </span>
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white leading-snug">{project.title}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{project.tagline}</p>
          </div>

          {/* Save / bookmark button */}
          <button
            onClick={() => onToggleSave(project.id)}
            className={`flex-shrink-0 p-2 rounded-xl border-2 transition-all ${saved ? "bg-indigo-600 border-indigo-600 text-white" : "border-gray-200 text-gray-400 hover:border-indigo-300 hover:text-indigo-500"}`}
            title={saved ? "Remove from portfolio" : "Save to portfolio"}
          >
            <CheckIcon />
          </button>
        </div>

        {/* Stars */}
        <DifficultyStars level={project.difficulty} />

        {/* Tech stack pills */}
        {project.tech_stack && (
          <div className="flex flex-wrap gap-1.5 mt-3 dark:text-gray-300">
            {project.tech_stack.map((t, i) => (
              <span key={i} className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs px-2.5 py-1 rounded-full font-medium">
                {t}
              </span>
            ))}
          </div>
        )}

        {/* Impact statement */}
        {project.impact_statement && (
          <div className="mt-4 bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 rounded-xl p-3">
            <p className="text-xs font-semibold text-indigo-700 mb-0.5">💼 Why this impresses recruiters</p>
            <p className="text-sm text-indigo-800">{project.impact_statement}</p>
          </div>
        )}
      </div>

      {/* Expand toggle */}
      <button
        className="w-full flex items-center justify-between px-5 py-3 bg-gray-50 dark:bg-gray-700 border-t border-gray-100 dark:border-gray-600 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
        onClick={() => setExpanded((o) => !o)}
      >
        <span className="font-medium dark:text-gray-300">{expanded ? "Show less" : "View details"}</span>
        <ChevronIcon open={expanded} />
      </button>

      {/* Expanded section */}
      {expanded && (
        <div className="px-5 pb-5 pt-4 border-t border-gray-100 dark:border-gray-700 space-y-4">
          {/* Description */}
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{project.description}</p>

          {/* Key features */}
          {project.key_features && project.key_features.length > 0 && (
            <div>
              <p className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Key Features to Build</p>
              <ul className="space-y-1">
                {project.key_features.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="flex-shrink-0 mt-0.5 w-4 h-4 rounded-full bg-indigo-100 text-indigo-600 text-xs flex items-center justify-center font-bold">
                      {i + 1}
                    </span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Learning outcomes */}
          {project.learning_outcomes && project.learning_outcomes.length > 0 && (
            <div>
              <p className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">What You'll Learn</p>
              <div className="flex flex-wrap gap-2">
                {project.learning_outcomes.map((o, i) => (
                  <span key={i} className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full">
                    ✓ {o}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Skills from gaps */}
          {project.skills_from_gaps && project.skills_from_gaps.length > 0 && (
            <div>
              <p className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Addresses Your Skill Gaps</p>
              <div className="flex flex-wrap gap-2">
                {project.skills_from_gaps.map((s, i) => (
                  <span key={i} className="text-xs bg-orange-50 text-orange-700 border border-orange-200 px-2.5 py-1 rounded-full font-medium">
                    ⚡ {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Bonus extensions */}
          {project.bonus_extensions && project.bonus_extensions.length > 0 && (
            <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-3">
              <p className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">🚀 Bonus Extensions</p>
              <ul className="space-y-1">
                {project.bonus_extensions.map((e, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-400">→ {e}</li>
                ))}
              </ul>
            </div>
          )}

          {/* GitHub link */}
          {project.github_template && (
            <a
              href={project.github_template}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 px-4 py-2 rounded-lg transition-colors"
            >
              <GithubIcon /> Browse related repos
            </a>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Main component ───────────────────────────────────────────────────────────

const ProjectSuggestions = ({ projects = [], loading = false }) => {
  const [savedProjects, setSavedProjects] = useState(new Set());
  const [filter, setFilter] = useState("all");

  const toggleSave = (id) => {
    setSavedProjects((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const filteredProjects = filter === "saved"
    ? projects.filter((p) => savedProjects.has(p.id))
    : filter === "all"
    ? projects
    : projects.filter((p) => p.difficulty?.toLowerCase() === filter);

  // ── Loading skeleton ──
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse h-8 bg-gray-200 rounded w-1/3 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-2xl border-2 border-gray-100 dark:border-gray-700 border-t-4 border-t-gray-200 p-5 space-y-3 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/3" />
              <div className="h-6 bg-gray-100 rounded w-3/4" />
              <div className="h-4 bg-gray-100 rounded w-full" />
              <div className="flex gap-2">
                <div className="h-6 w-16 bg-gray-100 rounded-full" />
                <div className="h-6 w-20 bg-gray-100 rounded-full" />
              </div>
            </div>
          ))}
        </div>
        <p className="text-center text-gray-400 text-sm mt-2">Crafting project ideas for you…</p>
      </div>
    );
  }

  // ── Empty state ──
  if (!projects || projects.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-10 text-center">
        <div className="text-5xl mb-4">🛠️</div>
        <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-2">No Projects Yet</h3>
        <p className="text-gray-500 dark:text-gray-400 text-sm">Generate a roadmap to get personalized project suggestions.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-black text-gray-900 dark:text-white">🛠️ Project Suggestions</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-0.5">
            {projects.length} projects tailored to your skill gaps
            {savedProjects.size > 0 && ` · ${savedProjects.size} saved to portfolio`}
          </p>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-1.5 bg-gray-100 dark:bg-gray-700 p-1 rounded-xl text-sm">
          {[
            { key: "all", label: "All" },
            { key: "beginner", label: "Beginner" },
            { key: "intermediate", label: "Intermediate" },
            { key: "advanced", label: "Advanced" },
            { key: "saved", label: `Saved (${savedProjects.size})` },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${filter === key ? "bg-white dark:bg-gray-800 shadow text-gray-900 dark:text-white" : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Portfolio banner ── */}
      {savedProjects.size > 0 && (
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-5 text-white flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="font-bold text-lg">🎯 Portfolio in Progress</p>
            <p className="text-indigo-200 text-sm">
              You've saved {savedProjects.size} project{savedProjects.size !== 1 ? "s" : ""}. Complete them to build a standout portfolio.
            </p>
          </div>
          <button
            onClick={() => setFilter("saved")}
            className="flex-shrink-0 bg-white text-indigo-700 font-semibold px-5 py-2.5 rounded-xl hover:bg-indigo-50 transition-colors text-sm"
          >
            View Saved
          </button>
        </div>
      )}

      {/* ── Project grid ── */}
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredProjects.map((project, i) => (
            <ProjectCard
              key={project.id || i}
              project={project}
              index={i}
              saved={savedProjects.has(project.id)}
              onToggleSave={toggleSave}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-10 text-gray-400 dark:text-gray-500">
          <p className="text-4xl mb-3">🔍</p>
          <p>No projects match this filter.</p>
        </div>
      )}
    </div>
  );
};

export default ProjectSuggestions;