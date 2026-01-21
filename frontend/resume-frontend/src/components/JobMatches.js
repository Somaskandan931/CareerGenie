import React, { useEffect, useState, useCallback } from "react";

const API_BASE_URL = 'http://localhost:8000';

// Icon Components
const Star = ({ filled = false }) => (
  <svg className={`h-4 w-4 ${filled ? 'text-yellow-400' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
  </svg>
);

const Briefcase = ({ size = "h-6 w-6" }) => (
  <svg className={size} fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

const ExternalLink = () => (
  <svg className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
  </svg>
);

const JobMatches = ({ jobQuery, jobLocation, resumeText, filters = {}, setCareerAdvice, setSkillComparison }) => {
  const [matchedJobs, setMatchedJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  const matchJobs = useCallback(async () => {
    if (!resumeText || !jobQuery) {
      setMatchedJobs([]);
      setCareerAdvice(null);
      if (setSkillComparison) setSkillComparison(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const requestBody = {
        resume_text: resumeText,
        job_query: jobQuery,
        location: jobLocation || "India",
        num_jobs: 50,
        top_k: 10,
        // Add filters
        min_match_score: filters.minMatchScore || 40,
        experience_level: filters.experienceLevel || null,
        posted_within_days: filters.postedWithinDays || 14,
        exclude_remote: filters.excludeRemote || false
      };

      const response = await fetch(`${API_BASE_URL}/rag/match-realtime`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setMatchedJobs(data.matched_jobs || []);

      // Set stats
      setStats({
        total_fetched: data.total_jobs_fetched || 0,
        total_indexed: data.total_jobs_indexed || 0,
        search_query: data.search_query || ''
      });

      // Extract career advice if available
      if (data.career_advice && setCareerAdvice) {
        setCareerAdvice(data.career_advice);
      }

      // Extract skill comparison if available
      if (data.skill_comparison && setSkillComparison) {
        setSkillComparison(data.skill_comparison);
      }

    } catch (err) {
      let errorMsg = err.message;
      if (errorMsg.includes('SERPAPI_KEY') || errorMsg.includes('API key')) {
        errorMsg = 'Job search API not configured. Please add SERPAPI_KEY to your backend .env file.';
      } else if (errorMsg.includes('500')) {
        errorMsg = 'Server error. Please check backend logs and ensure all API keys are configured.';
      }
      setError(errorMsg);
      setMatchedJobs([]);
      if (setCareerAdvice) setCareerAdvice(null);
      if (setSkillComparison) setSkillComparison(null);
    } finally {
      setLoading(false);
    }
  }, [resumeText, jobQuery, jobLocation, filters, setCareerAdvice, setSkillComparison]);

  useEffect(() => {
    matchJobs();
  }, [matchJobs]);

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100 border-green-300';
    if (score >= 65) return 'text-yellow-600 bg-yellow-100 border-yellow-300';
    if (score >= 50) return 'text-orange-600 bg-orange-100 border-orange-300';
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
          <Star filled />
          <h2 className="text-2xl font-bold text-gray-900 ml-3">Job Matches</h2>
        </div>
        <div className="text-center py-16">
          <svg className="h-16 w-16 text-gray-300 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-gray-500 mt-4 text-lg">Upload your resume first to see job matches</p>
        </div>
      </div>
    );
  }

  if (!jobQuery) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
        <div className="flex items-center mb-6">
          <Star filled />
          <h2 className="text-2xl font-bold text-gray-900 ml-3">Job Matches</h2>
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
          <Star filled />
          <h2 className="text-2xl font-bold text-gray-900 ml-3">Job Matches</h2>
        </div>
        {matchedJobs.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium">
              {matchedJobs.length} {matchedJobs.length === 1 ? 'match' : 'matches'}
            </span>
            {stats && (
              <span className="text-xs text-gray-500">
                ({stats.total_fetched} jobs analyzed)
              </span>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div className="flex items-start">
            <AlertCircle />
            <div className="flex-1 ml-2">
              <span className="text-red-800 font-medium block">Error</span>
              <p className="text-red-700 mt-1 text-sm">{error}</p>
              <button onClick={matchJobs} className="mt-2 px-3 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200 text-sm font-medium">
                Try Again
              </button>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center p-12">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
          <p className="text-gray-600 font-medium">Finding your perfect job matches...</p>
          <p className="text-gray-500 text-sm mt-2">This may take 10-20 seconds...</p>
        </div>
      )}

      {!loading && matchedJobs.length === 0 && !error && (
        <div className="text-center py-16">
          <Briefcase size="h-16 w-16 text-gray-300 mx-auto" />
          <p className="text-gray-500 mt-4 text-lg">No job matches found</p>
          <p className="text-gray-400 mt-2 text-sm">Try adjusting your filters or search terms</p>
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
                  <span>📍 {job.location}</span>
                </div>
              </div>

              <div className="mt-4 sm:mt-0 sm:ml-6 text-center">
                <div className={`inline-flex items-center px-4 py-2 rounded-full text-lg font-bold border-2 ${getScoreColor(job.match_score || 0)}`}>
                  {Math.round(job.match_score || 0)}% Match
                </div>
                <div className="flex items-center justify-center mt-2 gap-1">
                  {getScoreStars(job.match_score || 0)}
                </div>
                <p className="text-sm text-gray-600 mt-2 font-medium">{job.recommendation}</p>
              </div>
            </div>

            {job.explanation && (
              <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-gray-700 leading-relaxed">{job.explanation}</p>
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

            {job.missing_skills && job.missing_skills.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-semibold text-gray-700 mb-2">⚠ Skills to Develop ({job.missing_skills.length}):</p>
                <div className="flex flex-wrap gap-2">
                  {job.missing_skills.map((skill, idx) => (
                    <span key={idx} className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-xs font-medium border border-orange-300">
                      {skill}
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

export default JobMatches;