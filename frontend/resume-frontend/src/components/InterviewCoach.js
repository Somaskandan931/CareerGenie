import React, { useState, useRef, useEffect, useCallback } from "react";

const API_BASE_URL = "http://localhost:8000";

const INTERVIEW_TYPES = [
  { value: "mixed",       label: "Mixed",       icon: "⚡", desc: "All question types" },
  { value: "technical",   label: "Technical",   icon: "💻", desc: "DSA & system design" },
  { value: "behavioural", label: "Behavioural",  icon: "🧠", desc: "STAR method & soft skills" },
  { value: "hr",          label: "HR",           icon: "🤝", desc: "Culture & career fit" },
];

const DIFFICULTY = ["easy", "medium", "hard"];

// ─── Icons ────────────────────────────────────────────────────────────────────
const Ico = ({ d, size = 5, className = "" }) => (
  <svg className={`w-${size} h-${size} ${className}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const MicIcon    = () => <Ico d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />;
const MicOffIcon = () => <Ico d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3zM3 3l18 18" />;
const CamIcon    = () => <Ico d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />;
const CamOffIcon = () => <Ico d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8zM3 3l18 18" />;
const SendIcon   = () => <Ico d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />;
const StopIcon   = () => <Ico d="M21 12a9 9 0 11-18 0 9 9 0 0118 0zM9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />;
const ChevronIcon = ({ open }) => <Ico d={open ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"} size={4} />;
const BackIcon   = () => <Ico d="M10 19l-7-7m0 0l7-7m-7 7h18" size={4} />;
const TrophyIcon = () => <Ico d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />;

// ─── Audio Visualizer ─────────────────────────────────────────────────────────
const AudioWave = ({ active }) => (
  <div className="flex items-center gap-0.5 h-6">
    {Array.from({ length: 7 }, (_, i) => (
      <div key={i} className={`w-0.5 rounded-full transition-all ${active ? "bg-emerald-400" : "bg-white/20"}`}
        style={{
          height: active ? `${8 + Math.sin(Date.now() / 200 + i) * 8}px` : "4px",
          animation: active ? `wave ${0.5 + i * 0.1}s ease-in-out infinite alternate` : "none",
          animationDelay: `${i * 0.08}s`,
        }} />
    ))}
    <style>{`@keyframes wave { from { height: 4px } to { height: 20px } }`}</style>
  </div>
);

// ─── Score Ring ───────────────────────────────────────────────────────────────
const ScoreRing = ({ score, size = 80 }) => {
  const r = size / 2 - 8;
  const circ = 2 * Math.PI * r;
  const pct  = score / 10;
  const color = score >= 8 ? "#10b981" : score >= 5 ? "#f59e0b" : "#ef4444";
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={6} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={6}
          strokeDasharray={circ} strokeDashoffset={circ * (1 - pct)} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease" }} />
      </svg>
      <p className="-mt-12 text-2xl font-black" style={{ color }}>{score}<span className="text-sm font-normal text-white/30">/10</span></p>
    </div>
  );
};

// ─── Feedback Panel ───────────────────────────────────────────────────────────
const FeedbackPanel = ({ feedback }) => {
  const [open, setOpen] = useState(true);
  if (!feedback) return null;
  return (
    <div className="rounded-2xl overflow-hidden mt-3" style={{ background: "rgba(124,58,237,0.08)", border: "1px solid rgba(124,58,237,0.2)" }}>
      <button onClick={() => setOpen(v => !v)} className="w-full flex items-center justify-between px-4 py-3">
        <span className="text-violet-300 text-sm font-semibold">📋 AI Feedback</span>
        <ChevronIcon open={open} />
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3">
          <div className="flex justify-center py-2"><ScoreRing score={feedback.score} /></div>
          {feedback.strengths?.length > 0 && (
            <div className="p-3 rounded-xl" style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)" }}>
              <p className="text-emerald-400 text-xs font-bold mb-1.5">✅ STRENGTHS</p>
              {feedback.strengths.map((s, i) => <p key={i} className="text-emerald-300 text-sm">• {s}</p>)}
            </div>
          )}
          {feedback.improvements?.length > 0 && (
            <div className="p-3 rounded-xl" style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)" }}>
              <p className="text-amber-400 text-xs font-bold mb-1.5">💡 IMPROVEMENTS</p>
              {feedback.improvements.map((s, i) => <p key={i} className="text-amber-300 text-sm">• {s}</p>)}
            </div>
          )}
          {feedback.sample_better_answer && (
            <div className="p-3 rounded-xl" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <p className="text-white/50 text-xs font-bold mb-1.5">⭐ MODEL ANSWER</p>
              <p className="text-white/70 text-sm leading-relaxed">{feedback.sample_better_answer}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Chat Bubble ──────────────────────────────────────────────────────────────
const Bubble = ({ message }) => {
  const isUser = message.role === "user";
  return (
    <div className={`flex items-end gap-2 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold ${isUser ? "bg-violet-600" : "bg-gradient-to-br from-blue-500 to-indigo-600"} text-white`}>
        {isUser ? "You" : "AI"}
      </div>
      <div className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
        isUser
          ? "bg-violet-600 text-white rounded-br-sm"
          : "text-white/85 rounded-bl-sm"
      }`} style={!isUser ? { background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.08)" } : {}}>
        {message.content}
      </div>
    </div>
  );
};

