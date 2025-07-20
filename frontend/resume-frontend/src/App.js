import { useState } from "react";
import ResumeForm from "./components/ResumeForm";
import JobSearch from "./components/JobSearch";
import JobMatches from "./components/JobMatches";

function App() {
  // Store resume data and keywords extracted from form
  const [resumeData, setResumeData] = useState(null);
  const [resumeKeywords, setResumeKeywords] = useState([]);

  // Store fetched jobs
  const [jobs, setJobs] = useState([]);

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <h1 className="text-center text-3xl font-bold mb-8">CareerGenie</h1>

      {/* Resume Form passes back resume data and keywords */}
      <ResumeForm setResumeData={setResumeData} setResumeKeywords={setResumeKeywords} />

      {/* Job Search fetches jobs and passes them up */}
      <JobSearch setJobs={setJobs} />

      {/* Job Match shows matching jobs based on resumeKeywords */}
      <JobMatches resumeKeywords={resumeKeywords} jobs={jobs} />
    </div>
  );
}

export default App;
