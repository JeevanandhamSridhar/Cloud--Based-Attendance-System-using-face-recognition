# Comprehensive Beginner Guide: How to Use the FastAPI Backend

Welcome to the backend documentation for the **Cloud-Based Smart Attendance System**. This guide is written specifically for developers, students, and examiners who want to understand, run, and test the FastAPI backend service from scratch.

---

## 1. What is FastAPI and How Does It Fit into This Project?

**FastAPI** is a high-performance, asynchronous Python web framework used to build modern RESTful Application Programming Interfaces (APIs). In this project, the system is architected with a decoupled Client-Server model:

```
┌──────────────────────────────────────┐          HTTP REST Requests          ┌──────────────────────────────────────────────┐
│          Frontend (React 18)         │ ───────────────────────────────────> │              Backend (FastAPI)               │
│        http://localhost:5173         │ <─────────────────────────────────── │            http://127.0.0.1:8000             │
└──────────────────────────────────────┘            JSON Responses            └──────────────────────────────────────────────┘
                                                                                                     │
                                                       ┌─────────────────────────────────────────────┴─────────────────────────────────────────────┐
                                                       ▼                                                                                           ▼
                                        ┌──────────────────────────────┐                                                            ┌──────────────────────────────┐
                                        │       AI Vision Engine       │                                                            │      Relational Database     │
                                        │  • SCRFD 512-D Face Detector │                                                            │  • SQLite (attendance.db)    │
                                        │  • MediaPipe FaceMesh Liveness│                                                           │  • User, Student, Session,   │
                                        │  • YCrCb Kerchief/Mask Guard │                                                            │    Attendance, Truancy logs  │
                                        └──────────────────────────────┘                                                            └──────────────────────────────┘
```

- **Frontend (Port 5173):** Built with React 18, Vite, and TailwindCSS. It provides the visual dashboard, camera scanner viewfinder, and forms.
- **Backend (Port 8000):** Built with FastAPI and Python 3.11. It receives requests, verifies JWT security tokens, runs the computer vision algorithms, and persists records into the database (`attendance.db`).

---

## 2. How to Start the FastAPI Backend

### Prerequisites
Make sure your Python virtual environment (`.venv`) is activated.

### Step 1: Open a Terminal in the Project Folder
```powershell
cd C:\Users\jeeva\.gemini\antigravity-ide\scratch\cloud-attendance
```

### Step 2: Start the Server
Run the startup script:
```powershell
.\.venv\Scripts\python.exe run_server.py
```
*Alternatively, you can run uvicorn directly:*
```powershell
.\.venv\Scripts\uvicorn.exe backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Confirm it is Running
When the server starts successfully, your terminal will display:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
[Startup] Seeded default course: CS301 - Data Structures & Algorithms
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

You can now open `http://127.0.0.1:8000/health` in your browser. It should return:
```json
{"status": "healthy"}
```

---

## 3. The Interactive Swagger API Documentation (`/docs`)

FastAPI has a built-in feature: **automatic interactive documentation**. You do not need Postman or third-party tools to test the API.

1. Open your web browser (Chrome, Edge, Firefox).
2. Go to: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
3. You will see a complete graphical dashboard listing every route categorized into 5 groups:
   - **Authentication (`/api/auth`)**
   - **Student Management (`/api/students`)**
   - **Course & Sessions (`/api/sessions`)**
   - **Attendance Scanner (`/api/attendance`)**
   - **Analytics & Truancy (`/api/analytics`)**

*(Alternative view: Redoc is available at `http://127.0.0.1:8000/redoc`)*

---

## 4. Step-by-Step Tutorial: How to Test Any Endpoint in Swagger UI

Most API routes in this project require you to be authenticated as a Faculty member. Here is how to log in:

### Step 1: Authorize (Log In) in Swagger UI
1. Scroll to the top right of the Swagger UI page and click the green **`Authorize`** button (with a padlock icon 🔓).
2. A popup window will appear with fields:
   - **username:** `faculty@college.edu`
   - **password:** `Password123!`
3. Click the **Authorize** button inside the popup.
4. Click **Close**. The padlock icon is now locked 🔒. All your requests in Swagger UI will now automatically send your JWT Bearer token!

