-- =============================================================================
-- AGNI Air-Gapped AI Workbench — PostgreSQL Enterprise Database Schema
-- Target: PostgreSQL 14+ / 16+
-- Multi-User Privacy, Local Authentication, Isolated Threads & Long-Term Memory
-- =============================================================================

-- Enable UUID extension if available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- Table: users (Table 1: User Authentication & Credentials)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(64) PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(128),
    role VARCHAR(32) NOT NULL DEFAULT 'engineer',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

COMMENT ON TABLE users IS 'Stores local engineer credentials, roles, and identity for air-gap privacy';

-- -----------------------------------------------------------------------------
-- Table: conversations (Table 2: User-Isolated Chat Threads)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(64) REFERENCES users(username) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL DEFAULT 'New Technical Session',
    model_id VARCHAR(64) NOT NULL DEFAULT 'engineering-intelligence',
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_username ON conversations(username);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_archived ON conversations(is_archived);

COMMENT ON TABLE conversations IS 'Stores operator multi-turn chat sessions and active specialist model route, isolated by username';

-- -----------------------------------------------------------------------------
-- Table: messages
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(64) PRIMARY KEY,
    conversation_id VARCHAR(64) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender VARCHAR(32) NOT NULL,
    text TEXT NOT NULL,
    model_used VARCHAR(128),
    tokens_prompt INTEGER NOT NULL DEFAULT 0,
    tokens_completion INTEGER NOT NULL DEFAULT 0,
    latency_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    tool_calls JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at ASC);

COMMENT ON TABLE messages IS 'Stores user prompts, AI responses, model provenance, and latency metrics';

-- -----------------------------------------------------------------------------
-- Table: documents (User-Isolated Confidential PDFs & Folder Locations)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(64) REFERENCES users(username) ON DELETE CASCADE,
    thread_id VARCHAR(64) REFERENCES conversations(id) ON DELETE SET NULL,
    folder_path VARCHAR(512),
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_type VARCHAR(32) NOT NULL DEFAULT 'PDF',
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    file_size_str VARCHAR(32) NOT NULL DEFAULT '0 KB',
    pages INTEGER NOT NULL DEFAULT 1,
    category VARCHAR(64) NOT NULL DEFAULT 'Uploaded Document',
    status VARCHAR(32) NOT NULL DEFAULT 'uploaded',
    checksum_sha256 VARCHAR(64),
    qdrant_collection VARCHAR(64) NOT NULL DEFAULT 'mrpl_knowledge_base',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_documents_username ON documents(username);
CREATE INDEX IF NOT EXISTS idx_documents_thread_id ON documents(thread_id);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_checksum ON documents(checksum_sha256);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at DESC);

COMMENT ON TABLE documents IS 'Tracks confidential on-premise documents indexed for RAG retrieval per user';

-- -----------------------------------------------------------------------------
-- Table: document_chunks
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER NOT NULL DEFAULT 1,
    text_content TEXT NOT NULL,
    qdrant_point_id VARCHAR(64),
    embedding_model VARCHAR(64) DEFAULT 'bge-m3',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_qdrant_id ON document_chunks(qdrant_point_id);

COMMENT ON TABLE document_chunks IS 'Text slice boundaries mapped to Qdrant vector embedding points';

-- -----------------------------------------------------------------------------
-- Table: long_term_memories (Extra Table: Cross-Session User & Plant Memory)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS long_term_memories (
    id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(64) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    thread_id VARCHAR(64) REFERENCES conversations(id) ON DELETE SET NULL,
    memory_type VARCHAR(64) NOT NULL DEFAULT 'preference',
    memory_key VARCHAR(128) NOT NULL,
    memory_content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ltm_username ON long_term_memories(username);
CREATE INDEX IF NOT EXISTS idx_ltm_key ON long_term_memories(memory_key);

COMMENT ON TABLE long_term_memories IS 'Stores cross-session user memories, plant preferences, and contextual facts';

-- -----------------------------------------------------------------------------
-- Table: audit_reports
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_reports (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(64) REFERENCES conversations(id) ON DELETE SET NULL,
    document_ids JSONB DEFAULT '[]'::jsonb,
    report_type VARCHAR(64) NOT NULL DEFAULT 'Industrial Inspection Audit',
    file_path VARCHAR(512) NOT NULL,
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'generated',
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_reports_generated_at ON audit_reports(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_reports_conversation ON audit_reports(conversation_id);

COMMENT ON TABLE audit_reports IS 'Tracks generated Word (.docx) inspection and compliance audit reports';

-- -----------------------------------------------------------------------------
-- Table: security_audit_logs
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS security_audit_logs (
    id VARCHAR(64) PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(64) NOT NULL,
    ip_address VARCHAR(64) NOT NULL DEFAULT '127.0.0.1',
    request_id VARCHAR(64),
    external_connections_detected INTEGER NOT NULL DEFAULT 0,
    severity VARCHAR(32) NOT NULL DEFAULT 'INFO',
    details JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_security_audit_logs_timestamp ON security_audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_security_audit_logs_event_type ON security_audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_security_audit_logs_severity ON security_audit_logs(severity);

COMMENT ON TABLE security_audit_logs IS 'Immutable audit trail of zero-egress checks, model routing, and security events';

-- -----------------------------------------------------------------------------
-- Table: code_execution_runs
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS code_execution_runs (
    id VARCHAR(64) PRIMARY KEY,
    conversation_id VARCHAR(64) REFERENCES conversations(id) ON DELETE SET NULL,
    code_snippet TEXT NOT NULL,
    language VARCHAR(32) NOT NULL DEFAULT 'python',
    status VARCHAR(32) NOT NULL DEFAULT 'success',
    stdout TEXT NOT NULL DEFAULT '',
    stderr TEXT NOT NULL DEFAULT '',
    execution_time_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_code_exec_conversation ON code_execution_runs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_code_exec_executed_at ON code_execution_runs(executed_at DESC);

COMMENT ON TABLE code_execution_runs IS 'Tracks isolated local sandbox code executions for engineering computations';

-- -----------------------------------------------------------------------------
-- Table: vision_analyses
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vision_analyses (
    id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    image_path VARCHAR(512) NOT NULL,
    image_hash VARCHAR(64),
    prompt TEXT,
    scan_summary TEXT,
    detected_defects JSONB DEFAULT '[]'::jsonb,
    model_used VARCHAR(64) NOT NULL DEFAULT 'qwen2-vl:7b',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vision_analyses_session ON vision_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_vision_analyses_created_at ON vision_analyses(created_at DESC);

COMMENT ON TABLE vision_analyses IS 'Inspection diagram scans, P&ID component classifications, and defect detections';