// ─── Setup Screen ─────────────────────────────────────────────────────────────
const SetupScreen = ({ onStart }) => {
  const [role,        setRole]        = useState("Software Engineer");
  const [type,        setType]        = useState("mixed");
  const [difficulty,  setDifficulty]  = useState("medium");
  const [numQ,        setNumQ]        = useState(5);
  const [camPreview,  setCamPreview]  = useState(false);
  const [camError,    setCamError]    = useState(false);
  const previewRef = useRef(null);
  const streamRef  = useRef(null);

  useEffect(() => {
    return () => { if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop()); };
  }, []);

  const testCam = async () => {
    if (camPreview) {
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      setCamPreview(false); return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      streamRef.current = stream;
      if (previewRef.current) previewRef.current.srcObject = stream;
      setCamPreview(true); setCamError(false);
    } catch { setCamError(true); }
  };

  const diffColors = { easy: "#10b981", medium: "#f59e0b", hard: "#ef4444" };

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif", minHeight: "100vh", background: "#0d0d14", color: "#fff", display: "flex", flexDirection: "column" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />

      {/* Header */}
      <div className="px-6 pt-8 pb-4">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-2xl flex items-center justify-center text-xl" style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)" }}>🎙️</div>
            <div>
              <h1 className="text-2xl font-black">AI Mock Interview</h1>
              <p className="text-white/40 text-sm">Live camera · Voice · Real-time AI feedback</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 px-6 pb-10 overflow-y-auto">
        <div className="max-w-2xl mx-auto space-y-5">

          {/* Camera preview */}
          <div className="rounded-2xl overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)" }}>
            <div className="p-4 border-b border-white/8">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-semibold text-sm">Camera & Microphone</p>
                  <p className="text-white/40 text-xs mt-0.5">Test your setup before starting</p>
                </div>
                <button onClick={testCam}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${camPreview ? "bg-red-500/15 border-red-500/30 text-red-400 border" : "border border-white/15 text-white/60 hover:border-white/25 hover:text-white/90"}`}>
                  {camPreview ? <><CamOffIcon />Stop Preview</> : <><CamIcon />Test Camera</>}
                </button>
              </div>
            </div>
            <div className="aspect-video relative" style={{ background: "#080810" }}>
              {camPreview ? (
                <video ref={previewRef} autoPlay playsInline muted className="w-full h-full object-cover" />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
                  <div className="w-16 h-16 rounded-2xl flex items-center justify-center" style={{ background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.25)" }}>
                    <span className="text-3xl">🎥</span>
                  </div>
                  <p className="text-white/30 text-sm">Camera preview will appear here</p>
                  {camError && <p className="text-red-400 text-xs">⚠️ Camera access denied — check browser permissions</p>}
                </div>
              )}
              {camPreview && (
                <div className="absolute bottom-3 left-3 flex items-center gap-2 px-2.5 py-1.5 rounded-lg" style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(8px)" }}>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-white text-xs font-medium">Camera active</span>
                </div>
              )}
            </div>
          </div>

          {/* Config */}
          <div className="rounded-2xl p-5 space-y-5" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.07)" }}>
            {/* Role */}
            <div>
              <label className="block text-xs font-bold mb-2" style={{ color: "rgba(255,255,255,0.4)", letterSpacing: "0.08em", textTransform: "uppercase" }}>Target Role</label>
              <input value={role} onChange={e => setRole(e.target.value)}
                placeholder="e.g. Software Engineer, Product Manager, Data Scientist"
                className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-white/25 outline-none focus:border-violet-500/60 transition-colors"
                style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)" }} />
            </div>

            {/* Interview type */}
            <div>
              <label className="block text-xs font-bold mb-2" style={{ color: "rgba(255,255,255,0.4)", letterSpacing: "0.08em", textTransform: "uppercase" }}>Interview Type</label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {INTERVIEW_TYPES.map(t => (
                  <button key={t.value} onClick={() => setType(t.value)}
                    className={`flex flex-col items-center gap-1 py-3 rounded-xl border text-center transition-all ${type === t.value
                      ? "border-violet-500/60 text-white"
                      : "border-white/8 text-white/40 hover:border-white/15 hover:text-white/70"}`}
                    style={type === t.value ? { background: "rgba(124,58,237,0.15)" } : {}}>
                    <span className="text-xl">{t.icon}</span>
                    <span className="text-xs font-semibold">{t.label}</span>
                    <span className="text-xs opacity-60 leading-tight">{t.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Difficulty + count */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold mb-2" style={{ color: "rgba(255,255,255,0.4)", letterSpacing: "0.08em", textTransform: "uppercase" }}>Difficulty</label>
                <div className="flex gap-2">
                  {DIFFICULTY.map(d => (
                    <button key={d} onClick={() => setDifficulty(d)}
                      className={`flex-1 py-2 rounded-xl text-xs font-semibold border capitalize transition-all ${difficulty === d ? "text-white" : "text-white/40 border-white/8 hover:border-white/15"}`}
                      style={difficulty === d ? { background: `${diffColors[d]}20`, borderColor: `${diffColors[d]}50`, color: diffColors[d] } : {}}>
                      {d}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold mb-2" style={{ color: "rgba(255,255,255,0.4)", letterSpacing: "0.08em", textTransform: "uppercase" }}>Questions</label>
                <div className="flex gap-2">
                  {[3, 5, 7, 10].map(n => (
                    <button key={n} onClick={() => setNumQ(n)}
                      className={`flex-1 py-2 rounded-xl text-xs font-semibold border transition-all ${numQ === n
                        ? "bg-violet-600/20 border-violet-500/50 text-violet-300"
                        : "border-white/8 text-white/40 hover:border-white/15"}`}>
                      {n}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Start button */}
          <button onClick={() => onStart({ role, type, difficulty, numQ })}
            className="w-full py-4 rounded-2xl text-base font-black tracking-wide transition-all active:scale-98 hover:scale-[1.01]"
            style={{ background: "linear-gradient(135deg,#7c3aed 0%,#2563eb 100%)", boxShadow: "0 8px 30px rgba(124,58,237,0.4)" }}>
            🚀 Start Live Interview
          </button>
          <p className="text-center text-white/25 text-xs">Your camera and microphone will be activated when the interview begins</p>
        </div>
      </div>
    </div>
  );
};

// ─── Live Interview Room ───────────────────────────────────────────────────────
const LiveInterviewRoom = ({ config, onEnd }) => {
  const localVideoRef = useRef(null);
  const streamRef     = useRef(null);
  const chatEndRef    = useRef(null);
  const recognitionRef = useRef(null);

  const [messages,      setMessages]      = useState([]);
  const [input,         setInput]         = useState("");
  const [loading,       setLoading]       = useState(false);
  const [sessionId,     setSessionId]     = useState(null);
  const [currentQ,      setCurrentQ]      = useState(null);
  const [qIndex,        setQIndex]        = useState(0);
  const [totalQ,        setTotalQ]        = useState(config.numQ);
  const [feedback,      setFeedback]      = useState(null);
  const [latestFeedback, setLatestFeedback] = useState(null);
  const [elapsed,       setElapsed]       = useState(0);
  const [micOn,         setMicOn]         = useState(true);
  const [camOn,         setCamOn]         = useState(true);
  const [listening,     setListening]     = useState(false);
  const [phase,         setPhase]         = useState("intro"); // intro | qa | done
  const [scores,        setScores]        = useState([]);
  const [initError,     setInitError]     = useState(null);

  // Init camera + session
  useEffect(() => {
    (async () => {
      // Camera
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        streamRef.current = stream;
        if (localVideoRef.current) localVideoRef.current.srcObject = stream;
      } catch { setInitError("Camera/mic denied. You can still type your answers."); }

      // Session init
      try {
        const r = await fetch(`${API_BASE_URL}/interview/start`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role: config.role, interview_type: config.type, difficulty: config.difficulty, num_questions: config.numQ }),
        });
        const d = await r.json();
        setSessionId(d.session_id);
        setTotalQ(d.total_questions || config.numQ);
        setMessages([{ role: "assistant", content: d.opening_message || `Welcome! I'm your AI interviewer. We'll have ${config.numQ} ${config.difficulty} questions for a ${config.role} role. Let's begin!` }]);
        setPhase("qa");
        // First question
        await askNext(d.session_id, 0);
      } catch {
        setMessages([{ role: "assistant", content: `Welcome! I'm your AI interviewer for a ${config.role} ${config.type} interview. Ready when you are — type your answer below or use the mic!` }]);
        setPhase("qa");
      }
    })();
    return () => {
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      if (recognitionRef.current) recognitionRef.current.abort();
    };
  }, []);

  const askNext = async (sid, idx) => {
    try {
      const r = await fetch(`${API_BASE_URL}/interview/next-question`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sid || sessionId, question_index: idx }),
      });
      const d = await r.json();
      if (d.done) { setPhase("done"); return; }
      const q = d.question;
      setCurrentQ(q);
      setQIndex(idx);
      setMessages(m => [...m, { role: "assistant", content: `**Q${idx + 1}:** ${q.question}${q.hints ? `\n\n💡 Hint: ${q.hints}` : ""}` }]);
    } catch {
      // Fallback inline question generation
      const fallbackQ = "Tell me about a time you solved a challenging technical problem. Walk me through your approach.";
      setCurrentQ({ question: fallbackQ, type: config.type, difficulty: config.difficulty });
      setQIndex(idx);
      setMessages(m => [...m, { role: "assistant", content: `**Q${idx + 1}:** ${fallbackQ}` }]);
    }
  };

  // Timer
  useEffect(() => {
    const id = setInterval(() => setElapsed(e => e + 1), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const fmt = (s) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

  const submitAnswer = async (answer = input) => {
    if (!answer.trim() || loading) return;
    const ans = answer.trim();
    setInput("");
    setMessages(m => [...m, { role: "user", content: ans }]);
    setLoading(true);
    setLatestFeedback(null);

    try {
      const r = await fetch(`${API_BASE_URL}/interview/evaluate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: currentQ?.question || "Interview question", answer: ans, role: config.role, interview_type: config.type }),
      });
      const d = await r.json();
      const fb = d.feedback;
      setLatestFeedback(fb);
      setScores(s => [...s, fb.score]);

      const nextMsg = fb.follow_up_question
        ? `Good answer! Score: ${fb.score}/10\n\n${fb.follow_up_question}`
        : `Score: ${fb.score}/10 — ${fb.score >= 7 ? "Well done!" : "Keep practising!"}`;
      setMessages(m => [...m, { role: "assistant", content: nextMsg, feedback: fb }]);

      const next = qIndex + 1;
      if (next >= totalQ) {
        setTimeout(() => setPhase("done"), 1200);
      } else {
        await askNext(sessionId, next);
      }
    } catch {
      setMessages(m => [...m, { role: "assistant", content: "Answer received! Moving to next question…" }]);
      const next = qIndex + 1;
      if (next >= totalQ) setPhase("done");
      else await askNext(sessionId, next);
    } finally { setLoading(false); }
  };

  // Voice
  const toggleVoice = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) { alert("Speech recognition not supported in this browser."); return; }
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false); return;
    }
    const rec = new SpeechRecognition();
    rec.continuous = true; rec.interimResults = true; rec.lang = "en-US";
    rec.onresult = (e) => {
      const transcript = Array.from(e.results).map(r => r[0].transcript).join("");
      setInput(transcript);
    };
    rec.onend = () => setListening(false);
    rec.start();
    recognitionRef.current = rec;
    setListening(true);
  };

  const toggleCam = () => {
    streamRef.current?.getVideoTracks().forEach(t => { t.enabled = !camOn; });
    setCamOn(v => !v);
  };

  const toggleMic = () => {
    streamRef.current?.getAudioTracks().forEach(t => { t.enabled = !micOn; });
    setMicOn(v => !v);
  };

  const avgScore = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : null;

  // ── Done screen ─────────────────────────────────────────────────────────────
  if (phase === "done") {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: "#0d0d14", fontFamily: "'DM Sans', sans-serif" }}>
        <div className="max-w-md w-full px-6 text-center">
          <div className="w-20 h-20 rounded-3xl mx-auto mb-6 flex items-center justify-center text-4xl" style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)" }}>🏆</div>
          <h2 className="text-2xl font-black text-white mb-2">Interview Complete!</h2>
          <p className="text-white/40 text-sm mb-8">{config.numQ} questions · {fmt(elapsed)} · {config.role}</p>

          {avgScore && (
            <div className="flex justify-center mb-8">
              <div className="text-center">
                <ScoreRing score={parseFloat(avgScore)} size={120} />
                <p className="text-white/50 text-sm mt-3">Average Score</p>
              </div>
            </div>
          )}

          {scores.length > 0 && (
            <div className="flex items-end justify-center gap-1.5 mb-8 h-16">
              {scores.map((s, i) => (
                <div key={i} className="flex flex-col items-center gap-1">
                  <div className="w-6 rounded-t-md" style={{ height: `${s * 5}px`, background: s >= 8 ? "#10b981" : s >= 5 ? "#f59e0b" : "#ef4444" }} />
                  <span className="text-white/30 text-xs">Q{i + 1}</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-3">
            <button onClick={onEnd}
              className="flex-1 py-3 rounded-2xl text-sm font-bold border border-white/10 text-white/60 hover:text-white/90 transition-colors">
              ← Exit
            </button>
            <button onClick={() => window.location.reload()}
              className="flex-1 py-3 rounded-2xl text-sm font-bold text-white transition-all"
              style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)", boxShadow: "0 6px 20px rgba(124,58,237,0.35)" }}>
              Try Again 🔄
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex flex-col" style={{ background: "#0d0d14", fontFamily: "'DM Sans', sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />

      {/* Top bar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/8">
        <div className="flex items-center gap-3">
          <button onClick={onEnd} className="w-8 h-8 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/40 hover:text-white/70 transition-all">
            <BackIcon />
          </button>
          <div>
            <p className="text-white text-sm font-semibold">{config.role} Interview</p>
            <p className="text-white/30 text-xs capitalize">{config.type} · {config.difficulty}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Progress */}
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              {Array.from({ length: totalQ }, (_, i) => (
                <div key={i} className="w-1.5 h-1.5 rounded-full" style={{ background: i < qIndex ? "#10b981" : i === qIndex ? "#7c3aed" : "rgba(255,255,255,0.15)" }} />
              ))}
            </div>
            <span className="text-white/40 text-xs">{qIndex + 1}/{totalQ}</span>
          </div>
          <span className="flex items-center gap-1.5 text-xs font-medium" style={{ color: "rgba(255,255,255,0.35)" }}>
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />{fmt(elapsed)}
          </span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: Camera */}
        <div className="w-64 flex-shrink-0 border-r border-white/8 flex flex-col" style={{ background: "#090910" }}>
          {/* Local cam */}
          <div className="aspect-video relative" style={{ background: "#050508" }}>
            {camOn ? (
              <video ref={localVideoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <span className="text-white/20 text-sm">Camera off</span>
              </div>
            )}
            <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between">
              <span className="text-xs text-white/50 bg-black/50 px-1.5 py-0.5 rounded">You</span>
              <AudioWave active={micOn && listening} />
            </div>
          </div>

          {/* AI interviewer avatar */}
          <div className="flex-1 flex flex-col items-center justify-center p-4 gap-3">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl"
              style={{ background: "linear-gradient(135deg,#7c3aed20,#2563eb20)", border: "1px solid rgba(124,58,237,0.3)" }}>
              🤖
            </div>
            <div className="text-center">
              <p className="text-white/70 text-xs font-semibold">AI Interviewer</p>
              <p className="text-white/30 text-xs mt-0.5">
                {loading ? "Evaluating…" : "Ready"}
              </p>
            </div>
            {loading && (
              <div className="flex gap-1">
                {[0, 1, 2].map(i => <span key={i} className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />)}
              </div>
            )}
          </div>

          {/* Cam/mic controls */}
          <div className="p-3 border-t border-white/8 flex gap-2">
            <button onClick={toggleMic}
              className={`flex-1 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 border transition-all ${micOn ? "border-white/10 text-white/50 hover:border-white/20" : "border-red-500/40 text-red-400 bg-red-500/10"}`}>
              {micOn ? <MicIcon /> : <MicOffIcon />}
            </button>
            <button onClick={toggleCam}
              className={`flex-1 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 border transition-all ${camOn ? "border-white/10 text-white/50 hover:border-white/20" : "border-red-500/40 text-red-400 bg-red-500/10"}`}>
              {camOn ? <CamIcon /> : <CamOffIcon />}
            </button>
          </div>
        </div>

        {/* Right: Chat */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {initError && (
            <div className="px-4 py-2 border-b border-white/8" style={{ background: "rgba(245,158,11,0.08)" }}>
              <p className="text-amber-400 text-xs">⚠️ {initError}</p>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.map((m, i) => (
              <div key={i}>
                <Bubble message={m} />
                {m.feedback && <FeedbackPanel feedback={m.feedback} />}
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-xs text-white font-bold">AI</div>
                <div className="flex gap-1 px-4 py-3 rounded-2xl rounded-bl-sm" style={{ background: "rgba(255,255,255,0.06)" }}>
                  {[0,1,2].map(i => <span key={i} className="w-2 h-2 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: `${i * 0.12}s` }} />)}
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-white/8">
            <div className="flex gap-2 items-end">
              <div className="flex-1 relative">
                <textarea
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submitAnswer(); } }}
                  placeholder={listening ? "🎙️ Listening… speak your answer" : "Type your answer… (Enter to submit, Shift+Enter for newline)"}
                  rows={3}
                  className="w-full px-4 py-3 rounded-2xl text-sm text-white placeholder-white/25 outline-none resize-none transition-colors"
                  style={{ background: "rgba(255,255,255,0.05)", border: `1px solid ${listening ? "rgba(16,185,129,0.5)" : "rgba(255,255,255,0.1)"}` }}
                  disabled={loading}
                />
                {listening && (
                  <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2 py-1 rounded-lg" style={{ background: "rgba(16,185,129,0.15)" }}>
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-emerald-400 text-xs">Listening</span>
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-2">
                {/* Voice button */}
                <button onClick={toggleVoice}
                  className={`w-11 h-11 rounded-xl flex items-center justify-center transition-all active:scale-95 border ${listening ? "border-emerald-500/50 text-emerald-400 animate-pulse" : "border-white/10 text-white/40 hover:border-white/20 hover:text-white/70"}`}
                  style={listening ? { background: "rgba(16,185,129,0.15)" } : {}}>
                  <MicIcon />
                </button>
                {/* Send */}
                <button onClick={() => submitAnswer()} disabled={!input.trim() || loading}
                  className="w-11 h-11 rounded-xl flex items-center justify-center transition-all disabled:opacity-30 active:scale-95 text-white"
                  style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)", boxShadow: input.trim() ? "0 4px 12px rgba(124,58,237,0.35)" : "none" }}>
                  <SendIcon />
                </button>
              </div>
            </div>

            {/* Quick responses */}
            <div className="flex flex-wrap gap-2 mt-3">
              {["Can you repeat the question?", "Give me a moment to think", "I'm not sure, can I skip?"].map(q => (
                <button key={q} onClick={() => submitAnswer(q)}
                  className="text-xs px-3 py-1.5 rounded-full border border-white/10 text-white/40 hover:border-white/20 hover:text-white/70 transition-colors">
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── Main Wrapper ─────────────────────────────────────────────────────────────
const InterviewCoach = ({ resumeText = "", userId = "default_user" }) => {
  const [phase,  setPhase]  = useState("setup");   // setup | live
  const [config, setConfig] = useState(null);

  if (phase === "live" && config) {
    return <LiveInterviewRoom config={config} onEnd={() => setPhase("setup")} />;
  }

  return <SetupScreen onStart={(cfg) => { setConfig(cfg); setPhase("live"); }} />;
};

export default InterviewCoach;