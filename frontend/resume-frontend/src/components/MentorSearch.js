import React, { useState, useEffect, useCallback } from 'react';
import API_BASE_URL from '../config';

const Ico = ({ d, className = "w-4 h-4" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const I = {
  search:  "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
  mentor:  "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z",
  star:    "M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z",
  check:   "M5 13l4 4L19 7",
  alert:   "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  cal:     "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z",
  close:   "M6 18L18 6M6 6l12 12",
  clock:   "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
  tag:     "M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z",
  globe:   "M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9",
};

const inp = "w-full px-4 py-2.5 text-sm rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none transition";

const StarRating = ({ rating }) => {
  const full = Math.floor(rating);
  return (
    <div className="flex items-center gap-1">
      {[1,2,3,4,5].map(i => (
        <svg key={i} className={`w-3 h-3 ${i <= full ? "text-amber-400" : "text-white/15"}`} fill="currentColor" viewBox="0 0 20 20">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
      <span className="text-xs text-slate-500 ml-1">{rating?.toFixed(1)}</span>
    </div>
  );
};

const MentorCard = ({ mentor, onBook }) => {
  const [expanded, setExpanded] = useState(false);
  const id = mentor.mentor_id || mentor.id;

  return (
    <div className="rounded-2xl border border-white/8 overflow-hidden transition-all hover:border-violet-500/25"
      style={{ background: "rgba(255,255,255,0.03)" }}>
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start gap-4 mb-4">
          <div className="w-12 h-12 rounded-xl flex-shrink-0 flex items-center justify-center text-lg font-black text-white"
            style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)" }}>
            {(mentor.name || "?").slice(0, 2).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-0.5">
              <h3 className="text-sm font-semibold text-white">{mentor.name}</h3>
              {mentor.available && (
                <span className="text-xs bg-emerald-500/15 border border-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full">
                  Available
                </span>
              )}
            </div>
            <p className="text-xs text-violet-300 font-medium truncate">{mentor.title}</p>
            <p className="text-xs text-slate-500 truncate">{mentor.company}{mentor.experience_years ? ` · ${mentor.experience_years}y exp` : ""}</p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-lg font-black text-white">
              {mentor.currency === "USD" ? "$" : "₹"}{mentor.hourly_rate || mentor.session_fee || 0}
            </p>
            <p className="text-xs text-slate-600">/hr</p>
          </div>
        </div>

        <StarRating rating={mentor.rating || 4.5} />

        {/* Tags */}
        {(mentor.expertise || mentor.industries || []).length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {[...(mentor.expertise || []), ...(mentor.industries || [])].slice(0, 5).map((tag, i) => (
              <span key={i} className="text-xs bg-white/5 border border-white/8 text-slate-400 px-2.5 py-1 rounded-full">{tag}</span>
            ))}
          </div>
        )}

        {/* Languages */}
        {(mentor.languages || mentor.languages_spoken || []).length > 0 && (
          <div className="flex items-center gap-1.5 mt-3">
            <Ico d={I.globe} className="w-3 h-3 text-slate-600" />
            <span className="text-xs text-slate-500">
              {(mentor.languages || mentor.languages_spoken).join(", ")}
            </span>
          </div>
        )}

        {/* Bio */}
        {mentor.bio && (
          <p className="text-xs text-slate-400 leading-relaxed mt-3 line-clamp-2">{mentor.bio}</p>
        )}

        {/* Stats row */}
        <div className="flex items-center gap-4 mt-3 pt-3 border-t border-white/5">
          {mentor.total_sessions > 0 && (
            <span className="text-xs text-slate-500">{mentor.total_sessions} sessions</span>
          )}
          {mentor.location && (
            <span className="text-xs text-slate-500">📍 {mentor.location}</span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="px-5 pb-4 flex gap-2">
        <button onClick={() => setExpanded(v => !v)}
          className="flex-1 text-xs border border-white/10 text-slate-400 px-4 py-2 rounded-xl hover:border-white/20 hover:text-slate-300 transition">
          {expanded ? "Hide Details" : "View Details"}
        </button>
        <button onClick={() => onBook(mentor)}
          className="flex-1 text-xs bg-violet-600 hover:bg-violet-500 text-white font-semibold px-4 py-2 rounded-xl transition">
          Book Session
        </button>
      </div>

      {/* Expanded: full bio */}
      {expanded && mentor.bio && (
        <div className="px-5 pb-4 border-t border-white/5 pt-3">
          <p className="text-xs text-slate-300 leading-relaxed">{mentor.bio}</p>
        </div>
      )}
    </div>
  );
};

const BookingModal = ({ mentor, userId, onClose, onSuccess }) => {
  const [date, setDate]       = useState("");
  const [time, setTime]       = useState("");
  const [topic, setTopic]     = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const minDate = new Date().toISOString().split("T")[0];

  const handleBook = async () => {
    if (!date || !time) { setError("Please select both date and time."); return; }
    if (!userId)        { setError("User ID required. Reload the page."); return; }
    setError(null); setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/mentor/book`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          // ✅ FIXED: use mentor_id (backend field), not mentor.id
          mentor_id:    mentor.mentor_id || mentor.id,
          user_id:      userId,
          session_date: date,
          session_time: time,
          duration_hours: 1,
          topic:  topic,
          notes:  topic,
          mentor_name:   mentor.name,
          mentor_domain: (mentor.expertise || [])[0] || "",
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Booking failed");
      onSuccess(`Session booked with ${mentor.name} on ${date} at ${time}!`);
      onClose();
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)" }}
      onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="w-full max-w-md rounded-2xl border border-white/10 p-6"
        style={{ background: "#0d1117" }}>
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-sm font-semibold text-white">Book with {mentor.name}</h3>
            <p className="text-xs text-slate-500 mt-0.5">{mentor.title}</p>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-xl border border-white/10 flex items-center justify-center text-slate-400 hover:text-white transition">
            <Ico d={I.close} className="w-3.5 h-3.5" />
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4 text-xs text-red-400">
            <Ico d={I.alert} className="w-3.5 h-3.5 flex-shrink-0" />{error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Session Date</label>
            <input type="date" value={date} onChange={e => setDate(e.target.value)} min={minDate}
              className={inp + " [color-scheme:dark]"} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Session Time</label>
            <input type="time" value={time} onChange={e => setTime(e.target.value)}
              className={inp + " [color-scheme:dark]"} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Topic / Goals <span className="text-slate-600">(optional)</span></label>
            <textarea value={topic} onChange={e => setTopic(e.target.value)} rows={2}
              placeholder="What would you like to discuss?"
              className={inp + " resize-none"} />
          </div>
        </div>

        <div className="flex gap-3 mt-5">
          <button onClick={onClose}
            className="flex-1 text-sm border border-white/10 text-slate-400 px-4 py-2.5 rounded-xl hover:border-white/20 transition">
            Cancel
          </button>
          <button onClick={handleBook} disabled={loading}
            className="flex-1 text-sm bg-violet-600 hover:bg-violet-500 text-white font-semibold px-4 py-2.5 rounded-xl disabled:opacity-40 transition flex items-center justify-center gap-2">
            {loading ? <><span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Booking…</> : "Confirm Booking"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default function MentorSearch({ userId, userSkills = [] }) {
  const [query,    setQuery]    = useState("");
  const [domain,   setDomain]   = useState("");
  const [mentors,  setMentors]  = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [domains,  setDomains]  = useState([]);
  const [booking,  setBooking]  = useState(null); // mentor to book
  const [toast,    setToast]    = useState(null);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/mentor/domains`)
      .then(r => r.json())
      .then(d => setDomains(d.domains || []))
      .catch(() => setDomains(["Technology","Business","Design","Data Science","Marketing","Finance"]));
  }, []);

  const search = useCallback(async (q = query, d = domain) => {
    setLoading(true); setSearched(true);
    try {
      const res = await fetch(`${API_BASE_URL}/mentor/search`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, domain: d, user_skills: userSkills, user_id: userId }),
      });
      const data = await res.json();
      setMentors(data.mentors || []);
    } catch { setMentors([]); }
    finally { setLoading(false); }
  }, [query, domain, userSkills, userId]);

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 4000);
  };

  return (
    <div className="space-y-5">
      {/* Search card */}
      <div className="rounded-2xl border border-white/10 p-5" style={{ background: "rgba(255,255,255,0.03)" }}>
        <div className="flex items-center gap-3 mb-5">
          <div className="w-8 h-8 rounded-xl bg-teal-500/15 flex items-center justify-center">
            <Ico d={I.mentor} className="w-4 h-4 text-teal-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Find Expert Mentors</h2>
            <p className="text-xs text-slate-500">1:1 career guidance from industry professionals</p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <div className="relative flex-1">
            <Ico d={I.search} className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input value={query} onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && search()}
              placeholder="Search by name, expertise, company…"
              className="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none transition" />
          </div>
          <select value={domain} onChange={e => setDomain(e.target.value)}
            className="w-full sm:w-44 px-4 py-2.5 text-sm rounded-xl border border-white/10 bg-white/5 text-white focus:ring-2 focus:ring-teal-500 outline-none cursor-pointer [color-scheme:dark]">
            <option value="">All Domains</option>
            {domains.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
          <button onClick={() => search()} disabled={loading}
            className="flex items-center gap-2 bg-teal-600 hover:bg-teal-500 text-white text-sm font-semibold px-5 py-2.5 rounded-xl disabled:opacity-40 transition-all whitespace-nowrap">
            {loading
              ? <><span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Searching…</>
              : <><Ico d={I.search} className="w-4 h-4" />Search</>}
          </button>
        </div>

        {/* Domain quick-picks */}
        {domains.length > 0 && !searched && (
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-slate-600 uppercase tracking-widest font-medium w-full mb-1">Browse by domain</span>
            {domains.slice(0, 6).map(d => (
              <button key={d} onClick={() => { setDomain(d); search(query, d); }}
                className="text-xs border border-white/10 text-slate-400 hover:border-teal-500/30 hover:text-teal-300 px-3 py-1.5 rounded-full transition-all">
                {d}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="rounded-2xl border border-white/8 p-10 text-center" style={{ background: "rgba(255,255,255,0.02)" }}>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500 mx-auto mb-3" />
          <p className="text-sm text-slate-400">Finding mentors…</p>
        </div>
      )}

      {/* Results */}
      {!loading && mentors.length > 0 && (
        <div className="space-y-4">
          <p className="text-xs text-slate-500">
            {mentors.length} mentor{mentors.length !== 1 ? "s" : ""} found
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {mentors.map((mentor, idx) => (
              <MentorCard key={mentor.mentor_id || mentor.id || idx} mentor={mentor} onBook={setBooking} />
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && searched && mentors.length === 0 && (
        <div className="rounded-2xl border border-white/8 p-10 text-center" style={{ background: "rgba(255,255,255,0.02)" }}>
          <Ico d={I.mentor} className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <p className="text-sm text-slate-500">No mentors found — try different keywords or domain</p>
        </div>
      )}

      {/* Empty initial state */}
      {!loading && !searched && (
        <div className="rounded-2xl border border-white/8 p-10 text-center" style={{ background: "rgba(255,255,255,0.02)" }}>
          <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center"
            style={{ background: "rgba(20,184,166,0.1)", border: "1px solid rgba(20,184,166,0.2)" }}>
            <Ico d={I.mentor} className="w-8 h-8 text-teal-400" />
          </div>
          <h3 className="text-sm font-semibold text-white mb-1">Connect with Industry Experts</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Search for mentors by expertise, domain, or company. Get personalised 1:1 coaching for your career.
          </p>
        </div>
      )}

      {/* Booking modal */}
      {booking && (
        <BookingModal
          mentor={booking}
          userId={userId}
          onClose={() => setBooking(null)}
          onSuccess={showToast}
        />
      )}

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 bg-emerald-600 text-white text-sm font-medium px-5 py-3 rounded-2xl shadow-2xl"
          style={{ animation: "slideUp 0.3s ease" }}>
          <Ico d={I.check} className="w-4 h-4" />
          {toast}
          <button onClick={() => setToast(null)} className="ml-2 opacity-70 hover:opacity-100">
            <Ico d={I.close} className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      <style>{`@keyframes slideUp { from { transform: translateY(20px); opacity: 0 } to { transform: translateY(0); opacity: 1 } }`}</style>
    </div>
  );
}