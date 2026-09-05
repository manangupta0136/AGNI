/**
 * MRPL AI WORKBENCH - System & API Configuration
 * 
 * Central configuration object holding model placeholders,
 * backend API routes, and default application settings.
 */

const CONFIG = {
  APP_NAME: 'MRPL AI WORKBENCH',
  APP_SUBTITLE: 'Secure Enterprise AI Workspace',
  SECURITY_BADGE: 'On-Premise PSU Network',
  DEFAULT_THEME: 'light',
  
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
      backendModel: 'qwen2-vl:7b',
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
    GENERATE_WORD: '/documents/generate-word'
  }
};

// Export to global scope
if (typeof window !== 'undefined') {
  window.CONFIG = CONFIG;
}
