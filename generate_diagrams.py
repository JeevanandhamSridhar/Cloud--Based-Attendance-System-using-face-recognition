import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "reports_export", "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------------------------------------------
# FIGURE 1: 4-TIER END-TO-END SYSTEM ARCHITECTURE
# -------------------------------------------------------------
def generate_fig1_architecture():
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=300)
    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("#ffffff")
    ax.axis('off')

    plt.title("Cloud-Based Smart Attendance System: 4-Tier End-to-End Architecture", 
              fontsize=15, fontweight='bold', pad=20, color="#0f172a")

    # Colors
    c_client = "#e0e7ff" # Indigo light
    c_client_b = "#4338ca"
    c_api = "#dcfce7"    # Emerald light
    c_api_b = "#047857"
    c_ai = "#fef3c7"     # Amber light
    c_ai_b = "#b45309"
    c_data = "#f1f5f9"   # Slate light
    c_data_b = "#334155"

    def draw_box(x, y, w, h, title, items, bg_col, border_col, title_col):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.04",
                                      facecolor=bg_col, edgecolor=border_col, linewidth=2, zorder=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h - 0.06, title, fontsize=11, fontweight='bold', color=title_col,
                ha='center', va='top', zorder=3)
        y_text = y + h - 0.12
        for it in items:
            ax.text(x + 0.03, y_text, f"• {it}", fontsize=9, color="#1e293b", va='top', zorder=3)
            y_text -= 0.055

    # Tier 1: Client Tier
    draw_box(0.04, 0.52, 0.42, 0.38, "1. Client Presentation Tier (React 18 + Vite)", [
        "HTML5 getUserMedia Video Camera Feed (1280x720)",
        "Offscreen Frame Capture & Base64 Ingestion Canvas",
        "Direct Left-to-Right Bounding Box HUD Overlay",
        "Dual Modes: Main Campus Gate vs Classroom Lecture",
        "Faculty Review Queue & Truancy Discrepancy View",
        "Axios REST Client with JWT Bearer Interceptors"
    ], c_client, c_client_b, c_client_b)

    # Tier 2: Application API Tier
    draw_box(0.54, 0.52, 0.42, 0.38, "2. Application & API Tier (FastAPI Async)", [
        "Asynchronous Non-Blocking REST API (Uvicorn)",
        "OAuth2 Password Bearer Security & Direct bcrypt Hash",
        "Lifespan Context Manager & DB Auto-Migrations",
        "AttenFace Continuous Presence Dynamic Scorer",
        "Dual-Tier Truancy & Bunking Correlation Matrix",
        "Institutional CSV Sheet Streamer & Analytics Engine"
    ], c_api, c_api_b, c_api_b)

    # Tier 3: AI Computer Vision Core
    draw_box(0.04, 0.08, 0.42, 0.38, "3. Biometric Computer Vision Pipeline", [
        "InsightFace SCRFD Face Detector (buffalo_sc)",
        "MobileFaceNet ArcFace 512-D Unit Hypersphere Embedder",
        "MediaPipe FaceMesh 468 3D Landmarks EAR Liveness",
        "Temporal EAR Variance (< 0.00008 Rejects Static Spoofs)",
        "Biological YCrCb Chrominance Lower-Face Occlusion Guard",
        "Adaptive Periocular Threshold (0.38 for Mask/Kerchief)"
    ], c_ai, c_ai_b, c_ai_b)

    # Tier 4: Data Tier
    draw_box(0.54, 0.08, 0.42, 0.38, "4. Persistence Tier (Dual Engine Architecture)", [
        "Local Engine: SQLite (attendance.db) Zero-Config",
        "Cloud Engine: Supabase PostgreSQL with pgvector",
        "HNSW Approximate Nearest Neighbor (ANN) Cosine Index",
        "Privacy by Design: Zero Raw Photo Storage (Vectors Only)",
        "Daily Campus Attendance & Lecture Attendance Tables",
        "Borderline Verification Queue (48% - 60% Confidence)"
    ], c_data, c_data_b, c_data_b)

    # Connectors
    # Client -> API
    ax.annotate("", xy=(0.54, 0.71), xytext=(0.46, 0.71),
                arrowprops=dict(arrowstyle="->", color="#3b82f6", lw=2.5, mutation_scale=15))
    ax.text(0.50, 0.73, "POST /scan-frame\n(base64 frame)", fontsize=8, color="#1e40af", ha='center', fontweight='bold')

    # API -> AI Core
    ax.annotate("", xy=(0.25, 0.46), xytext=(0.75, 0.52),
                arrowprops=dict(arrowstyle="->", color="#d97706", lw=2.5, mutation_scale=15, connectionstyle="arc3,rad=-0.15"))
    ax.text(0.50, 0.47, "Extract 512-D Vectors + Liveness + Occlusion", fontsize=8, color="#92400e", ha='center', fontweight='bold')

    # AI Core -> Data
    ax.annotate("", xy=(0.54, 0.27), xytext=(0.46, 0.27),
                arrowprops=dict(arrowstyle="->", color="#059669", lw=2.5, mutation_scale=15))
    ax.text(0.50, 0.29, "Cosine Match\n(pgvector/SQL)", fontsize=8, color="#065f46", ha='center', fontweight='bold')

    # Data -> API
    ax.annotate("", xy=(0.75, 0.52), xytext=(0.75, 0.46),
                arrowprops=dict(arrowstyle="->", color="#334155", lw=2.0, mutation_scale=15))

    path = os.path.join(OUTPUT_DIR, "fig1_system_architecture.png")
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"Generated {path}")

