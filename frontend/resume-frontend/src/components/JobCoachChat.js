import React, { useState, useRef, useEffect } from "react";
import API_BASE_URL from '../config';

const SUGGESTED = [
  "How do I negotiate salary for a senior role?",
  "Should I apply for senior roles with 2 years experience?",
  "How do I transition from backend to full-stack?",
  "How do I explain a 6-month gap in interviews?",
  "What's the best way to network when I'm introverted?",
  "How do I write a strong resume summary?",
];

const Ico = ({ d, className = "w-4 h-4" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const I = {
  send:  "M12 19l9 2-9-18-9 18 9-2zm0 0v-8",
  bot:   "M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17H3a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-2",
  user:  "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
  trash: "M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16",
  spark: "M13 10V3L4 14h7v7l9-11h-7z",
};

const Bubble = ({ msg }) => {
  const isUser = msg.role === "user";
  const content = msg.content ?? msg.reply ?? msg.response ?? "";
  return (
    <div className={`flex items-end gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center ${
        isUser
          ? "bg-violet-600"
          : "bg-gradient-to-br from-amber-500 to-orange-600"
      }`}>
        <Ico d={isUser ? I.user : I.bot} className="w-3.5 h-3.5 text-white" />
      </div>
      <div className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
        isUser
          ? "bg-violet-600 text-white rounded-br-sm"
          : "text-slate-200 rounded-bl-sm border border-white/8"
      }`} style={!isUser ? { background: "rgba(255,255,255,0.06)" } : {}}>
        {content.split("\n").map((line, i, arr) => (
          <span key={i}>{line}{i < arr.length - 1 && <br />}</span>
        ))}
      </div>
    </div>
  );
};

const TypingDots = () => (
  <div className="flex items-end gap-2.5">
    <div className="w-7 h-7 rounded-full flex-shrink-0 bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
      <Ico d={I.bot} className="w-3.5 h-3.5 text-white" />
    </div>
    <div className="flex gap-1 px-4 py-3 rounded-2xl rounded-bl-sm border border-white/8"
      style={{ background: "rgba(255,255,255,0.06)" }}>
      {[0,1,2].map(i => (
        <span key={i} className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce"
          style={{ animationDelay: `${i * 0.12}s` }} />
      ))}
    </div>
  </div>
);

export default function JobCoachChat({ resumeText = "", userId }) {
  const [messages, setMessages] = useState([{
    role: "assistant",
    content: "Hi! I'm Genie, your career coach 👋\n\nI can help with career decisions, resume advice, salary negotiation, job search strategies, and more. What's on your mind?",
  }]);
  const [input, setInput]   = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState(null);
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const send = async (text) => {
    const content = (text || input).trim();
    if (!content || loading) return;
    const newMsgs = [...messages, { role: "user", content }];
    setMessages(newMsgs);
    setInput(""); setLoading(true); setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/coach/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: newMsgs.map(m => ({ role: m.role, content: m.content })),
          resume_text: resumeText || null,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
      setMessages(prev => [...prev, { role: "assistant", content: data.reply ?? data.response ?? data.content ?? "" }]);
    } catch (e) {
      let msg = e.message || "Something went wrong.";
      if (msg.includes("No LLM providers") || msg.includes("LLM") || msg.includes("500")) {
        msg = "AI service temporarily unavailable. Please check that your API keys (GROQ_API_KEY or ANTHROPIC_API_KEY) are set in Render environment variables, then redeploy.";
      }
      setError(msg);
    }
    finally { setLoading(false); inputRef.current?.focus(); }
  };

  const clear = () => {
    setMessages([{ role: "assistant", content: "Chat cleared! How can I help with your career today?" }]);
    setError(null);
  };

  return (
    <div className="rounded-2xl border border-white/10 overflow-hidden flex flex-col"
      style={{ background: "rgba(255,255,255,0.03)", height: "640px" }}>

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/8"
        style={{ background: "rgba(255,255,255,0.04)" }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: "linear-gradient(135deg,#f59e0b,#ea580c)" }}>
            <Ico d={I.spark} className="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">Genie — Career Coach</p>
            <p className="text-xs text-slate-500">Your personal AI counsellor</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {resumeText && (
            <span className="text-xs bg-emerald-500/15 border border-emerald-500/20 text-emerald-400 px-2.5 py-1 rounded-full">
              📄 Resume loaded
            </span>
          )}
          <button onClick={clear} title="Clear chat"
            className="w-8 h-8 rounded-xl border border-white/10 flex items-center justify-center text-slate-500 hover:text-slate-300 hover:border-white/20 transition-all">
            <Ico d={I.trash} className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4">
        {messages.map((m, i) => <Bubble key={i} msg={m} />)}
        {loading && <TypingDots />}
        {error && (
          <div className="text-center">
            <span className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 px-3 py-1 rounded-full">
              {error} — try again
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggested (only first message) */}
      {messages.length === 1 && (
        <div className="px-5 pb-3 border-t border-white/5">
          <p className="text-xs text-slate-600 mb-2 mt-3 font-medium uppercase tracking-widest">Quick questions</p>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTED.slice(0, 3).map((q, i) => (
              <button key={i} onClick={() => send(q)}
                className="text-xs border border-white/10 text-slate-400 hover:border-amber-500/30 hover:text-amber-300 px-3 py-1.5 rounded-full transition-all">
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="px-5 py-4 border-t border-white/8">
        <div className="flex gap-2.5 items-end">
          <textarea
            ref={inputRef} rows={2} value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder="Ask me anything about your career… (Enter to send)"
            disabled={loading}
            className="flex-1 resize-none px-4 py-3 rounded-xl text-sm text-white placeholder-slate-600 outline-none transition-all"
            style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)" }}
          />
          <button onClick={() => send()} disabled={loading || !input.trim()}
            className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-white disabled:opacity-30 transition-all"
            style={{ background: "linear-gradient(135deg,#f59e0b,#ea580c)" }}>
            <Ico d={I.send} className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}