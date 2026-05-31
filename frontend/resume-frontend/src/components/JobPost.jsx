import { useState } from "react";
import API_BASE_URL from '../config';

const Ico = ({ d, className = "w-4 h-4" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const I = {
  check: "M5 13l4 4L19 7",
  alert: "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  post:  "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
};

const inp = "w-full px-4 py-2.5 text-sm rounded-xl border border-white/10 bg-white/5 text-white placeholder-slate-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none transition";

export default function JobPost() {
  const [form, setForm] = useState({
    title: "", company: "", location: "India",
    employment_type: "Full-time", description: "",
    requirements: "", salary_range: "", contact_email: "",
  });
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState(null);
  const [error,   setError]   = useState(null);

  const handleChange = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async () => {
    if (!form.title || !form.company || !form.description) {
      setError("Title, Company and Description are required."); return;
    }
    setLoading(true); setError(null); setResult(null);
    try {
      const res  = await fetch(`${API_BASE_URL}/jobs/post`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Post failed");
      setResult(data);
      setForm({ title:"",company:"",location:"India",employment_type:"Full-time",
                description:"",requirements:"",salary_range:"",contact_email:"" });
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const Field = ({ label, name, type = "text", placeholder = "", required = false, big = false }) => (
    <div>
      <label className="block text-xs font-medium text-slate-400 mb-1.5">
        {label}{required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      {big ? (
        <textarea name={name} value={form[name]} onChange={handleChange}
          placeholder={placeholder} rows={4}
          className={inp + " resize-none"} />
      ) : (
        <input type={type} name={name} value={form[name]} onChange={handleChange}
          placeholder={placeholder} className={inp} />
      )}
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto">
      <div className="rounded-2xl border border-white/10 p-6" style={{ background: "rgba(255,255,255,0.03)" }}>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-xl bg-orange-500/15 flex items-center justify-center">
            <Ico d={I.post} className="w-4 h-4 text-orange-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Post a Job</h2>
            <p className="text-xs text-slate-500">Your posting goes live immediately on the candidate board.</p>
          </div>
        </div>

        {result && (
          <div className="mb-5 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-start gap-2">
            <Ico d={I.check} className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-emerald-400">{result.message}</p>
              <p className="text-xs text-emerald-600 mt-0.5">Job ID: {result.job_id}</p>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-5 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-2">
            <Ico d={I.alert} className="w-4 h-4 text-red-400 flex-shrink-0" />
            <p className="text-sm text-red-400">{error}</p>
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
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Employment Type</label>
              <select name="employment_type" value={form.employment_type} onChange={handleChange}
                className={inp + " cursor-pointer [color-scheme:dark]"}>
                {["Full-time","Part-time","Contract","Internship","Remote"].map(t => (
                  <option key={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>
          <Field label="Job Description" name="description"
            placeholder="Describe the role, responsibilities, and what success looks like…" big required />
          <Field label="Requirements" name="requirements"
            placeholder="Skills, experience, qualifications…" big />
          <div className="grid grid-cols-2 gap-4">
            <Field label="Salary Range"  name="salary_range"  placeholder="e.g. ₹8–12 LPA" />
            <Field label="Contact Email" name="contact_email" type="email" placeholder="hr@company.com" />
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <p className="text-xs text-slate-600">Visible immediately to all candidates.</p>
          <button onClick={handleSubmit} disabled={loading}
            className="flex items-center gap-2 bg-orange-600 hover:bg-orange-500 disabled:opacity-40 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-all">
            {loading
              ? <><span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />Posting…</>
              : <><Ico d={I.post} className="w-4 h-4" />Post Job</>}
          </button>
        </div>
      </div>
    </div>
  );
}