-- ==============================================================================
-- CLOUD-BASED SMART ATTENDANCE SYSTEM - SUPABASE / POSTGRESQL SCHEMA
-- Extension: pgvector (512-Dimensional ArcFace Vector Similarity Search)
-- ==============================================================================

-- 1. Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Drop existing tables if rebuilding (clean migration)
DROP TABLE IF EXISTS attendance_events CASCADE;
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS class_sessions CASCADE;
DROP TABLE IF EXISTS subjects CASCADE;
DROP TABLE IF EXISTS face_embeddings CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 3. System Users (Admin / Faculty / Student accounts)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'faculty', 'student')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. Enrolled Students Registry
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(50) UNIQUE NOT NULL, -- e.g. 23CS001
    name VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL DEFAULT 'Computer Science',
    year INT NOT NULL DEFAULT 3,
    section VARCHAR(10) DEFAULT 'A',
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'graduated')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. Face Embeddings (512-Dimensional Vector per student, NO RAW PHOTOS STORED)
CREATE TABLE face_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    embedding vector(512) NOT NULL, -- ArcFace 512-D float representation
    model_version VARCHAR(50) NOT NULL DEFAULT 'ArcFace_SCRFD_buffalo_sc_512',
    is_primary BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Fast approximate nearest neighbor (HNSW) index on cosine similarity
CREATE INDEX IF NOT EXISTS idx_face_embeddings_hnsw 
ON face_embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 6. Academic Subjects / Courses
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL, -- e.g. CS301
    name VARCHAR(150) NOT NULL,       -- e.g. Data Structures & Algorithms
    department VARCHAR(100) NOT NULL DEFAULT 'Computer Science',
    faculty_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 7. Class Sessions (Faculty scheduled lecture windows)
CREATE TABLE class_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    faculty_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    room VARCHAR(50) NOT NULL DEFAULT 'Lab-01',
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'active', 'completed', 'cancelled')),
    checkpoint_interval_mins INT NOT NULL DEFAULT 5, -- AttenFace continuous checkpoint interval
    min_presence_percentage FLOAT NOT NULL DEFAULT 75.0, -- Institutional threshold for 'present'
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 8. Aggregated Session Attendance (Computed Presence Scores)
CREATE TABLE attendance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES class_sessions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'absent' CHECK (status IN ('present', 'partial', 'absent', 'flagged_review')),
    presence_score FLOAT NOT NULL DEFAULT 0.0, -- (successful checkpoints / total checkpoints) * 100
    confidence_avg FLOAT DEFAULT 0.0,
    first_seen TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    checkpoints_detected INT NOT NULL DEFAULT 0,
    total_checkpoints INT NOT NULL DEFAULT 1,
    verified_by_faculty BOOLEAN DEFAULT FALSE,
    faculty_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_student_session UNIQUE (session_id, student_id)
);

-- 9. Checkpoint Attendance Events (Continuous observations stream)
CREATE TABLE attendance_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    attendance_id UUID REFERENCES attendance(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES class_sessions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confidence FLOAT NOT NULL,      -- Vector cosine similarity (0.0 to 1.0)
    liveness_score FLOAT NOT NULL,  -- Liveness check confidence (0.0 to 1.0)
    ear_value FLOAT,                -- Eye Aspect Ratio during observation
    is_live BOOLEAN NOT NULL DEFAULT TRUE,
    camera_id VARCHAR(50) DEFAULT 'WEBCAM-01'
);

-- 10. Performance Indexes
CREATE INDEX IF NOT EXISTS idx_attendance_session ON attendance(session_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_events_session_timestamp ON attendance_events(session_id, timestamp);

-- ==============================================================================
-- DATABASE HELPER FUNCTION: Cosine Similarity Matching in pgvector
-- ==============================================================================
CREATE OR REPLACE FUNCTION match_student_face(
    query_embedding vector(512),
    match_threshold float DEFAULT 0.50,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    student_id UUID,
    student_code VARCHAR,
    student_name VARCHAR,
    department VARCHAR,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id AS student_id,
        s.student_id AS student_code,
        s.name AS student_name,
        s.department AS department,
        -- Cosine similarity = 1 - cosine distance (<=> operator)
        (1 - (fe.embedding <=> query_embedding))::float AS similarity
    FROM face_embeddings fe
    JOIN students s ON s.id = fe.student_id
    WHERE (1 - (fe.embedding <=> query_embedding)) >= match_threshold
    ORDER BY fe.embedding <=> query_embedding ASC
    LIMIT match_count;
END;
$$;