# -------------------------------------------------------------
# FIGURE 2: DUAL-TIER TRUANCY & BUNKING DETECTION ENGINE
# -------------------------------------------------------------
def generate_fig2_truancy():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("#ffffff")
    ax.axis('off')

    plt.title("Dual-Tier Attendance Hierarchy & Automated Truancy/Bunking Detection Engine", 
              fontsize=14, fontweight='bold', pad=18, color="#0f172a")

    # Step 1: Input Scan
    rect1 = patches.FancyBboxPatch((0.05, 0.65), 0.26, 0.22, boxstyle="round,pad=0.02",
                                   facecolor="#ede9fe", edgecolor="#6d28d9", linewidth=2)
    ax.add_patch(rect1)
    ax.text(0.18, 0.81, "Student Biometric Scan", fontsize=11, fontweight='bold', color="#5b21b6", ha='center')
    ax.text(0.07, 0.75, "• SCRFD Face Detection\n• MobileFaceNet ArcFace 512-D\n• MediaPipe Liveness Verified", fontsize=9, color="#1e293b")

    # Tier 1 Branch
    rect2 = patches.FancyBboxPatch((0.40, 0.75), 0.28, 0.18, boxstyle="round,pad=0.02",
                                   facecolor="#e0f2fe", edgecolor="#0284c7", linewidth=2)
    ax.add_patch(rect2)
    ax.text(0.54, 0.88, "Tier 1: Main Campus Gate", fontsize=10, fontweight='bold', color="#0369a1", ha='center')
    ax.text(0.42, 0.83, "• session_id = 'campus_gate'\n• Records DailyCampusAttendance\n• First Entry Time: e.g. 08:42 AM\n• Gate Status = 'present'", fontsize=8.5, color="#1e293b")

    # Tier 2 Branch
    rect3 = patches.FancyBboxPatch((0.40, 0.50), 0.28, 0.18, boxstyle="round,pad=0.02",
                                   facecolor="#fef3c7", edgecolor="#d97706", linewidth=2)
    ax.add_patch(rect3)
    ax.text(0.54, 0.63, "Tier 2: Classroom Lecture", fontsize=10, fontweight='bold', color="#b45309", ha='center')
    ax.text(0.42, 0.58, "• session_id = Lecture UUID\n• AttenFace Checkpoints (5 min)\n• Presence % Calculation\n• Auto-Credits Campus Presence", fontsize=8.5, color="#1e293b")

    # Truancy Engine Core
    rect4 = patches.FancyBboxPatch((0.74, 0.50), 0.23, 0.43, boxstyle="round,pad=0.02",
                                   facecolor="#fee2e2", edgecolor="#b91c1c", linewidth=2)
    ax.add_patch(rect4)
    ax.text(0.855, 0.88, "Truancy Correlation Matrix", fontsize=10, fontweight='bold', color="#991b1b", ha='center')
    ax.text(0.76, 0.82, "For each student today:\nT(i, s, d) =", fontsize=9, fontweight='bold', color="#7f1d1d")
    ax.text(0.76, 0.73, "1. Gate: 1 & Class: 1\n   -> ATTENDING_CLASS\n   (Normal Attendance)", fontsize=8, color="#065f46")
    ax.text(0.76, 0.62, "2. Gate: 1 & Class: 0\n   -> BUNKING_CLASS!\n   (On Campus, Skipped Class)", fontsize=8, fontweight='bold', color="#991b1b")
    ax.text(0.76, 0.53, "3. Gate: 0 & Class: 0\n   -> FULL_DAY_ABSENT\n   (Never entered campus)", fontsize=8, color="#475569")

    # Arrows
    ax.annotate("", xy=(0.40, 0.84), xytext=(0.31, 0.78),
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2))
    ax.annotate("", xy=(0.40, 0.59), xytext=(0.31, 0.74),
                arrowprops=dict(arrowstyle="->", color="#d97706", lw=2))
    ax.annotate("", xy=(0.74, 0.80), xytext=(0.68, 0.84),
                arrowprops=dict(arrowstyle="->", color="#334155", lw=2))
    ax.annotate("", xy=(0.74, 0.62), xytext=(0.68, 0.59),
                arrowprops=dict(arrowstyle="->", color="#334155", lw=2))

    # Bottom Discrepancy Actions Table
    table_y = 0.08
    ax.text(0.05, 0.38, "Real-Time Actionable Enforcement Workflow:", fontsize=11, fontweight='bold', color="#0f172a")

    rect5 = patches.FancyBboxPatch((0.05, 0.06), 0.90, 0.28, boxstyle="round,pad=0.02",
                                   facecolor="#ffffff", edgecolor="#cbd5e1", linewidth=1.5)
    ax.add_patch(rect5)

    headers = ["Condition Detected", "System Classification", "Dashboard & Roster Display", "Automated Administrative Action"]
    col_x = [0.08, 0.28, 0.50, 0.74]
    for x, h in zip(col_x, headers):
        ax.text(x, 0.29, h, fontsize=9.5, fontweight='bold', color="#1e293b")

    rows = [
        ("Entered Gate (08:45 AM) & Attended Class", "ATTENDING_CLASS", "[NORMAL] Green: Present (90%)", "Attendance credited normally"),
        ("Entered Gate (08:45 AM) & Skipped CS301", "BUNKING_CLASS", "[ALERT] Rose: Bunking Flagged", "Alert SMS to Warden & Parents; Flagged in CSV"),
        ("No Gate Record & Missed All Classes", "FULL_DAY_ABSENT", "[ABSENT] Slate: Full Day Absent", "Recorded as absent in university ERP"),
        ("Missed Gate & Entered Class Directly", "ATTENDING_CLASS", "[AUTO-CREDIT] In Class (Gate Synced)", "System ensures daily campus status = present")
    ]
    y_row = 0.24
    for r in rows:
        c = "#991b1b" if "BUNKING" in r[1] else "#065f46" if "ATTENDING" in r[1] else "#475569"
        ax.text(col_x[0], y_row, r[0], fontsize=8, color="#334155")
        ax.text(col_x[1], y_row, r[1], fontsize=8, fontweight='bold', color=c)
        ax.text(col_x[2], y_row, r[2], fontsize=8, color="#334155")
        ax.text(col_x[3], y_row, r[3], fontsize=8, color="#1e293b")
        y_row -= 0.05

    path = os.path.join(OUTPUT_DIR, "fig2_dual_tier_truancy.png")
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"Generated {path}")

