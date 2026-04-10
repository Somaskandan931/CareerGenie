import React, { useState, useRef, useEffect, useCallback } from "react";
import VideoPanel from "./VideoPanel";
import LiveFeedback from "./LiveFeedback";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
const WS_BASE =
  process.env.REACT_APP_WS_URL ||
  (window.location.protocol === "https:" ? "wss://" : "ws://") +
    (process.env.REACT_APP_API_HOST || "localhost:8000");

const INTERVIEW_TYPES = [
  { value: "mixed",       label: "Mixed",      icon: "⚡", desc: "All question types" },
  { value: "technical",  label: "Technical",   icon: "💻", desc: "DSA & system design" },
  { value: "behavioural",label: "Behavioural", icon: "🧠", desc: "STAR method & soft skills" },
  { value: "hr",         label: "HR",          icon: "🤝", desc: "Culture & career fit" },
];

const DIFFICULTY = ["easy", "medium", "hard"];

// ─── Shared icon component ────────────────────────────────────────────────────
const Ico = ({ d, size = 5, className = "" }) => (
  <svg className={`w-${size} h-${size} ${className}`} fill="none" viewBox="0 0 24 24"
    stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const MicIcon    = () => <Ico d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />;
const MicOffIcon = () => <Ico d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3zM3 3l18 18" />;
const CamIcon    = () => <Ico d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />;
const CamOffIcon = () => <Ico d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8zM3 3l18 18" />;
const SendIcon   = () => <Ico d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />;
const BackIcon   = () => <Ico d="M10 19l-7-7m0 0l7-7m-7 7h18" size={4} />;
const ChevronIcon = ({ open }) => <Ico d={open ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"} size={4} />;

// ─── Audio waveform animation ──────────────────────────────────────────────────
const AudioWave = ({ active }) => (
  <div className="flex items-center gap-0.5 h-6">
    {Array.from({ length: 7 }, (_, i) => (
      <div key={i}
        className={`w-0.5 rounded-full transition-all ${active ? "bg-emerald-400" : "bg-white/20"}`}
        style={{
          height: "4px",
          animation: active ? `wave ${0.5 + i * 0.1}s ease-in-out infinite alternate` : "none",
          animationDelay: `${i * 0.08}s`,
        }} />
    ))}
    <style>{`@keyframes wave { from { height: 4px } to { height: 20px } }`}</style>
  </div>
);

// ─── Score ring ────────────────────────────────────────────────────────────────
const ScoreRing = ({ score, size = 80 }) => {
  const r    = size / 2 - 8;
  const circ = 2 * Math.PI * r;
  const color = score >= 8 ? "#10b981" : score >= 5 ? "#f59e0b" : "#ef4444";
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={6} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={6}
          strokeDasharray={circ} strokeDashoffset={circ * (1 - score / 10)} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease" }} />
      </svg>
      <p className="-mt-12 text-2xl font-black" style={{ color }}>
        {score}<span className="text-sm font-normal text-white/30">/10</span>
      </p>
    </div>
  );
};

// ─── Inline feedback panel (used inside chat) ──────────────────────────────────
const FeedbackPanel = ({ feedback }) => {
  const [open, setOpen] = useState(true);
  if (!feedback) return null;
  return (
    <div className="rounded-2xl overflow-hidden mt-3"
      style={{ background: "rgba(124,58,237,0.08)", border: "1px solid rgba(124,58,237,0.2)" }}>
      <button onClick={() => setOpen(v => !v)} className="w-full flex items-center justify-between px-4 py-3">
        <span className="text-violet-300 text-sm font-semibold">📋 AI Feedback</span>
        <ChevronIcon open={open} />
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3">
          <div className="flex justify-center py-2"><ScoreRing score={feedback.score} /></div>
          {feedback.strengths?.length > 0 && (
            <div className="p-3 rounded-xl"
              style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)" }}>
              <p className="text-emerald-400 text-xs font-bold mb-1.5">✅ STRENGTHS</p>
              {feedback.strengths.map((s, i) => <p key={i} className="text-emerald-300 text-sm">• {s}</p>)}
            </div>
          )}
          {feedback.improvements?.length > 0 && (
            <div className="p-3 rounded-xl"
              style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)" }}>
              <p className="text-amber-400 text-xs font-bold mb-1.5">💡 IMPROVEMENTS</p>
              {feedback.improvements.map((s, i) => <p key={i} className="text-amber-300 text-sm">• {s}</p>)}
            </div>
          )}
          {feedback.sample_better_answer && (
            <div className="p-3 rounded-xl"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <p className="text-white/50 text-xs font-bold mb-1.5">⭐ MODEL ANSWER</p>
              <p className="text-white/70 text-sm leading-relaxed">{feedback.sample_better_answer}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Chat bubble ───────────────────────────────────────────────────────────────
const Bubble = ({ message }) => {
  const isUser = message.role === "user";
  return (
    <div className={`flex items-end gap-2 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold ${
        isUser ? "bg-violet-600" : "bg-gradient-to-br from-blue-500 to-indigo-600"} text-white`}>
        {isUser ? "You" : "AI"}
      </div>
      <div className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
        isUser ? "bg-violet-600 text-white rounded-br-sm" : "text-white/85 rounded-bl-sm"}`}
        style={!isUser ? { background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.08)" } : {}}>
        {message.content}
      </div>
    </div>
  );
};


// ═════════════════════════════════════════════════════════════════════════════
// AI LIVE INTERVIEW MODAL
// Uses /interview/live/start → /interview/live/next  (REST fallback)
// and /ws/interview/{session_id}                     (WebSocket primary)
// ═════════════════════════════════════════════════════════════════════════════

const AILiveInterviewModal = ({ config, onClose }) => {
  const videoRef    = useRef(null);
  const streamRef   = useRef(null);
  const recognRef   = useRef(null);
  const wsRef       = useRef(null);
  const chatEndRef  = useRef(null);
  const fullTransRef = useRef("");

  const [phase, setPhase]           = useState("loading"); // loading|qa|done
  const [sessionId, setSessionId]   = useState(null);
  const [question, setQuestion]     = useState("");
  const [qIndex, setQIndex]         = useState(0);
  const [totalQ, setTotalQ]         = useState(config.numQ);
  const [transcript, setTranscript] = useState("");
  const [feedback, setFeedback]     = useState(null);
  const [summary, setSummary]       = useState(null);
  const [loading, setLoading]       = useState(false);
  const [listening, setListening]   = useState(false);
  const [micOn, setMicOn]           = useState(true);
  const [camOn, setCamOn]           = useState(true);
  const [scores, setScores]         = useState([]);
  const [elapsed, setElapsed]       = useState(0);
  const [initError, setInitError]   = useState(null);
  const [messages, setMessages]     = useState([]);

  const fmt = (s) =>
    `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

  // ── Timer ────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (phase !== "qa") return;
    const id = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(id);
  }, [phase]);

  // ── Auto-scroll chat ─────────────────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Camera + session init ─────────────────────────────────────────────────
  useEffect(() => {
    let mounted = true;

    (async () => {
      // 1. Camera
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        });
        if (!mounted) { stream.getTracks().forEach((t) => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
      } catch {
        setInitError("Camera/mic not available — you can still type your answers.");
      }

      // 2. Start AI session
      try {
        const res = await fetch(`${API_BASE_URL}/interview/live/start`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            role: config.role,
            interview_type: config.type,
            resume_text: config.resumeText || "",
            num_questions: config.numQ,
          }),
        });
        const data = await res.json();
        if (!mounted) return;

        setSessionId(data.session_id);
        setTotalQ(data.total_questions || config.numQ);
        setQuestion(data.question);
        setQIndex(data.q_index || 0);
        setMessages([{
          role: "assistant",
          content: `Welcome to your ${config.role} ${config.type} interview! Here's your first question:\n\n${data.question}`,
        }]);
        setPhase("qa");

        // 3. Connect WebSocket for real-time updates
        const ws = new WebSocket(`${WS_BASE}/ws/interview/${data.session_id}`);
        wsRef.current = ws;

        ws.onmessage = ({ data: raw }) => {
          try {
            const msg = JSON.parse(raw);
            if (msg.type === "question") {
              const p = msg.payload;
              setQuestion(p.question);
              setFeedback(p.feedback || null);
              setQIndex(p.q_index);
              if (p.feedback) {
                setScores((s) => [...s, p.feedback.score]);
                setMessages((m) => [...m,
                  { role: "assistant", content: `Q${p.q_index + 1}: ${p.question}`, feedback: p.feedback },
                ]);
              } else {
                setMessages((m) => [...m,
                  { role: "assistant", content: `Q${p.q_index + 1}: ${p.question}` },
                ]);
              }
              setTranscript(""); fullTransRef.current = "";
              setLoading(false);
            }
            if (msg.type === "done") {
              const p = msg.payload;
              setFeedback(p.feedback || null);
              setSummary(p.summary || null);
              if (p.feedback) setScores((s) => [...s, p.feedback.score]);
              setPhase("done");
              setLoading(false);
            }
          } catch { /* ignore parse errors */ }
        };
      } catch (err) {
        if (!mounted) return;
        setInitError("Could not connect to interview server. Please try again.");
        setPhase("qa"); // allow manual fallback
        setMessages([{
          role: "assistant",
          content: `Welcome! I'll conduct your ${config.role} interview. Type or speak your answers below.`,
        }]);
      }
    })();

    return () => {
      mounted = false;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      recognRef.current?.abort();
      wsRef.current?.close();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Submit answer ─────────────────────────────────────────────────────────
  const submitAnswer = useCallback(async (override) => {
    const ans = (override || transcript).trim();
    if (!ans || loading) return;

    stopListening();
    setMessages((m) => [...m, { role: "user", content: ans }]);
    setTranscript(""); fullTransRef.current = "";
    setLoading(true);
    setFeedback(null);

    // WS path (preferred)
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "transcript", text: ans }));
      // Response handled by ws.onmessage — loading cleared there
      return;
    }

    // REST fallback
    try {
      const res = await fetch(`${API_BASE_URL}/interview/live/next`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, transcript: ans }),
      });
      const data = await res.json();

      if (data.done) {
        setFeedback(data.feedback || null);
        setSummary(data.summary || null);
        if (data.feedback) setScores((s) => [...s, data.feedback.score]);
        setPhase("done");
      } else {
        setQuestion(data.question);
        setFeedback(data.feedback || null);
        setQIndex(data.q_index);
        if (data.feedback) {
          setScores((s) => [...s, data.feedback.score]);
          setMessages((m) => [...m,
            { role: "assistant", content: `Q${data.q_index + 1}: ${data.question}`, feedback: data.feedback },
          ]);
        } else {
          setMessages((m) => [...m,
            { role: "assistant", content: `Q${data.q_index + 1}: ${data.question}` },
          ]);
        }
      }
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Answer received. Moving on…" }]);
    } finally {
      setLoading(false);
    }
  }, [transcript, loading, sessionId]);

  // ── Speech recognition ───────────────────────────────────────────────────
  const startListening = () => {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) { alert("Speech recognition not supported. Please type."); return; }
    const rec = new SpeechRec();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";
    rec.onresult = (e) => {
      let interim = "", final = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) final += e.results[i][0].transcript + " ";
        else interim += e.results[i][0].transcript;
      }
      if (final) fullTransRef.current += final;
      setTranscript(fullTransRef.current + interim);
    };
    rec.onend = () => setListening(false);
    rec.start();
    recognRef.current = rec;
    setListening(true);
  };

  const stopListening = () => {
    recognRef.current?.stop();
    setListening(false);
  };

  const toggleVoice = () => (listening ? stopListening() : startListening());

  // ── Camera/mic toggles ───────────────────────────────────────────────────
  const toggleMic = () => {
    streamRef.current?.getAudioTracks().forEach((t) => (t.enabled = !micOn));
    setMicOn((v) => !v);
  };
  const toggleCam = () => {
    streamRef.current?.getVideoTracks().forEach((t) => (t.enabled = !camOn));
    setCamOn((v) => !v);
  };

  const avgScore = scores.length
    ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1)
    : null;

  // ── Done screen ───────────────────────────────────────────────────────────
  if (phase === "done") {
    const perf = summary?.performance || (avgScore >= 8 ? "Excellent" : avgScore >= 6 ? "Good" : "Needs Practice");
    const perfColor = perf === "Excellent" ? "#10b981" : perf === "Good" ? "#f59e0b" : "#ef4444";

    return (
      <div className="flex flex-col items-center justify-center h-full py-8 text-center gap-5">
        <div className="w-20 h-20 rounded-3xl flex items-center justify-center text-4xl mx-auto"
          style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)" }}>🏆</div>
        <div>
          <h2 className="text-2xl font-black text-white">Interview Complete!</h2>
          <p className="text-white/40 text-sm mt-1">{config.numQ} questions · {fmt(elapsed)} · {config.role}</p>
        </div>

        {avgScore && (
          <div className="flex justify-center">
            <div>
              <ScoreRing score={parseFloat(avgScore)} size={120} />
              <p className="text-white/40 text-sm mt-2 text-center">Average Score</p>
            </div>
          </div>
        )}

        {/* Score bars */}
        {scores.length > 0 && (
          <div className="flex items-end justify-center gap-1.5 h-16 mt-2">
            {scores.map((s, i) => (
              <div key={i} className="flex flex-col items-center gap-1">
                <div className="w-6 rounded-t-md"
                  style={{ height: `${s * 5}px`, background: s >= 8 ? "#10b981" : s >= 5 ? "#f59e0b" : "#ef4444" }} />
                <span className="text-white/30 text-xs">Q{i + 1}</span>
              </div>
            ))}
          </div>
        )}

        <div
          className="px-6 py-2 rounded-full text-sm font-bold"
          style={{ background: `${perfColor}20`, color: perfColor, border: `1px solid ${perfColor}40` }}
        >
          {perf}
        </div>

        {feedback?.sample_better_answer && (
          <div className="max-w-sm mx-auto p-4 rounded-2xl text-left"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
            <p className="text-white/40 text-xs font-bold mb-1">💡 Last tip</p>
            <p className="text-white/65 text-xs leading-relaxed">{feedback.sample_better_answer}</p>
          </div>
        )}

        <div className="flex gap-3 mt-2">
          <button onClick={onClose}
            className="px-5 py-2.5 rounded-xl text-sm font-bold border border-white/10 text-white/60 hover:text-white/90 transition-colors">
            ← Exit
          </button>
          <button onClick={() => { onClose(); setTimeout(onClose, 50); }}
            className="px-6 py-2.5 rounded-xl text-sm font-bold text-white transition-all hover:scale-[1.02]"
            style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)", boxShadow: "0 6px 20px rgba(124,58,237,0.35)" }}>
            Try Again 🔄
          </button>
        </div>
      </div>
    );
  }

  // ── Loading ───────────────────────────────────────────────────────────────
  if (phase === "loading") {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl animate-pulse"
          style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)" }}>🤖</div>
        <p className="text-white/50 text-sm">Preparing your interview…</p>
        <div className="flex gap-1.5">
          {[0,1,2].map(i => <span key={i} className="w-2 h-2 rounded-full bg-violet-400 animate-bounce"
            style={{ animationDelay: `${i*0.15}s` }} />)}
        </div>
      </div>
    );
  }

  // ── Active QA ─────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full overflow-hidden">

      {/* Top bar */}
      <div className="flex items-center justify-between px-1 pb-3"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
        <div className="flex items-center gap-3">
          <div>
            <p className="text-white text-sm font-semibold">{config.role} Interview</p>
            <p className="text-white/30 text-xs capitalize">{config.type} · {config.difficulty}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Progress dots */}
          <div className="flex items-center gap-1.5">
            {Array.from({ length: totalQ }, (_, i) => (
              <div key={i} className="w-1.5 h-1.5 rounded-full transition-colors"
                style={{ background: i < qIndex ? "#10b981" : i === qIndex ? "#7c3aed" : "rgba(255,255,255,0.15)" }} />
            ))}
            <span className="text-white/40 text-xs ml-1">{qIndex + 1}/{totalQ}</span>
          </div>
          <span className="text-white/35 text-xs flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse inline-block" />
            {fmt(elapsed)}
          </span>
          <button onClick={onClose} className="text-white/30 hover:text-white/70 text-sm transition-colors">✕</button>
        </div>
      </div>

      {initError && (
        <div className="px-4 py-2 rounded-xl mb-3"
          style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)" }}>
          <p className="text-amber-400 text-xs">⚠️ {initError}</p>
        </div>
      )}

      <div className="flex flex-1 gap-4 overflow-hidden mt-3">

        {/* ── Left panel: camera + current question ───────────────────────── */}
        <div className="w-56 flex-shrink-0 flex flex-col gap-3">
          {/* Camera */}
          <div className="rounded-2xl overflow-hidden relative" style={{ aspectRatio: "4/3", background: "#050508" }}>
            {camOn
              ? <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
              : <div className="w-full h-full flex items-center justify-center text-3xl">👤</div>
            }
            <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between">
              <span className="text-xs text-white/50 bg-black/50 px-1.5 py-0.5 rounded">You</span>
              <AudioWave active={listening} />
            </div>
          </div>

          {/* AI avatar */}
          <div className="rounded-2xl p-3 flex flex-col items-center gap-2"
            style={{ background: "rgba(124,58,237,0.08)", border: "1px solid rgba(124,58,237,0.2)" }}>
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
              style={{ background: "linear-gradient(135deg,#7c3aed20,#2563eb20)" }}>🤖</div>
            <p className="text-white/50 text-xs font-semibold text-center">AI Interviewer</p>
            {loading && (
              <div className="flex gap-1">
                {[0,1,2].map(i => <span key={i} className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce"
                  style={{ animationDelay: `${i*0.12}s` }} />)}
              </div>
            )}
          </div>

          {/* Cam/mic buttons */}
          <div className="flex gap-2">
            <button onClick={toggleMic}
              className={`flex-1 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 border transition-all
                ${micOn ? "border-white/10 text-white/50 hover:border-white/20" : "border-red-500/40 text-red-400 bg-red-500/10"}`}>
              {micOn ? <MicIcon /> : <MicOffIcon />}
            </button>
            <button onClick={toggleCam}
              className={`flex-1 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 border transition-all
                ${camOn ? "border-white/10 text-white/50 hover:border-white/20" : "border-red-500/40 text-red-400 bg-red-500/10"}`}>
              {camOn ? <CamIcon /> : <CamOffIcon />}
            </button>
          </div>
        </div>

        {/* ── Right panel: chat + input ────────────────────────────────────── */}
        <div className="flex-1 flex flex-col overflow-hidden">

          {/* Chat history */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-1">
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
                  {[0,1,2].map(i => <span key={i} className="w-2 h-2 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: `${i*0.12}s` }} />)}
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Live feedback from last answer */}
          {feedback && <div className="mt-2"><LiveFeedback feedback={feedback} compact /></div>}

          {/* Input area */}
          <div className="mt-3 pt-3" style={{ borderTop: "1px solid rgba(255,255,255,0.08)" }}>
            <div className="flex gap-2 items-end">
              <div className="flex-1 relative">
                <textarea
                  value={transcript}
                  onChange={(e) => { setTranscript(e.target.value); fullTransRef.current = e.target.value; }}
                  onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submitAnswer(); } }}
                  placeholder={listening ? "🎙️ Listening… speak your answer" : "Type your answer… (Enter to submit)"}
                  rows={3}
                  disabled={loading}
                  className="w-full px-4 py-3 rounded-2xl text-sm text-white placeholder-white/25 outline-none resize-none transition-colors"
                  style={{
                    background: "rgba(255,255,255,0.05)",
                    border: `1px solid ${listening ? "rgba(16,185,129,0.5)" : "rgba(255,255,255,0.1)"}`,
                  }}
                />
                {listening && (
                  <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2 py-1 rounded-lg"
                    style={{ background: "rgba(16,185,129,0.15)" }}>
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-emerald-400 text-xs">Live</span>
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-2">
                <button onClick={toggleVoice}
                  className={`w-11 h-11 rounded-xl flex items-center justify-center transition-all active:scale-95 border
                    ${listening
                      ? "border-emerald-500/50 text-emerald-400 animate-pulse"
                      : "border-white/10 text-white/40 hover:border-white/20 hover:text-white/70"}`}
                  style={listening ? { background: "rgba(16,185,129,0.15)" } : {}}>
                  <MicIcon />
                </button>
                <button onClick={() => submitAnswer()} disabled={!transcript.trim() || loading}
                  className="w-11 h-11 rounded-xl flex items-center justify-center transition-all disabled:opacity-30 active:scale-95 text-white"
                  style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)", boxShadow: transcript.trim() ? "0 4px 12px rgba(124,58,237,0.35)" : "none" }}>
                  <SendIcon />
                </button>
              </div>
            </div>

            {/* Quick phrases */}
            <div className="flex flex-wrap gap-2 mt-2">
              {["Can you repeat the question?", "Give me a moment to think", "I'm not sure"].map((q) => (
                <button key={q} onClick={() => submitAnswer(q)}
                  className="text-xs px-3 py-1 rounded-full border border-white/10 text-white/40 hover:border-white/20 hover:text-white/70 transition-colors">
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


// ═════════════════════════════════════════════════════════════════════════════
// SETUP SCREEN
// ═════════════════════════════════════════════════════════════════════════════

const SetupScreen = ({ onStart, resumeText }) => {
  const [role, setRole]           = useState("Software Engineer");
  const [type, setType]           = useState("mixed");
  const [difficulty, setDifficulty] = useState("medium");
  const [numQ, setNumQ]           = useState(5);
  const [camPreview, setCamPreview] = useState(false);
  const [camError, setCamError]   = useState(false);
  const previewRef = useRef(null);
  const streamRef  = useRef(null);

  useEffect(() => {
    return () => { streamRef.current?.getTracks().forEach((t) => t.stop()); };
  }, []);

  const testCam = async () => {
    if (camPreview) {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      setCamPreview(false);
      return;
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
            <div className="w-10 h-10 rounded-2xl flex items-center justify-center text-xl"
              style={{ background: "linear-gradient(135deg,#7c3aed,#2563eb)" }}>🎙️</div>
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
            <div className="p-4" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-semibold text-sm">Camera & Microphone</p>
                  <p className="text-white/40 text-xs mt-0.5">Test your setup before starting</p>
                </div>
                <button onClick={testCam}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                    camPreview ? "bg-red-500/15 border-red-500/30 text-red-400 border" : "border border-white/15 text-white/60 hover:border-white/25"}`}>
                  {camPreview ? <><CamOffIcon /> Stop Preview</> : <><CamIcon /> Test Camera</>}
                </button>
              </div>
            </div>
            <div className="aspect-video relative" style={{ background: "#080810" }}>
              {camPreview
                ? <video ref={previewRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
                    <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                      style={{ background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.25)" }}>
                      <span className="text-3xl">🎥</span>
                    </div>
                    <p className="text-white/30 text-sm">Camera preview will appear here</p>
                    {camError && <p className="text-red-400 text-xs">⚠️ Camera access denied — check browser permissions</p>}
                  </div>
                )
              }
              {camPreview && (
                <div className="absolute bottom-3 left-3 flex items-center gap-2 px-2.5 py-1.5 rounded-lg"
                  style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(8px)" }}>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-white text-xs font-medium">Camera active</span>
                </div>
              )}
            </div>
          </div>

          {/* Config card */}
          <div className="rounded-2xl p-5 space-y-5"
            style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.07)" }}>
            {/* Role */}
            <div>
              <label className="block text-xs font-bold mb-2"
                style={{ color: "rgba(255,255,255,0.4)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                Target Role
              </label>
              <input value={role} onChange={(e) => setRole(e.target.value)}
                placeholder="e.g. Software Engineer, Product Manager, Data Scientist"
                className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-white/25 outline-none focus:border-violet-500/60 transition-colors"
                style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)" }} />
            </div>

            {/* Type */}
            <div>
              <label className="block text-xs font-bold mb-2"
                style={{ color: "rgba(255,255,255,0.4)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                Interview Type
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {INTERVIEW_TYPES.map((t) => (
                  <button key={t.value} onClick={() => setType(t.value)}
                    className={`flex flex-col items-center gap-1 py-3 rounded-xl border text-center transition-all ${
                      type === t.value ? "border-violet-500/60 text-white" : "border-white/8 text-white/40 hover:border-white/15 hover:text-white/70"}`}
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
                <label className="block text-xs font-bold mb-2"
                  style={{ color: "rgba(255,255,255,0.4)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                  Difficulty
                </label>
                <div className="flex gap-2">
                  {DIFFICULTY.map((d) => (
                    <button key={d} onClick={() => setDifficulty(d)}
                      className={`flex-1 py-2 rounded-xl text-xs font-semibold border capitalize transition-all ${
                        difficulty === d ? "text-white" : "text-white/40 border-white/8 hover:border-white/15"}`}
                      style={difficulty === d ? { background: `${diffColors[d]}20`, borderColor: `${diffColors[d]}50`, color: diffColors[d] } : {}}>
                      {d}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold mb-2"
                  style={{ color: "rgba(255,255,255,0.4)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                  Questions
                </label>
                <div className="flex gap-2">
                  {[3, 5, 7, 10].map((n) => (
                    <button key={n} onClick={() => setNumQ(n)}
                      className={`flex-1 py-2 rounded-xl text-xs font-semibold border transition-all ${
                        numQ === n ? "bg-violet-600/20 border-violet-500/50 text-violet-300" : "border-white/8 text-white/40 hover:border-white/15"}`}>
                      {n}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* CTA */}
          <button onClick={() => onStart({ role, type, difficulty, numQ, resumeText })}
            className="w-full py-4 rounded-2xl text-base font-black tracking-wide transition-all active:scale-98 hover:scale-[1.01]"
            style={{ background: "linear-gradient(135deg,#7c3aed 0%,#2563eb 100%)", boxShadow: "0 8px 30px rgba(124,58,237,0.4)" }}>
            🚀 Start Live Interview
          </button>
          <p className="text-center text-white/25 text-xs">
            Camera and microphone will activate when the interview begins
          </p>
        </div>
      </div>
    </div>
  );
};


// ═════════════════════════════════════════════════════════════════════════════
// MAIN WRAPPER — InterviewCoach
// ═════════════════════════════════════════════════════════════════════════════

const InterviewCoach = ({ resumeText = "", userId = "default_user" }) => {
  // Setup ↔ live interview phase
  const [phase,  setPhase]  = useState("setup");  // "setup" | "live" | "mentor"
  const [config, setConfig] = useState(null);

  // Mentor room session
  const [mentorRoomId] = useState(
    () => Math.random().toString(36).slice(2, 8).toUpperCase()
  );
  const [showMentor, setShowMentor] = useState(false);

  // ── Render: live AI interview (full-screen modal) ─────────────────────────
  if (phase === "live" && config) {
    return (
      <div className="fixed inset-0 z-50 flex flex-col"
        style={{ background: "#0d0d14", fontFamily: "'DM Sans', sans-serif" }}>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />

        {/* Modal header */}
        <div className="flex items-center justify-between px-5 py-3"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
          <button onClick={() => setPhase("setup")}
            className="w-8 h-8 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/40 hover:text-white/70 transition-all">
            <BackIcon />
          </button>
          <p className="text-white/60 text-sm font-semibold">AI Mock Interview</p>
          {/* Mentor video toggle inside interview */}
          <button onClick={() => setShowMentor((v) => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border border-white/15 text-white/50 hover:border-white/25 hover:text-white/80 transition-all">
            📹 Mentor
          </button>
        </div>

        {/* Interview content */}
        <div className="flex-1 overflow-hidden p-5">
          <AILiveInterviewModal config={config} onClose={() => setPhase("setup")} />
        </div>

        {/* Floating mentor video */}
        {showMentor && (
          <VideoPanel roomId={mentorRoomId} role="candidate" onClose={() => setShowMentor(false)} />
        )}
      </div>
    );
  }

  // ── Render: setup screen ──────────────────────────────────────────────────
  return (
    <div className="relative">
      <SetupScreen
        resumeText={resumeText}
        onStart={(cfg) => { setConfig(cfg); setPhase("live"); }}
      />

      {/* ── Mentor session launch bar ──────────────────────────────────────── */}
      <div
        className="fixed bottom-0 left-0 right-0 z-40 flex items-center justify-between px-6 py-3"
        style={{
          background: "rgba(8,8,18,0.95)",
          backdropFilter: "blur(16px)",
          borderTop: "1px solid rgba(255,255,255,0.07)",
          fontFamily: "'DM Sans', sans-serif",
        }}
      >
        <div className="flex items-center gap-2">
          <span className="text-white/30 text-xs">Want a human mentor?</span>
          <span
            className="text-xs font-bold px-2 py-0.5 rounded-md text-indigo-300"
            style={{ background: "rgba(99,102,241,0.15)" }}
          >
            Room: {mentorRoomId}
          </span>
        </div>
        <button
          onClick={() => setShowMentor((v) => !v)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02]"
          style={{
            background: showMentor
              ? "rgba(220,38,38,0.3)"
              : "linear-gradient(135deg,#4f46e5,#7c3aed)",
            border: showMentor ? "1px solid rgba(220,38,38,0.5)" : "none",
            boxShadow: showMentor ? "none" : "0 4px 14px rgba(99,102,241,0.35)",
          }}
        >
          {showMentor ? "📵 Close Video" : "📹 Start Mentor Session"}
        </button>
      </div>

      {/* Floating mentor video panel */}
      {showMentor && (
        <VideoPanel roomId={mentorRoomId} role="candidate" onClose={() => setShowMentor(false)} />
      )}
    </div>
  );
};

export default InterviewCoach;