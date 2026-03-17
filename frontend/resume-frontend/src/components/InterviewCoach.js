import React, { useState, useRef, useEffect } from "react";

const API_BASE_URL = "http://localhost:8000";

const INTERVIEW_TYPES = [
  { value: "mixed", label: "Mixed (All types)" },
  { value: "technical", label: "Technical" },
  { value: "behavioural", label: "Behavioural (STAR)" },
  { value: "hr", label: "HR / Culture fit" },
];

const DIFFICULTY_COLORS = {
  easy: "bg-green-100 text-green-700 border-green-200",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
  hard: "bg-red-100 text-red-700 border-red-200",
};

const TYPE_COLORS = {
  technical: "bg-blue-100 text-blue-700 border-blue-200",
  behavioural: "bg-purple-100 text-purple-700 border-purple-200",
  hr: "bg-orange-100 text-orange-700 border-orange-200",
};

// ─── Icons ────────────────────────────────────────────────────────────────────
const SendIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);
const MicIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
  </svg>
);
const StarIcon = ({ filled }) => (
  <svg className={`w-4 h-4 ${filled ? "text-yellow-400" : "text-gray-300"}`} fill="currentColor" viewBox="0 0 20 20">
    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
  </svg>
);
const ChevronIcon = ({ open }) => (
  <svg className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
);

// ─── Score bar ────────────────────────────────────────────────────────────────
const ScoreBar = ({ score }) => {
  const color = score >= 8 ? "bg-green-500" : score >= 5 ? "bg-yellow-400" : "bg-red-500";
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-600">Score</span>
        <span className="font-bold">{score}/10</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${score * 10}%` }} />
      </div>
      <div className="flex justify-between mt-0.5">
        {[...Array(5)].map((_, i) => <StarIcon key={i} filled={i < Math.round(score / 2)} />)}
      </div>
    </div>
  );
};

// ─── Feedback card ────────────────────────────────────────────────────────────
const FeedbackCard = ({ feedback }) => {
  const [open, setOpen] = useState(true);
  return (
    <div className="border border-indigo-200 bg-indigo-50 rounded-xl overflow-hidden mt-3">
      <button onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-indigo-900">
        📋 Answer Feedback
        <ChevronIcon open={open} />
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3 text-sm">
          <ScoreBar score={feedback.score} />
          {feedback.strengths?.length > 0 && (
            <div>
              <p className="font-semibold text-green-800 mb-1">✅ Strengths</p>
              <ul className="space-y-0.5">
                {feedback.strengths.map((s, i) => (
                  <li key={i} className="flex gap-1.5 text-green-700"><span>•</span>{s}</li>
                ))}
              </ul>
            </div>
          )}
          {feedback.improvements?.length > 0 && (
            <div>
              <p className="font-semibold text-orange-800 mb-1">💡 Improvements</p>
              <ul className="space-y-0.5">
                {feedback.improvements.map((s, i) => (
                  <li key={i} className="flex gap-1.5 text-orange-700"><span>•</span>{s}</li>
                ))}
              </ul>
            </div>
          )}
          {feedback.sample_better_answer && (
            <div className="bg-white border border-gray-200 rounded-lg p-3">
              <p className="font-semibold text-gray-700 mb-1 text-xs uppercase tracking-wide">Model Answer</p>
              <p className="text-gray-700">{feedback.sample_better_answer}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Chat bubble ──────────────────────────────────────────────────────────────
const Bubble = ({ message }) => {
  const isUser = message.role === "user";
  return (
    <div className={`flex items-start gap-2 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
        isUser ? "bg-indigo-600 text-white" : "bg-gradient-to-br from-blue-500 to-indigo-600 text-white"
      }`}>
        {isUser ? "You" : "AI"}
      </div>
      <div className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
        isUser ? "bg-indigo-600 text-white rounded-tr-sm" : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm"
      }`}>
        {message.content.split('\n').map((l, i) => <span key={i}>{l}{i < message.content.split('\n').length - 1 && <br />}</span>)}
      </div>
    </div>
  );
};

