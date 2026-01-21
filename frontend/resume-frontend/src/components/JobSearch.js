import React, { useState } from "react";

const SearchIcon = ({ size = "h-5 w-5" }) => (
  <svg className={size} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const AlertCircle = () => (
  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const CheckCircle = () => (
  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const Briefcase = ({ size = "h-6 w-6" }) => (
  <svg className={size} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6" />
  </svg>
);

const JobSearch = ({ setJobQuery, setJobLocation, setFilters }) => {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("India");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Filter state
  const [localFilters, setLocalFilters] = useState({
    experienceLevel: '',
    minMatchScore: 40,
    postedWithinDays: 14,
    excludeRemote: false
  });

  const popularSearches = [
    { query: "software engineer", location: "India" },
    { query: "data scientist", location: "Bangalore" },
    { query: "product manager", location: "Mumbai" },
    { query: "frontend developer", location: "Pune" },
  ];

  const handleSearch = async (searchQuery = query, searchLocation = location) => {
    const trimmedQuery = searchQuery.trim();

    if (!trimmedQuery) {
      setError("Please enter a search term");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      setJobQuery(trimmedQuery);
      setJobLocation(searchLocation.trim() || "India");

      // Pass filters to parent
      if (setFilters) {
        setFilters(localFilters);
      }

      setSuccess(`Searching for "${trimmedQuery}" jobs in ${searchLocation || "India"}...`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setJobQuery("");
      setJobLocation("");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSearch();
  };

  const handleQuickSearch = (popularQuery, popularLocation) => {
    setQuery(popularQuery);
    setLocation(popularLocation);
    handleSearch(popularQuery, popularLocation);
  };

  const handleFilterChange = (key, value) => {
    setLocalFilters(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      <div className="flex items-center mb-6">
        <Briefcase />
        <h2 className="text-2xl font-bold text-gray-900 ml-3">Job Search</h2>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div className="flex items-start">
            <AlertCircle />
            <div className="flex-1 ml-2">
              <span className="text-red-800 font-medium block">Error</span>
              <p className="text-red-700 mt-1 text-sm">{error}</p>
              <button onClick={() => setError(null)} className="mt-2 text-red-600 hover:text-red-800 transition-colors text-sm">
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
          <div className="flex items-start">
            <CheckCircle />
            <span className="text-green-800 font-medium ml-2">{success}</span>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {/* Main Search Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Job Title or Keywords <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="e.g. Software Engineer, Data Scientist"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                disabled={loading}
              />
              <SearchIcon size="h-5 w-5 absolute left-3 top-3.5 text-gray-400" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
            <div className="relative">
              <input
                type="text"
                placeholder="e.g. India, Bangalore, Mumbai"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                disabled={loading}
              />
              <svg className="absolute left-3 top-3.5 h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Advanced Filters */}
        <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-sm font-medium text-gray-700 mb-3">🔍 Advanced Filters</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Experience Level</label>
              <select
                value={localFilters.experienceLevel}
                onChange={(e) => handleFilterChange('experienceLevel', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
              >
                <option value="">All Levels</option>
                <option value="entry">Entry Level</option>
                <option value="mid">Mid Level</option>
                <option value="senior">Senior Level</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-gray-600 mb-1">Min Match Score (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={localFilters.minMatchScore}
                onChange={(e) => handleFilterChange('minMatchScore', Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-600 mb-1">Posted Within</label>
              <select
                value={localFilters.postedWithinDays}
                onChange={(e) => handleFilterChange('postedWithinDays', Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
              >
                <option value="7">Last 7 Days</option>
                <option value="14">Last 14 Days</option>
                <option value="30">Last 30 Days</option>
                <option value="60">Last 60 Days</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-gray-600 mb-1">Remote Jobs</label>
              <label className="flex items-center mt-2">
                <input
                  type="checkbox"
                  checked={localFilters.excludeRemote}
                  onChange={(e) => handleFilterChange('excludeRemote', e.target.checked)}
                  className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                />
                <span className="ml-2 text-sm text-gray-700">Exclude Remote</span>
              </label>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => handleSearch()}
            disabled={loading || !query.trim()}
            className="flex-1 md:flex-none bg-gradient-to-r from-green-600 to-green-700 text-white py-3 px-8 rounded-lg font-semibold hover:from-green-700 hover:to-green-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2 inline-block"></div>
                Searching...
              </>
            ) : (
              <>
                <SearchIcon size="h-5 w-5 inline mr-2" />
                Search Jobs
              </>
            )}
          </button>

          <button
            onClick={() => {
              setQuery("");
              setLocation("India");
              setError(null);
              setSuccess(null);
              setLocalFilters({
                experienceLevel: '',
                minMatchScore: 40,
                postedWithinDays: 14,
                excludeRemote: false
              });
            }}
            disabled={loading}
            className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
          >
            Clear
          </button>
        </div>

        {/* Popular Searches */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-sm font-medium text-gray-700 mb-3">Popular Searches:</p>
          <div className="flex flex-wrap gap-2">
            {popularSearches.map((item, idx) => (
              <button
                key={idx}
                onClick={() => handleQuickSearch(item.query, item.location)}
                disabled={loading}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                {item.query} • {item.location}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobSearch;