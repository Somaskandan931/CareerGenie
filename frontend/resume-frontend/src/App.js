import { useState, useEffect, useCallback } from "react";

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Icon Components
const Star = ({ filled = false }) => (
  <svg className={`h-4 w-4 ${filled ? 'text-yellow-400' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
  </svg>
);

const Briefcase = ({ size = "h-6 w-6", color = "text-green-600" }) => (
  <svg className={`${size} ${color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6" />
  </svg>
);

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

const ExternalLink = () => (
  <svg className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
  </svg>
);

// Job Search Component
const JobSearch = ({ setJobQuery, setJobLocation }) => {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("India");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

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

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      <div className="flex items-center mb-6">
        <Briefcase />
        <h2 className="text-2xl font-bold text-gray-900 ml-3">Job Search</h2>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
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
            <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
            <span className="text-green-800 font-medium">{success}</span>
          </div>
        </div>
      )}

      <div className="space-y-4">
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
              <SearchIcon className="absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
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
                <SearchIcon className="inline mr-2" />
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
            }}
            disabled={loading}
            className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
          >
            Clear
          </button>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-sm font-medium text-gray-700 mb-3">Popular Searches:</p>
          <div className="flex flex-wrap gap-2">
            {popularSearches.map((item, idx) => (
              <button
                key={idx}
                onClick={() => handleQuickSearch(item.query, item.location)}
                disabled={loading}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition-colors"
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

// Job Matches Component
const JobMatches = ({ jobQuery, jobLocation, resumeText }) => {
  const [matchedJobs, setMatchedJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiMessage, setApiMessage] = useState(null);

  const matchJobs = useCallback(async () => {
    if (!resumeText || !jobQuery) {
      setMatchedJobs([]);
      return;
    }

    setLoading(true);
    setError(null);
    setApiMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/match-realtime`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_text: resumeText,
          job_query: jobQuery,
          location: jobLocation || "India",
          num_jobs: 30,
          top_k: 10,
          use_cache: true
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.error_message) {
        setApiMessage(data.error_message);
      } else if (data.warnings && data.warnings.length > 0) {
        setApiMessage(data.warnings.join('. '));
      }

      setMatchedJobs(data.matched_jobs || []);

    } catch (err) {
      // Better error message for API key issues
      let errorMsg = err.message;
      if (errorMsg.includes('SEARCHAPI_KEY') || errorMsg.includes('API key')) {
        errorMsg = 'Job search API not configured. Please add SEARCHAPI_KEY to your backend .env file.';
      } else if (errorMsg.includes('500')) {
        errorMsg = 'Server error. Please check backend logs and ensure all API keys are configured.';
      }
      setError(errorMsg);
      setMatchedJobs([]);
    } finally {
      setLoading(false);
    }
  }, [resumeText, jobQuery, jobLocation]);

  useEffect(() => {
    matchJobs();
  }, [matchJobs]);

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100 border-green-300';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100 border-yellow-300';
    if (score >= 40) return 'text-orange-600 bg-orange-100 border-orange-300';
    return 'text-red-600 bg-red-100 border-red-300';
  };

  const getScoreStars = (score) => {
    const stars = Math.round(score / 20);
    return Array.from({ length: 5 }, (_, i) => <Star key={i} filled={i < stars} />);
  };

  if (!resumeText) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
        <div className="flex items-center mb-6">
          <Star filled className="h-6 w-6 text-yellow-500 mr-3" />
          <h2 className="text-2xl font-bold text-gray-900">Job Matches</h2>
        </div>
        <div className="text-center py-16">
          <svg className="h-16 w-16 text-gray-300 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-gray-500 mt-4 text-lg">Enter your resume first to see job matches</p>
        </div>
      </div>
    );
  }

  if (!jobQuery) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
        <div className="flex items-center mb-6">
          <Star filled className="h-6 w-6 text-yellow-500 mr-3" />
          <h2 className="text-2xl font-bold text-gray-900">Job Matches</h2>
        </div>
        <div className="text-center py-16">
          <SearchIcon size="h-16 w-16 text-gray-300 mx-auto" />
          <p className="text-gray-500 mt-4 text-lg">Search for jobs to see matches</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Star filled className="h-6 w-6 text-yellow-500 mr-3" />
          <h2 className="text-2xl font-bold text-gray-900">Job Matches</h2>
        </div>
        {matchedJobs.length > 0 && (
          <span className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium">
            {matchedJobs.length} {matchedJobs.length === 1 ? 'match' : 'matches'}
          </span>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <span className="text-red-800 font-medium block">Error</span>
              <p className="text-red-700 mt-1 text-sm">{error}</p>
              <button onClick={matchJobs} className="mt-2 px-3 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200 text-sm font-medium">
                Try Again
              </button>
            </div>
          </div>
        </div>
      )}

      {apiMessage && !error && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <p className="text-blue-800 text-sm">{apiMessage}</p>
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center p-12">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
          <p className="text-gray-600 font-medium">Finding your perfect job matches...</p>
          <p className="text-gray-500 text-sm mt-2">This may take 5-15 seconds...</p>
        </div>
      )}

      {!loading && matchedJobs.length === 0 && !error && (
        <div className="text-center py-16">
          <Briefcase size="h-16 w-16" color="text-gray-300 mx-auto" />
          <p className="text-gray-500 mt-4 text-lg">No job matches found</p>
          <p className="text-gray-400 mt-2 text-sm">Try different search terms</p>
        </div>
      )}

      <div className="space-y-6">
        {matchedJobs.map((job, index) => (
          <div key={index} className="border-2 border-gray-200 rounded-xl p-6 hover:shadow-xl hover:border-blue-300 transition-all">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-2">{job.title}</h3>
                <p className="text-lg text-gray-700 font-medium mb-1">{job.company}</p>
                <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
                  <span>{job.location}</span>
                  <span>•</span>
                  <span>{job.employment_type || 'Full-time'}</span>
                </div>
              </div>

              <div className="mt-4 sm:mt-0 sm:ml-6 text-center">
                <div className={`inline-flex items-center px-4 py-2 rounded-full text-lg font-bold border-2 ${getScoreColor(job.match_score || 0)}`}>
                  {Math.round(job.match_score || 0)}% Match
                </div>
                <div className="flex items-center justify-center mt-2 gap-1">
                  {getScoreStars(job.match_score || 0)}
                </div>
              </div>
            </div>

            {job.explanation && (
              <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-700">{job.explanation}</p>
              </div>
            )}

            {job.matched_skills && job.matched_skills.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-semibold text-gray-700 mb-2">✓ Matching Skills ({job.matched_skills.length}):</p>
                <div className="flex flex-wrap gap-2">
                  {job.matched_skills.map((skill, idx) => (
                    <span key={idx} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-medium border border-green-300">
                      ✓ {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 pt-4 border-t border-gray-200">
              {job.apply_link && (
                <a
                  href={job.apply_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium inline-flex items-center"
                >
                  Apply Now
                  <ExternalLink />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Main App
export default function App() {
  const [jobQuery, setJobQuery] = useState("");
  const [jobLocation, setJobLocation] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [uploadError, setUploadError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [backendConfig, setBackendConfig] = useState(null);

  // Check backend configuration on startup
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/config`);
        if (response.ok) {
          const config = await response.json();
          setBackendConfig(config);
        }
      } catch (err) {
        console.error('Failed to check backend config:', err);
      }
    };
    checkBackend();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Accept both PDF and DOCX files
    const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(file.type)) {
      setUploadError('Please upload a PDF or DOCX file');
      return;
    }

    setUploading(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch("http://localhost:8000/upload-resume/parse",
      {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to parse resume');
      }

      const data = await response.json();
      // The backend returns parsed_data and resume_text
      setResumeText(data.resume_text || data.parsed_data?.raw_text || '');
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-center">
            <div className="flex items-center">
              <div className="bg-gradient-to-r from-blue-600 to-green-600 p-2 rounded-lg mr-3">
                <Briefcase size="h-8 w-8" color="text-white" />
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                  CareerGenie
                </h1>
                <p className="text-sm text-gray-500">Powered by AI & RAG</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Backend Configuration Warning */}
        {backendConfig && (!backendConfig.searchapi_key_present || !backendConfig.anthropic_key_present) && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 mb-8 rounded-r-lg">
            <div className="flex items-start">
              <svg className="h-6 w-6 text-yellow-400 mr-3 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-yellow-800 mb-2">⚙️ Backend Configuration Required</h3>
                <p className="text-yellow-700 text-sm mb-3">
                  Some features won't work until you configure the backend .env file:
                </p>
                <ul className="text-yellow-700 text-sm space-y-1 mb-3">
                  {!backendConfig.searchapi_key_present && (
                    <li className="flex items-center">
                      <span className="text-red-500 mr-2">✗</span>
                      <strong>SEARCHAPI_KEY</strong> - Required for job search
                    </li>
                  )}
                  {!backendConfig.anthropic_key_present && (
                    <li className="flex items-center">
                      <span className="text-red-500 mr-2">✗</span>
                      <strong>ANTHROPIC_API_KEY</strong> - Required for AI-powered matching
                    </li>
                  )}
                </ul>
                <div className="bg-yellow-100 p-3 rounded text-xs font-mono text-yellow-900">
                  <p className="font-semibold mb-1">Create backend/.env file with:</p>
                  <p>SEARCHAPI_KEY=your_serpapi_key_here</p>
                  <p>ANTHROPIC_API_KEY=your_anthropic_key_here</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Resume Input */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <div className="bg-blue-600 p-2 rounded-lg mr-3">
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Your Resume</h2>
          </div>

          <div className="space-y-4">
            {/* Upload Error */}
            {uploadError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <span className="text-red-800 font-medium block">Upload Error</span>
                    <p className="text-red-700 mt-1 text-sm">{uploadError}</p>
                    <button onClick={() => setUploadError(null)} className="mt-2 text-red-600 hover:text-red-800 transition-colors text-sm">
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* PDF Upload Section */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-400 transition-colors">
              <div className="text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <div className="mt-4">
                  <label htmlFor="resume-upload" className="cursor-pointer">
                    <span className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium">
                      <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                      </svg>
                      {uploading ? 'Uploading...' : 'Upload Resume (PDF/DOCX)'}
                    </span>
                    <input
                      id="resume-upload"
                      type="file"
                      accept=".pdf,.doc,.docx"
                      onChange={handleFileUpload}
                      disabled={uploading}
                      className="hidden"
                    />
                  </label>
                  <p className="mt-2 text-xs text-gray-500">
                    PDF or DOCX files • Max 10MB
                  </p>
                </div>
                {uploading && (
                  <div className="mt-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="text-sm text-gray-600 mt-2">Processing your resume...</p>
                  </div>
                )}
              </div>
            </div>


            {resumeText && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <div>
                    <span className="text-green-800 font-medium">Resume ready!</span>
                    <p className="text-green-700 text-sm mt-1">
                      {resumeText.length} characters • Now search for jobs to see matches
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <JobSearch setJobQuery={setJobQuery} setJobLocation={setJobLocation} />
        <JobMatches jobQuery={jobQuery} jobLocation={jobLocation} resumeText={resumeText} />
      </main>

      <footer className="bg-gray-900 text-white py-8 mt-16">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p className="text-gray-400 text-sm">© 2025 CareerGenie. Powered by AI to match you with your dream job.</p>
        </div>
      </footer>
    </div>
  );
}