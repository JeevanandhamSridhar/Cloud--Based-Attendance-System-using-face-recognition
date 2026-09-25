import React, { useEffect, useState } from "react";
import {
  Users,
  Video,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  TrendingUp,
  RefreshCw,
  ShieldAlert,
  Building2,
  UserX,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { fetchDashboardSummary, fetchActiveSession } from "../services/api";

export default function DashboardPage({ setActiveTab }) {
  const [summary, setSummary] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sumData, sessData] = await Promise.all([
        fetchDashboardSummary().catch(() => null),
        fetchActiveSession().catch(() => null),
      ]);
      setSummary(sumData);
      setActiveSession(sessData);
    } catch (err) {
      console.error("Dashboard load failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 20000);
    return () => clearInterval(timer);
  }, []);

  // Chart data
  const pieData = [
    { name: "Present (>=75%)", value: summary?.today_present_count || 0, color: "#10b981" },
    { name: "Partial (50-74%)", value: summary?.today_partial_count || 0, color: "#f59e0b" },
    { name: "Absent (<50%)", value: summary?.today_absent_count || 0, color: "#ef4444" },
  ];

  return (
    <div className="space-y-6">
      {/* Top Welcome & Actions Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Institutional Attendance &amp; Truancy Analytics
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Dual-Tier Biometrics: Campus Gate check-in vs Continuous Classroom lecture presence monitoring.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={loadData}
            className="flex items-center space-x-2 px-3 py-2 rounded-lg glass-card text-xs font-medium text-slate-300 hover:text-white hover:border-slate-600 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setActiveTab("scanner")}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-600/20 transition"
          >
            <Video className="w-4 h-4" />
            <span>Launch Live Scanner</span>
          </button>
        </div>
      </div>

      {/* Active Session Hero Banner */}
      {activeSession ? (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-950/70 via-slate-900 to-indigo-950/60 border border-emerald-500/30 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 transform translate-x-8 -translate-y-8 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="flex h-2.5 w-2.5 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                </span>
                <span className="text-xs uppercase font-bold tracking-wider text-emerald-400">
                  Lecture In Progress
                </span>
              </div>
              <h2 className="text-xl font-bold text-white">
                {activeSession.subject_name} ({activeSession.subject_code})
              </h2>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-300">
                <span>Room: <strong className="text-white">{activeSession.room}</strong></span>
                <span>Checkpoints: <strong className="text-white">Every {activeSession.checkpoint_interval_mins} mins</strong></span>
                <span>Threshold: <strong className="text-white">{activeSession.min_presence_percentage}% Presence</strong></span>
              </div>
            </div>
            <button
              onClick={() => setActiveTab("scanner")}
              className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/30 transition transform hover:-translate-y-0.5"
            >
              <span>Open Scanner Feed</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-xl glass-card border border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400">
              <Clock className="w-4 h-4" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-200">No active lecture currently running</p>
              <p className="text-xs text-slate-400">Main gate scanning or classroom lectures can be launched anytime from Live Scanner.</p>
            </div>
          </div>
          <button
            onClick={() => setActiveTab("sessions")}
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 underline underline-offset-4"
          >
            Schedule Session &rarr;
          </button>
        </div>
      )}

      {/* KPI Stats Grid (Dual-Tier 6-Card Overview) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* Card 1: Total Enrolled */}
        <div className="p-4 rounded-2xl glass-panel space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-medium uppercase tracking-wider">Enrolled</span>
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-white">
            {summary?.total_enrolled_students ?? "--"}
          </div>
          <p className="text-[11px] text-slate-400">Biometric database</p>
        </div>

        {/* Card 2: Campus Gate Today */}
        <div className="p-4 rounded-2xl glass-panel space-y-2 border border-sky-500/20">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-medium uppercase tracking-wider text-sky-300">Campus In</span>
            <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400">
              <Building2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-sky-400">
            {summary?.today_campus_entry_count ?? 0}
          </div>
          <p className="text-[11px] text-slate-400">Entered gate today</p>
        </div>

        {/* Card 3: Class Present */}
        <div className="p-4 rounded-2xl glass-panel space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-medium uppercase tracking-wider">Class Present</span>
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-emerald-400">
            {summary?.today_present_count ?? "--"}
          </div>
          <p className="text-[11px] text-slate-400">
            {summary?.today_total_attendances ? `Across ${summary.today_total_attendances} records` : "In scheduled classes"}
          </p>
        </div>

        {/* Card 4: Avg Presence Score */}
        <div className="p-4 rounded-2xl glass-panel space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-medium uppercase tracking-wider">Avg Presence</span>
            <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-blue-400">
            {summary?.average_presence_percentage ? `${summary.average_presence_percentage}%` : "--"}
          </div>
          <p className="text-[11px] text-slate-400">Checkpoints metric</p>
        </div>

        {/* Card 5: Low Attendance Defaulters */}
        <div className="p-4 rounded-2xl glass-panel space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-medium uppercase tracking-wider">Watchlist</span>
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-amber-400">
            {summary?.low_attendance_students?.length ?? 0}
          </div>
          <p className="text-[11px] text-slate-400">Overall &lt; 75% rate</p>
        </div>

        {/* Card 6: Truancy / Bunking Alert */}
        <div className={`p-4 rounded-2xl space-y-2 border transition ${
          (summary?.bunking_flagged_count ?? 0) > 0
            ? "bg-rose-950/30 border-rose-500/50 shadow-lg shadow-rose-950/50"
            : "glass-panel border-slate-800"
        }`}>
          <div className="flex items-center justify-between text-slate-400">
            <span className={`text-[11px] font-bold uppercase tracking-wider ${
              (summary?.bunking_flagged_count ?? 0) > 0 ? "text-rose-400" : "text-slate-400"
            }`}>
              Bunking Alert
            </span>
            <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className={`text-2xl font-extrabold ${
            (summary?.bunking_flagged_count ?? 0) > 0 ? "text-rose-400 animate-pulse" : "text-slate-300"
          }`}>
            {summary?.bunking_flagged_count ?? 0}
          </div>
          <p className="text-[11px] text-rose-300/80">On campus, missed class</p>
        </div>
      </div>

      {/* Analytics Charts & Low Attendance Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Attendance Distribution Chart */}
        <div className="p-5 rounded-2xl glass-panel space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Today's Attendance Status
          </h3>
          <div className="h-56 w-full flex items-center justify-center">
            {summary?.today_total_attendances > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "0.5rem",
                      color: "#fff",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-slate-500 text-xs">
                No attendance recorded yet today.<br />Start a session to see real-time charts.
              </div>
            )}
          </div>
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-semibold">
              Present: {summary?.today_present_count || 0}
            </div>
            <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 font-semibold">
              Partial: {summary?.today_partial_count || 0}
            </div>
            <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 font-semibold">
              Absent: {summary?.today_absent_count || 0}
            </div>
          </div>
        </div>

        {/* Low Attendance Warning Table */}
        <div className="lg:col-span-2 p-5 rounded-2xl glass-panel space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Defaulter Warning Watchlist (&lt; 75% Attendance)
              </h3>
            </div>
            <span className="text-xs text-slate-400">Institutional Rule</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold">
                  <th className="py-2.5 px-3">Student ID</th>
                  <th className="py-2.5 px-3">Full Name</th>
                  <th className="py-2.5 px-3">Department</th>
                  <th className="py-2.5 px-3 text-right">Attendance %</th>
                  <th className="py-2.5 px-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {summary?.low_attendance_students && summary.low_attendance_students.length > 0 ? (
                  summary.low_attendance_students.map((st) => (
                    <tr key={st.student_id} className="hover:bg-slate-800/30 transition">
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-200">{st.student_code}</td>
                      <td className="py-2.5 px-3 font-medium text-white">{st.name}</td>
                      <td className="py-2.5 px-3 text-slate-400">{st.department}</td>
                      <td className="py-2.5 px-3 text-right font-bold text-rose-400">
                        {st.attendance_pct}%
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 text-[10px] font-semibold border border-rose-500/30">
                          Critical
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="py-8 text-center text-slate-400">
                      No students currently below the 75% attendance threshold. Excellent!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