# -------------------------------------------------------------
# FIGURE 3: ATTENFACE CONTINUOUS PRESENCE TIMELINE
# -------------------------------------------------------------
def generate_fig3_attenface():
    fig, ax = plt.subplots(figsize=(13, 6.5), dpi=300)
    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("#ffffff")
    ax.axis('off')

    plt.title("AttenFace Continuous Presence Validation: Dynamic Elapsed Checkpoints & 5-Min Grace Window", 
              fontsize=13, fontweight='bold', pad=18, color="#0f172a")

    # Time Axis Line
    ax.plot([0.08, 0.92], [0.65, 0.65], color="#475569", lw=3, zorder=1)

    # Markers for checkpoints: -15m, 0m (Start), 5m, 10m, 15m, 20m, 25m, 30m, 60m (End)
    points = [
        (0.12, "-15 min\nPre-Lecture", "#6366f1", "Early Arrival\nGrandfathered"),
        (0.24, "0 min\nLecture Start", "#059669", "Interval 0\nActivated"),
        (0.36, "5 min\nCheckpoint 1", "#059669", "Detected\n(Presence 100%)"),
        (0.48, "10 min\nCheckpoint 2", "#0284c7", "Wiping Face / Mask\n(Grace Window Active)"),
        (0.60, "15 min\nCheckpoint 3", "#059669", "Periocular Match\n(Presence 100%)"),
        (0.72, "20 min\nCheckpoint 4", "#dc2626", "Student Left Room\n(Drop to Partial)"),
        (0.88, "60 min\nLecture End", "#1e293b", "Final Score Locked\n& Exported")
    ]

    for x, label, color, annot in points:
        ax.scatter([x], [0.65], color=color, s=200, zorder=3, edgecolors="#ffffff", linewidth=2)
        ax.text(x, 0.70, label, ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=color)
        ax.text(x, 0.58, annot, ha='center', va='top', fontsize=7.5, color="#334155")

    # Formula Box
    rect = patches.FancyBboxPatch((0.08, 0.08), 0.84, 0.38, boxstyle="round,pad=0.03",
                                  facecolor="#eff6ff", edgecolor="#3b82f6", linewidth=1.5)
    ax.add_patch(rect)

    ax.text(0.50, 0.40, "Mathematical Formulation of Dynamic Checkpoint Denominator", 
            ha='center', fontsize=11, fontweight='bold', color="#1e3a8a")
    ax.text(0.12, 0.32, r"Elapsed Checkpoints:  $K(t) = \max\left(1, \left\lfloor\frac{t - t_{\mathrm{start}}}{I}\right\rfloor + 1\right)$", 
            fontsize=10.5, color="#1e293b")
    ax.text(0.12, 0.24, r"Continuous Presence Score:  $P(t) = \min\left(100.0, \frac{\text{Distinct Detected Intervals}}{\min(K(t), N_{\mathrm{total}})} \times 100\%\right)$", 
            fontsize=10.5, color="#1e293b")
    ax.text(0.12, 0.16, "Institutional Criteria:  Present (>= 75%) | Partial (50% - 74%) | Absent (< 50%)", 
            fontsize=10, fontweight='bold', color="#047857")
    ax.text(0.12, 0.10, "Temporal Hysteresis Grace Window: If last seen <= 5 mins ago, attendance is maintained at Present.", 
            fontsize=8.5, fontstyle='italic', color="#475569")

    path = os.path.join(OUTPUT_DIR, "fig3_attenface_checkpoints.png")
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"Generated {path}")

