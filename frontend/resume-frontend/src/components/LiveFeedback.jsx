import { useState, useEffect } from "react";

/**
 * LiveFeedback
 * ─────────────
 * Animated feedback card shown in real-time after each interview answer.
 *
 * Props:
 *   feedback — { score: 1-10, strengths: [], improvements: [], sample_better_answer: "" }
 *   compact  — boolean: show collapsed by default (default false)
 */
export default function LiveFeedback({ feedback, compact = false }) {
  const [open, setOpen] = useState(!compact);

  // Re-open whenever new feedback arrives
  useEffect(() => {
    if (feedback) setOpen(true);
  }, [feedback]);

  if (!feedback) return null;

  const {
    score = 5,
    strengths = [],
    improvements = [],
    sample_better_answer = "",
  } = feedback;

  const color =
    score >= 8 ? "#10b981" : score >= 5 ? "#f59e0b" : "#ef4444";
  const label =
    score >= 8 ? "Excellent" : score >= 6 ? "Good" : score >= 4 ? "Fair" : "Needs Work";

  const r = 28;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - score / 10);

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: "rgba(99,102,241,0.07)",
        border: "1px solid rgba(99,102,241,0.2)",
        fontFamily: "'DM Sans', sans-serif",
        animation: "feedbackSlide 0.3s ease",
      }}
    >
      <style>{`
        @keyframes feedbackSlide {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* ── Header (toggle) ───────────────────────────────────────────────── */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 transition-colors hover:bg-white/[0.02]"
      >
        <div className="flex items-center gap-2">
          <span className="text-indigo-300 text-sm font-semibold">📊 Live AI Feedback</span>
          {!open && (
            <span
              className="text-xs font-bold px-2 py-0.5 rounded-full"
              style={{ background: `${color}25`, color }}
            >
              {score}/10
            </span>
          )}
        </div>
        <span className="text-white/30 text-xs">{open ? "▲ hide" : "▼ show"}</span>
      </button>

      {/* ── Body ──────────────────────────────────────────────────────────── */}
      {open && (
        <div className="px-4 pb-4 space-y-3">

          {/* Score row */}
          <div className="flex items-center gap-4 py-1">
            {/* Ring */}
            <svg width={72} height={72} style={{ transform: "rotate(-90deg)", flexShrink: 0 }}>
              <circle
                cx={36} cy={36} r={r}
                fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={6}
              />
              <circle
                cx={36} cy={36} r={r}
                fill="none" stroke={color} strokeWidth={6}
                strokeDasharray={circ}
                strokeDashoffset={offset}
                strokeLinecap="round"
                style={{ transition: "stroke-dashoffset 0.8s ease" }}
              />
            </svg>

            {/* Score text — centred inside ring via negative margin trick */}
            <div style={{ marginLeft: -72 - 16, width: 72, textAlign: "center" }}>
              <span className="text-2xl font-black" style={{ color }}>
                {score}
              </span>
              <span className="text-white/30 text-sm">/10</span>
            </div>

            {/* Label */}
            <div style={{ marginLeft: 8 }}>
              <p className="text-white/90 text-sm font-bold">{label}</p>
              <p className="text-white/40 text-xs mt-0.5">AI evaluation score</p>
            </div>
          </div>

          {/* Strengths */}
          {strengths.length > 0 && (
            <div
              className="p-3 rounded-xl"
              style={{
                background: "rgba(16,185,129,0.08)",
                border: "1px solid rgba(16,185,129,0.18)",
              }}
            >
              <p className="text-emerald-400 text-xs font-bold mb-1.5 uppercase tracking-wider">
                ✅ Strengths
              </p>
              {strengths.map((s, i) => (
                <p key={i} className="text-emerald-300 text-xs leading-relaxed">
                  • {s}
                </p>
              ))}
            </div>
          )}

          {/* Improvements */}
          {improvements.length > 0 && (
            <div
              className="p-3 rounded-xl"
              style={{
                background: "rgba(245,158,11,0.08)",
                border: "1px solid rgba(245,158,11,0.18)",
              }}
            >
              <p className="text-amber-400 text-xs font-bold mb-1.5 uppercase tracking-wider">
                💡 Improve
              </p>
              {improvements.map((s, i) => (
                <p key={i} className="text-amber-300 text-xs leading-relaxed">
                  • {s}
                </p>
              ))}
            </div>
          )}

          {/* Model answer */}
          {sample_better_answer && (
            <div
              className="p-3 rounded-xl"
              style={{
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.07)",
              }}
            >
              <p className="text-white/40 text-xs font-bold mb-1.5 uppercase tracking-wider">
                ⭐ Model Answer
              </p>
              <p className="text-white/65 text-xs leading-relaxed">
                {sample_better_answer}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}