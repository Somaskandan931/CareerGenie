import React, { useState } from "react";

const API_BASE = "http://localhost:8000";

const JobSearch = ({
  setResumeText,
  setJobQuery,
  setLocation
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState(false);

  // -------------------------------
  // Resume upload handler
  // -------------------------------
  const handleResumeUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    setUploaded(false);

    try {
      const response = await fetch(`${API_BASE}/upload-resume/parse`, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        throw new Error("Resume upload failed");
      }

      const data = await response.json();

      // 🔑 CRITICAL: lift resume text to App.js
      setResumeText(data.resume_text);
      setUploaded(true);

    } catch (err) {
      console.error(err);
      alert("Failed to upload resume");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ marginBottom: "20px" }}>
      <h2>Job Search</h2>

      {/* Resume Upload */}
      <div style={{ marginBottom: "10px" }}>
        <label>
          Upload Resume (PDF / DOC):
          <br />
          <input
            type="file"
            accept=".pdf,.doc,.docx"
            onChange={handleResumeUpload}
          />
        </label>

        {uploading && <p>📄 Uploading resume...</p>}
        {uploaded && <p style={{ color: "green" }}>✅ Resume uploaded</p>}
      </div>

      {/* Job Query */}
      <div style={{ marginBottom: "10px" }}>
        <input
          type="text"
          placeholder="Job role (e.g. Software Engineer)"
          onChange={(e) => setJobQuery(e.target.value)}
          style={{ width: "300px" }}
        />
      </div>

      {/* Location */}
      <div>
        <input
          type="text"
          placeholder="Location (optional)"
          onChange={(e) => setLocation(e.target.value)}
          style={{ width: "300px" }}
        />
      </div>
    </div>
  );
};

export default JobSearch;
