import { useState, useRef, useEffect, useCallback } from "react";

const ICE_SERVERS = {
  iceServers: [
    { urls: "stun:stun.l.google.com:19302" },
    { urls: "stun:stun1.l.google.com:19302" },
  ],
};

const WS_BASE =
  process.env.REACT_APP_WS_URL ||
  (window.location.protocol === "https:" ? "wss://" : "ws://") +
    (process.env.REACT_APP_API_HOST || "localhost:8000");

// ─── Icon helpers ──────────────────────────────────────────────────────────────
const Ico = ({ d, size = 5, cls = "" }) => (
  <svg
    className={`w-${size} h-${size} ${cls}`}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    strokeWidth={1.8}
  >
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);
const MicIcon = () => (
  <Ico d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
);
const MicOffIcon = () => (
  <Ico d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3zM3 3l18 18" />
);
const CamIcon = () => (
  <Ico d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
);
const CamOffIcon = () => (
  <Ico d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8zM3 3l18 18" />
);

/**
 * Floating Google-Meet-style WebRTC video panel.
 *
 * Props:
 *   roomId   — shared room identifier (6-char string shown to peer)
 *   role     — "mentor" | "candidate"
 *   onClose  — called when panel is dismissed
 */
export default function VideoPanel({ roomId, role = "candidate", onClose }) {
  const [status, setStatus] = useState("idle"); // idle | connecting | connected | error
  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);
  const [remoteLabel, setRemoteLabel] = useState("Waiting for peer…");

  const localRef = useRef(null);
  const remoteRef = useRef(null);
  const pcRef = useRef(null);
  const wsRef = useRef(null);
  const localStream = useRef(null);

  // ── Send a message over the signaling socket ─────────────────────────────
  const send = useCallback((msg) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }, []);

  // ── Full teardown ────────────────────────────────────────────────────────
  const cleanup = useCallback(() => {
    localStream.current?.getTracks().forEach((t) => t.stop());
    pcRef.current?.close();
    wsRef.current?.close();
    localStream.current = null;
    pcRef.current = null;
    wsRef.current = null;
  }, []);

  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  // ── Start: getUserMedia → RTCPeerConnection → WebSocket ─────────────────
  const startSession = useCallback(async () => {
    setStatus("connecting");
    try {
      // 1. Acquire local media
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: true,
      });
      localStream.current = stream;
      if (localRef.current) localRef.current.srcObject = stream;

      // 2. Create peer connection
      const pc = new RTCPeerConnection(ICE_SERVERS);
      pcRef.current = pc;
      stream.getTracks().forEach((t) => pc.addTrack(t, stream));

      // Remote track → remoteRef
      pc.ontrack = (e) => {
        if (remoteRef.current) {
          remoteRef.current.srcObject = e.streams[0];
          setRemoteLabel(role === "mentor" ? "Candidate" : "Mentor");
        }
      };

      // Connection state monitoring
      pc.onconnectionstatechange = () => {
        const s = pc.connectionState;
        if (s === "connected") setStatus("connected");
        if (s === "failed" || s === "disconnected") setStatus("error");
      };

      // 3. Open signaling WebSocket
      const ws = new WebSocket(`${WS_BASE}/ws/room/${roomId}/${role}`);
      wsRef.current = ws;

      ws.onopen = () => setStatus("connecting");

      ws.onmessage = async ({ data }) => {
        let msg;
        try {
          msg = JSON.parse(data);
        } catch {
          return;
        }

        if (msg.type === "peer_joined") {
          setRemoteLabel(role === "mentor" ? "Candidate" : "Mentor");
          // Mentor initiates the offer
          if (role === "mentor") {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            send({ type: "offer", payload: offer });
          }
        }

        if (msg.type === "offer") {
          await pc.setRemoteDescription(new RTCSessionDescription(msg.payload));
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          send({ type: "answer", payload: answer });
        }

        if (msg.type === "answer") {
          await pc.setRemoteDescription(new RTCSessionDescription(msg.payload));
        }

        if (msg.type === "ice") {
          await pc.addIceCandidate(new RTCIceCandidate(msg.payload)).catch(() => {});
        }

        if (msg.type === "peer_left") {
          setStatus("idle");
          setRemoteLabel("Peer disconnected");
          if (remoteRef.current) remoteRef.current.srcObject = null;
        }
      };

      ws.onerror = () => setStatus("error");

      // Forward ICE candidates to peer
      pc.onicecandidate = ({ candidate }) => {
        if (candidate) send({ type: "ice", payload: candidate });
      };
    } catch (err) {
      console.error("[VideoPanel] startSession error:", err);
      setStatus("error");
    }
  }, [roomId, role, send]);

  // ── Controls ─────────────────────────────────────────────────────────────
  const toggleMic = () => {
    localStream.current?.getAudioTracks().forEach((t) => (t.enabled = !micOn));
    setMicOn((v) => !v);
  };

  const toggleCam = () => {
    localStream.current?.getVideoTracks().forEach((t) => (t.enabled = !camOn));
    setCamOn((v) => !v);
  };

  const endCall = () => {
    cleanup();
    setStatus("idle");
  };

  // ── Status indicator ─────────────────────────────────────────────────────
  const dotColor = {
    idle: "bg-gray-500",
    connecting: "bg-yellow-400 animate-pulse",
    connected: "bg-emerald-400",
    error: "bg-red-500",
  }[status];

  const statusLabel = {
    idle: "Ready",
    connecting: "Connecting…",
    connected: "Live",
    error: "Connection Error",
  }[status];

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div
      className="fixed bottom-6 right-6 z-50 w-80 rounded-2xl overflow-hidden shadow-2xl select-none"
      style={{
        background: "rgba(8,8,18,0.96)",
        border: "1px solid rgba(255,255,255,0.1)",
        backdropFilter: "blur(24px)",
        fontFamily: "'DM Sans', sans-serif",
      }}
    >
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&display=swap"
        rel="stylesheet"
      />

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div
        className="flex items-center justify-between px-4 py-2.5"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}
      >
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColor}`} />
          <span className="text-xs text-white/60 font-medium">
            {statusLabel} · Room{" "}
            <span className="text-white/90 font-bold tracking-wider">{roomId}</span>
          </span>
        </div>
        <button
          onClick={() => {
            cleanup();
            onClose?.();
          }}
          className="w-6 h-6 rounded-full flex items-center justify-center text-white/30 hover:text-white hover:bg-white/10 transition-all text-sm"
        >
          ✕
        </button>
      </div>

      {/* ── Remote video ────────────────────────────────────────────────── */}
      <div className="relative bg-black" style={{ aspectRatio: "16/9" }}>
        <video
          ref={remoteRef}
          autoPlay
          playsInline
          className="w-full h-full object-cover"
        />

        {status !== "connected" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl"
              style={{
                background: "rgba(124,58,237,0.15)",
                border: "1px solid rgba(124,58,237,0.25)",
              }}
            >
              📹
            </div>
            <p className="text-white/30 text-xs">{remoteLabel}</p>
          </div>
        )}

        {status === "connected" && (
          <div
            className="absolute top-2 left-2 px-2 py-0.5 rounded-md text-xs font-semibold text-emerald-300"
            style={{ background: "rgba(0,0,0,0.5)" }}
          >
            {remoteLabel}
          </div>
        )}

        {/* ── Local PiP ─────────────────────────────────────────────────── */}
        <div
          className="absolute bottom-2 right-2 rounded-xl overflow-hidden"
          style={{
            width: 80,
            height: 56,
            border: "1px solid rgba(255,255,255,0.2)",
            background: "#0a0a14",
          }}
        >
          {camOn ? (
            <video
              ref={localRef}
              autoPlay
              muted
              playsInline
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-lg">
              👤
            </div>
          )}
        </div>
      </div>

      {/* ── Controls ────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-center gap-3 py-3 px-4">
        {status === "idle" ? (
          <button
            onClick={startSession}
            className="w-full py-2.5 rounded-xl text-sm font-bold text-white transition-all hover:scale-[1.02] active:scale-95"
            style={{
              background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
              boxShadow: "0 6px 20px rgba(99,102,241,0.35)",
            }}
          >
            📹 Join Session
          </button>
        ) : (
          <>
            <CtrlBtn
              active={micOn}
              onClick={toggleMic}
              title={micOn ? "Mute mic" : "Unmute mic"}
            >
              {micOn ? <MicIcon /> : <MicOffIcon />}
            </CtrlBtn>

            <CtrlBtn
              active={camOn}
              onClick={toggleCam}
              title={camOn ? "Turn off camera" : "Turn on camera"}
            >
              {camOn ? <CamIcon /> : <CamOffIcon />}
            </CtrlBtn>

            <button
              onClick={endCall}
              title="End call"
              className="w-10 h-10 rounded-full flex items-center justify-center text-white text-lg transition-all hover:scale-105 active:scale-95"
              style={{ background: "#dc2626", boxShadow: "0 4px 12px rgba(220,38,38,0.4)" }}
            >
              📵
            </button>
          </>
        )}
      </div>

      {/* ── Room ID hint (for sharing) ───────────────────────────────────── */}
      {status === "idle" && (
        <p className="text-center text-white/20 text-xs pb-3">
          Share room ID{" "}
          <span className="text-white/50 font-bold">{roomId}</span> with your mentor
        </p>
      )}
    </div>
  );
}

// ── Small control button ───────────────────────────────────────────────────────
function CtrlBtn({ active, onClick, title, children }) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`w-10 h-10 rounded-full flex items-center justify-center transition-all hover:scale-105 active:scale-95 ${
        active
          ? "text-white/70 hover:text-white"
          : "text-red-400"
      }`}
      style={{
        background: active ? "rgba(255,255,255,0.1)" : "rgba(220,38,38,0.2)",
        border: `1px solid ${active ? "rgba(255,255,255,0.15)" : "rgba(220,38,38,0.4)"}`,
      }}
    >
      {children}
    </button>
  );
}