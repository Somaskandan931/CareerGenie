import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

const JobMatches = ({ resumeText, jobQuery, location }) => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!resumeText || !jobQuery) return;

    const fetchMatches = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE}/rag/match-realtime`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            resume_text: resumeText,
            job_query: jobQuery,
            location: location || "",
            num_jobs: 30,
            top_k: 10,
            use_cache: true
          })
        });

        if (!response.ok) {
          throw new Error("Failed to fetch job matches");
        }

        const data = await response.json();
        setJobs(data.matched_jobs || []);
      } catch (err) {
        console.error(err);
        setError("Unable to load job matches.");
      } finally {
        setLoading(false);
      }
    };

    fetchMatches();
  }, [resumeText, jobQuery, location]);

  if (loading) return <p>🔍 Matching jobs...</p>;
  if (error) return <p style={{ color: "red" }}>{error}</p>;
  if (!jobs.length) return <p>No matching jobs found.</p>;

  return (
    <div>
      <h2>Job Matches</h2>

      {jobs.map((job) => (
        <div
          key={job.job_id}
          style={{
            border: "1px solid #ddd",
            padding: "12px",
            marginBottom: "12px",
            borderRadius: "6px"
          }}
        >
          <h3>{job.title}</h3>
          <p>
            <strong>{job.company}</strong> — {job.location}
          </p>

          <p>
            <strong>Match Score:</strong> {job.match_score}% <br />
            <strong>Recommendation:</strong> {job.recommendation}
          </p>

          <p>{job.explanation}</p>

          {job.matched_skills?.length > 0 && (
            <p>
              <strong>Matched Skills:</strong>{" "}
              {job.matched_skills.join(", ")}
            </p>
          )}

          {job.missing_required_skills?.length > 0 && (
            <p>
              <strong>Missing Skills:</strong>{" "}
              {job.missing_required_skills.join(", ")}
            </p>
          )}

          {job.apply_link && (
            <a
              href={job.apply_link}
              target="_blank"
              rel="noopener noreferrer"
            >
              Apply →
            </a>
          )}
        </div>
      ))}
    </div>
  );
};

export default JobMatches;
