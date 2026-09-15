/**
 * AGNI: Air-Gapped Neural Intelligence - System & API Configuration
 * 
 * Central configuration object holding model placeholders,
 * backend API routes, and default application settings.
 */

const CONFIG = {
  APP_NAME: 'AGNI: Air-Gapped Neural Intelligence',
  APP_SHORT_NAME: 'AGNI',
  APP_SUBTITLE: 'Air-Gapped Neural Intelligence',
  SECURITY_BADGE: 'On-Premise PSU Network',
  DEFAULT_THEME: 'dark',
  
  // Navigation Section Items
  NAV_ITEMS: [
    { id: 'home', label: 'Home', icon: 'home' },
    { id: 'chat', label: 'Chat', icon: 'chat' },
    { id: 'documents', label: 'Documents', icon: 'fileText' },
    { id: 'knowledge', label: 'Knowledge Base', icon: 'database' },
    { id: 'models', label: 'Model Hub', icon: 'cpu' },
    { id: 'tools', label: 'Agent Tools', icon: 'tool' },
    { id: 'history', label: 'Task History', icon: 'clock' },
    { id: 'settings', label: 'Settings', icon: 'settings' }
  ],

  // Quick Action Cards
  QUICK_ACTIONS: [
    {
      id: 'doc-analysis',
      title: 'Document Analysis',
      desc: 'Extract safety findings & engineering specs',
      prompt: 'Analyze the selected document and extract key safety findings',
      icon: 'fileSearch'
    },
    {
      id: 'code-automation',
      title: 'Code & Automation',
      desc: 'Python scripts, telemetry & SCADA parsers',
      prompt: 'Write a Python script to parse refinery telemetry logs',
      icon: 'terminal'
    },
    {
      id: 'data-analysis',
      title: 'Data Analysis',
      desc: 'Financial, vendor scorecard & unit metrics',
      prompt: 'Compare vendor scorecard metrics and pricing summaries',
      icon: 'barChart'
    },
    {
      id: 'image-ocr',
      title: 'Image & OCR',
      desc: 'Inspection diagrams, P&ID schematics & blueprints',
      prompt: 'Review engineering diagrams for Unit-4 piping integrity',
      icon: 'eye'
    },
    {
      id: 'report-gen',
      title: 'Report Generation',
      desc: 'OISD safety reports & compliance docs',
      prompt: 'Generate an OISD-137 compliance safety report summary',
      icon: 'fileCheck'
    }
  ],

  // Agent Tools Metadata — mirrors the tools actually registered on the
  // orchestrator in BACKEND/brain.py, so this list means something real
  // rather than describing capabilities that don't exist server-side.
  AGENT_TOOLS: [
    { id: 'tool-file', name: 'File Read/Write', status: 'Active', desc: 'Read/write local text files (read_file, write_file)' },
    { id: 'tool-code', name: 'Code Execution', status: 'Active', desc: 'Air-gapped Python sandbox (execute_code_tool)' },
    { id: 'tool-docgen', name: 'Document Generation', status: 'Active', desc: 'Generate PDF, Word & PowerPoint files (pdf_tool, docx_tool, pptx_tool)' },
    { id: 'tool-pdfread', name: 'PDF Reader & OCR', status: 'Active', desc: 'Extract text from PDFs, scanned pages routed to vision OCR (read_pdf_tool)' },
    { id: 'tool-search', name: 'Knowledge Base Search', status: 'Active', desc: 'Qdrant vector retrieval over indexed documents (rag_search)' },
    { id: 'tool-vision', name: 'Vision Analysis', status: 'Active', desc: 'Analyze images, scans & diagrams via local vision model (analyze_image)' }
  ],

  // System & Network Status Metadata
  SYSTEM_STATUS: [
    { label: 'External Connections', value: 'None (Air-Gapped)', status: 'secure' },
    { label: 'Model Hosting', value: 'Local GPU / CPU Cluster', status: 'ready' },
    { label: 'Agent Tools', value: '6 Modules Active', status: 'active' },
    { label: 'Data Boundary', value: '100% On-Premise MRPL', status: 'secure' }
  ],

  // Backend Model Options (for future Ollama & Router integration)
  MODELS: [
    {
      id: 'general-assistant',
      name: 'MRPL General Assistant',
      backendModel: 'llama3.1:8b',
      badge: 'Corporate & Policy',
      description: 'Corporate policies, HR rules, official PSU administrative queries.',
      code: 'GEN',
      icon: 'building'
    },
    {
      id: 'engineering-intelligence',
      name: 'Engineering Intelligence',
      backendModel: 'qwen2.5-coder:7b',
      badge: 'Refinery & Specs',
      description: 'Refinery equipment, piping standards, safety compliance & SOPs.',
      code: 'ENG',
      icon: 'cog'
    },
    {
      id: 'document-vision-analyst',
      name: 'Document Vision Analyst',
      backendModel: 'qwen2.5vl:3b',
      badge: 'Vision & Multimodal',
      description: 'Contract audit, multi-document synthesis & inspection diagram analysis.',
      code: 'VIS',
      icon: 'eye'
    }
  ],

  // Placeholder API Endpoint Configuration for FastAPI Backend
  API_BASE_URL: 'http://127.0.0.1:8000/api/v1',
  ENDPOINTS: {
    CHAT: '/chat',
    CHAT_STREAM: '/chat/stream',
    UPLOAD_DOC: '/documents/upload',
    GET_DOCS: '/documents',
    GET_MODELS: '/models',
    GENERATE_WORD: '/documents/generate-word',
    TRANSCRIBE: '/transcribe',
    SPEAK: '/speak'
  }
};

// Export to global scope
if (typeof window !== 'undefined') {
  window.CONFIG = CONFIG;
}
