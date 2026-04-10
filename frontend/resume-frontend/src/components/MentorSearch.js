import React, { useState, useEffect, useCallback } from 'react';

import API_BASE_URL from '../config';

const MentorSearch = ({ userId, userSkills = [] }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [domain, setDomain] = useState('');
  const [mentors, setMentors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMentor, setSelectedMentor] = useState(null);
  const [bookingData, setBookingData] = useState({ date: '', time: '', message: '' });
  const [bookingStatus, setBookingStatus] = useState(null);
  const [domains, setDomains] = useState([]);

  // Fetch available domains on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/mentor/domains`)
      .then(res => res.json())
      .then(data => setDomains(data.domains || []))
      .catch(() => setDomains(['Technology', 'Business', 'Design', 'Marketing', 'Data Science']));
  }, []);

  const searchMentors = useCallback(async () => {
    if (!searchQuery.trim() && !domain) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/mentor/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          domain: domain,
          user_skills: userSkills,
          user_id: userId
        })
      });
      const data = await res.json();
      setMentors(data.mentors || []);
    } catch (error) {
      console.error('Error searching mentors:', error);
      setMentors([]);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, domain, userSkills, userId]);

  const handleBookSession = async (mentor) => {
    if (!bookingData.date || !bookingData.time) {
      setBookingStatus({ error: 'Please select date and time' });
      return;
    }
    setBookingStatus(null);
    try {
      const res = await fetch(`${API_BASE_URL}/mentor/book`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mentor_id: mentor.id,
          user_id: userId,
          date: bookingData.date,
          time: bookingData.time,
          message: bookingData.message,
          mentor_name: mentor.name,
          mentor_domain: mentor.domain
        })
      });
      const data = await res.json();
      if (res.ok) {
        setBookingStatus({ success: `Session booked with ${mentor.name} on ${bookingData.date} at ${bookingData.time}` });
        setSelectedMentor(null);
        setBookingData({ date: '', time: '', message: '' });
      } else {
        setBookingStatus({ error: data.detail || 'Booking failed' });
      }
    } catch (error) {
      setBookingStatus({ error: 'Network error. Please try again.' });
    }
  };

  const getMatchBadge = (score) => {
    if (score >= 0.8) return { label: 'High Match', color: 'bg-green-100 text-green-700 border-green-200' };
    if (score >= 0.5) return { label: 'Medium Match', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' };
    return { label: 'Low Match', color: 'bg-gray-100 text-gray-600 border-gray-200' };
  };

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Find Expert Mentors</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-5">
          Connect with industry experts for 1:1 career guidance, mock interviews, and skill coaching
        </p>
        
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && searchMentors()}
            placeholder="Search by name, expertise, or company..."
            className="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="w-full sm:w-48 px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Domains</option>
            {domains.map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
          
          <button
            onClick={searchMentors}
            disabled={loading}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Searching...
              </>
            ) : (
              'Search Mentors'
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      {mentors.length > 0 && (
        <div className="space-y-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Found {mentors.length} mentor{mentors.length !== 1 ? 's' : ''}</p>
          {mentors.map((mentor, idx) => {
            const match = getMatchBadge(mentor.match_score);
            return (
              <div key={idx} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 hover:shadow-md transition-shadow">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 flex-wrap mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{mentor.name}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${match.color}`}>
                        {match.label} · {Math.round(mentor.match_score * 100)}%
                      </span>
                      {mentor.verified && (
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">✓ Verified</span>
                      )}
                    </div>
                    <p className="text-sm text-indigo-600 dark:text-indigo-400 font-medium mb-1">{mentor.title}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">{mentor.company} · {mentor.experience} years exp · {mentor.domain}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{mentor.bio}</p>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {mentor.expertise?.slice(0, 4).map((skill, i) => (
                        <span key={i} className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded-full">
                          {skill}
                        </span>
                      ))}
                      {mentor.expertise?.length > 4 && (
                        <span className="text-xs text-gray-400">+{mentor.expertise.length - 4} more</span>
                      )}
                    </div>
                    {mentor.match_reason && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 italic">✨ {mentor.match_reason}</p>
                    )}
                  </div>
                  
                  <div className="flex flex-col items-end gap-2">
                    <div className="text-right">
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">₹{mentor.session_fee}</p>
                      <p className="text-xs text-gray-400">per session (45 min)</p>
                    </div>
                    <button
                      onClick={() => setSelectedMentor(selectedMentor?.id === mentor.id ? null : mentor)}
                      className="px-4 py-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-lg text-sm font-medium hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors"
                    >
                      {selectedMentor?.id === mentor.id ? 'Cancel' : 'Book Session'}
                    </button>
                  </div>
                </div>
                
                {/* Booking Form */}
                {selectedMentor?.id === mentor.id && (
                  <div className="mt-5 pt-5 border-t border-gray-100 dark:border-gray-700">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Schedule a session with {mentor.name}</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                      <input
                        type="date"
                        value={bookingData.date}
                        onChange={(e) => setBookingData({ ...bookingData, date: e.target.value })}
                        min={new Date().toISOString().split('T')[0]}
                        className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                      <input
                        type="time"
                        value={bookingData.time}
                        onChange={(e) => setBookingData({ ...bookingData, time: e.target.value })}
                        className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    </div>
                    <textarea
                      value={bookingData.message}
                      onChange={(e) => setBookingData({ ...bookingData, message: e.target.value })}
                      placeholder="What would you like to discuss? (optional)"
                      rows={2}
                      className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 resize-none mb-4"
                    />
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleBookSession(mentor)}
                        className="px-5 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
                      >
                        Confirm Booking
                      </button>
                      <button
                        onClick={() => setSelectedMentor(null)}
                        className="px-5 py-2 border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* No results */}
      {!loading && mentors.length === 0 && searchQuery && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-8 text-center">
          <p className="text-gray-500 dark:text-gray-400">No mentors found matching your criteria.</p>
          <p className="text-sm text-gray-400 mt-2">Try adjusting your search or domain filter.</p>
        </div>
      )}

      {/* Booking status */}
      {bookingStatus && (
        <div className={`fixed bottom-4 right-4 p-4 rounded-lg shadow-lg transition-all ${
          bookingStatus.success ? 'bg-green-100 border border-green-300 text-green-800' : 'bg-red-100 border border-red-300 text-red-800'
        }`}>
          <p className="text-sm">{bookingStatus.success || bookingStatus.error}</p>
          <button 
            onClick={() => setBookingStatus(null)}
            className="absolute top-1 right-2 text-xs opacity-70 hover:opacity-100"
          >
            ✕
          </button>
        </div>
      )}

      {/* Initial state / empty search */}
      {!loading && mentors.length === 0 && !searchQuery && !domain && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center">
            <svg className="w-8 h-8 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Connect with Industry Experts</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
            Search for mentors by name, expertise, or domain. Get personalised 1:1 coaching for your career growth.
          </p>
          <div className="flex flex-wrap gap-2 justify-center mt-4">
            {domains.slice(0, 4).map(d => (
              <button
                key={d}
                onClick={() => { setDomain(d); searchMentors(); }}
                className="text-xs px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MentorSearch;