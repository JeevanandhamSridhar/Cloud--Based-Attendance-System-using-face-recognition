import React from "react";
import {
  Camera,
  LayoutDashboard,
  Users,
  Calendar,
  FileSpreadsheet,
  ShieldCheck,
  LogOut,
  UserCheck,
} from "lucide-react";

export default function Navbar({ activeTab, setActiveTab, activeSession, currentUser, onLogout }) {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "scanner", label: "Live Scanner", icon: Camera, highlight: true },
    { id: "sessions", label: "Class Sessions", icon: Calendar },
    { id: "students", label: "Students Registry", icon: Users },
    { id: "reports", label: "Reports & Review", icon: FileSpreadsheet },
  ];

  return (
    <header className="sticky top-0 z-40 glass-panel border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab("dashboard")}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
                  SmartAttendance
                </span>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  ArcFace AI
                </span>
              </div>
              <p className="text-xs text-slate-400">Continuous Presence Validation</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                      : item.highlight
                      ? "text-emerald-400 hover:bg-emerald-500/10 hover:text-emerald-300"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-white" : item.highlight ? "text-emerald-400" : "text-slate-400"}`} />
                  <span>{item.label}</span>
                  {item.highlight && activeSession && (
                    <span className="flex h-2 w-2 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Status & Profile */}
          <div className="flex items-center space-x-3">
            {activeSession ? (
              <div className="hidden lg:flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Active: {activeSession.subject_code || "Lecture"} ({activeSession.room})</span>
              </div>
            ) : (
              <div className="hidden lg:flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-400 text-xs">
                <span className="h-2 w-2 rounded-full bg-slate-500"></span>
                <span>No Active Lecture</span>
              </div>
            )}

            <div className="flex items-center pl-2 border-l border-slate-800 space-x-2">
              <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 text-xs font-bold">
                {currentUser?.full_name ? currentUser.full_name.charAt(0) : "P"}
              </div>
              <div className="hidden sm:block text-left text-xs">
                <p className="font-semibold text-slate-200">{currentUser?.full_name || "Faculty Member"}</p>
                <p className="text-slate-400 capitalize">{currentUser?.role || "Faculty"}</p>
              </div>
              {onLogout && (
                <button
                  onClick={onLogout}
                  title="Logout"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
