import { useState, useEffect } from "react";

// Import components
import JobSearch from './components/JobSearch';
import JobMatches from './components/JobMatches';
import SkillAssessmentDashboard from './components/SkillAssessmentDashboard';

const API_BASE_URL = 'http://localhost:8000';

// Icon Components
const Briefcase = ({ size = "h-6 w-6", color = "text-green-600" }) => (
  <svg className={`${size} ${color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6" />
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

const LightBulb = ({ size = "h-6 w-6" }) => (
  <svg className={size} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
  </svg>
);

const BookOpen = ({ size = "h-6 w-6" }) => (
  <svg className={size} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const TrendingUp = ({ size = "h-6 w-6" }) => (
  <svg className={size} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  </svg>
);

const ExternalLink = () => (
  <svg className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
  </svg>
);

// Career Advice Component
const CareerAdvice = ({ careerAdvice }) => {
  if (!careerAdvice) return null;

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      <div className="flex items-center mb-6">
        <div className="bg-purple-600 p-2 rounded-lg mr-3">
          <LightBulb size="h-6 w-6 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900">Career Guidance</h2>
      </div>

      {/* Current Assessment */}
      {careerAdvice.current_assessment && (
        <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
          <h3 className="font-semibold text-blue-900 mb-2">📊 Current Assessment</h3>
          <p className="text-blue-800 text-sm">{careerAdvice.current_assessment}</p>
        </div>
      )}

      {/* Skill Gaps */}
      {careerAdvice.skill_gaps && careerAdvice.skill_gaps.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <span className="text-red-500 mr-2">⚠️</span>
            Critical Skill Gaps ({careerAdvice.skill_gaps.length})
          </h3>
          <div className="space-y-2">
            {careerAdvice.skill_gaps.map((gap, idx) => (
              <div key={idx} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-red-900">{gap.skill}</p>
                    <p className="text-xs text-red-700 mt-1">
                      Current: {gap.current_level} → Target: {gap.target_level}
                    </p>
                  </div>
                  <span className="text-xs bg-red-200 text-red-800 px-2 py-1 rounded-full">
                    {gap.importance}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Learning Path */}
      {careerAdvice.learning_path && careerAdvice.learning_path.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <BookOpen size="h-5 w-5 text-green-600 mr-2" />
            Recommended Learning Resources
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {careerAdvice.learning_path.map((resource, idx) => (
              <div key={idx} className="p-4 bg-green-50 border border-green-200 rounded-lg hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-green-900">{resource.title}</p>
                    <div className="flex gap-2 mt-2 text-xs">
                      <span className="bg-green-200 text-green-800 px-2 py-1 rounded">
                        {resource.type}
                      </span>
                      <span className="bg-gray-200 text-gray-800 px-2 py-1 rounded">
                        {resource.duration}
                      </span>
                      <span className="bg-blue-200 text-blue-800 px-2 py-1 rounded">
                        {resource.difficulty}
                      </span>
                    </div>
                  </div>
                  {resource.url && (
                    <a
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 text-green-600 hover:text-green-800"
                    >
                      <ExternalLink />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Career Progression */}
      {careerAdvice.career_progression && careerAdvice.career_progression.length > 0 && (
        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <TrendingUp size="h-5 w-5 text-indigo-600 mr-2" />
            Career Progression Path
          </h3>
          <div className="space-y-4">
            {careerAdvice.career_progression.map((stage, idx) => (
              <div key={idx} className="relative pl-8 pb-4">
                {idx < careerAdvice.career_progression.length - 1 && (
                  <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-indigo-200"></div>
                )}
                <div className="absolute left-0 top-1 w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                  {idx + 1}
                </div>
                <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-indigo-900">{stage.role}</h4>
                    <span className="text-xs bg-indigo-200 text-indigo-800 px-2 py-1 rounded-full">
                      {stage.timeline}
                    </span>
                  </div>
                  <p className="text-sm text-indigo-700 mb-2">
                    <strong>Key Skills:</strong> {stage.key_skills_needed.join(", ")}
                  </p>
                  <p className="text-xs text-indigo-600">
                    {stage.typical_responsibilities.join(" • ")}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Market Insights */}
      {careerAdvice.market_insights && (
        <div className="mb-6 p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded">
          <h3 className="font-semibold text-yellow-900 mb-2">💡 Market Insights</h3>
          <p className="text-yellow-800 text-sm">{careerAdvice.market_insights}</p>
        </div>
      )}

      {/* Action Plan */}
      {careerAdvice.action_plan && careerAdvice.action_plan.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <span className="text-green-500 mr-2">✓</span>
            Action Plan
          </h3>
          <div className="space-y-2">
            {careerAdvice.action_plan.map((action, idx) => (
              <div key={idx} className="flex items-start p-3 bg-gray-50 border border-gray-200 rounded-lg">
                <span className="flex-shrink-0 w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs font-bold mr-3 mt-0.5">
                  {idx + 1}
                </span>
                <p className="text-sm text-gray-700">{action}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Main App
export default function App() {
  const [jobQuery, setJobQuery] = useState("");
  const [jobLocation, setJobLocation] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [filters, setFilters] = useState({});
  const [careerAdvice, setCareerAdvice] = useState(null);
  const [skillComparison, setSkillComparison] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [backendConfig, setBackendConfig] = useState(null);

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

      const response = await fetch(`${API_BASE_URL}/upload-resume/parse`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to parse resume');
      }

      const data = await response.json();
      setResumeText(data.resume_text || '');
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
                  Career Genie
                </h1>
                <p className="text-sm text-gray-500">AI-Powered Job Discovery + Skill Assessment</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Backend Configuration Warning */}
        {backendConfig && (!backendConfig.serpapi_key_present || !backendConfig.anthropic_key_present) && (
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
                  {!backendConfig.serpapi_key_present && (
                    <li className="flex items-center">
                      <span className="text-red-500 mr-2">✗</span>
                      <strong>SERPAPI_KEY</strong> - Required for job search
                    </li>
                  )}
                  {!backendConfig.anthropic_key_present && (
                    <li className="flex items-center">
                      <span className="text-red-500 mr-2">✗</span>
                      <strong>ANTHROPIC_API_KEY</strong> - Required for AI-powered matching & career advice
                    </li>
                  )}
                </ul>
                <div className="bg-yellow-100 p-3 rounded text-xs font-mono text-yellow-900">
                  <p className="font-semibold mb-1">Create backend/.env file with:</p>
                  <p>SERPAPI_KEY=your_serpapi_key_here</p>
                  <p>ANTHROPIC_API_KEY=your_anthropic_key_here</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Resume Upload Section */}
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
            {uploadError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start">
                  <AlertCircle />
                  <div className="flex-1 ml-2">
                    <span className="text-red-800 font-medium block">Upload Error</span>
                    <p className="text-red-700 mt-1 text-sm">{uploadError}</p>
                    <button onClick={() => setUploadError(null)} className="mt-2 text-red-600 hover:text-red-800 transition-colors text-sm">
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            )}

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
                  <CheckCircle />
                  <div className="ml-2">
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

        {/* Job Search Component */}
        <JobSearch
          setJobQuery={setJobQuery}
          setJobLocation={setJobLocation}
          setFilters={setFilters}
        />

        {/* Skill Assessment Dashboard */}
        <SkillAssessmentDashboard
          resumeSkills={skillComparison?.resume_skills || []}
          jobSkills={skillComparison?.job_skills || []}
          comparison={skillComparison}
        />

        {/* Job Matches Component */}
        <JobMatches
          jobQuery={jobQuery}
          jobLocation={jobLocation}
          resumeText={resumeText}
          filters={filters}
          setCareerAdvice={setCareerAdvice}
          setSkillComparison={setSkillComparison}
        />

        {/* Career Advice Component */}
        <CareerAdvice careerAdvice={careerAdvice} />
      </main>

      <footer className="bg-gray-900 text-white py-8 mt-16">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p className="text-gray-400 text-sm">© 2025 Career Genie. AI-powered job discovery with skill gap analysis & personalized learning paths.</p>
        </div>
      </footer>
    </div>
  );
}