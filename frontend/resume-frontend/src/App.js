import { useState, createContext, useContext, useEffect, useCallback } from "react";

// Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Simple icon components
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

const Download = () => (
  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
  </svg>
);

const Upload = () => (
  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
  </svg>
);

const Search = () => (
  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const FileText = () => (
  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const Briefcase = () => (
  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6" />
  </svg>
);

const Star = ({ className = "h-4 w-4", filled = false }) => (
  <svg className={`${className} ${filled ? 'text-yellow-400' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
  </svg>
);

// API Service
class APIService {
  static async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Unable to connect to server. Please check your connection.');
      }
      throw error;
    }
  }

  static async buildResume(resumeData) {
    return this.request('/builder/build-resume', {
      method: 'POST',
      body: JSON.stringify(resumeData),
    });
  }

  static async uploadResume(file) {
    const formData = new FormData();
    formData.append('file', file);

    return fetch(`${API_BASE_URL}/upload-resume/parse`, {
      method: 'POST',
      body: formData,
    }).then(async (response) => {
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed: ${response.status}`);
      }
      return response.json();
    });
  }

  static async searchJobs(query, location, salary_min, salary_max) {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (location) params.append('location', location);
    if (salary_min) params.append('salary_min', salary_min);
    if (salary_max) params.append('salary_max', salary_max);

    return this.request(`/search-jobs/search?${params.toString()}`);
  }

  static async matchJobs(resumeText) {
    return this.request('/match-jobs/match', {
      method: 'POST',
      body: JSON.stringify({ resume_text: resumeText }),
    });
  }
}

// Context for global state management
const AppContext = createContext();

const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};

// Enhanced Error Display Component
const ErrorDisplay = ({ error, onRetry, onDismiss }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
    <div className="flex items-start">
      <AlertCircle className="h-5 w-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <span className="text-red-800 font-medium block">Error</span>
        <p className="text-red-700 mt-1 text-sm">{error}</p>
        <div className="mt-3 flex gap-2">
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-3 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200 transition-colors text-sm font-medium"
            >
              Try Again
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="px-3 py-1 text-red-600 hover:text-red-800 transition-colors text-sm"
            >
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  </div>
);

// Enhanced Loading Component
const LoadingSpinner = ({ message = "Loading...", size = "h-12 w-12" }) => (
  <div className="flex flex-col items-center justify-center p-8">
    <div className={`animate-spin rounded-full ${size} border-b-2 border-blue-600`}></div>
    <p className="mt-4 text-gray-600 text-sm">{message}</p>
  </div>
);

// Success Message Component
const SuccessMessage = ({ message, onDismiss }) => (
  <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
    <div className="flex items-start">
      <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <span className="text-green-800 font-medium block">{message}</span>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="mt-2 text-green-600 hover:text-green-800 transition-colors text-sm"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  </div>
);

// File Upload Component
const FileUpload = ({ onFileSelect, accept, loading, error }) => {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <div
      className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
        dragActive
          ? 'border-blue-400 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400'
      } ${loading ? 'opacity-50 pointer-events-none' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept={accept}
        onChange={handleChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        disabled={loading}
      />
      <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
      <p className="text-lg font-medium text-gray-900 mb-2">
        {dragActive ? 'Drop your file here' : 'Upload your resume'}
      </p>
      <p className="text-sm text-gray-500">
        Drag and drop or click to select • PDF, DOC, DOCX supported
      </p>
    </div>
  );
};

