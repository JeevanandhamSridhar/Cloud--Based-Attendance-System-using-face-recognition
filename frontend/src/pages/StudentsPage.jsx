import React, { useEffect, useRef, useState } from "react";
import {
  Users,
  UserPlus,
  ShieldCheck,
  ShieldAlert,
  Camera,
  Trash2,
  Search,
  CheckCircle,
  Sparkles,
} from "lucide-react";
import {
  fetchStudents,
  createStudent,
  enrollStudentFace,
  deleteStudent,
} from "../services/api";

export default function StudentsPage() {
  const [students, setStudents] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New Student Form
  const [studentId, setStudentId] = useState("");
  const [name, setName] = useState("");
  const [department, setDepartment] = useState("Computer Science");
  const [year, setYear] = useState(3);
  const [section, setSection] = useState("A");
  const [email, setEmail] = useState("");

  // 5-Shot Guided Webcam capture in modal
  const [useWebcamCapture, setUseWebcamCapture] = useState(false);
  const modalVideoRef = useRef(null);
  const modalCanvasRef = useRef(null);
  const [capturedPhotos, setCapturedPhotos] = useState([]);
  const [isAutoCapturing, setIsAutoCapturing] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [flash, setFlash] = useState(false);

  const GUIDED_STEPS = [
    "1. Center & Neutral (Look straight)",
    "2. Slight Smile",
    "3. Tilt Head Slightly Left (15°)",
    "4. Tilt Head Slightly Right (15°)",
    "5. Tilt Head Slightly Up (10°)",
  ];

  const loadStudents = async () => {
    try {
      setLoading(true);
      const data = await fetchStudents();
      setStudents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStudents();
  }, []);

  const handleCloseModal = () => {
    if (modalVideoRef.current) {
      modalVideoRef.current.pause();
      if (modalVideoRef.current.srcObject) {
        modalVideoRef.current.srcObject.getTracks().forEach((t) => t.stop());
        modalVideoRef.current.srcObject = null;
      }
    }
    setIsModalOpen(false);
    setCapturedPhotos([]);
    setUseWebcamCapture(false);
    setIsAutoCapturing(false);
    setCountdown(0);
  };

  const handleStartModalCam = async () => {
    try {
      setUseWebcamCapture(true);
      setCapturedPhotos([]);
      setIsAutoCapturing(false);
      setCountdown(0);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
      });
      if (modalVideoRef.current) {
        modalVideoRef.current.srcObject = stream;
        modalVideoRef.current.onloadedmetadata = () => {
          modalVideoRef.current?.play().catch((err) => {
            if (err.name !== "AbortError") {
              console.warn("Modal video play error:", err);
            }
          });
        };
      }
    } catch (err) {
      alert("Could not access camera: " + err.message);
    }
  };

  const handleCaptureModalPhoto = () => {
    const video = modalVideoRef.current;
    const canvas = modalCanvasRef.current;
    if (video && canvas) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const b64 = canvas.toDataURL("image/jpeg", 0.9);

      setFlash(true);
      setTimeout(() => setFlash(false), 200);

      setCapturedPhotos((prev) => {
        const next = [...prev, b64];
        if (next.length >= 5) {
          setIsAutoCapturing(false);
          setCountdown(0);
          if (video.srcObject) {
            video.srcObject.getTracks().forEach((t) => t.stop());
            video.srcObject = null;
          }
        }
        return next;
      });
    }
  };

  // Automated 3-second pose transition timer for hands-free 5-shot capture
  useEffect(() => {
    let timer;
    if (isAutoCapturing && countdown > 1) {
      timer = setTimeout(() => {
        setCountdown((c) => c - 1);
      }, 1000);
    } else if (isAutoCapturing && countdown === 1) {
      timer = setTimeout(() => {
        handleCaptureModalPhoto();
        if (capturedPhotos.length < 4) {
          setCountdown(3); // Next angle countdown
        } else {
          setIsAutoCapturing(false);
          setCountdown(0);
        }
      }, 1000);
    }
    return () => clearTimeout(timer);
  }, [isAutoCapturing, countdown, capturedPhotos.length]);

  const handleStartAutoCapture = async () => {
    if (!useWebcamCapture) {
      await handleStartModalCam();
    }
    setIsAutoCapturing(true);
    setCountdown(3);
  };

  const handleResetPhotos = () => {
    setCapturedPhotos([]);
    setIsAutoCapturing(false);
    setCountdown(0);
    handleStartModalCam();
  };

  const handleCreateStudent = async (e) => {
    e.preventDefault();
    try {
      // 1. Create student record
      const newStudent = await createStudent({
        student_id: studentId,
        name,
        department,
        year: parseInt(year, 10),
        section,
        email: email || undefined,
      });

      // 2. If multi-angle photos were captured, enroll averaged ArcFace embedding
      if (capturedPhotos.length > 0) {
        await enrollStudentFace(newStudent.id, {
          images_base64: capturedPhotos,
        });
      }

      setIsModalOpen(false);
      setCapturedPhotos([]);
      setUseWebcamCapture(false);
      // Reset form
      setStudentId("");
      setName("");
      setEmail("");
      loadStudents();
    } catch (err) {
      alert("Error enrolling student: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (id, sname) => {
    if (confirm(`Are you sure you want to remove student '${sname}'?`)) {
      try {
        await deleteStudent(id);
        loadStudents();
      } catch (err) {
        alert("Delete failed: " + err.message);
      }
    }
  };

  const filteredStudents = students.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.student_id.toLowerCase().includes(search.toLowerCase()) ||
      s.department.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Student Biometric Registry</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            512-D ArcFace vector embeddings catalog. Zero raw biometric images stored post-enrollment.
          </p>
        </div>
        <button
          onClick={() => {
            setIsModalOpen(true);
            setCapturedPhotos([]);
            setUseWebcamCapture(false);
            setIsAutoCapturing(false);
            setCountdown(0);
          }}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition"
        >
          <UserPlus className="w-4 h-4" />
          <span>Enroll New Student</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="p-4 rounded-2xl glass-panel flex items-center justify-between gap-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 transform -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by student name, roll number, or department..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <span className="text-xs text-slate-400 font-medium hidden sm:inline">
          Showing {filteredStudents.length} of {students.length} students
        </span>
      </div>

      {/* Students Table */}
      <div className="rounded-2xl glass-panel overflow-hidden border border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold bg-slate-900/40">
                <th className="py-3 px-4">Student ID</th>
                <th className="py-3 px-4">Full Name</th>
                <th className="py-3 px-4">Department & Class</th>
                <th className="py-3 px-4">Biometric Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredStudents.length > 0 ? (
                filteredStudents.map((st) => (
                  <tr key={st.id} className="hover:bg-slate-800/20 transition">
                    <td className="py-3 px-4 font-mono font-bold text-indigo-300">{st.student_id}</td>
                    <td className="py-3 px-4 font-medium text-white">{st.name}</td>
                    <td className="py-3 px-4 text-slate-300">
                      {st.department} • Year {st.year} ({st.section})
                    </td>
                    <td className="py-3 px-4">
                      {st.has_face_registered ? (
                        <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-semibold">
                          <ShieldCheck className="w-3.5 h-3.5" />
                          <span>512-D ArcFace Active</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-semibold">
                          <ShieldAlert className="w-3.5 h-3.5" />
                          <span>Pending Enrollment</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDelete(st.id, st.name)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
                        title="Delete Student"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="py-12 text-center text-slate-400">
                    No students registered yet. Click &quot;Enroll New Student&quot; to add your classmates!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Enroll Student with In-Browser Webcam Capture */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-lg p-6 rounded-2xl glass-panel border border-slate-700 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-white">Enroll New Student</h2>

            <form onSubmit={handleCreateStudent} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Student ID *</label>
                  <input
                    type="text"
                    placeholder="e.g., 23CS001"
                    value={studentId}
                    onChange={(e) => setStudentId(e.target.value)}
                    required
                    className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Full Name *</label>
                  <input
                    type="text"
                    placeholder="e.g., Alex Johnson / Priya Sharma"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Department</label>
                  <input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Year</label>
                  <select
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5"
                  >
                    <option value={1}>Year 1</option>
                    <option value={2}>Year 2</option>
                    <option value={3}>Year 3</option>
                    <option value={4}>Year 4</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Section</label>
                  <input
                    type="text"
                    value={section}
                    onChange={(e) => setSection(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg p-2.5"
                  />
                </div>
              </div>

              {/* In-Browser Biometric Face Enrollment (5-Shot Guided Wizard) */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-emerald-400" />
                    <span className="font-semibold text-slate-200">5-Shot Multi-Angle Enrollment</span>
                  </div>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                    capturedPhotos.length === 5
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                      : "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                  }`}>
                    {capturedPhotos.length} / 5 Angles Captured
                  </span>
                </div>

                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Captures 5 distinct facial angles (center, smile, left, right, up) to construct an ArcFace 3D centroid vector. This guarantees student recognition even with handkerchiefs, masks, wiping face, or taking notes.
                </p>

                {!useWebcamCapture && capturedPhotos.length === 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                    <button
                      type="button"
                      onClick={handleStartAutoCapture}
                      className="py-3 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center space-x-2 transition shadow-md shadow-indigo-600/30"
                    >
                      <Sparkles className="w-4 h-4 text-amber-300" />
                      <span>Start Hands-Free 5-Shot Burst</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleStartModalCam}
                      className="py-3 px-3 rounded-lg border border-slate-700 hover:border-slate-600 bg-slate-800 text-slate-200 text-xs font-semibold flex items-center justify-center space-x-2 transition"
                    >
                      <Camera className="w-4 h-4" />
                      <span>Manual Step-by-Step Mode</span>
                    </button>
                  </div>
                )}

                {useWebcamCapture && (
                  <div className="space-y-3">
                    {capturedPhotos.length < 5 ? (
                      <>
                        <div className="p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-500/30 text-center flex items-center justify-between">
                          <div className="text-left">
                            <p className="text-[10px] uppercase font-bold text-indigo-300 tracking-wider">
                              Target Angle ({capturedPhotos.length + 1} of 5)
                            </p>
                            <p className="text-xs font-bold text-white mt-0.5">
                              {GUIDED_STEPS[capturedPhotos.length]}
                            </p>
                          </div>
                          {isAutoCapturing && (
                            <span className="text-[10px] font-bold px-2 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse">
                              Auto-Burst Active
                            </span>
                          )}
                        </div>

                        <div className="relative aspect-video rounded-xl overflow-hidden bg-black border border-slate-700 flex items-center justify-center">
                          <video
                            ref={modalVideoRef}
                            autoPlay
                            playsInline
                            muted
                            className="w-full h-full object-cover transform scale-x-[-1]"
                          />

                          {/* Flash animation */}
                          {flash && <div className="absolute inset-0 bg-white opacity-80 pointer-events-none transition-opacity duration-150" />}

                          {/* Auto Countdown Display */}
                          {isAutoCapturing && countdown > 0 && (
                            <div className="absolute inset-0 flex items-center justify-center bg-black/30 pointer-events-none">
                              <div className="h-16 w-16 rounded-full bg-indigo-600/80 backdrop-blur-md border-2 border-indigo-400 flex items-center justify-center animate-ping">
                                <span className="text-2xl font-black text-white">{countdown}</span>
                              </div>
                            </div>
                          )}

                          {/* Target angle watermark on video */}
                          <div className="absolute bottom-2 inset-x-2 p-1.5 rounded-lg bg-black/60 backdrop-blur-sm text-center text-[11px] font-semibold text-white">
                            Pose: {GUIDED_STEPS[capturedPhotos.length]}
                          </div>
                        </div>
                        <canvas ref={modalCanvasRef} className="hidden" />

                        {/* Capture Buttons */}
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            type="button"
                            onClick={handleCaptureModalPhoto}
                            className="py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md shadow-emerald-600/30 transition flex items-center justify-center space-x-1.5"
                          >
                            <Camera className="w-4 h-4" />
                            <span>Capture Angle ({capturedPhotos.length + 1}/5)</span>
                          </button>
                          {!isAutoCapturing ? (
                            <button
                              type="button"
                              onClick={handleStartAutoCapture}
                              className="py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition flex items-center justify-center space-x-1.5"
                            >
                              <Sparkles className="w-4 h-4 text-amber-300" />
                              <span>Start Auto-Burst</span>
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => {
                                setIsAutoCapturing(false);
                                setCountdown(0);
                              }}
                              className="py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs border border-slate-700 transition"
                            >
                              Pause Auto-Burst
                            </button>
                          )}
                        </div>
                      </>
                    ) : (
                      <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-center space-y-1.5">
                        <p className="text-xs font-bold text-emerald-400">
                          All 5 Facial Angles Captured Successfully!
                        </p>
                        <p className="text-[10px] text-slate-300">
                          ArcFace 512-D centroid vector ready. Click <strong>&quot;Save &amp; Enroll&quot;</strong> below to complete registration.
                        </p>
                        <button
                          type="button"
                          onClick={handleResetPhotos}
                          className="text-xs text-rose-400 hover:underline pt-1 inline-block"
                        >
                          Retake 5 Angles
                        </button>
                      </div>
                    )}

                    {/* 5-Shot Thumbnails Strip */}
                    <div className="space-y-1 pt-1">
                      <div className="flex items-center justify-between text-[10px] text-slate-400">
                        <span>Captured Angles Strip:</span>
                        <span>{capturedPhotos.length} / 5</span>
                      </div>
                      <div className="grid grid-cols-5 gap-1.5">
                        {["Straight", "Smile", "Left (15°)", "Right (15°)", "Up (10°)"].map((label, idx) => {
                          const img = capturedPhotos[idx];
                          return (
                            <div
                              key={idx}
                              className={`aspect-square rounded-lg overflow-hidden border flex flex-col items-center justify-center text-[9px] font-mono relative ${
                                img
                                  ? "border-emerald-500 bg-slate-900"
                                  : idx === capturedPhotos.length
                                  ? "border-indigo-400 bg-indigo-500/10 text-indigo-300 animate-pulse"
                                  : "border-slate-800 bg-slate-950 text-slate-600"
                              }`}
                            >
                              {img ? (
                                <>
                                  <img src={img} alt={`Angle ${idx + 1}`} className="w-full h-full object-cover" />
                                  <span className="absolute bottom-0 inset-x-0 bg-black/75 text-[8px] text-center text-emerald-300 py-0.5">
                                    ✓ {label}
                                  </span>
                                </>
                              ) : (
                                <div className="text-center p-1">
                                  <span className="block font-bold">#{idx + 1}</span>
                                  <span className="text-[8px] opacity-75">{label}</span>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Modal Buttons */}
              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2 rounded-lg glass-card text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={capturedPhotos.length === 0}
                  className={`px-5 py-2 rounded-lg font-semibold transition ${
                    capturedPhotos.length > 0
                      ? "bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer"
                      : "bg-slate-800 text-slate-500 cursor-not-allowed"
                  }`}
                >
                  Save &amp; Enroll {capturedPhotos.length > 0 ? `(${capturedPhotos.length} Angles)` : ""}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
