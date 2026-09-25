import React, { useEffect, useState } from "react";
import Navbar from "./components/Navbar";
import DashboardPage from "./pages/DashboardPage";
import ScannerPage from "./pages/ScannerPage";
import SessionsPage from "./pages/SessionsPage";
import StudentsPage from "./pages/StudentsPage";
import ReportsPage from "./pages/ReportsPage";
import {
  fetchActiveSession,
  getStoredUser,
  loginUser,
  logoutUser,
} from "./services/api";
import { ShieldCheck, LogIn, Lock, Mail, Sparkles, Eye, EyeOff } from "lucide-react";

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [activeSession, setActiveSession] = useState(null);

  // Login form state
  const [email, setEmail] = useState("faculty@college.edu");
  const [password, setPassword] = useState("Password123!");
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const handleDemoLogin = async (e) => {
    if (e) e.preventDefault();
    setIsLoggingIn(true);
    setLoginError("");
    setEmail("faculty@college.edu");
    setPassword("Password123!");
    try {
      const data = await loginUser("faculty@college.edu", "Password123!");
      setCurrentUser(data.user);
      return data.user;
    } catch (err) {
      console.warn("Backend auth error:", err.message);
      setLoginError(err.response?.data?.detail || "Could not log in. Ensure backend is running.");
      return null;
    } finally {
      setIsLoggingIn(false);
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem("smart_att_token");
      if (token) {
        try {
          const profile = await getProfile();
          setCurrentUser(profile);
          return;
        } catch (e) {
          console.warn("Stored token invalid or expired. Re-authenticating...");
          localStorage.removeItem("smart_att_token");
          localStorage.removeItem("smart_att_user");
        }
      }
      // If no valid token or token expired, auto-login with default demo faculty
      await handleDemoLogin();
    };
    initAuth();

    const handleUnauthorized = async () => {
      console.warn("Session expired or unauthorized. Auto re-authenticating demo faculty...");
      setCurrentUser(null);
      await handleDemoLogin();
    };

    window.addEventListener("auth:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("auth:unauthorized", handleUnauthorized);
  }, []);

  // Poll for active session
  useEffect(() => {
    if (!currentUser) return;
    const checkActive = async () => {
      try {
        const s = await fetchActiveSession();
        setActiveSession(s);
      } catch (err) {
        // Silently skip if polling encounters network blip
      }
    };
    checkActive();
    const interval = setInterval(checkActive, 10000);
    return () => clearInterval(interval);
  }, [currentUser]);

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setIsLoggingIn(true);
    setLoginError("");
    try {
      const data = await loginUser(email, password);
      setCurrentUser(data.user);
    } catch (err) {
      setLoginError(err.response?.data?.detail || "Invalid credentials. Ensure backend is running.");
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    logoutUser();
    setCurrentUser(null);
  };

  // If unauthenticated, show institutional login screen
  if (!currentUser) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 relative overflow-hidden">
        {/* Background Ambient Glows */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="w-full max-w-md p-8 rounded-3xl glass-panel border border-slate-800 shadow-2xl relative z-10 space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-emerald-500 items-center justify-center shadow-xl shadow-indigo-600/30 mb-2">
              <ShieldCheck className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Smart Attendance</h1>
            <p className="text-xs text-slate-400">
              ArcFace 512-D Embeddings • Liveness Detection • AttenFace Continuous Presence
            </p>
          </div>

          {loginError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs text-center">
              {loginError}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-300 font-semibold mb-1.5">Institutional Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-3 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-slate-300 font-semibold">Password</label>
                <button
                  type="button"
                  onClick={() => {
                    setEmail("faculty@college.edu");
                    setPassword("Password123!");
                  }}
                  className="text-[10px] text-indigo-400 hover:text-indigo-300 font-mono underline"
                >
                  Fill Default (Password123!)
                </button>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-10 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoggingIn}
              className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition flex items-center justify-center space-x-2"
            >
              <LogIn className="w-4 h-4" />
              <span>{isLoggingIn ? "Authenticating..." : "Sign In to Portal"}</span>
            </button>
          </form>

          {/* Quick Demo Button */}
          <div className="pt-2 border-t border-slate-800 text-center">
            <button
              type="button"
              onClick={handleDemoLogin}
              className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center justify-center space-x-1.5 mx-auto py-1 px-3 rounded-lg hover:bg-emerald-500/10 transition"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Demo Faculty Quick-Login (Prof. Jeevanandham)</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeSession={activeSession}
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "dashboard" && <DashboardPage setActiveTab={setActiveTab} />}
        {activeTab === "scanner" && <ScannerPage />}
        {activeTab === "sessions" && <SessionsPage setActiveTab={setActiveTab} />}
        {activeTab === "students" && <StudentsPage />}
        {activeTab === "reports" && <ReportsPage />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500">
        <p>
          Cloud-Based Smart Attendance System • B.Sc Computer Science Final Year Project • Powered by ArcFace &amp; AttenFace
        </p>
      </footer>
    </div>
  );
}
