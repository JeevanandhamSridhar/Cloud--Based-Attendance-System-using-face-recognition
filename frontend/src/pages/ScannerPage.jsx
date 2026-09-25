import React, { useEffect, useRef, useState } from "react";
import {
  Camera,
  CameraOff,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  ShieldAlert,
  Play,
  Square,
  Activity,
  Layers,
  Sparkles,
  FlipHorizontal,
} from "lucide-react";
import {
  fetchActiveSession,
  fetchSessions,
  scanFrame,
  startSession,
  endSession,
  fetchSessionAttendance,
} from "../services/api";

export default function ScannerPage() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const captureCanvasRef = useRef(null);
  const scanIntervalRef = useRef(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [activeSession, setActiveSession] = useState(null);
  const [availableSessions, setAvailableSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [scanInterval, setScanInterval] = useState(2000); // 2 seconds
  const [isScanning, setIsScanning] = useState(true);

  const [lastScanResult, setLastScanResult] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [statusMessage, setStatusMessage] = useState("Camera ready. Starting feed...");
  const [fps, setFps] = useState(0);

  // 1. Load active class sessions & load existing attendance from DB
  const loadSessions = async () => {
    try {
      const [active, all] = await Promise.all([
        fetchActiveSession().catch(() => null),
        fetchSessions().catch(() => []),
      ]);
      setActiveSession(active);
      setAvailableSessions(all);
      if (active) {
        setSelectedSessionId(active.id);
        loadExistingAttendance(active.id);
      } else if (all.length > 0) {
        setSelectedSessionId(all[0].id);
        loadExistingAttendance(all[0].id);
      }
    } catch (err) {
      console.error("Error loading sessions:", err);
    }
  };

  const loadExistingAttendance = async (sessId) => {
    if (!sessId) return;
    try {
      const records = await fetchSessionAttendance(sessId);
      if (records && records.length > 0) {
        setRecentEvents(
          records.map((r) => ({
            id: r.id,
            name: r.student_name,
            code: r.student_code,
            confidence: r.confidence_avg || 85.0,
            status: r.status,
            time: r.last_seen
              ? new Date(r.last_seen).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
              : "Logged",
            presence_score: r.presence_score,
          }))
        );
      } else {
        setRecentEvents([]);
      }
    } catch (err) {
      console.error("Error loading session attendance:", err);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleStartCurrentSession = async () => {
    if (!selectedSessionId) return;
    try {
      await startSession(selectedSessionId);
      const all = await fetchSessions();
      setAvailableSessions(all);
      const active = all.find((s) => s.id === selectedSessionId) || all.find((s) => s.status === "active");
      setActiveSession(active);
      await loadExistingAttendance(selectedSessionId);
      setStatusMessage("Lecture session is now ACTIVE! Pre-arrival scans grandfathered into Interval 0.");
    } catch (err) {
      alert("Failed to start session: " + err.message);
    }
  };

  const handleEndCurrentSession = async () => {
    if (!selectedSessionId) return;
    try {
      await endSession(selectedSessionId);
      const all = await fetchSessions();
      setAvailableSessions(all);
      setActiveSession(null);
      await loadExistingAttendance(selectedSessionId);
      setStatusMessage("Lecture session COMPLETED. Attendance scores finalized.");
    } catch (err) {
      alert("Failed to end session: " + err.message);
    }
  };

  // 2. Start Webcam Feed
  const startCamera = async () => {
    try {
      setStatusMessage("Requesting webcam access...");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        const playVideo = () => {
          videoRef.current?.play().catch((err) => {
            if (err.name !== "AbortError") {
              console.warn("Scanner video playback error:", err);
            }
          });
        };
        if (videoRef.current.readyState >= 1) {
          playVideo();
        } else {
          videoRef.current.onloadedmetadata = playVideo;
        }
        setIsStreaming(true);
        setStatusMessage("Webcam stream active. Real-time scanner engaged.");
      }
    } catch (err) {
      console.error("Webcam error:", err);
      setStatusMessage(`Camera access error: ${err.message}. Please allow camera permissions.`);
      setIsStreaming(false);
    }
  };

  const stopCamera = () => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.pause();
      if (videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach((t) => t.stop());
        videoRef.current.srcObject = null;
      }
    }
    setIsStreaming(false);
    setStatusMessage("Camera paused.");
  };

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  // 3. Continuous Scan Frame Loop
  useEffect(() => {
    if (!isStreaming || !isScanning || !selectedSessionId) return;

    let isProcessing = false;
    let lastTime = performance.now();

    const intervalId = setInterval(async () => {
      if (isProcessing) return;
      if (!videoRef.current || !videoRef.current.videoWidth) return;

      isProcessing = true;
      try {
        const now = performance.now();
        setFps(Math.round(1000 / Math.max(1, now - lastTime)));
        lastTime = now;

        // Capture frame onto offscreen canvas
        const video = videoRef.current;
        const capCanvas = captureCanvasRef.current;
        capCanvas.width = video.videoWidth;
        capCanvas.height = video.videoHeight;
        const ctx = capCanvas.getContext("2d");
        ctx.drawImage(video, 0, 0, capCanvas.width, capCanvas.height);

        const base64Data = capCanvas.toDataURL("image/jpeg", 0.85);

        // Transmit frame to FastAPI server
        const res = await scanFrame({
          session_id: selectedSessionId,
          image_base64: base64Data,
          client_is_live: true,
          ear_value: 0.28,
        });

        setLastScanResult(res);

        // Draw bounding boxes on display overlay canvas
        drawBoundingBoxes(res.matches, video.videoWidth, video.videoHeight);

        // Update or insert into cumulative live attendance list
        if (res.matches && res.matches.length > 0) {
          const validMatches = res.matches.filter((m) => m.student_name);
          if (validMatches.length > 0) {
            setRecentEvents((prev) => {
              const updated = [...prev];
              validMatches.forEach((vm) => {
                const existingIdx = updated.findIndex((u) => u.code === vm.student_code);
                if (existingIdx >= 0) {
                  updated[existingIdx] = {
                    ...updated[existingIdx],
                    confidence: vm.confidence,
                    status: vm.status,
                    is_occluded: vm.is_occluded,
                    visibility_score: vm.visibility_score,
                    time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
                  };
                } else {
                  updated.unshift({
                    id: vm.student_id || Math.random().toString(),
                    name: vm.student_name,
                    code: vm.student_code,
                    confidence: vm.confidence,
                    status: vm.status,
                    is_occluded: vm.is_occluded,
                    visibility_score: vm.visibility_score,
                    time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
                    presence_score: 100.0,
                  });
                }
              });
              return updated;
            });
          }
        }
      } catch (err) {
        console.error("Frame scan failed:", err);
      } finally {
        isProcessing = false;
      }
    }, scanInterval);

    scanIntervalRef.current = intervalId;

    return () => {
      clearInterval(intervalId);
      scanIntervalRef.current = null;
    };
  }, [isStreaming, isScanning, selectedSessionId, scanInterval]);

  // State for camera mirroring: true for natural selfie mirror view
  const [isMirrored, setIsMirrored] = useState(true);

  // 4. Draw bounding boxes on overlay canvas
  const drawBoundingBoxes = (matches, srcW, srcH) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!matches || matches.length === 0) return;

    const scaleX = canvas.width / srcW;
    const scaleY = canvas.height / srcH;

    matches.forEach((m) => {
      if (!m.bbox || m.bbox.length !== 4) return;
      const [x1, y1, x2, y2] = m.bbox;

      const rw = (x2 - x1) * scaleX;
      const rh = (y2 - y1) * scaleY;
      // If mirrored (selfie mode), flip the X box coordinate horizontally on the canvas
      const rx = isMirrored ? canvas.width - (x2 * scaleX) : x1 * scaleX;
      const ry = y1 * scaleY;

      let strokeColor = "#94a3b8"; // Gray for unknown
      let label = "Unknown Face";
      let badgeBg = "rgba(51, 65, 85, 0.85)";

      if (m.status === "present") {
        strokeColor = "#10b981"; // Bright Green
        label = `${m.student_name} (${m.confidence}%) - LIVE`;
        badgeBg = "rgba(16, 185, 129, 0.9)";
      } else if (m.status === "present_occluded") {
        strokeColor = "#06b6d4"; // Electric Cyan
        const visPct = Math.round((m.visibility_score || 0.6) * 100);
        label = `${m.student_name} (${m.confidence}%) - KERCHIEF/MASK (${visPct}% Vis)`;
        badgeBg = "rgba(6, 182, 212, 0.92)";
      } else if (m.status === "flagged") {
        strokeColor = "#f59e0b"; // Yellow/Amber
        label = `${m.student_name} (${m.confidence}%) - REVIEW`;
        badgeBg = "rgba(245, 158, 11, 0.9)";
      } else if (m.status === "spoof_rejected") {
        strokeColor = "#ef4444"; // Crimson Red
        label = `SPOOF DETECTED: ${m.student_name || "REJECTED"}`;
        badgeBg = "rgba(239, 68, 68, 0.9)";
      } else if (m.is_occluded) {
        strokeColor = "#64748b";
        label = `Face Occluded (Kerchief / Mask) - Unknown`;
        badgeBg = "rgba(71, 85, 105, 0.85)";
      }

      // Draw rounded rectangle
      ctx.lineWidth = 3;
      ctx.strokeStyle = strokeColor;
      ctx.beginPath();
      ctx.roundRect(rx, ry, rw, rh, 10);
      ctx.stroke();

      // Corner target brackets
      const bracketLen = 14;
      ctx.lineWidth = 4;
      ctx.beginPath();
      // Top-left
      ctx.moveTo(rx, ry + bracketLen);
      ctx.lineTo(rx, ry);
      ctx.lineTo(rx + bracketLen, ry);
      // Top-right
      ctx.moveTo(rx + rw - bracketLen, ry);
      ctx.lineTo(rx + rw, ry);
      ctx.lineTo(rx + rw, ry + bracketLen);
      // Bottom-left
      ctx.moveTo(rx, ry + rh - bracketLen);
      ctx.lineTo(rx, ry + rh);
      ctx.lineTo(rx + bracketLen, ry + rh);
      // Bottom-right
      ctx.moveTo(rx + rw - bracketLen, ry + rh);
      ctx.lineTo(rx + rw, ry + rh);
      ctx.lineTo(rx + rw, ry + rh - bracketLen);
      ctx.stroke();

      // Draw Badge Label (Always upright and readable from left-to-right)
      ctx.font = "bold 13px Inter, sans-serif";
      const textWidth = ctx.measureText(label).width;
      ctx.fillStyle = badgeBg;
      ctx.beginPath();
      ctx.roundRect(rx, Math.max(0, ry - 26), textWidth + 16, 22, 6);
      ctx.fill();

      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, rx + 8, Math.max(16, ry - 10));
    });
  };

  return (
    <div className="space-y-6">
      {/* Hidden offscreen canvas for capturing raw camera frames */}
      <canvas ref={captureCanvasRef} className="hidden" />

      {/* Header & Session Control Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-4 rounded-2xl glass-panel">
        <div>
          <div className="flex items-center space-x-2">
            <span className="flex h-2.5 w-2.5 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <h1 className="text-xl font-bold text-white tracking-tight">
              Classroom Live Facial Recognition Scanner
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time SCRFD Multi-Face Detection + ArcFace 512-D Embeddings + Anti-Spoofing
          </p>
        </div>

        {/* Session Selector & Scanner Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2">
            <label className="text-xs font-semibold text-slate-300">Target Scanner:</label>
            <select
              value={selectedSessionId}
              onChange={(e) => {
                setSelectedSessionId(e.target.value);
                if (e.target.value !== "campus_gate") {
                  loadExistingAttendance(e.target.value);
                } else {
                  setRecentEvents([]);
                }
              }}
              className="bg-slate-900 border border-slate-700 text-white text-xs rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="campus_gate">🏛️ Main Campus Gate (Daily College Check-in)</option>
              {availableSessions.map((s) => (
                <option key={s.id} value={s.id}>
                  📚 {s.subject_code} - {s.subject_name} ({s.room}) [{s.status.toUpperCase()}]
                </option>
              ))}
            </select>
          </div>

          {/* Quick Lecture Start / End Button */}
          {(() => {
            const current = availableSessions.find((s) => s.id === selectedSessionId);
            if (current?.status === "scheduled") {
              return (
                <button
                  onClick={handleStartCurrentSession}
                  className="flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/30 transition"
                  title="Activate Lecture Session"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Start Lecture</span>
                </button>
              );
            }
            if (current?.status === "active") {
              return (
                <button
                  onClick={handleEndCurrentSession}
                  className="flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30 text-xs font-semibold transition"
                  title="End Lecture Session"
                >
                  <Square className="w-3 h-3 fill-current" />
                  <span>End Lecture</span>
                </button>
              );
            }
            return null;
          })()}

          <div className="flex items-center space-x-2">
            {isStreaming ? (
              <button
                onClick={stopCamera}
                className="flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
              >
                <CameraOff className="w-3.5 h-3.5 text-rose-400" />
                <span>Pause</span>
              </button>
            ) : (
              <button
                onClick={startCamera}
                className="flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/30 transition"
              >
                <Camera className="w-3.5 h-3.5" />
                <span>Start Camera</span>
              </button>
            )}

            <button
              onClick={() => setIsScanning(!isScanning)}
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition ${
                isScanning
                  ? "bg-indigo-600 hover:bg-indigo-500 text-white"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
              }`}
            >
              {isScanning ? <Square className="w-3 h-3 fill-current" /> : <Play className="w-3 h-3 fill-current" />}
              <span>{isScanning ? "Scanning Active" : "Resume Scan"}</span>
            </button>

            {/* Mirror / Flip Camera Toggle */}
            <button
              onClick={() => setIsMirrored(!isMirrored)}
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold border transition ${
                isMirrored
                  ? "bg-indigo-600/30 text-indigo-300 border-indigo-500/50"
                  : "bg-slate-800 text-slate-300 border-slate-700 hover:text-white"
              }`}
              title="Toggle Normal vs Mirror Selfie View"
            >
              <FlipHorizontal className="w-3.5 h-3.5" />
              <span>{isMirrored ? "Mirrored" : "Normal"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Scanner Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Live Camera Feed & Viewfinder */}
        <div className="lg:col-span-2 space-y-3">
          {/* Lecture Lifecycle Notice Banner */}
          {(() => {
            if (selectedSessionId === "campus_gate") {
              return (
                <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-between text-xs text-indigo-300">
                  <div className="flex items-center space-x-2">
                    <span className="h-2 w-2 rounded-full bg-indigo-400 animate-ping"></span>
                    <span>
                      <strong>Main Campus Gate Mode Active:</strong> Scanning students entering the college. Automatically records daily campus presence and entry timestamps.
                    </span>
                  </div>
                  <span className="px-2.5 py-1 rounded-md bg-indigo-500/20 text-indigo-300 font-mono text-[10px] font-bold border border-indigo-500/30 shrink-0 ml-3">
                    CAMPUS GATE
                  </span>
                </div>
              );
            }
            const current = availableSessions.find((s) => s.id === selectedSessionId);
            if (current?.status === "scheduled") {
              return (
                <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between text-xs text-amber-300">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                    <span>
                      <strong>Pre-Lecture Check-in Active:</strong> Camera can be started now! Students arriving early before lecture starts will be preserved and automatically counted when you click <strong>Start Lecture</strong>.
                    </span>
                  </div>
                  <button
                    onClick={handleStartCurrentSession}
                    className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition shrink-0 ml-3 shadow-md shadow-emerald-600/20"
                  >
                    Start Lecture Now
                  </button>
                </div>
              );
            }
            if (current?.status === "active") {
              return (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between text-xs text-emerald-300">
                  <div className="flex items-center space-x-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping"></span>
                    <span>
                      <strong>Lecture In Progress:</strong> Logging continuous checkpoints every {current.checkpoint_interval_mins} mins. Occlusions &amp; masks handled with grace window.
                    </span>
                  </div>
                  <button
                    onClick={handleEndCurrentSession}
                    className="px-3 py-1 rounded-lg bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30 font-semibold transition text-[11px]"
                  >
                    End Lecture
                  </button>
                </div>
              );
            }
            return null;
          })()}
          <div className="relative aspect-video rounded-2xl overflow-hidden glass-panel border border-slate-700/60 shadow-2xl bg-black flex items-center justify-center">
            {/* Raw Webcam Video Element */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover transition-transform duration-200 ${
                isMirrored ? "transform scale-x-[-1]" : ""
              }`}
            />

            {/* Bounding Box Drawing Overlay Canvas - Never flipped via CSS so text is always readable */}
            <canvas
              ref={canvasRef}
              width={1280}
              height={720}
              className="absolute inset-0 w-full h-full object-cover pointer-events-none"
            />

            {/* Animated Laser Scanning Line */}
            {isStreaming && isScanning && <div className="animate-scan-line pointer-events-none" />}

            {/* HUD Overlay Details */}
            <div className="absolute top-3 left-3 flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-950/80 backdrop-blur-md border border-slate-800 text-xs">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-mono font-semibold text-emerald-400">LIVE FEED</span>
              <span className="text-slate-400">|</span>
              <span className="font-mono text-slate-300">{fps} FPS</span>
            </div>

            <div className="absolute top-3 right-3 flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-950/80 backdrop-blur-md border border-slate-800 text-xs">
              <ShieldCheck className="w-4 h-4 text-indigo-400" />
              <span className="font-semibold text-slate-200">ArcFace 512-D + Occlusion Guard</span>
            </div>

            {/* Bottom HUD: Live Detection Status */}
            <div className="absolute bottom-3 inset-x-3 p-3 rounded-xl bg-slate-950/85 backdrop-blur-md border border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-3">
                <span className="text-slate-400 font-medium">In Frame:</span>
                <span className="font-bold text-white px-2 py-0.5 rounded bg-slate-800">
                  {lastScanResult?.faces_detected ?? 0} Faces
                </span>
                <span className="text-slate-400">|</span>
                <span className="text-slate-400 font-medium">Recognized:</span>
                <span className="font-bold text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30">
                  {lastScanResult?.students_recognized ?? 0} Students
                </span>
              </div>
              <span className="text-slate-400 hidden sm:inline">{statusMessage}</span>
            </div>
          </div>

          {/* Quick Legend Bar */}
          <div className="p-3 rounded-xl glass-card flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
              <span className="text-slate-300 font-medium">Verified Live</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-cyan-400"></span>
              <span className="text-slate-300 font-medium">Kerchief/Mask (Preserved)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-amber-500"></span>
              <span className="text-slate-300 font-medium">Borderline (Flagged)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-rose-500"></span>
              <span className="text-slate-300 font-medium">Anti-Spoof Rejected</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-slate-500"></span>
              <span className="text-slate-300 font-medium">Unknown Face</span>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Live Real-Time Attendance Stream Drawer */}
        <div className="p-5 rounded-2xl glass-panel space-y-4 flex flex-col h-[520px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                Live Attendance Stream
              </h2>
            </div>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              AttenFace
            </span>
          </div>

          {/* Scrollable Event Feed */}
          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
            {recentEvents.length > 0 ? (
              recentEvents.map((evt) => (
                <div
                  key={evt.id}
                  className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition flex items-center justify-between"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-1.5">
                      {evt.status === "present" ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      ) : evt.status === "present_occluded" ? (
                        <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                      ) : evt.status === "flagged" ? (
                        <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                      ) : (
                        <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                      )}
                      <p className="text-xs font-bold text-white">{evt.name}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-[11px] font-mono text-slate-400">{evt.code}</span>
                      {evt.status === "present_occluded" && (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
                          Kerchief/Mask
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`text-xs font-bold ${evt.status === "present_occluded" ? "text-cyan-400" : "text-emerald-400"}`}>
                      {evt.confidence}%
                    </span>
                    <p className="text-[10px] text-slate-400">{evt.time}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400 space-y-2">
                <Layers className="w-8 h-8 text-slate-500" />
                <p className="text-xs font-medium">Awaiting facial detection events...</p>
                <p className="text-[11px] text-slate-400">Position enrolled students in front of the webcam.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