// Enhanced Resume Form Component
const ResumeForm = () => {
  const { setResumeData, setResumeText } = useAppContext();
  const [mode, setMode] = useState('form'); // 'form' or 'upload'
  const [form, setForm] = useState({
    personal_info: {
      name: "",
      email: "",
      phone: "",
      address: ""
    },
    education: [],
    experience: [],
    skills: [],
    projects: []
  });

  const [loading, setLoading] = useState(false);
  const [pdfData, setPdfData] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);

  const validateForm = () => {
    if (!form.personal_info.name.trim()) {
      setError('Name is required');
      return false;
    }
    if (!form.personal_info.email.trim()) {
      setError('Email is required');
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.personal_info.email)) {
      setError('Please enter a valid email address');
      return false;
    }
    if (form.skills.length === 0) {
      setError('At least one skill is required');
      return false;
    }
    return true;
  };

  const handleFormChange = (section, field, value) => {
    setForm(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
    if (error) setError(null);
  };

  const handleSkillsChange = (value) => {
    const skills = value.split(',').map(s => s.trim()).filter(Boolean);
    setForm(prev => ({ ...prev, skills }));
    if (error) setError(null);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await APIService.buildResume(form);

      if (response.pdf_base64) {
        setPdfData(response.pdf_base64);
        setSuccess('Resume generated successfully!');
      }

      // Create resume text for matching
      const resumeText = `${form.personal_info.name} ${form.personal_info.email} ${form.skills.join(' ')} ${form.experience.map(exp => exp.description || '').join(' ')}`;

      setResumeData(form);
      setResumeText(resumeText);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];

    if (!allowedTypes.includes(file.type)) {
      setError('Only PDF, DOC, and DOCX files are supported');
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setLoading(true);
    setError(null);
    setUploadedFile(file);

    try {
      const response = await APIService.uploadResume(file);

      if (response.parsed_data) {
        setForm(response.parsed_data);
        setResumeData(response.parsed_data);
        setResumeText(response.resume_text || file.name);
        setSuccess('Resume uploaded and parsed successfully!');
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = () => {
    if (!pdfData) return;

    try {
      const link = document.createElement('a');
      link.href = `data:application/pdf;base64,${pdfData}`;
      link.download = `${form.personal_info.name || 'resume'}.pdf`;
      link.click();
    } catch (err) {
      setError('Failed to download PDF');
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <FileText className="h-6 w-6 text-blue-600 mr-3" />
          <h2 className="text-2xl font-bold text-gray-900">Resume Builder</h2>
        </div>

        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setMode('form')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              mode === 'form'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Create New
          </button>
          <button
            onClick={() => setMode('upload')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              mode === 'upload'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Upload Existing
          </button>
        </div>
      </div>

      {error && (
        <ErrorDisplay
          error={error}
          onRetry={() => setError(null)}
          onDismiss={() => setError(null)}
        />
      )}

      {success && (
        <SuccessMessage
          message={success}
          onDismiss={() => setSuccess(null)}
        />
      )}

      {mode === 'upload' ? (
        <div>
          <FileUpload
            onFileSelect={handleFileUpload}
            accept=".pdf,.doc,.docx"
            loading={loading}
            error={error}
          />
          {loading && <LoadingSpinner message="Parsing your resume..." />}
          {uploadedFile && !loading && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-blue-800 font-medium">Uploaded: {uploadedFile.name}</p>
              <p className="text-blue-600 text-sm">Your resume has been parsed and is ready for job matching</p>
            </div>
          )}
        </div>
      ) : (
        <form onSubmit={handleFormSubmit} className="space-y-6">
          {/* Personal Information */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Personal Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.personal_info.name}
                  onChange={(e) => handleFormChange('personal_info', 'name', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your full name"
                  disabled={loading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={form.personal_info.email}
                  onChange={(e) => handleFormChange('personal_info', 'email', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your email"
                  disabled={loading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
                <input
                  type="tel"
                  value={form.personal_info.phone}
                  onChange={(e) => handleFormChange('personal_info', 'phone', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your phone number"
                  disabled={loading}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
                <input
                  type="text"
                  value={form.personal_info.address}
                  onChange={(e) => handleFormChange('personal_info', 'address', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your address"
                  disabled={loading}
                />
              </div>
            </div>
          </div>

          {/* Skills */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Skills <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={3}
              value={form.skills.join(', ')}
              onChange={(e) => handleSkillsChange(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g. Python, SQL, React, Project Management"
              disabled={loading}
            />
            <p className="text-sm text-gray-500 mt-1">Separate skills with commas</p>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-3 px-6 rounded-lg font-semibold hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Building Resume...
              </>
            ) : (
              <>
                <FileText className="h-5 w-5 mr-2" />
                Build Resume
              </>
            )}
          </button>

          {/* PDF Download */}
          {pdfData && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-800 font-medium">Your resume is ready!</p>
                  <p className="text-green-600 text-sm">Click to download your PDF resume</p>
                </div>
                <button
                  onClick={downloadPDF}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download PDF
                </button>
              </div>
            </div>
          )}
        </form>
      )}
    </div>
  );
};

// Enhanced Job Search Component
const JobSearch = () => {
  const { setJobs } = useAppContext();
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [salaryMin, setSalaryMin] = useState("");
  const [salaryMax, setSalaryMax] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      setError("Please enter a search term");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await APIService.searchJobs(
        query.trim(),
        location.trim(),
        salaryMin ? parseInt(salaryMin) : null,
        salaryMax ? parseInt(salaryMax) : null
      );

      if (response.jobs) {
        setJobs(response.jobs);
      } else {
        setJobs([]);
      }
    } catch (err) {
      setError(err.message);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      <div className="flex items-center mb-6">
        <Briefcase className="h-6 w-6 text-green-600 mr-3" />
        <h2 className="text-2xl font-bold text-gray-900">Job Search</h2>
      </div>

      {error && (
        <ErrorDisplay
          error={error}
          onRetry={handleSearch}
          onDismiss={() => setError(null)}
        />
      )}

      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Job Title or Keywords <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Software Engineer, Product Manager, Python"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              disabled={loading}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
            <input
              type="text"
              placeholder="e.g. San Francisco, Remote"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              disabled={loading}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Minimum Salary</label>
            <input
              type="number"
              placeholder="e.g. 80000"
              value={salaryMin}
              onChange={(e) => setSalaryMin(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              disabled={loading}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Maximum Salary</label>
            <input
              type="number"
              placeholder="e.g. 150000"
              value={salaryMax}
              onChange={(e) => setSalaryMax(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              disabled={loading}
            />
          </div>
        </div>

        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="w-full md:w-auto bg-gradient-to-r from-green-600 to-green-700 text-white py-3 px-8 rounded-lg font-semibold hover:from-green-700 hover:to-green-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Searching Jobs...
            </>
          ) : (
            <>
              <Search className="h-5 w-5 mr-2" />
              Search Jobs
            </>
          )}
        </button>
      </div>
    </div>
  );
};

// Enhanced Job Matches Component
const JobMatches = () => {
  const { resumeText, jobs } = useAppContext();
  const [matchedJobs, setMatchedJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const processMatches = useCallback(async () => {
    if (!resumeText || !jobs.length) {
      setMatchedJobs([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await APIService.matchJobs(resumeText);

      if (response.matched_jobs) {
        setMatchedJobs(response.matched_jobs);
      } else {
        setMatchedJobs([]);
      }
    } catch (err) {
      setError(err.message);
      setMatchedJobs([]);
    } finally {
      setLoading(false);
    }
  }, [resumeText, jobs]);

  // Auto-process matches when resume or jobs change
  useEffect(() => {
    processMatches();
  }, [processMatches]);

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    if (score >= 40) return 'text-orange-600 bg-orange-100';
    return 'text-red-600 bg-red-100';
  };

  const getScoreStars = (score) => {
    const stars = Math.round(score / 20);
    return Array.from({ length: 5 }, (_, i) => (
      <Star key={i} className="h-4 w-4" filled={i < stars} />
    ));
  };

  if (!resumeText) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Job Matches</h2>
        <div className="text-center py-12">
          <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Submit your resume first to see job matches</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-8">
      <div className="flex items-center mb-6">
        <Star className="h-6 w-6 text-yellow-500 mr-3" filled />
        <h2 className="text-2xl font-bold text-gray-900">Job Matches</h2>
        {matchedJobs.length > 0 && (
          <span className="ml-auto bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
            {matchedJobs.length} {matchedJobs.length === 1 ? 'match' : 'matches'}
          </span>
        )}
      </div>

      {error && (
        <ErrorDisplay
          error={error}
          onRetry={processMatches}
          onDismiss={() => setError(null)}
        />
      )}

      {loading && <LoadingSpinner message="Analyzing job matches..." />}

      {!loading && matchedJobs.length === 0 && jobs.length > 0 && !error && (
        <div className="text-center py-12">
          <Briefcase className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No job matches found. Try searching for different roles.</p>
        </div>
      )}

      {!loading && jobs.length === 0 && !error && (
        <div className="text-center py-12">
          <Search className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Search for jobs to see matches with your resume</p>
        </div>
      )}

      <div className="space-y-6">
        {matchedJobs.map((job) => (
          <div key={job.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow duration-200">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-2">{job.title}</h3>
                <p className="text-lg text-gray-600 mb-1">{job.company}</p>
                <p className="text-sm text-gray-500 mb-2">{job.location} • {job.type}</p>
                {job.salary && (
                  <p className="text-sm font-medium text-green-600">{job.salary}</p>
                )}
              </div>

              <div className="mt-4 sm:mt-0 sm:ml-6 text-center">
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold ${getScoreColor(job.fit_score || 0)}`}>
                  {job.fit_score || 0}% Match
                </div>
                <div className="flex items-center justify-center mt-2">
                  {getScoreStars(job.fit_score || 0)}
                </div>
              </div>
            </div>

            <p className="text-gray-700 mb-4">{job.description}</p>

            {job.matched_requirements && job.matched_requirements.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-semibold text-gray-700 mb-2">Your Matching Skills:</p>
                <div className="flex flex-wrap gap-2">
                  {job.matched_requirements.map((skill, idx) => (
                    <span key={idx} className="bg-green-100 text-green-800 px-2 py-1 rounded-md text-xs font-medium">
                      ✓ {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 pt-4 border-t border-gray-100">
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                Apply Now
              </button>
              <button className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
                Save Job
              </button>
              <button className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
                View Details
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [resumeData, setResumeData] = useState(null);
  const [resumeText, setResumeText] = useState("");
  const [jobs, setJobs] = useState([]);

  const contextValue = {
    resumeData,
    setResumeData,
    resumeText,
    setResumeText,
    jobs,
    setJobs
  };

  return (
    <AppContext.Provider value={contextValue}>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex items-center justify-center">
              <div className="flex items-center">
                <div className="bg-gradient-to-r from-blue-600 to-green-600 p-2 rounded-lg mr-3">
                  <Briefcase className="h-8 w-8 text-white" />
                </div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                  CareerGenie
                </h1>
              </div>
            </div>
            <p className="text-center text-gray-600 mt-2">
              AI-powered resume building and job matching platform
            </p>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-4xl mx-auto px-4 py-8">
          <ResumeForm />
          <JobSearch />
          <JobMatches />
        </main>

        {/* Footer */}
        <footer className="bg-gray-900 text-white py-8 mt-16">
          <div className="max-w-4xl mx-auto px-4 text-center">
            <p className="text-gray-400">
              © 2025 CareerGenie. Powered by AI to match you with your dream job.
            </p>
          </div>
        </footer>
      </div>
    </AppContext.Provider>
  );
}

export default App;