### Step 2: Test an Endpoint (e.g., Get All Students)
1. In the documentation, click on the **`GET /api/students`** bar to expand it.
2. Click the **`Try it out`** button on the right.
3. Click the blue **`Execute`** button.
4. Scroll down slightly to see the **Server Response**:
   - **Code:** `200` (Success)
   - **Response body:** `[]` (Initially empty because you start from scratch!)

---

## 5. Complete API Endpoints Reference

### 🔐 Category 1: Authentication (`/api/auth`)

| Method | Endpoint | Description | Requires Auth? |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Log in with email & password; returns a JWT access token. | No |
| `POST` | `/api/auth/register` | Register a new faculty/admin account. | No |
| `GET` | `/api/auth/me` | Fetch details of the currently logged-in user. | **Yes** (Bearer Token) |

#### Example: Logging in via `POST /api/auth/login`
**Request Body:**
```json
{
  "email": "faculty@college.edu",
  "password": "Password123!"
}
```
**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "faculty@college.edu",
    "full_name": "Dr. Alexander Reed (Faculty Admin)",
    "role": "faculty"
  }
}
```

---

### 👨‍🎓 Category 2: Student Management (`/api/students`)

| Method | Endpoint | Description | Requires Auth? |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/students` | List all students in the database. | **Yes** |
| `POST` | `/api/students` | Create a new student record (profile only). | **Yes** |
| `GET` | `/api/students/{student_id}` | Fetch a specific student's details. | **Yes** |
| `POST` | `/api/students/{student_id}/enroll-face` | Enroll a student's facial biometric vector. | **Yes** |
| `DELETE` | `/api/students/{student_id}` | **Permanently delete** a student, their face vector, and history. | **Yes** |

#### Example: Creating a Student via `POST /api/students`
**Request Body:**
```json
{
  "student_id": "23CS101",
  "name": "Jane Doe",
  "department": "Computer Science",
  "year": 3,
  "section": "A",
  "email": "jane.doe@college.edu"
}
```
**Response (201 Created):**
```json
{
  "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "student_id": "23CS101",
  "name": "Jane Doe",
  "department": "Computer Science",
  "year": 3,
  "section": "A",
  "email": "jane.doe@college.edu",
  "has_face_registered": false,
  "created_at": "2026-09-25T14:40:00"
}
```

#### Example: Deleting a Student via `DELETE /api/students/{student_id}`
You can pass either the UUID (`9b1deb4d-...`) or the Roll Number (`23CS101`):
```
DELETE /api/students/23CS101
```
**Response (200 OK):**
```json
{
  "success": true,
  "message": "Student 'Jane Doe' permanently removed from system."
}
```
*Note: This permanently deletes the student from SQLite, removes their face embedding from `data/embeddings.json`, and clears any cached vectors. They will never reappear on refresh or reboot.*

---

### 📚 Category 3: Courses & Class Sessions (`/api/sessions`)

| Method | Endpoint | Description | Requires Auth? |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/sessions/subjects` | List academic subjects / courses. | **Yes** |
| `POST` | `/api/sessions/subjects` | Create a new subject (e.g., CS302 Machine Learning). | **Yes** |
| `POST` | `/api/sessions` | Schedule a class lecture session. | **Yes** |
| `GET` | `/api/sessions/active` | Get the currently active/ongoing class session. | **Yes** |
| `POST` | `/api/sessions/{session_id}/end` | End an ongoing class lecture session. | **Yes** |

#### Example: Starting a Class Session via `POST /api/sessions`
**Request Body:**
```json
{
  "subject_id": "<subject-uuid>",
  "room": "Room-304",
  "start_time": "2026-09-25T10:00:00",
  "end_time": "2026-09-25T11:00:00"
}
```

---

### 📷 Category 4: Attendance Scanner Engine (`/api/attendance`)

| Method | Endpoint | Description | Requires Auth? |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/attendance/scan-frame` | Real-time computer vision inference endpoint. | **Yes** |
| `POST` | `/api/attendance/campus/mark` | Record daily Campus Main Gate entry. | **Yes** |
| `GET` | `/api/attendance/campus/today` | Fetch today's campus gate arrival log. | **Yes** |
| `GET` | `/api/attendance/session/{session_id}` | Fetch AttenFace continuous presence scores for a lecture. | **Yes** |

