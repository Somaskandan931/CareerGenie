import React, { useState, useEffect } from "react";

const API_BASE_URL = "http://localhost:8000";

// ─── Icons ────────────────────────────────────────────────────────────────────

const SearchIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const StarIcon = ({ filled }) => (
  <svg className={`w-4 h-4 ${filled ? "text-yellow-400" : "text-gray-300"}`} fill="currentColor" viewBox="0 0 20 20">
    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
  </svg>
);

const GlobeIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const CurrencyIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const CalendarIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const ClockIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const LanguageIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
  </svg>
);

const CheckIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
  </svg>
);

const XIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

// ─── Mentor Card ─────────────────────────────────────────────────────────────

const MentorCard = ({ mentor, onBook, userSessions = [] }) => {
  const [expanded, setExpanded] = useState(false);
  const [showBooking, setShowBooking] = useState(false);

  const hasSession = userSessions.some(s =>
    s.mentor_id === mentor.mentor_id &&
    ['pending', 'confirmed'].includes(s.status)
  );

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <StarIcon key={i} filled={i < Math.floor(rating)} />
    ));
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border-2 border-gray-100 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-all">
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">{mentor.name}</h3>
              <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                {mentor.experience_years}+ yrs
              </span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {mentor.title} at {mentor.company}
            </p>
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <GlobeIcon /> {mentor.location}
              </span>
              <span className="flex items-center gap-1">
                <LanguageIcon /> {mentor.languages_spoken.join(", ")}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1">
              {renderStars(mentor.rating)}
              <span className="text-sm font-bold text-gray-900 dark:text-white ml-1">
                {mentor.rating}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">{mentor.total_sessions} sessions</p>
          </div>
        </div>

        {/* Expertise tags */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          {mentor.expertise.slice(0, 3).map((exp, i) => (
            <span key={i} className="text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 px-2 py-1 rounded-full">
              {exp}
            </span>
          ))}
          {mentor.expertise.length > 3 && (
            <span className="text-xs bg-gray-100 text-gray-600 border border-gray-200 px-2 py-1 rounded-full">
              +{mentor.expertise.length - 3} more
            </span>
          )}
        </div>

        {/* Rate and actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <CurrencyIcon />
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              {mentor.hourly_rate} {mentor.currency}
            </span>
            <span className="text-xs text-gray-500">/hour</span>
          </div>
          <div className="flex gap-2">
            {hasSession ? (
              <span className="px-4 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-medium flex items-center gap-1">
                <CheckIcon /> Session Booked
              </span>
            ) : (
              <button
                onClick={() => onBook(mentor)}
                className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg text-sm font-medium hover:from-indigo-700 hover:to-purple-700 transition-all"
              >
                Book Session
              </button>
            )}
            <button
              onClick={() => setExpanded(!expanded)}
              className="px-3 py-2 border-2 border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50"
            >
              {expanded ? "Show less" : "Details"}
            </button>
          </div>
        </div>
      </div>

      {/* Expanded bio */}
      {expanded && (
        <div className="border-t border-gray-100 dark:border-gray-700 px-5 py-4 bg-gray-50 dark:bg-gray-700/50">
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">{mentor.bio}</p>

          {/* Industries */}
          <div className="mb-2">
            <p className="text-xs font-semibold text-gray-500 mb-1">Industries</p>
            <div className="flex flex-wrap gap-1">
              {mentor.industries.map((ind, i) => (
                <span key={i} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full">
                  {ind}
                </span>
              ))}
            </div>
          </div>

          {/* Full expertise list */}
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-1">All expertise areas</p>
            <div className="flex flex-wrap gap-1">
              {mentor.expertise.map((exp, i) => (
                <span key={i} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full">
                  {exp}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Booking Modal ──────────────────────────────────────────────────────────

const BookingModal = ({ mentor, onClose, onConfirm, userId = "default_user" }) => {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [duration, setDuration] = useState(1);
  const [topic, setTopic] = useState("");
  const [notes, setNotes] = useState("");
  const [availableSlots, setAvailableSlots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    if (date) {
      setLoading(true);
      fetch(`${API_BASE_URL}/mentors/${mentor.mentor_id}/slots?date=${date}`)
        .then(res => res.json())
        .then(data => setAvailableSlots(data.available_slots || []))
        .catch(() => setAvailableSlots([]))
        .finally(() => setLoading(false));
    }
  }, [date, mentor.mentor_id]);

  const handleConfirm = async () => {
    if (!date || !time) return;

    setBooking(true);
    try {
      const res = await fetch(`${API_BASE_URL}/mentors/book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          mentor_id: mentor.mentor_id,
          session_date: date,
          session_time: time,
          duration_hours: duration,
          topic,
          notes
        })
      });

      if (!res.ok) throw new Error("Booking failed");
      const data = await res.json();
      onConfirm(data.session);
    } catch (err) {
      alert("Booking failed: " + err.message);
    } finally {
      setBooking(false);
    }
  };

  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minDate = tomorrow.toISOString().split("T")[0];
  const maxDate = new Date();
  maxDate.setDate(maxDate.getDate() + 30);
  const maxDateStr = maxDate.toISOString().split("T")[0];

  const totalCost = mentor.hourly_rate * duration;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Book a Session</h2>
              <p className="text-sm text-gray-500 mt-1">with {mentor.name}</p>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
              <XIcon />
            </button>
          </div>

          {/* Mentor summary */}
          <div className="bg-indigo-50 dark:bg-indigo-900/30 rounded-xl p-4 mb-6">
            <p className="text-sm font-medium text-indigo-900 dark:text-indigo-200">{mentor.title}</p>
            <p className="text-sm text-indigo-700 dark:text-indigo-300">{mentor.company} · {mentor.location}</p>
          </div>

          {/* Booking form */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Session Topic <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. System Design interview prep, Career advice, Resume review"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-400"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  min={minDate}
                  max={maxDateStr}
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Duration
                </label>
                <select
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-400"
                >
                  <option value={1}>1 hour</option>
                  <option value={2}>2 hours</option>
                  <option value={3}>3 hours</option>
                </select>
              </div>
            </div>

            {date && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Available Time Slots <span className="text-red-500">*</span>
                </label>
                {loading ? (
                  <div className="flex items-center gap-2 p-4">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600" />
                    <span className="text-sm text-gray-500">Loading slots...</span>
                  </div>
                ) : availableSlots.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {availableSlots.map((slot) => (
                      <button
                        key={slot}
                        onClick={() => setTime(slot)}
                        className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                          time === slot
                            ? "bg-indigo-600 text-white border-indigo-600"
                            : "border-gray-300 text-gray-700 hover:border-indigo-400 hover:text-indigo-600"
                        }`}
                      >
                        {slot}
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 p-2 bg-gray-50 rounded-lg">No slots available on this date</p>
                )}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Additional Notes
              </label>
              <textarea
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="What specific topics would you like to discuss? Any preparation you've done?"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-400 resize-none"
              />
            </div>

            {/* Pricing summary */}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Price Summary</p>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Rate: {mentor.hourly_rate} {mentor.currency}/hour</span>
                <span className="font-medium">{duration} hour(s)</span>
              </div>
              <div className="flex justify-between text-lg font-bold mt-2 pt-2 border-t border-gray-200">
                <span>Total</span>
                <span className="text-indigo-600">{totalCost} {mentor.currency}</span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                onClick={handleConfirm}
                disabled={!date || !time || !topic || booking}
                className="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 rounded-xl font-semibold disabled:opacity-50 hover:from-indigo-700 hover:to-purple-700 transition-all"
              >
                {booking ? (
                  <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white inline mr-2" />Processing...</>
                ) : (
                  "Confirm Booking"
                )}
              </button>
              <button
                onClick={onClose}
                className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── My Sessions Panel ─────────────────────────────────────────────────────

const MySessions = ({ sessions = [], onRefresh }) => {
  const [loading, setLoading] = useState({});

  const cancelSession = async (sessionId) => {
    if (!window.confirm("Are you sure you want to cancel this session?")) return;

    setLoading({ ...loading, [sessionId]: true });
    try {
      const res = await fetch(`${API_BASE_URL}/mentors/sessions/${sessionId}/cancel?user_id=default_user`, {
        method: "POST"
      });
      if (!res.ok) throw new Error("Cancellation failed");
      onRefresh();
    } catch (err) {
      alert("Failed to cancel: " + err.message);
    } finally {
      setLoading({ ...loading, [sessionId]: false });
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: "bg-yellow-100 text-yellow-800 border-yellow-200",
      confirmed: "bg-green-100 text-green-800 border-green-200",
      completed: "bg-blue-100 text-blue-800 border-blue-200",
      cancelled: "bg-red-100 text-red-800 border-red-200"
    };
    return colors[status] || "bg-gray-100 text-gray-800 border-gray-200";
  };

  if (sessions.length === 0) {
    return (
      <div className="bg-gray-50 rounded-xl p-8 text-center">
        <p className="text-gray-500">No sessions booked yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {sessions.map((session) => (
        <div key={session.session_id} className="bg-white border border-gray-200 rounded-xl p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="font-bold text-gray-900">{session.mentor_name}</h4>
                <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${getStatusColor(session.status)}`}>
                  {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
                </span>
              </div>
              <p className="text-sm text-gray-600">{session.mentor_title} · {session.mentor_company}</p>
              <div className="flex flex-wrap gap-4 mt-2 text-sm">
                <span className="flex items-center gap-1 text-gray-500">
                  <CalendarIcon /> {session.session_date}
                </span>
                <span className="flex items-center gap-1 text-gray-500">
                  <ClockIcon /> {session.session_time} ({session.duration_hours}h)
                </span>
                <span className="flex items-center gap-1 text-gray-500">
                  <CurrencyIcon /> {session.total_cost} {session.currency}
                </span>
              </div>
              <p className="text-sm text-gray-700 mt-2 bg-gray-50 p-2 rounded-lg">
                <span className="font-medium">Topic:</span> {session.topic}
              </p>
            </div>
            {session.status === 'pending' || session.status === 'confirmed' ? (
              <button
                onClick={() => cancelSession(session.session_id)}
                disabled={loading[session.session_id]}
                className="px-3 py-1 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50"
              >
                {loading[session.session_id] ? "..." : "Cancel"}
              </button>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
};

// ─── Main Component ─────────────────────────────────────────────────────────

const MentorSearch = ({ userId = "default_user", userSkills = [] }) => {
  const [mentors, setMentors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    expertise: "",
    industry: "",
    language: "",
    maxRate: "",
    minRating: 4.0,
    country: ""
  });
  const [selectedMentor, setSelectedMentor] = useState(null);
  const [userSessions, setUserSessions] = useState([]);
  const [activeTab, setActiveTab] = useState("search"); // search | my-sessions
  const [industries, setIndustries] = useState([]);
  const [languages, setLanguages] = useState([]);

  // Fetch user sessions
  useEffect(() => {
    fetch(`${API_BASE_URL}/mentors/sessions/${userId}`)
      .then(res => res.json())
      .then(data => setUserSessions(data.sessions || []))
      .catch(() => setUserSessions([]));
  }, [userId]);

  // Fetch filter options
  useEffect(() => {
    fetch(`${API_BASE_URL}/mentors/industries`)
      .then(res => res.json())
      .then(data => setIndustries(data.industries || []))
      .catch(() => setIndustries([]));

    fetch(`${API_BASE_URL}/mentors/languages`)
      .then(res => res.json())
      .then(data => setLanguages(data.languages || []))
      .catch(() => setLanguages([]));
  }, []);

  const searchMentors = async () => {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (filters.expertise) params.append("expertise", filters.expertise);
    if (filters.industry) params.append("industry", filters.industry);
    if (filters.language) params.append("language", filters.language);
    if (filters.maxRate) params.append("max_rate", filters.maxRate);
    if (filters.minRating) params.append("min_rating", filters.minRating);
    if (filters.country) params.append("country", filters.country);

    try {
      const res = await fetch(`${API_BASE_URL}/mentors/search?${params}`);
      if (!res.ok) throw new Error("Search failed");
      const data = await res.json();
      setMentors(data.mentors || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBook = (mentor) => {
    setSelectedMentor(mentor);
  };

  const handleBookingConfirm = (session) => {
    setSelectedMentor(null);
    setUserSessions([...userSessions, session]);
    setActiveTab("my-sessions");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 text-white">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🌍</span>
          <div>
            <h1 className="text-2xl font-black">Expert Mentors</h1>
            <p className="text-indigo-200 text-sm">Connect with industry experts worldwide for 1:1 mentoring calls</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-gray-100 p-1 rounded-xl w-fit">
        <button
          onClick={() => setActiveTab("search")}
          className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "search"
              ? "bg-white shadow text-gray-900"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          🔍 Find Mentors
        </button>
        <button
          onClick={() => setActiveTab("my-sessions")}
          className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "my-sessions"
              ? "bg-white shadow text-gray-900"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          📅 My Sessions {userSessions.length > 0 && `(${userSessions.length})`}
        </button>
      </div>

      {activeTab === "search" ? (
        <>
          {/* Search filters */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Expertise
                </label>
                <input
                  type="text"
                  value={filters.expertise}
                  onChange={(e) => setFilters({ ...filters, expertise: e.target.value })}
                  placeholder="e.g. System Design, ML, Career"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  onKeyDown={(e) => e.key === "Enter" && searchMentors()}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Industry
                </label>
                <select
                  value={filters.industry}
                  onChange={(e) => setFilters({ ...filters, industry: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="">All Industries</option>
                  {industries.map((ind) => (
                    <option key={ind} value={ind}>{ind}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Language
                </label>
                <select
                  value={filters.language}
                  onChange={(e) => setFilters({ ...filters, language: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="">Any Language</option>
                  {languages.map((lang) => (
                    <option key={lang} value={lang}>{lang}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Max Rate (USD)
                </label>
                <input
                  type="number"
                  value={filters.maxRate}
                  onChange={(e) => setFilters({ ...filters, maxRate: e.target.value })}
                  placeholder="e.g. 150"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Min Rating
                </label>
                <select
                  value={filters.minRating}
                  onChange={(e) => setFilters({ ...filters, minRating: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value={4.0}>4.0+ stars</option>
                  <option value={4.5}>4.5+ stars</option>
                  <option value={4.8}>4.8+ stars</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Country
                </label>
                <input
                  type="text"
                  value={filters.country}
                  onChange={(e) => setFilters({ ...filters, country: e.target.value })}
                  placeholder="e.g. India, USA, UK"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-5">
              <button
                onClick={searchMentors}
                disabled={loading}
                className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 transition-all flex items-center gap-2"
              >
                {loading ? (
                  <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />Searching...</>
                ) : (
                  <><SearchIcon /> Find Mentors</>
                )}
              </button>
              <button
                onClick={() => setFilters({ expertise: "", industry: "", language: "", maxRate: "", minRating: 4.0, country: "" })}
                className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50"
              >
                Clear
              </button>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}
          </div>

          {/* Results */}
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4" />
              <p className="text-gray-500">Finding the perfect mentor for you...</p>
            </div>
          ) : mentors.length > 0 ? (
            <div className="space-y-4">
              <p className="text-sm text-gray-500">Found {mentors.length} mentors</p>
              <div className="space-y-4">
                {mentors.map((mentor) => (
                  <MentorCard
                    key={mentor.mentor_id}
                    mentor={mentor}
                    onBook={handleBook}
                    userSessions={userSessions}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-2xl border-2 border-dashed border-gray-200">
              <p className="text-4xl mb-3">🔍</p>
              <p className="text-gray-500">Use the filters above to find mentors</p>
            </div>
          )}
        </>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Your Sessions</h2>
          <MySessions
            sessions={userSessions}
            onRefresh={() => {
              fetch(`${API_BASE_URL}/mentors/sessions/${userId}`)
                .then(res => res.json())
                .then(data => setUserSessions(data.sessions || []));
            }}
          />
        </div>
      )}

      {/* Booking modal */}
      {selectedMentor && (
        <BookingModal
          mentor={selectedMentor}
          onClose={() => setSelectedMentor(null)}
          onConfirm={handleBookingConfirm}
          userId={userId}
        />
      )}
    </div>
  );
};

export default MentorSearch;