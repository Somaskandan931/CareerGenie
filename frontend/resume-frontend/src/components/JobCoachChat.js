import React, { useState, useRef, useEffect } from "react";

const API_BASE_URL = "http://localhost:8000";

const SUGGESTED_QUESTIONS = [
  "How should I negotiate my salary for a senior developer role?",
  "I have 2 years of experience — should I apply for senior positions?",
  "How do I transition from backend to full-stack development?",
  "What should I put in my resume summary section?",
  "How do I explain a 6-month employment gap in an interview?",
  "What's the best way to network when I'm shy?",
];

// ─── Icons ────────────────────────────────────────────────────────────────────
const SendIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);
const BotIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17H3a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-2" />
  </svg>
);
const UserIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);
const TrashIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

// ─── Message bubble ───────────────────────────────────────────────────────────
const Bubble = ({ message }) => {
  const isUser = message.role === "user";
  // Normalise content: backend may return reply/response/content — fall back to empty string
  const content = message.content ?? message.reply ?? message.response ?? "";
  const lines = content.split('\n');
  return (
    <div className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? "bg-indigo-600 text-white" : "bg-gradient-to-br from-orange-500 to-red-500 text-white"
      }`}>
        {isUser ? <UserIcon /> : <BotIcon />}
      </div>
      <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
        isUser
          ? "bg-indigo-600 text-white rounded-tr-sm"
          : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm"
      }`}>
        {lines.map((line, i) => (
          <span key={i}>{line}{i < lines.length - 1 && <br />}</span>
        ))}
      </div>
    </div>
  );
};

// ─── Typing indicator ─────────────────────────────────────────────────────────
const TypingIndicator = () => (
  <div className="flex items-start gap-3">
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-red-500 text-white flex items-center justify-center">
      <BotIcon />
    </div>
    <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
      <div className="flex gap-1 items-center h-5">
        {[0, 1, 2].map(i => (
          <div key={i} className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }} />
        ))}
      </div>
    </div>
  </div>
);

// ─── Main Component ───────────────────────────────────────────────────────────
const JobCoachChat = ({ resumeText = "" }) => {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hi! I'm Genie, your career coach 👋\n\nI can help you with career decisions, resume advice, salary negotiation, job search strategies, and more. What's on your mind?"
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const content = (text || input).trim();
    if (!content || loading) return;

    const userMsg = { role: "user", content };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/coach/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: newMessages.map(m => ({ role: m.role, content: m.content })),
          resume_text: resumeText || null,
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
      const reply = data.reply ?? data.response ?? data.content ?? "";
      setMessages(prev => [...prev, { role: "assistant", content: reply }]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([{
      role: "assistant",
      content: "Chat cleared! How can I help you with your career today?"
    }]);
    setError(null);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden flex flex-col" style={{ height: "680px" }}>
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-500 to-red-600 px-6 py-4 text-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
            <BotIcon />
          </div>
          <div>
            <p className="font-bold text-lg">Genie — Career Coach</p>
            <p className="text-orange-100 text-xs">Your personal career counsellor · Powered by Groq</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {resumeText && (
            <span className="text-xs bg-white/20 px-2 py-1 rounded-full">📄 Resume loaded</span>
          )}
          <button onClick={clearChat} title="Clear chat"
            className="p-2 hover:bg-white/20 rounded-lg transition-colors">
            <TrashIcon />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4 bg-gray-50 dark:bg-gray-900">
        {messages.map((m, i) => <Bubble key={i} message={m} />)}
        {loading && <TypingIndicator />}
        {error && (
          <div className="text-center">
            <span className="text-xs text-red-600 bg-red-50 border border-red-200 px-3 py-1 rounded-full">
              {error} — try again
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggested questions — shown when only the greeting exists */}
      {messages.length === 1 && (
        <div className="px-5 pb-3 bg-gray-50 dark:bg-gray-900 border-t border-gray-100 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">Suggested questions:</p>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTED_QUESTIONS.slice(0, 3).map((q, i) => (
              <button key={i} onClick={() => sendMessage(q)}
                className="text-xs bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 hover:border-orange-300 hover:text-orange-700 dark:text-gray-300 dark:hover:text-orange-400 text-gray-600 px-3 py-1.5 rounded-full transition-colors">
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="px-5 py-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-3 items-end">
          <textarea
            ref={inputRef}
            rows={2}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything about your career… (Enter to send, Shift+Enter for new line)"
            className="flex-1 resize-none px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-orange-400 focus:border-transparent outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
            disabled={loading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="flex-shrink-0 w-11 h-11 bg-gradient-to-r from-orange-500 to-red-600 text-white rounded-xl flex items-center justify-center hover:from-orange-600 hover:to-red-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md"
          >
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
};

export default JobCoachChat;