# -------------------------------------------------------------
# FIGURE 4: LIVENESS & OCCLUSION BIOMETRIC PIPELINES
# -------------------------------------------------------------
def generate_fig4_liveness_occlusion():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    for ax in [ax1, ax2]:
        ax.set_facecolor("#f8fafc")
        ax.axis('off')

    # Subplot 1: Anti-Spoofing
    ax1.set_title("A. Dual-Tier Anti-Spoofing Architecture", fontsize=11, fontweight='bold', pad=12, color="#0f172a")
    
    stages1 = [
        ("Input Video Frame", "1280x720 RGB stream from webcam", "#f1f5f9", "#475569"),
        ("MediaPipe FaceMesh", "Tracks 468 3D facial landmarks in real time", "#e0e7ff", "#4338ca"),
        ("Eye Aspect Ratio (EAR)", r"EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)", "#fef3c7", "#b45309"),
        ("Tier 1: Blink Cycle Test", "Blink cycle: open -> EAR < 0.20 -> EAR > 0.24", "#dcfce7", "#059669"),
        ("Tier 2: EAR Variance Check", "Var(EAR) < 0.00008 across 25 frames = STATIC PHOTO", "#fee2e2", "#dc2626"),
        ("Decision Output", "LIVE HUMAN (Green HUD) vs SPOOF ATTACK (Rejected)", "#ffffff", "#0f172a")
    ]
    y = 0.85
    for title, desc, bg, border in stages1:
        rect = patches.FancyBboxPatch((0.05, y), 0.90, 0.11, boxstyle="round,pad=0.02",
                                      facecolor=bg, edgecolor=border, linewidth=1.5)
        ax1.add_patch(rect)
        ax1.text(0.08, y + 0.07, title, fontsize=9.5, fontweight='bold', color=border)
        ax1.text(0.08, y + 0.025, desc, fontsize=7.5, color="#1e293b")
        if y > 0.15:
            ax1.annotate("", xy=(0.50, y - 0.03), xytext=(0.50, y),
                         arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.5))
        y -= 0.15

    # Subplot 2: Occlusion Guard
    ax2.set_title("B. Biological YCrCb Skin Occlusion Guard", fontsize=11, fontweight='bold', pad=12, color="#0f172a")
    
    stages2 = [
        ("Face Bounding Box Crop", "Detected face from SCRFD detector", "#f1f5f9", "#475569"),
        ("Spatial Anatomical Split", "Upper 45% (Forehead/Eyes) vs Lower 45% (Mouth/Nose)", "#e0f2fe", "#0284c7"),
        ("YCrCb Chrominance Segmentation", "Skin range: 133 <= Cr <= 173 and 77 <= Cb <= 127", "#fef3c7", "#b45309"),
        ("Lower Skin Ratio Evaluation", "Lower Skin Ratio < 22% -> Handkerchief / Mask detected", "#fee2e2", "#dc2626"),
        ("Adaptive Periocular Match", "Lowers cosine threshold from 0.48 to 0.38 for eyes", "#dcfce7", "#059669"),
        ("Cyan HUD Box & Presence", "Maintains presence; attendance score never drops", "#ecfeff", "#0891b2")
    ]
    y = 0.85
    for title, desc, bg, border in stages2:
        rect = patches.FancyBboxPatch((0.05, y), 0.90, 0.11, boxstyle="round,pad=0.02",
                                      facecolor=bg, edgecolor=border, linewidth=1.5)
        ax2.add_patch(rect)
        ax2.text(0.08, y + 0.07, title, fontsize=9.5, fontweight='bold', color=border)
        ax2.text(0.08, y + 0.025, desc, fontsize=7.5, color="#1e293b")
        if y > 0.15:
            ax2.annotate("", xy=(0.50, y - 0.03), xytext=(0.50, y),
                         arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.5))
        y -= 0.15

    path = os.path.join(OUTPUT_DIR, "fig4_liveness_occlusion.png")
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"Generated {path}")