#### What Happens Inside `POST /api/attendance/scan-frame`?
When the React frontend captures a camera frame, it sends a Base64-encoded image:
1. **SCRFD Detection:** Detects face bounding boxes on CPU in ~28ms.
2. **MediaPipe FaceMesh:** Calculates 468 landmarks and Eye Aspect Ratio (EAR) blink rate. If static photo detected, flags spoofing.
3. **YCrCb Skin Chrominance Occlusion:** Checks lower face for handkerchief, kerchief, or medical mask. If occluded, applies adaptive periocular threshold ($0.38$) and sets bounding box HUD to Electric Cyan.
4. **ArcFace Embedding:** Generates 512-D unit hyper-sphere vector.
5. **Continuous Scoring:** Increments presence checkpoint and recalculates presence percentage ($P_s = \frac{C_{\text{detected}}}{N_{\text{elapsed}}} \times 100\%$).

---

### 📊 Category 5: Analytics & Truancy Engine (`/api/analytics`)

| Method | Endpoint | Description | Requires Auth? |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/analytics/dashboard` | Returns overall summary stats (students, sessions, avg presence). | **Yes** |
| `GET` | `/api/analytics/bunking-report` | **Dual-Tier Truancy Audit:** Compares campus entries vs class sessions to detect bunking. | **Yes** |
| `GET` | `/api/analytics/export/csv/{session_id}` | Download official academic CSV attendance register. | **Yes** |

#### Example: Dual-Tier Bunking Audit via `GET /api/analytics/bunking-report?session_id=<session_id>`
**Response:**
```json
[
  {
    "student_id": "23CS101",
    "name": "Jane Doe",
    "campus_status": "ENTERED_CAMPUS",
    "gate_entry_time": "08:45 AM",
    "class_status": "ABSENT_IN_CLASS",
    "truancy_status": "BUNKING_CLASS",
    "alert_level": "CRITICAL"
  }
]
```

---

## 6. How to Test the API using Python (Script Example)

You can interact with FastAPI from any Python script. Here is an end-to-end example:

```python
import requests

BASE_URL = "http://127.0.0.1:8000/api"

# 1. Log in to get the JWT token
login_data = {
    "email": "faculty@college.edu",
    "password": "Password123!"
}
res = requests.post(f"{BASE_URL}/auth/login", json=login_data)
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Successfully logged in! Token acquired.")

# 2. Add a new student
new_student = {
    "student_id": "23CS105",
    "name": "David Miller",
    "department": "Computer Science",
    "year": 3,
    "section": "A",
    "email": "david.cs@college.edu"
}
st_res = requests.post(f"{BASE_URL}/students", json=new_student, headers=headers)
student = st_res.json()
print("Created Student:", student["name"], "ID:", student["id"])

# 3. List all students
list_res = requests.get(f"{BASE_URL}/students", headers=headers)
print("Total Students in Registry:", len(list_res.json()))

# 4. Delete the student
del_res = requests.delete(f"{BASE_URL}/students/{student['id']}", headers=headers)
print("Delete Response:", del_res.json()["message"])
```

---

## 7. How to Test the API using Terminal cURL

### Log in and get token:
```bash
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d "{\"email\":\"faculty@college.edu\",\"password\":\"Password123!\"}"
```

### List all students (using the token returned from above):
```bash
curl -X GET "http://127.0.0.1:8000/api/students" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 8. Summary of Key Architectural Features

1. **Zero Raw Photo Storage:** Raw images sent to `/api/attendance/scan-frame` or `/api/students/{id}/enroll-face` are processed strictly in volatile RAM, converted to 512-D float vectors, and immediately discarded.
2. **Permanent Deletions:** Calling `DELETE /api/students/{id}` immediately cleans SQLite, purges `data/embeddings.json`, and removes face matcher cache.
3. **Zero Automatic Seeding:** The system starts clean. You add students and courses when you want, and deleted students never resurrect.
4. **CORS Enabled:** Cross-Origin Resource Sharing is enabled for `http://localhost:5173`, `http://localhost:3000`, and all standard development ports.
