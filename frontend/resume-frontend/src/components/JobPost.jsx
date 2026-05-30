import { useState } from "react";
import API_BASE_URL from '../config';

export default function JobPost() {
  const [form, setForm] = useState({
    title:           "",
    company:         "",
    location:        "India",
    employment_type: "Full-time",
    description:     "",
    requirements:    "",
    salary_range:    "",
    contact_email:   "",
  });
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState(null);
  const [error,   setError]   = useState(null);

  const handleChange = (e) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async () => {
    if (!form.title || !form.company || !form.description) {
      setError("Title, Company and Description are required.");
      return;
    }
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/jobs/post`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Post failed");
      setResult(data);
      setForm({
        title: "", company: "", location: "India", employment_type: "Full-time",
        description: "", requirements: "", salary_range: "", contact_email: "",
      });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const Field = ({ label, name, type = "text", placeholder = "", required = false, big = false }) => (
    <div>
      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
        {label}{required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      {big ? (
        <textarea
          name={name}
          value={form[name]}
          onChange={handleChange}
          placeholder={placeholder}
          rows={4}
          className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
        />
      ) : (
        <input
          type={type}
          name={name}
          value={form[name]}
          onChange={handleChange}
          placeholder={placeholder}
          className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      )}
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6">

        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Post a Job</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Your posting goes live immediately in the candidate job board.
          </p>
        </div>

        {result && (
          <div className="mb-5 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl text-sm text-green-700 dark:text-green-300">
            ✅ {result.message}{" "}
            <span className="text-xs opacity-70 ml-1">(ID: {result.job_id})</span>
          </div>
        )}

        {error && (
          <div className="mb-5 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl text-sm text-red-700 dark:text-red-300">
            ❌ {error}
          </div>
        )}

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Job Title"  name="title"   placeholder="e.g. Senior Python Engineer" required />
            <Field label="Company"    name="company" placeholder="e.g. Acme Corp"               required />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Location" name="location" placeholder="e.g. Chennai, India" />
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                Employment Type
              </label>
              <select
                name="employment_type"
                value={form.employment_type}
                onChange={handleChange}
                className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {["Full-time", "Part-time", "Contract", "Internship", "Remote"].map(t => (
                  <option key={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          <Field
            label="Job Description"
            name="description"
            placeholder="Describe the role, responsibilities, and what success looks like..."
            big
            required
          />
          <Field
            label="Requirements"
            name="requirements"
            placeholder="Skills, experience, qualifications..."
            big
          />

          <div className="grid grid-cols-2 gap-4">
            <Field label="Salary Range"   name="salary_range"  placeholder="e.g. ₹8–12 LPA" />
            <Field label="Contact Email"  name="contact_email" type="email" placeholder="hr@company.com" />
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <p className="text-xs text-gray-400 dark:text-gray-500">
            Visible immediately to all candidates on the job board.
          </p>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {loading ? "Posting..." : "Post Job →"}
          </button>
        </div>

      </div>
    </div>
  );
}