# -------------------------------------------------------------
# FIGURE 5: DATABASE ER SCHEMA
# -------------------------------------------------------------
def generate_fig5_er_diagram():
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("#ffffff")
    ax.axis('off')

    plt.title("Relational Database Entity-Relationship (ER) Schema with Daily Campus Gate Tracking", 
              fontsize=13, fontweight='bold', pad=18, color="#0f172a")

    def draw_entity(x, y, w, h, table_name, fields, color):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                      facecolor="#ffffff", edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        header = patches.Rectangle((x, y + h - 0.05), w, 0.05, facecolor=color)
        ax.add_patch(header)
        ax.text(x + w/2, y + h - 0.03, table_name, fontsize=9.5, fontweight='bold', color="#ffffff", ha='center', va='center')
        
        y_f = y + h - 0.08
        for f in fields:
            ax.text(x + 0.015, y_f, f, fontsize=7.5, color="#1e293b", va='top')
            y_f -= 0.032

    # Entities
    draw_entity(0.03, 0.55, 0.26, 0.35, "STUDENTS", [
        "PK  id (UUID / String)",
        "UK  student_id (Roll No)",
        "    name (Full Name)",
        "    department (Branch)",
        "    year, section",
        "UK  email",
        "    status ('active')",
        "    created_at (Timestamp)"
    ], "#3b82f6")

    draw_entity(0.03, 0.08, 0.26, 0.38, "DAILY_CAMPUS_ATTENDANCE", [
        "PK  id (UUID / String)",
        "FK  student_id -> STUDENTS",
        "UK  (student_id, date)",
        "    date (YYYY-MM-DD)",
        "    status ('present' / 'absent')",
        "    first_entry_time",
        "    last_seen_time",
        "    entry_gate ('gate_1')"
    ], "#0284c7")

    draw_entity(0.36, 0.55, 0.26, 0.35, "FACE_EMBEDDINGS", [
        "PK  id (UUID / String)",
        "FK  student_id -> STUDENTS",
        "    embedding_json (512-D float)",
        "    model_version ('buffalo_sc')",
        "    sample_count (5-shot)",
        "    is_primary (Boolean)",
        "    created_at (Timestamp)"
    ], "#8b5cf6")

    draw_entity(0.70, 0.55, 0.27, 0.38, "CLASS_SESSIONS", [
        "PK  id (UUID / String)",
        "FK  subject_id -> SUBJECTS",
        "FK  faculty_id -> USERS",
        "    room ('Lab 3 / Room 101')",
        "    start_time, end_time",
        "    status ('scheduled'/'active')",
        "    checkpoint_interval_mins (5)",
        "    min_presence_percentage (75%)"
    ], "#10b981")

    draw_entity(0.36, 0.08, 0.28, 0.40, "ATTENDANCE", [
        "PK  id (UUID / String)",
        "FK  session_id -> CLASS_SESSIONS",
        "FK  student_id -> STUDENTS",
        "    status ('present'/'partial'/'absent')",
        "    presence_score (Float %)",
        "    confidence_avg (Float)",
        "    face_visibility_score (Float)",
        "    occlusion_count (Int)",
        "    checkpoints_detected / total",
        "    verified_by_faculty (Boolean)"
    ], "#f59e0b")

    draw_entity(0.70, 0.08, 0.27, 0.40, "ATTENDANCE_EVENTS", [
        "PK  id (UUID / String)",
        "FK  session_id -> CLASS_SESSIONS",
        "FK  student_id -> STUDENTS",
        "    timestamp (Datetime)",
        "    confidence (Cosine similarity)",
        "    is_live (Boolean)",
        "    ear_value (Float)",
        "    is_occluded (Boolean)",
        "    occlusion_type ('mask'/'kerchief')",
        "    visibility_score (Float)"
    ], "#ef4444")

    # Connectors
    # STUDENTS -> DAILY_CAMPUS_ATTENDANCE
    ax.annotate("", xy=(0.16, 0.46), xytext=(0.16, 0.55),
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2))
    ax.text(0.18, 0.50, "1:N (Daily Gate Logs)", fontsize=8, color="#0369a1")

    # STUDENTS -> FACE_EMBEDDINGS
    ax.annotate("", xy=(0.36, 0.72), xytext=(0.29, 0.72),
                arrowprops=dict(arrowstyle="->", color="#8b5cf6", lw=2))
    ax.text(0.31, 0.74, "1:1", fontsize=8, color="#6d28d9")

    # STUDENTS -> ATTENDANCE
    ax.annotate("", xy=(0.36, 0.28), xytext=(0.29, 0.60),
                arrowprops=dict(arrowstyle="->", color="#f59e0b", lw=2, connectionstyle="arc3,rad=-0.1"))
    
    # CLASS_SESSIONS -> ATTENDANCE
    ax.annotate("", xy=(0.50, 0.48), xytext=(0.70, 0.65),
                arrowprops=dict(arrowstyle="->", color="#10b981", lw=2, connectionstyle="arc3,rad=0.1"))

    # ATTENDANCE -> ATTENDANCE_EVENTS
    ax.annotate("", xy=(0.70, 0.28), xytext=(0.64, 0.28),
                arrowprops=dict(arrowstyle="->", color="#ef4444", lw=2))
    ax.text(0.66, 0.30, "1:N", fontsize=8, color="#b91c1c")

    path = os.path.join(OUTPUT_DIR, "fig5_database_er.png")
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"Generated {path}")

if __name__ == "__main__":
    generate_fig1_architecture()
    generate_fig2_truancy()
    generate_fig3_attenface()
    generate_fig4_liveness_occlusion()
    generate_fig5_er_diagram()
    print("All 5 high-resolution figures generated successfully!")
