import { useState } from "react";
import axios from "axios";

export default function ResumeForm({ setResumeData, setResumeKeywords }) {
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    education: "",
    experience: "",
    skills: "",
  });

  const [loading, setLoading] = useState(false);
  const [pdfLink, setPdfLink] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResumeData(form);

    const keywords = form.skills.split(",").map((k) => k.trim()).filter(Boolean);
    setResumeKeywords(keywords);

    setLoading(true);
    setError(null);
    setPdfLink(null);

    try {
      const payload = {
        ...form,
        skills: keywords,
      };

      const res = await axios.post("http://localhost:8000/builder/generate-latex", payload);
      if (res.data.download_link) {
        setPdfLink(`http://localhost:8000${res.data.download_link}`);
      } else {
        setError("PDF generation failed.");
      }
    } catch (err) {
      setError("Could not connect to backend. Please check if it's running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-xl mx-auto p-6 bg-white rounded shadow mb-8">
      <h2 className="text-xl font-semibold mb-4">Resume Builder</h2>

      {["name", "email", "phone", "education", "experience", "skills"].map((field) => (
        <div key={field} className="mb-3">
          <label className="block font-semibold capitalize mb-1">{field}</label>
          <textarea
            rows={field === "skills" ? 2 : 3}
            name={field}
            className="w-full p-2 border border-gray-300 rounded"
            value={form[field]}
            onChange={handleChange}
            placeholder={field === "skills" ? "e.g. Python, SQL, React" : `Enter your ${field}`}
          />
        </div>
      ))}

      <button
        type="submit"
        disabled={loading}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Generating..." : "Submit Resume"}
      </button>

      {error && <p className="text-red-600 mt-4">❌ {error}</p>}
      {pdfLink && (
        <div className="mt-4">
          <p className="text-green-600 font-semibold">✅ Resume generated!</p>
          <a href={pdfLink} target="_blank" rel="noreferrer" className="text-blue-500 underline">
            Download PDF
          </a>
        </div>
      )}
    </form>
  );
}
