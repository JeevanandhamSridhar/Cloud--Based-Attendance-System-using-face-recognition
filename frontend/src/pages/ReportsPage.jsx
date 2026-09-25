import React, { useEffect, useState } from "react";
import {
  FileSpreadsheet,
  Download,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Filter,
  RefreshCw,
  Sliders,
  Building2,
  ShieldAlert,
  UserCheck,
  UserX,
  Eye,
} from "lucide-react";
import {
  fetchSessions,
  fetchSessionAttendance,
  fetchReviewQueue,
  fetchBunkingReport,
  verifyAttendance,
  getExportCsvUrl,
} from "../services/api";

export default function ReportsPage() {
  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [bunkingRecords, setBunkingRecords] = useState([]);
  const [viewMode, setViewMode] = useState("roster"); // "roster" | "truancy"
  const [truancyFilter, setTruancyFilter] = useState("ALL"); // "ALL" | "BUNKING_CLASS" | "ATTENDING_CLASS" | "FULL_DAY_ABSENT"
  const [loading, setLoading] = useState(false);

  const loadSessions = async () => {
    try {
      const data = await fetchSessions();
      setSessions(data);
      if (data.length > 0 && !selectedSessionId) {
        setSelectedSessionId(data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadAttendance = async (sessId) => {
    if (!sessId) return;
    try {
      setLoading(true);
      const [att, rev, bunk] = await Promise.all([
        fetchSessionAttendance(sessId).catch(() => []),
        fetchReviewQueue(sessId).catch(() => []),
        fetchBunkingReport(sessId).catch(() => []),
      ]);
      setAttendanceRecords(att);
      setReviewQueue(rev);
      setBunkingRecords(bunk);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (selectedSessionId) {
      loadAttendance(selectedSessionId);
    }
  }, [selectedSessionId]);

  const handleVerify = async (attId, approved) => {
    try {
      await verifyAttendance(attId, approved);
      loadAttendance(selectedSessionId);
    } catch (err) {
      alert("Verification update failed: " + err.message);
    }
  };

  const currentSession = sessions.find((s) => s.id === selectedSessionId);
  const bunkingFlaggedCount = bunkingRecords.filter(
    (b) => b.truancy_classification === "BUNKING_CLASS"
  ).length;

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-4 rounded-2xl glass-panel">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Attendance Reports &amp; Faculty Review Queue
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit continuous presence checkpoints and verify borderline biometric matches.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Session Selector */}
          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedSessionId}
              onChange={(e) => setSelectedSessionId(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-white text-xs rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.subject_code} - {s.subject_name} ({new Date(s.start_time).toLocaleDateString()})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => loadAttendance(selectedSessionId)}
            className="p-2 rounded-lg glass-card text-slate-300 hover:text-white"
            title="Refresh Table"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>

          {/* Download Official CSV Report Button */}
          {selectedSessionId && (
            <a
              href={getExportCsvUrl(selectedSessionId)}
              download
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/30 transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV Sheet</span>
            </a>
          )}
        </div>
      </div>

      {/* Borderline Review Queue Section (Faculty 1-Click Verification) */}
      {reviewQueue.length > 0 && (
        <div className="p-5 rounded-2xl bg-amber-950/20 border border-amber-500/30 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-amber-400" />
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                Borderline Matches Flagged for Review ({reviewQueue.length})
              </h2>
            </div>
            <span className="text-[11px] text-amber-300">
              Confidence between 48% - 60%
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {reviewQueue.map((item) => (
              <div
                key={item.id}
                className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-slate-200">{item.student_code}</span>
                    <span className="text-xs font-bold text-amber-400">{item.confidence_avg}% Match</span>
                  </div>
                  <p className="text-sm font-semibold text-white mt-0.5">{item.student_name}</p>
                  <p className="text-[11px] text-slate-400">
                    Presence Score: <strong className="text-slate-200">{item.presence_score}%</strong> ({item.checkpoints_detected}/{item.total_checkpoints} checkpoints)
                  </p>
                </div>

                <div className="flex items-center space-x-2 pt-2 border-t border-slate-800">
                  <button
                    onClick={() => handleVerify(item.id, true)}
                    className="flex-1 flex items-center justify-center space-x-1 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600 text-emerald-300 hover:text-white border border-emerald-500/30 text-xs font-semibold transition"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Approve</span>
                  </button>
                  <button
                    onClick={() => handleVerify(item.id, false)}
                    className="flex-1 flex items-center justify-center space-x-1 py-1.5 rounded-lg bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30 text-xs font-semibold transition"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Reject</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* View Switcher: Lecture Roster vs Campus Gate Truancy Audit */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode("roster")}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
              viewMode === "roster"
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                : "text-slate-400 hover:text-white glass-card"
            }`}
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Classroom Lecture Roster ({attendanceRecords.length})</span>
          </button>

          <button
            onClick={() => setViewMode("truancy")}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
              viewMode === "truancy"
                ? "bg-purple-600 text-white shadow-lg shadow-purple-600/20"
                : "text-slate-400 hover:text-white glass-card"
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Campus Gate vs Class Truancy Audit</span>
            {bunkingFlaggedCount > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-rose-500 text-white text-[10px] font-bold animate-pulse">
                {bunkingFlaggedCount} Flagged
              </span>
            )}
          </button>
        </div>

        {viewMode === "truancy" && (
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400">Filter Classification:</span>
            <select
              value={truancyFilter}
              onChange={(e) => setTruancyFilter(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-white text-xs rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-purple-500 focus:outline-none"
            >
              <option value="ALL">All Students ({bunkingRecords.length})</option>
              <option value="BUNKING_CLASS">🚨 Bunking Detected ({bunkingFlaggedCount})</option>
              <option value="ATTENDING_CLASS">✅ Attending Normally</option>
              <option value="FULL_DAY_ABSENT">⚪ Full Day Absent</option>
            </select>
          </div>
        )}
      </div>

      {viewMode === "roster" ? (
        /* Main Attendance Roster Table */
        <div className="rounded-2xl glass-panel overflow-hidden border border-slate-800 space-y-2 p-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                Official Session Attendance Roster
              </h2>
              {currentSession && (
                <p className="text-xs text-slate-400">
                  Course: {currentSession.subject_name} ({currentSession.subject_code}) • Room: {currentSession.room}
                </p>
              )}
            </div>
            <span className="text-xs font-semibold text-slate-300">
              {attendanceRecords.length} Students Logged
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold bg-slate-900/40">
                  <th className="py-3 px-4">Student ID</th>
                  <th className="py-3 px-4">Student Name</th>
                  <th className="py-3 px-4">Presence Score %</th>
                  <th className="py-3 px-4">Face Visibility &amp; Occlusion</th>
                  <th className="py-3 px-4">Checkpoints</th>
                  <th className="py-3 px-4">First Seen</th>
                  <th className="py-3 px-4">Last Seen</th>
                  <th className="py-3 px-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {attendanceRecords.length > 0 ? (
                  attendanceRecords.map((r) => {
                    let badge = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
                    if (r.status === "partial") badge = "bg-amber-500/10 text-amber-400 border-amber-500/30";
                    if (r.status === "absent") badge = "bg-rose-500/10 text-rose-400 border-rose-500/30";
                    if (r.status === "flagged_review") badge = "bg-purple-500/10 text-purple-400 border-purple-500/30";

                    return (
                      <tr key={r.id} className="hover:bg-slate-800/20 transition">
                        <td className="py-3 px-4 font-mono font-bold text-indigo-300">{r.student_code}</td>
                        <td className="py-3 px-4 font-medium text-white">{r.student_name}</td>
                        <td className="py-3 px-4 font-bold text-slate-200">
                          <div className="flex items-center space-x-2">
                            <div className="w-16 h-2 rounded-full bg-slate-800 overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  r.presence_score >= 75
                                    ? "bg-emerald-500"
                                    : r.presence_score >= 50
                                    ? "bg-amber-500"
                                    : "bg-rose-500"
                                }`}
                                style={{ width: `${Math.min(100, r.presence_score)}%` }}
                              />
                            </div>
                            <span>{r.presence_score}%</span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="space-y-0.5">
                            <span className="text-slate-200 font-semibold text-xs">
                              {r.face_visibility_score ? `${r.face_visibility_score}% Clear` : "100% Clear"}
                            </span>
                            {r.occlusion_count > 0 && (
                              <p className="text-[10px] text-cyan-400 font-medium">
                                {r.occlusion_count} kerchief/mask event{r.occlusion_count > 1 ? "s" : ""}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-slate-400">
                          {r.checkpoints_detected} / {r.total_checkpoints} intervals
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-400">
                          {r.first_seen ? new Date(r.first_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : "--"}
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-400">
                          {r.last_seen ? new Date(r.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : "--"}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${badge}`}>
                            {r.status.replace("_", " ")}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan="8" className="py-12 text-center text-slate-400">
                      No attendance records for this lecture yet. Start the scanner to record presence.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Campus vs Class Truancy Audit Section */
        <div className="space-y-4">
          {/* Truancy Stat Overview Chips */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl glass-panel space-y-1">
              <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wider flex items-center space-x-1">
                <Building2 className="w-3.5 h-3.5 text-indigo-400" />
                <span>On Campus Today</span>
              </span>
              <p className="text-xl font-extrabold text-white">
                {bunkingRecords.filter((b) => b.campus_status === "present_on_campus").length}
              </p>
              <p className="text-[10px] text-slate-400">Scanned at gate or lecture</p>
            </div>

            <div className="p-3.5 rounded-xl glass-panel space-y-1">
              <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wider flex items-center space-x-1">
                <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Attending Class</span>
              </span>
              <p className="text-xl font-extrabold text-emerald-400">
                {bunkingRecords.filter((b) => b.truancy_classification === "ATTENDING_CLASS").length}
              </p>
              <p className="text-[10px] text-slate-400">Present in room session</p>
            </div>

            <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-500/30 space-y-1">
              <span className="text-[11px] text-rose-300 font-medium uppercase tracking-wider flex items-center space-x-1">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                <span>Bunking Flagged</span>
              </span>
              <p className="text-xl font-extrabold text-rose-400">
                {bunkingFlaggedCount}
              </p>
              <p className="text-[10px] text-rose-300/80">On campus, skipped lecture!</p>
            </div>

            <div className="p-3.5 rounded-xl glass-panel space-y-1">
              <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wider flex items-center space-x-1">
                <UserX className="w-3.5 h-3.5 text-slate-400" />
                <span>Full Day Absent</span>
              </span>
              <p className="text-xl font-extrabold text-slate-300">
                {bunkingRecords.filter((b) => b.truancy_classification === "FULL_DAY_ABSENT").length}
              </p>
              <p className="text-[10px] text-slate-400">Never entered campus</p>
            </div>
          </div>

          {/* Truancy Matrix Table */}
          <div className="rounded-2xl glass-panel overflow-hidden border border-slate-800 space-y-2 p-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                  <Building2 className="w-4 h-4 text-purple-400" />
                  <span>Dual-Tier Campus Gate vs Classroom Lecture Audit</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Automated discrepancy matrix: Flags students recorded at the college gate who skipped the course lecture.
                </p>
              </div>
              <span className="text-xs font-semibold text-slate-300">
                Showing {bunkingRecords.filter((b) => truancyFilter === "ALL" || b.truancy_classification === truancyFilter).length} Students
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold bg-slate-900/40">
                    <th className="py-3 px-4">Student ID</th>
                    <th className="py-3 px-4">Student Name</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Campus Gate Entry</th>
                    <th className="py-3 px-4">Classroom Presence</th>
                    <th className="py-3 px-4">Truancy Discrepancy Classification</th>
                    <th className="py-3 px-4 text-right">Faculty Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {bunkingRecords
                    .filter((b) => truancyFilter === "ALL" || b.truancy_classification === truancyFilter)
                    .map((item) => {
                      const isBunking = item.truancy_classification === "BUNKING_CLASS";
                      const isAttending = item.truancy_classification === "ATTENDING_CLASS";

                      return (
                        <tr
                          key={item.student_id}
                          className={`transition ${
                            isBunking
                              ? "bg-rose-950/20 hover:bg-rose-950/30"
                              : "hover:bg-slate-800/20"
                          }`}
                        >
                          <td className="py-3 px-4 font-mono font-bold text-indigo-300">
                            {item.student_code}
                          </td>
                          <td className="py-3 px-4 font-medium text-white">
                            {item.student_name}
                          </td>
                          <td className="py-3 px-4 text-slate-400">
                            {item.department}
                          </td>
                          <td className="py-3 px-4">
                            {item.campus_status === "present_on_campus" ? (
                              <div className="flex flex-col">
                                <span className="inline-flex items-center space-x-1 text-emerald-400 font-semibold text-xs">
                                  <CheckCircle2 className="w-3 h-3" />
                                  <span>Present on Campus</span>
                                </span>
                                {item.campus_entry_time && (
                                  <span className="text-[10px] text-slate-400 font-mono">
                                    Gate In: {new Date(item.campus_entry_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                  </span>
                                )}
                              </div>
                            ) : (
                              <span className="text-slate-500 font-mono text-xs">
                                Not Recorded at Gate
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center space-x-2">
                              <span
                                className={`font-semibold capitalize text-xs ${
                                  item.class_status === "present"
                                    ? "text-emerald-400"
                                    : item.class_status === "partial"
                                    ? "text-amber-400"
                                    : "text-rose-400"
                                }`}
                              >
                                {item.class_status}
                              </span>
                              <span className="text-slate-400 text-[11px]">
                                ({item.class_presence_score}%)
                              </span>
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            {isBunking ? (
                              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 font-bold text-[11px] animate-pulse">
                                <ShieldAlert className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                                <span>🚨 Bunking: On Campus, Skipped Class!</span>
                              </span>
                            ) : isAttending ? (
                              <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold text-[11px]">
                                <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                                <span>Attending Class Normally</span>
                              </span>
                            ) : (
                              <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-medium text-[11px]">
                                <UserX className="w-3 h-3 text-slate-500 shrink-0" />
                                <span>Full Day Absent</span>
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right">
                            {isBunking ? (
                              <span className="text-[11px] text-rose-400 font-semibold underline underline-offset-2 cursor-pointer hover:text-rose-300">
                                Alert Warden / SMS
                              </span>
                            ) : (
                              <span className="text-[11px] text-slate-500 font-mono">
                                Verified
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
