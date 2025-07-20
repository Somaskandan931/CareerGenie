import { useState } from "react";
import axios from "axios";

export default function JobSearch({ setJobs }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await axios.get("http://localhost:8000/jobs/search-jobs", {
        params: { query },  // sends ?query=yourQuery
      });

      if (res.data.results) {
        setJobs(res.data.results);
      } else {
        setJobs([]);
        setError("No jobs found.");
      }
    } catch (err) {
      console.error("Job search error:", err);
      setJobs([]);
      setError("Failed to fetch jobs. Please try again.");
    }

    setLoading(false);
  };

  return (
    <div className="max-w-xl mx-auto p-6 bg-white rounded shadow mb-8">
      <h2 className="text-xl font-semibold mb-4">Job Search</h2>

      <input
        type="text"
        placeholder="Search jobs..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full p-2 border border-gray-300 rounded mb-2"
      />

      <button
        onClick={handleSearch}
        disabled={loading}
        className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
      >
        {loading ? "Searching..." : "Search Jobs"}
      </button>

      {error && <p className="text-red-600 mt-4">❌ {error}</p>}
    </div>
  );
}
