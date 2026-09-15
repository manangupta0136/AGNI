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

-- -----------------------------------------------------------------------------
-- Table: model_registry (Available Open-Weight Models & Task Capabilities)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_registry (
    id VARCHAR(64) PRIMARY KEY,
    model_id VARCHAR(64) UNIQUE NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    task_type VARCHAR(64) NOT NULL, -- 'reasoning', 'coding', 'vision'
    is_installed BOOLEAN NOT NULL DEFAULT FALSE,
    context_window INTEGER DEFAULT 8192,
    status VARCHAR(32) DEFAULT 'available',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_registry_task ON model_registry(task_type);
CREATE INDEX IF NOT EXISTS idx_model_registry_status ON model_registry(status);

COMMENT ON TABLE model_registry IS 'Catalog of available open-weight models and their specialized industrial capabilities';

-- -----------------------------------------------------------------------------
-- Table: knowledge_sources (Categories of Plant SOPs, Standards, and Manuals)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id VARCHAR(64) PRIMARY KEY,
    source_name VARCHAR(128) NOT NULL,
    source_type VARCHAR(64) NOT NULL, -- 'SOP', 'Standard', 'Manual', 'Correspondence'
    connection_path VARCHAR(512),
    sync_status VARCHAR(32) DEFAULT 'synced',
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_knowledge_sources_type ON knowledge_sources(source_type);

COMMENT ON TABLE knowledge_sources IS 'Hierarchical source categories for plant SOPs, ASME/OISD standards, and manuals';

-- Add source_id to documents if not present
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'documents' AND column_name = 'source_id'
    ) THEN
        ALTER TABLE documents ADD COLUMN source_id VARCHAR(64) REFERENCES knowledge_sources(id) ON DELETE SET NULL;
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Table: agent_tasks (Parent Record for Autonomous Agentic Workflows)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_tasks (
    id VARCHAR(64) PRIMARY KEY,
    conversation_id VARCHAR(64) REFERENCES conversations(id) ON DELETE CASCADE,
    username VARCHAR(64) REFERENCES users(username) ON DELETE SET NULL,
    goal TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_conv ON agent_tasks(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_user ON agent_tasks(username);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);

COMMENT ON TABLE agent_tasks IS 'Primary parent record for multi-step agentic workflows and goals';

-- -----------------------------------------------------------------------------
-- Table: routing_decisions (Model Auto-Selection Provenance)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS routing_decisions (
    id VARCHAR(64) PRIMARY KEY,
    task_id VARCHAR(64) REFERENCES agent_tasks(id) ON DELETE CASCADE,
    message_id VARCHAR(64),
    requested_task_type VARCHAR(64) NOT NULL, -- 'reasoning', 'coding', 'vision'
    candidate_models JSONB DEFAULT '[]'::jsonb,
    selected_model VARCHAR(64) NOT NULL,
    reason TEXT NOT NULL,
    decided_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_routing_decisions_task ON routing_decisions(task_id);
CREATE INDEX IF NOT EXISTS idx_routing_decisions_model ON routing_decisions(selected_model);

COMMENT ON TABLE routing_decisions IS 'Transparent audit trail of automatic model selection decisions';

-- -----------------------------------------------------------------------------
-- Table: agent_task_steps (Step-by-Step Execution Trace)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_task_steps (
    id VARCHAR(64) PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL REFERENCES agent_tasks(id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,
    step_type VARCHAR(64) NOT NULL, -- 'understand_query', 'rag_retrieval', 'determine_assumptions', 'code_calculation', 'verify_calculation', 'generate_report'
    tool_used VARCHAR(64),
    input_ref TEXT,
    output_ref TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'done',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_task_steps_task_id ON agent_task_steps(task_id);
CREATE INDEX IF NOT EXISTS idx_task_steps_index ON agent_task_steps(task_id, step_index);

COMMENT ON TABLE agent_task_steps IS 'Individual steps executed by the agent for complete execution traceability';

-- Link task_step_id to code_execution_runs and vision_analyses
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'code_execution_runs' AND column_name = 'task_step_id'
    ) THEN
        ALTER TABLE code_execution_runs ADD COLUMN task_step_id VARCHAR(64) REFERENCES agent_task_steps(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'vision_analyses' AND column_name = 'task_step_id'
    ) THEN
        ALTER TABLE vision_analyses ADD COLUMN task_step_id VARCHAR(64) REFERENCES agent_task_steps(id) ON DELETE SET NULL;
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- Table: tool_invocations (Granular Tool Execution Audit)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tool_invocations (
    id VARCHAR(64) PRIMARY KEY,
    task_step_id VARCHAR(64) REFERENCES agent_task_steps(id) ON DELETE CASCADE,
    tool_name VARCHAR(64) NOT NULL,
    input_payload JSONB,
    output_payload JSONB,
    status VARCHAR(32) NOT NULL DEFAULT 'success',
    duration_ms DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    invoked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tool_invocations_step ON tool_invocations(task_step_id);
CREATE INDEX IF NOT EXISTS idx_tool_invocations_tool ON tool_invocations(tool_name);

COMMENT ON TABLE tool_invocations IS 'Granular metrics and payloads for every local tool call';

-- -----------------------------------------------------------------------------
-- Table: task_assumptions (Vague Query Resolution & Grounded Defaults)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS task_assumptions (
    id VARCHAR(64) PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL REFERENCES agent_tasks(id) ON DELETE CASCADE,
    parameter_name VARCHAR(128) NOT NULL,
    assumed_value VARCHAR(128) NOT NULL,
    unit VARCHAR(32),
    source_document_id VARCHAR(64) REFERENCES documents(id) ON DELETE SET NULL,
    source_chunk_id VARCHAR(64),
    standard_name VARCHAR(128) NOT NULL, -- e.g. 'ASME B31.3', 'OISD 141'
    reason TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT TRUE,
    is_user_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_assumptions_task ON task_assumptions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_assumptions_param ON task_assumptions(parameter_name);

COMMENT ON TABLE task_assumptions IS 'Records grounded industrial baseline assumptions retrieved for vague queries';

-- -----------------------------------------------------------------------------
-- Table: deliverables (Generic Deliverables: Word, Excel, PPT, Code)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deliverables (
    id VARCHAR(64) PRIMARY KEY,
    task_id VARCHAR(64) REFERENCES agent_tasks(id) ON DELETE SET NULL,
    step_id VARCHAR(64) REFERENCES agent_task_steps(id) ON DELETE SET NULL,
    deliverable_type VARCHAR(64) NOT NULL, -- 'approval_note', 'calculation_report', 'board_presentation', 'inspection_audit'
    file_format VARCHAR(32) NOT NULL, -- 'docx', 'xlsx', 'pptx', 'pdf', 'py'
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'generated',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deliverables_task ON deliverables(task_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_type ON deliverables(deliverable_type);

COMMENT ON TABLE deliverables IS 'Catalog of all generated deliverables (Word, Excel, PPT, Python, Approval notes)';

-- -----------------------------------------------------------------------------
-- Table: network_events (Air-Gap Zero Egress Proof Trail)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS network_events (
    id VARCHAR(64) PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(128) NOT NULL DEFAULT '127.0.0.1',
    destination VARCHAR(128) NOT NULL DEFAULT '127.0.0.1',
    direction VARCHAR(32) NOT NULL DEFAULT 'LOCAL',
    connection_type VARCHAR(32) NOT NULL DEFAULT 'TCP',
    external_connection BOOLEAN NOT NULL DEFAULT FALSE,
    bytes_transferred BIGINT NOT NULL DEFAULT 0,
    blocked BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_network_events_time ON network_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_network_events_ext ON network_events(external_connection);

COMMENT ON TABLE network_events IS 'Live network event log proving 0 external connections and complete air-gap compliance';