// ─── Question Bank Panel ──────────────────────────────────────────────────────
const QuestionBank = ({ questions, onSelectQuestion }) => {
  const [selected, setSelected] = useState(null);
  const [answer, setAnswer] = useState("");
  const [loadingEval, setLoadingEval] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [role, setRole] = useState("");

  const evaluateAnswer = async (q) => {
    if (!answer.trim()) return;
    setLoadingEval(true);
    setFeedback(null);
    try {
      const res = await fetch(`${API_BASE_URL}/interview/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q.question, answer, role: role || "Software Engineer",
                               interview_type: q.type }),
      });
      if (!res.ok) throw new Error("Evaluation failed");
      const data = await res.json();
      setFeedback(data.feedback);
    } catch (e) {
      setFeedback({ score: 0, strengths: [], improvements: ["Evaluation unavailable — check backend."],
                    sample_better_answer: "", follow_up_question: "" });
    } finally {
      setLoadingEval(false);
    }
  };

  if (!questions || questions.length === 0) return null;

  return (
    <div className="space-y-3">
      <input type="text" value={role} onChange={e => setRole(e.target.value)}
        placeholder="Role being practiced (for evaluation context)"
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-400" />

      {questions.map((q, i) => (
        <div key={i} className={`border rounded-xl overflow-hidden transition-all ${
          selected === i ? "border-blue-400 shadow-md" : "border-gray-200 hover:border-gray-300"
        }`}>
          <button className="w-full flex items-start gap-3 p-4 text-left bg-white hover:bg-gray-50"
            onClick={() => { setSelected(selected === i ? null : i); setAnswer(""); setFeedback(null); }}>
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center mt-0.5">
              {i + 1}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900">{q.question}</p>
              <div className="flex gap-1.5 mt-1.5 flex-wrap">
                <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${TYPE_COLORS[q.type] || TYPE_COLORS.technical}`}>
                  {q.type}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${DIFFICULTY_COLORS[q.difficulty] || ""}`}>
                  {q.difficulty}
                </span>
              </div>
            </div>
            <ChevronIcon open={selected === i} />
          </button>

          {selected === i && (
            <div className="px-4 pb-4 bg-gray-50 border-t border-gray-100 space-y-3">
              {q.hints && (
                <p className="text-xs text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg px-3 py-2">
                  💡 Hint: {q.hints}
                </p>
              )}
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Your Answer</label>
                <textarea rows={4} value={answer} onChange={e => setAnswer(e.target.value)}
                  placeholder="Type your answer here to get AI feedback…"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none focus:ring-2 focus:ring-blue-400" />
              </div>
              <button onClick={() => evaluateAnswer(q)} disabled={loadingEval || !answer.trim()}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-5 py-2 rounded-lg text-sm font-semibold disabled:opacity-50 flex items-center gap-2 hover:from-blue-700 hover:to-indigo-700 transition-all">
                {loadingEval
                  ? <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />Evaluating...</>
                  : "Get AI Feedback"}
              </button>
              {feedback && <FeedbackCard feedback={feedback} />}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
const InterviewCoach = ({ resumeText = "" }) => {
  const [mode, setMode] = useState("setup"); // "setup" | "live" | "bank"
  const [role, setRole] = useState("");
  const [interviewType, setInterviewType] = useState("mixed");
  const [numQuestions, setNumQuestions] = useState(10);

  // Live chat
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState(null);
  const bottomRef = useRef(null);

  // Question bank
  const [questions, setQuestions] = useState([]);
  const [bankLoading, setBankLoading] = useState(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatLoading]);

  const startLiveInterview = async () => {
    if (!role.trim()) return;
    setChatLoading(true);
    setChatError(null);
    setMessages([]);
    try {
      const res = await fetch(`${API_BASE_URL}/interview/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{ role: "user", content: "Start the interview." }],
          role, interview_type: interviewType,
          resume_text: resumeText || null,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
      setMessages([{ role: "assistant", content: data.reply }]);
      setMode("live");
    } catch (e) {
      setChatError(e.message);
    } finally {
      setChatLoading(false);
    }
  };

  const sendChatMessage = async () => {
    const content = chatInput.trim();
    if (!content || chatLoading) return;
    const newMessages = [...messages, { role: "user", content }];
    setMessages(newMessages);
    setChatInput("");
    setChatLoading(true);
    setChatError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/interview/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: newMessages.map(m => ({ role: m.role, content: m.content })),
          role, interview_type: interviewType, resume_text: resumeText || null,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
      setMessages(prev => [...prev, { role: "assistant", content: data.reply }]);
    } catch (e) {
      setChatError(e.message);
    } finally {
      setChatLoading(false);
    }
  };

  const loadQuestionBank = async () => {
    if (!role.trim()) return;
    setBankLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/interview/questions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role, interview_type: interviewType,
                               resume_text: resumeText || null, num_questions: numQuestions }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setQuestions(data.questions || []);
      setMode("bank");
    } catch (e) {
      setChatError(e.message);
    } finally {
      setBankLoading(false);
    }
  };

  // ── Setup screen ──────────────────────────────────────────────────────────
  if (mode === "setup") {
    return (
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-7 text-white">
          <h2 className="text-2xl font-black mb-1">🎤 AI Interview Coach</h2>
          <p className="text-blue-200 text-sm">
            Practice with a live mock interview or browse a curated question bank — get instant AI feedback on every answer.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Target Role <span className="text-red-500">*</span>
              </label>
              <input type="text" value={role} onChange={e => setRole(e.target.value)}
                placeholder="e.g. Software Engineer, Data Scientist, EV Technician"
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-400" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Interview Type</label>
              <select value={interviewType} onChange={e => setInterviewType(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-400 bg-white">
                {INTERVIEW_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Question Bank Size</label>
              <select value={numQuestions} onChange={e => setNumQuestions(Number(e.target.value))}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-400 bg-white">
                {[5, 10, 15, 20].map(n => <option key={n} value={n}>{n} questions</option>)}
              </select>
            </div>
          </div>

          {resumeText && (
            <p className="text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
              ✅ Resume loaded — questions will be personalised to your background.
            </p>
          )}

          {chatError && (
            <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{chatError}</p>
          )}

          <div className="flex flex-wrap gap-3">
            <button onClick={startLiveInterview} disabled={!role.trim() || chatLoading}
              className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-7 py-3 rounded-xl font-semibold text-sm disabled:opacity-50 hover:from-blue-700 hover:to-indigo-800 transition-all shadow-md flex items-center gap-2">
              {chatLoading
                ? <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />Starting...</>
                : <><MicIcon />Start Live Interview</>}
            </button>
            <button onClick={loadQuestionBank} disabled={!role.trim() || bankLoading}
              className="px-7 py-3 border-2 border-blue-400 text-blue-700 rounded-xl font-semibold text-sm disabled:opacity-50 hover:bg-blue-50 transition-colors flex items-center gap-2">
              {bankLoading
                ? <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />Loading...</>
                : "📋 Browse Question Bank"}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: "🎤", title: "Live Mock Interview", desc: "The AI acts as your interviewer. Answer questions in real time and get live feedback after each response." },
            { icon: "📋", title: "Question Bank", desc: "Browse curated questions, practice your answers at your own pace, and get detailed AI scoring." },
            { icon: "📊", title: "Instant Scoring", desc: "Every answer is scored 0–10 with strengths, improvements, and a model answer to compare against." },
          ].map(c => (
            <div key={c.title} className="bg-white rounded-xl border border-gray-200 p-5">
              <p className="text-2xl mb-2">{c.icon}</p>
              <p className="font-bold text-gray-900 mb-1">{c.title}</p>
              <p className="text-sm text-gray-500">{c.desc}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Live interview chat ───────────────────────────────────────────────────
  if (mode === "live") {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-gray-900">🎤 Live Mock Interview — {role}</h3>
            <p className="text-xs text-gray-500 mt-0.5">{INTERVIEW_TYPES.find(t => t.value === interviewType)?.label} · Powered by Groq</p>
          </div>
          <button onClick={() => { setMode("setup"); setMessages([]); }}
            className="text-sm text-gray-500 hover:text-gray-800 border border-gray-300 px-4 py-1.5 rounded-lg hover:bg-gray-50 transition-colors">
            ← New Interview
          </button>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden flex flex-col" style={{ height: "580px" }}>
          <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4 bg-gray-50">
            {messages.map((m, i) => <Bubble key={i} message={m} />)}
            {chatLoading && (
              <div className="flex items-start gap-2">
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white text-xs font-bold flex items-center justify-center">AI</div>
                <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                  <div className="flex gap-1">
                    {[0,1,2].map(i => <div key={i} className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: `${i*0.15}s` }} />)}
                  </div>
                </div>
              </div>
            )}
            {chatError && (
              <div className="text-center">
                <span className="text-xs text-red-600 bg-red-50 border border-red-200 px-3 py-1 rounded-full">{chatError}</span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <div className="px-4 py-3 bg-white border-t border-gray-200 flex gap-3 items-end">
            <textarea rows={2} value={chatInput} onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChatMessage(); } }}
              placeholder="Type your answer… (Enter to send)"
              className="flex-1 resize-none px-3 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-400 outline-none"
              disabled={chatLoading} />
            <button onClick={sendChatMessage} disabled={chatLoading || !chatInput.trim()}
              className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-xl flex items-center justify-center disabled:opacity-40 hover:from-blue-700 transition-all shadow-md flex-shrink-0">
              <SendIcon />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Question bank ─────────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-bold text-gray-900">📋 Question Bank — {role}</h3>
          <p className="text-xs text-gray-500 mt-0.5">{questions.length} questions · {INTERVIEW_TYPES.find(t => t.value === interviewType)?.label}</p>
        </div>
        <button onClick={() => setMode("setup")}
          className="text-sm text-gray-500 hover:text-gray-800 border border-gray-300 px-4 py-1.5 rounded-lg hover:bg-gray-50 transition-colors">
          ← Back
        </button>
      </div>
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <QuestionBank questions={questions} />
      </div>
    </div>
  );
};

export default InterviewCoach;