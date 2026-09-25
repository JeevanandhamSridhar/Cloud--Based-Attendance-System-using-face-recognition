import axios from "axios";

const API = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

// Attach Authorization header if JWT token is stored
API.interceptors.request.use((config) => {
  const token = localStorage.getItem("smart_att_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-handle 401 Unauthorized
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear stale token and notify app to re-authenticate
      localStorage.removeItem("smart_att_token");
      localStorage.removeItem("smart_att_user");
      window.dispatchEvent(new Event("auth:unauthorized"));
    }
    return Promise.reject(error);
  }
);

// -------------------------------------------------------------
// AUTHENTICATION
// -------------------------------------------------------------
export const loginUser = async (email, password) => {
  const { data } = await API.post("/auth/login", { email, password });
  if (data.access_token) {
    localStorage.setItem("smart_att_token", data.access_token);
    localStorage.setItem("smart_att_user", JSON.stringify(data.user));
  }
  return data;
};

export const logoutUser = () => {
  localStorage.removeItem("smart_att_token");
  localStorage.removeItem("smart_att_user");
};

export const getStoredUser = () => {
  const u = localStorage.getItem("smart_att_user");
  return u ? JSON.parse(u) : null;
};

export const getProfile = async () => {
  const { data } = await API.get("/auth/me");
  return data;
};

// -------------------------------------------------------------
// STUDENTS
// -------------------------------------------------------------
export const fetchStudents = async () => {
  const { data } = await API.get("/students");
  return data;
};

export const createStudent = async (studentData) => {
  const { data } = await API.post("/students", studentData);
  return data;
};

export const enrollStudentFace = async (studentId, payload) => {
  const { data } = await API.post(`/students/${studentId}/enroll-face`, payload);
  return data;
};

export const deleteStudent = async (studentId) => {
  const { data } = await API.delete(`/students/${studentId}`);
  return data;
};

// -------------------------------------------------------------
// CLASS SESSIONS & COURSES
// -------------------------------------------------------------
export const fetchSubjects = async () => {
  const { data } = await API.get("/sessions/subjects");
  return data;
};

export const createSubject = async (subjectData) => {
  const { data } = await API.post("/sessions/subjects", subjectData);
  return data;
};

export const fetchSessions = async (statusFilter = null) => {
  const params = statusFilter ? { status_filter: statusFilter } : {};
  const { data } = await API.get("/sessions", { params });
  return data;
};

export const fetchActiveSession = async () => {
  const { data } = await API.get("/sessions/active");
  return data;
};

export const createSession = async (sessionData) => {
  const { data } = await API.post("/sessions", sessionData);
  return data;
};

export const startSession = async (sessionId) => {
  const { data } = await API.post(`/sessions/${sessionId}/start`);
  return data;
};

export const endSession = async (sessionId) => {
  const { data } = await API.post(`/sessions/${sessionId}/end`);
  return data;
};

// -------------------------------------------------------------
// LIVE ATTENDANCE & INFERENCE
// -------------------------------------------------------------
export const scanFrame = async (scanPayload) => {
  const { data } = await API.post("/attendance/scan-frame", scanPayload);
  return data;
};

export const fetchSessionAttendance = async (sessionId) => {
  const { data } = await API.get(`/attendance/session/${sessionId}`);
  return data;
};

export const fetchReviewQueue = async (sessionId) => {
  const { data } = await API.get(`/attendance/review-queue/${sessionId}`);
  return data;
};

export const verifyAttendance = async (attendanceId, approved, notes = "") => {
  const { data } = await API.post(`/attendance/verify/${attendanceId}`, {
    approved,
    notes,
  });
  return data;
};

export const fetchTodayCampusAttendance = async () => {
  const { data } = await API.get("/attendance/campus/today");
  return data;
};

// -------------------------------------------------------------
// ANALYTICS & EXPORT
// -------------------------------------------------------------
export const fetchDashboardSummary = async () => {
  const { data } = await API.get("/analytics/dashboard");
  return data;
};

export const fetchBunkingReport = async (sessionId) => {
  const { data } = await API.get(`/analytics/bunking-report?session_id=${sessionId}`);
  return data;
};

export const getExportCsvUrl = (sessionId) => {
  return `/api/analytics/export/csv/${sessionId}`;
};

export default API;
