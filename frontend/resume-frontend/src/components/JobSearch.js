import React, { useState } from "react";

const Ico = ({ d, className = "w-4 h-4" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const I = {
  search: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
  pin:    "M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z",
  filter: "M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z",
  check:  "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
  brief:  "M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
};

const POPULAR = [
  { query: "software engineer",  location: "India" },
  { query: "data scientist",     location: "Bangalore" },
  { query: "product manager",    location: "Mumbai" },
  { query: "frontend developer", location: "Pune" },
];

const inp = "w-full px-4 py-2.5 text-sm rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none transition";
const sel = inp + " cursor-pointer";

export default function JobSearch({ setJobQuery, setJobLocation, setFilters }) {
  const [query,    setQuery]    = useState("");
  const [location, setLocation] = useState("India");
  const [showF,    setShowF]    = useState(false);
  const [success,  setSuccess]  = useState(false);
  const [error,    setError]    = useState(null);
  const [localF, setLocalF]     = useState({
    experienceLevel: "", minMatchScore: 40, postedWithinDays: 14, excludeRemote: false,
  });

  const handleSearch = (q = query, loc = location) => {
    if (!q.trim()) { setError("Please enter a search term"); return; }
    setError(null);
    setJobQuery(q.trim());
    setJobLocation(loc);
    setFilters(localF);
    setSuccess(true);
    setTimeout(() => setSuccess(false), 2000);
  };

  return (
    <div className="rounded-2xl border border-white/10 bg-white/3 p-5 space-y-4">
      {/* Search row */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Ico d={I.search} className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
            placeholder="e.g. software engineer, data scientist…"
            className="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none transition"
          />
        </div>
        <div className="relative w-44">
          <Ico d={I.pin} className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            value={location}
            onChange={e => setLocation(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
            placeholder="Location"
            className="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none transition"
          />
        </div>
        <button onClick={() => handleSearch()}
          className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-all whitespace-nowrap">
          {success
            ? <><Ico d={I.check} className="w-4 h-4" />Searching…</>
            : <><Ico d={I.search} className="w-4 h-4" />Search</>}
        </button>
        <button onClick={() => setShowF(v => !v)}
          className={`flex items-center gap-1.5 text-sm px-4 py-2.5 rounded-xl border transition ${
            showF ? "bg-violet-500/15 border-violet-500/30 text-violet-300" : "border-white/10 text-slate-400 hover:border-white/20"
          }`}>
          <Ico d={I.filter} className="w-4 h-4" /> Filters
        </button>
      </div>

      {/* Error */}
      {error && <p className="text-xs text-red-400">{error}</p>}

      {/* Filters */}
      {showF && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-3 border-t border-white/5">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5">Experience</label>
            <select value={localF.experienceLevel}
              onChange={e => setLocalF(f => ({ ...f, experienceLevel: e.target.value }))}
              className={sel}>
              <option value="">Any Level</option>
              <option value="entry">Entry Level</option>
              <option value="mid">Mid Level</option>
              <option value="senior">Senior</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5">Min Match %</label>
            <select value={localF.minMatchScore}
              onChange={e => setLocalF(f => ({ ...f, minMatchScore: Number(e.target.value) }))}
              className={sel}>
              {[20, 40, 60, 80].map(v => <option key={v} value={v}>{v}%</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5">Posted Within</label>
            <select value={localF.postedWithinDays}
              onChange={e => setLocalF(f => ({ ...f, postedWithinDays: Number(e.target.value) }))}
              className={sel}>
              {[7, 14, 30, 90].map(d => <option key={d} value={d}>{d} days</option>)}
            </select>
          </div>
          <div className="flex items-end pb-0.5">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={localF.excludeRemote}
                onChange={e => setLocalF(f => ({ ...f, excludeRemote: e.target.checked }))}
                className="w-4 h-4 rounded border-white/20 bg-white/5 text-violet-500 focus:ring-violet-500" />
              <span className="text-sm text-slate-400">Exclude Remote</span>
            </label>
          </div>
        </div>
      )}

      {/* Popular searches */}
      <div>
        <p className="text-xs font-medium text-slate-600 uppercase tracking-widest mb-2">Popular</p>
        <div className="flex flex-wrap gap-2">
          {POPULAR.map((p, i) => (
            <button key={i}
              onClick={() => { setQuery(p.query); setLocation(p.location); handleSearch(p.query, p.location); }}
              className="flex items-center gap-1.5 text-xs border border-white/10 text-slate-400 hover:border-violet-500/30 hover:text-violet-300 px-3 py-1.5 rounded-full transition-all">
              <Ico d={I.brief} className="w-3 h-3" />
              {p.query} · {p.location}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}