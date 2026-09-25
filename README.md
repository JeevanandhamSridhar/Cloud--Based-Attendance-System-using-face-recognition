# Cloud-Based Smart Attendance System with Facial Recognition, Liveness Detection & Analytics

[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF.svg?style=flat&logo=vite&logoColor=white)](https://vitejs.dev)
[![InsightFace](https://img.shields.io/badge/ArcFace-InsightFace-red.svg?style=flat)](https://github.com/deepinsight/insightface)
[![MediaPipe](https://img.shields.io/badge/Liveness-MediaPipe_FaceMesh-blue.svg?style=flat)](https://mediapipe.dev)
[![pgvector](https://img.shields.io/badge/Database-PostgreSQL_pgvector-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)

An enterprise-grade, privacy-conscious facial recognition attendance platform built as an academic final-year B.Sc Computer Science project.

---

## 🌟 Key Differentiators & Innovations

1. **Continuous Presence Validation (Presence Score %)**
   - Instead of marking an entire lecture's attendance on a single morning detection, the system continuously logs periodic checkpoints during the class session (inspired by *AttenFace: Rao et al., IEEE CICT 2022*).
   - $\text{Presence Score} = \left( \frac{\text{Successful Checkpoints Detected}}{\text{Total Session Checkpoints}} \right) \times 100\%$
   - Configurable institutional policy: $\ge 75\%$ = **Present**, $50\text{--}74\%$ = **Partial**, $< 50\%$ = **Absent**.

2. **Zero-Raw-Biometric Storage (GDPR & Privacy by Design)**
   - After student enrollment, raw camera frames are discarded from memory.
   - **Only 512-dimensional ArcFace mathematical vectors** are persisted in the database. Faces cannot be reconstructed from normalized embedding vectors.

3. **Dual-Tier Liveness & Anti-Spoofing**
   - **Tier 1 (Real-time Edge):** 468-landmark MediaPipe FaceMesh Eye Aspect Ratio (EAR) blink verification. Detects static printed photographs, phone replays, and cutouts.
   - **Tier 2 (Quality & Variance):** Temporal landmark variance and motion history preventing static presentation attacks.

4. **Multi-Face Simultaneous Detection**
   - SCRFD (Sample and Computation Redistribution for Efficient Face Detection) processes multi-student groups simultaneously in a single frame.

5. **Faculty Borderline Review Queue**
   - Facial matches with confidence between $48\%$ and $60\%$ are flagged in an interactive review queue for 1-click teacher confirmation.

---

## 📁 Project Architecture

```
cloud-attendance/
├── core/
│   ├── __init__.py
│   ├── face_engine.py       # InsightFace SCRFD detector + ArcFace 512-D embedder
│   ├── liveness.py          # MediaPipe FaceMesh EAR blink calculation & anti-spoofing
│   └── matcher.py           # Cosine vector similarity & embeddings database manager
├── backend/
│   └── app/
│       ├── config.py        # Settings, CORS, JWT secrets & recognition thresholds
│       ├── database.py      # SQLAlchemy engine (local SQLite / Supabase PostgreSQL)
│       ├── models.py        # ORM models (Users, Students, Embeddings, Sessions, Attendance)
│       ├── schemas.py       # Pydantic validation schemas
│       ├── security.py      # Bcrypt password hashing & JWT token verification
│       ├── services/
│       │   └── presence.py  # AttenFace continuous presence score calculation engine
│       ├── api/
│       │   ├── auth.py      # Faculty & Admin login / registration (JWT)
│       │   ├── students.py  # Student registry & 512-D ArcFace vector enrollment
│       │   ├── sessions.py  # Class session scheduling, start/end lifecycle
│       │   ├── attendance.py# Multi-face frame scanner & borderline review queue
│       │   └── analytics.py # Dashboard KPIs & downloadable CSV export
│       └── main.py          # FastAPI application entrypoint
├── frontend/
│   ├── src/
│   │   ├── components/      # Navbar, Glassmorphic UI components
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx # Analytics KPIs, active lecture banner, Recharts
│   │   │   ├── ScannerPage.jsx   # Live webcam browser scanner with bounding boxes & HUD
│   │   │   ├── SessionsPage.jsx  # Lecture scheduling with custom AttenFace intervals
│   │   │   ├── StudentsPage.jsx  # Student registry with in-browser face capture wizard
│   │   │   └── ReportsPage.jsx   # Attendance roster, Borderline Review Queue & CSV export
│   │   └── services/api.js  # Axios API client
│   └── package.json
├── database/
│   └── schema.sql           # Supabase / PostgreSQL schema with pgvector & HNSW index
├── tests/
│   ├── test_pipeline.py     # AI engine & similarity math test suite
│   └── test_api.py          # Backend API & attendance lifecycle test suite
├── register.py              # CLI 5-shot student face enrollment tool
├── recognize.py             # CLI Live multi-face webcam monitor
├── test_camera.py           # Camera diagnostic utility (tests indices 0-3)
├── start_app.bat            # 1-Click Unified Full-Stack Launcher (Windows)
├── run_server.py            # FastAPI server launcher script
└── requirements.txt         # Pinned working Python dependencies
```

---

## 🚀 Running the Full-Stack Application

### Option A: 1-Click Unified Launch (Windows)
Simply double-click:
```
start_app.bat
```
This automatically launches both the **FastAPI Backend (Port 8000)** and the **React Vite Frontend (Port 5173)** in separate terminal windows.

### Option B: Manual Terminal Launch

#### Terminal 1 — Backend:
```powershell
cd C:\Users\jeeva\.gemini\antigravity-ide\scratch\cloud-attendance
.venv\Scripts\python.exe run_server.py
```
*API running at [http://127.0.0.1:8000](http://127.0.0.1:8000) (Interactive Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs))*

#### Terminal 2 — Frontend:
```powershell
cd C:\Users\jeeva\.gemini\antigravity-ide\scratch\cloud-attendance\frontend
cmd /c "npm run dev"
```
*Dashboard running at [http://localhost:5173](http://localhost:5173)*

### Default Demo Faculty Login
- **Email:** `faculty@college.edu`
- **Password:** `Password123!`
*(Or click the "Demo Faculty Quick-Login" button on the login screen for instant 1-click access!)*

---

## ☁️ Connecting to Supabase Cloud (Optional Production Mode)

1. Open your [Supabase Dashboard](https://supabase.com).
2. Create a new project.
3. In the **SQL Editor**, paste and run the contents of [`database/schema.sql`](database/schema.sql). This enables `pgvector` and builds the tables.
4. Copy your PostgreSQL connection string from **Project Settings -> Database -> Connection string (URI)**.
5. In `cloud-attendance/.env`, paste your URI:
   ```env
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
6. Restart the backend!

---

## 🧪 Automated Test Suite (100% Passing)

Run the complete test suite:
```powershell
.venv\Scripts\pytest.exe -v
```
Output:
```
tests/test_api.py::test_health_and_root PASSED                           [ 12%]
tests/test_api.py::test_auth_and_jwt_workflow PASSED                     [ 25%]
tests/test_api.py::test_student_management_and_embedding_enrollment PASSED [ 37%]
tests/test_api.py::test_session_lifecycle_and_attendance_flow PASSED     [ 50%]
tests/test_api.py::test_analytics_and_csv_export PASSED                  [ 62%]
tests/test_pipeline.py::test_face_engine_initialization PASSED           [ 75%]
tests/test_pipeline.py::test_matcher_cosine_similarity PASSED            [ 87%]
tests/test_pipeline.py::test_liveness_ear_calculation PASSED             [100%]
======================== 8 passed in 3.46s ========================
```
