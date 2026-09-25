import React, { useEffect, useState } from "react";
import {
  Calendar,
  Plus,
  Play,
  CheckCircle,
  Clock,
  MapPin,
  BookOpen,
  Sliders,
  AlertCircle,
} from "lucide-react";
import {
  fetchSessions,
  fetchSubjects,
  createSession,
  createSubject,
  startSession,
  endSession,
} from "../services/api";

export default function SessionsPage({ setActiveTab }) {
  const [sessions, setSessions] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New session form state
  const [subjectId, setSubjectId] = useState("");
  const [room, setRoom] = useState("Lab-01");
  const [checkpointInterval, setCheckpointInterval] = useState(5);
  const [minPresence, setMinPresence] = useState(75.0);

  // Flexible Timing State: "auto" (duration from current time) vs "manual" (explicit date & time picker)
  const [timeMode, setTimeMode] = useState("auto"); // "auto" | "manual"
  const [durationMins, setDurationMins] = useState(60);
  const [startImmediately, setStartImmediately] = useState(true);

  // Helper date / time formatters
  const getTodayDateStr = () => {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  };

  const getTimeStr = (d) => {
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    return `${hh}:${mm}`;
  };

  const [sessionDate, setSessionDate] = useState(getTodayDateStr());
  const [startTimeStr, setStartTimeStr] = useState(() => getTimeStr(new Date()));
  const [endTimeStr, setEndTimeStr] = useState(() => getTimeStr(new Date(Date.now() + 60 * 60 * 1000)));

  // New subject inline state
  const [isNewSubject, setIsNewSubject] = useState(false);
  const [newSubjCode, setNewSubjCode] = useState("");
  const [newSubjName, setNewSubjName] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const [sess, subjs] = await Promise.all([
        fetchSessions().catch(() => []),
        fetchSubjects().catch(() => []),
      ]);
      setSessions(sess);
      setSubjects(subjs);
      if (subjs.length > 0) setSubjectId(subjs[0].id);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateSession = async (e) => {
    e.preventDefault();
    try {
      let finalSubjectId = subjectId;
      if (isNewSubject) {
        const createdSubj = await createSubject({
          code: newSubjCode,
          name: newSubjName,
          department: "Computer Science",
        });
        finalSubjectId = createdSubj.id;
      }

      let startIso, endIso;
      if (timeMode === "auto") {
        const now = new Date();
        const end = new Date(now.getTime() + durationMins * 60 * 1000);
        startIso = now.toISOString();
        endIso = end.toISOString();
      } else {
        const startDt = new Date(`${sessionDate}T${startTimeStr}:00`);
        const endDt = new Date(`${sessionDate}T${endTimeStr}:00`);
        if (isNaN(startDt.getTime()) || isNaN(endDt.getTime())) {
          alert("Invalid date or time format. Please provide valid start and end times.");
          return;
        }
        if (endDt <= startDt) {
          alert("Lecture End Time must be later than Start Time.");
          return;
        }
        startIso = startDt.toISOString();
        endIso = endDt.toISOString();
      }

      const created = await createSession({
        subject_id: finalSubjectId,
        room,
        start_time: startIso,
        end_time: endIso,
        checkpoint_interval_mins: parseInt(checkpointInterval, 10),
        min_presence_percentage: parseFloat(minPresence),
      });

      if (startImmediately && timeMode === "auto") {
        try {
          await startSession(created.id);
        } catch (e) {
          console.warn("Auto-start notice:", e.message);
        }
      }

      setIsModalOpen(false);
      setIsNewSubject(false);
      loadData();
    } catch (err) {
      alert("Failed to create class session: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleStartSession = async (id) => {
    try {
      await startSession(id);
      loadData();
    } catch (err) {
      alert("Failed to start session: " + err.message);
    }
  };

  const handleEndSession = async (id) => {
    try {
      await endSession(id);
      loadData();
    } catch (err) {
      alert("Failed to end session: " + err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Class Sessions & Timetable</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Configure lecture windows and continuous presence policies for your courses.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition"
        >
          <Plus className="w-4 h-4" />
          <span>Schedule New Lecture</span>
        </button>
      </div>

      {/* Sessions Table / Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {sessions.map((s) => {
          const isActive = s.status === "active";
          const isCompleted = s.status === "completed";

          return (
            <div
              key={s.id}
              className={`p-5 rounded-2xl glass-panel space-y-4 border transition ${
                isActive
                  ? "border-emerald-500/50 bg-emerald-950/20 shadow-lg shadow-emerald-500/10"
                  : "border-slate-800"
              }`}
            >
              <div className="flex items-center justify-between">
                <span
                  className={`text-[10px] uppercase font-bold px-2.5 py-1 rounded-full border ${
                    isActive
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 animate-pulse"
                      : isCompleted
                      ? "bg-slate-800 text-slate-400 border-slate-700"
                      : "bg-indigo-500/20 text-indigo-300 border-indigo-500/40"
                  }`}
                >
                  {s.status}
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  {new Date(s.start_time).toLocaleDateString()}
                </span>
              </div>

              <div>
                <h3 className="text-lg font-bold text-white tracking-tight">{s.subject_name}</h3>
                <p className="text-xs font-mono text-indigo-400">{s.subject_code}</p>
              </div>

              <div className="space-y-1.5 text-xs text-slate-300 border-t border-slate-800/80 pt-3">
                <div className="flex items-center space-x-2">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  <span>Room: <strong className="text-white">{s.room}</strong></span>
                </div>
                <div className="flex items-center space-x-2">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span>
                    {new Date(s.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{" "}
                    {new Date(s.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <Sliders className="w-3.5 h-3.5 text-slate-400" />
                  <span>
                    Checkpoints: <strong>Every {s.checkpoint_interval_mins} mins</strong> (Min {s.min_presence_percentage}%)
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex items-center space-x-2">
                {!isActive && !isCompleted && (
                  <button
                    onClick={() => handleStartSession(s.id)}
                    className="flex-1 flex items-center justify-center space-x-1.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Start Lecture</span>
                  </button>
                )}

                {isActive && (
                  <>
                    <button
                      onClick={() => setActiveTab("scanner")}
                      className="flex-1 py-2 rounded-xl bg-emerald-500 text-slate-950 text-xs font-bold shadow-md shadow-emerald-500/20 transition"
                    >
                      Open Scanner
                    </button>
                    <button
                      onClick={() => handleEndSession(s.id)}
                      className="px-3 py-2 rounded-xl bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30 text-xs font-semibold transition"
                    >
                      End
                    </button>
                  </>
                )}

                {isCompleted && (
                  <button
                    onClick={() => setActiveTab("reports")}
                    className="w-full py-2 rounded-xl glass-card hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-semibold transition"
                  >
                    View Attendance Sheet &rarr;
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Schedule Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md p-6 rounded-2xl glass-panel border border-slate-700 shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-white">Schedule New Class Session</h2>

            <form onSubmit={handleCreateSession} className="space-y-3.5 text-xs">
              {/* Subject Selection */}
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Subject / Course</label>
                {!isNewSubject ? (
                  <div className="space-y-2">
                    <select
                      value={subjectId}
                      onChange={(e) => setSubjectId(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500"
                    >
                      {subjects.map((sub) => (
                        <option key={sub.id} value={sub.id}>
                          {sub.code} - {sub.name}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => setIsNewSubject(true)}
                      className="text-indigo-400 hover:text-indigo-300 text-[11px] underline"
                    >
                      + Create new course
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                    <input
                      type="text"
                      placeholder="Course Code (e.g., CS304)"
                      value={newSubjCode}
                      onChange={(e) => setNewSubjCode(e.target.value)}
                      required
                      className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2"
                    />
                    <input
                      type="text"
                      placeholder="Course Title (e.g., Computer Networks)"
                      value={newSubjName}
                      onChange={(e) => setNewSubjName(e.target.value)}
                      required
                      className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2"
                    />
                    <button
                      type="button"
                      onClick={() => setIsNewSubject(false)}
                      className="text-slate-400 hover:text-slate-300 text-[11px]"
                    >
                      Cancel new course
                    </button>
                  </div>
                )}
              </div>

              {/* Room */}
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Room / Lab</label>
                <input
                  type="text"
                  value={room}
                  onChange={(e) => setRoom(e.target.value)}
                  required
                  className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5"
                />
              </div>

              {/* Lecture Schedule & Timing (Automatic vs Manual Mode) */}
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-indigo-400" />
                    <span className="font-semibold text-slate-200">Lecture Timing &amp; Duration</span>
                  </div>
                  <div className="flex items-center rounded-lg bg-slate-950 p-0.5 border border-slate-800 text-[11px]">
                    <button
                      type="button"
                      onClick={() => setTimeMode("auto")}
                      className={`px-2.5 py-1 rounded-md font-medium transition ${
                        timeMode === "auto"
                          ? "bg-indigo-600 text-white shadow-sm"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      ⚡ Quick / Live
                    </button>
                    <button
                      type="button"
                      onClick={() => setTimeMode("manual")}
                      className={`px-2.5 py-1 rounded-md font-medium transition ${
                        timeMode === "manual"
                          ? "bg-indigo-600 text-white shadow-sm"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      📅 Manual Pick
                    </button>
                  </div>
                </div>

                {timeMode === "auto" ? (
                  <div className="space-y-2">
                    <label className="block text-[11px] text-slate-400">
                      Duration Preset (Starts Right Now):
                    </label>
                    <div className="grid grid-cols-5 gap-1.5">
                      {[
                        { label: "45m", val: 45 },
                        { label: "50m", val: 50 },
                        { label: "1 hr", val: 60 },
                        { label: "1.5h", val: 90 },
                        { label: "2 hrs", val: 120 },
                      ].map((item) => (
                        <button
                          key={item.val}
                          type="button"
                          onClick={() => setDurationMins(item.val)}
                          className={`py-1.5 px-1 rounded-lg text-xs font-semibold border transition ${
                            durationMins === item.val
                              ? "bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30"
                              : "bg-slate-800/60 border-slate-700/60 text-slate-400 hover:text-slate-200"
                          }`}
                        >
                          {item.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">Lecture Date</label>
                      <input
                        type="date"
                        value={sessionDate}
                        onChange={(e) => setSessionDate(e.target.value)}
                        required
                        className="w-full bg-slate-900 border border-slate-700 text-white text-xs rounded-lg p-2 focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-[11px] text-slate-400 mb-1">Start Time</label>
                        <input
                          type="time"
                          value={startTimeStr}
                          onChange={(e) => {
                            setStartTimeStr(e.target.value);
                            const parts = e.target.value.split(":");
                            if (parts.length === 2) {
                              const h = parseInt(parts[0], 10);
                              const m = parts[1];
                              const endH = (h + 1) % 24;
                              setEndTimeStr(`${String(endH).padStart(2, "0")}:${m}`);
                            }
                          }}
                          required
                          className="w-full bg-slate-900 border border-slate-700 text-white text-xs rounded-lg p-2 focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] text-slate-400 mb-1">End Time</label>
                        <input
                          type="time"
                          value={endTimeStr}
                          onChange={(e) => setEndTimeStr(e.target.value)}
                          required
                          className="w-full bg-slate-900 border border-slate-700 text-white text-xs rounded-lg p-2 focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Timing summary info pill */}
                <div className="p-2 rounded-lg bg-indigo-950/40 border border-indigo-500/20 flex items-center justify-between text-[11px]">
                  <span className="text-slate-300">
                    Window:{" "}
                    <strong className="text-indigo-300">
                      {timeMode === "auto"
                        ? `Now → Next ${durationMins} mins`
                        : `${startTimeStr} – ${endTimeStr} (${sessionDate})`}
                    </strong>
                  </span>
                  <span className="text-emerald-400 font-mono">
                    {Math.max(1, Math.round((timeMode === "auto" ? durationMins : 60) / checkpointInterval))} Checkpoints
                  </span>
                </div>

                {/* Immediate Activation Checkbox */}
                {timeMode === "auto" && (
                  <label className="flex items-center space-x-2 text-[11px] text-slate-300 cursor-pointer pt-1">
                    <input
                      type="checkbox"
                      checked={startImmediately}
                      onChange={(e) => setStartImmediately(e.target.checked)}
                      className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span>Start lecture immediately &amp; activate live attendance scanner</span>
                  </label>
                )}
              </div>

              {/* AttenFace Checkpoint Config */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Checkpoint Interval</label>
                  <select
                    value={checkpointInterval}
                    onChange={(e) => setCheckpointInterval(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5"
                  >
                    <option value={2}>Every 2 minutes</option>
                    <option value={5}>Every 5 minutes</option>
                    <option value={10}>Every 10 minutes</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Min Presence %</label>
                  <input
                    type="number"
                    min="50"
                    max="100"
                    value={minPresence}
                    onChange={(e) => setMinPresence(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5"
                  />
                </div>
              </div>

              {/* Modal Buttons */}
              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg glass-card text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold"
                >
                  Schedule Lecture
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
