import { useEffect, useState } from "react";
import axios from "axios";

export default function JobMatches({ resumeText, jobs }) {
  const [matchedJobs, setMatchedJobs] = useState([]);

  useEffect(() => {
    const fetchMatches = async () => {
      if (!resumeText || !jobs.length) return;

      try {
        const response = await axios.post("http://localhost:8000/matcher/match-jobs", {
          resume_text: resumeText,
          jobs: jobs,
        });
        setMatchedJobs(response.data.matches || []);
      } catch (err) {
        console.error("Job match error:", err);
        setMatchedJobs([]);
      }
    };

    fetchMatches();
  }, [resumeText, jobs]);

  return (
    <div className="max-w-xl mx-auto p-6 bg-white rounded shadow">
      <h2 className="text-xl font-semibold mb-4">Matched Jobs</h2>
      {matchedJobs.length === 0 && <p>No matched jobs found.</p>}
      <ul>
        {matchedJobs.map((job) => (
          <li key={job.id || job.title} className="border-b py-3">
            <h3 className="font-bold">{job.title}</h3>
            <p className="text-sm text-gray-600">{job.company}</p>
            {job.fit_score && (
              <p className="text-green-700 font-medium">✅ Fit Score: {job.fit_score}%</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
