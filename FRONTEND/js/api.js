/**
 * MRPL AI WORKBENCH - FastAPI Integration API Layer
 * 
 * Placeholder API module exposing asynchronous functions for backend integration.
 * The backend team will later replace these implementations with fetch/axios calls
 * pointing to FastAPI endpoints (POST /chat, POST /chat/stream, GET /documents, etc.)
 */

const api = {
  /**
   * Send a chat message payload to backend router
   * Future endpoint: POST /chat/stream or POST /chat
   */
  async sendMessage(payload) {
    console.log('[API Placeholder] POST /chat payload ready for FastAPI:', payload);
    
    // Simulate network latency for mock response lookup
    await new Promise(resolve => setTimeout(resolve, 300));

    let responseText = MOCK_DATA.RESPONSES.DEFAULT;
    const lowerMsg = payload.message.toLowerCase();

    if (lowerMsg.includes('report') || lowerMsg.includes('inspection') || lowerMsg.includes('piping')) {
      responseText = MOCK_DATA.RESPONSES.INSPECTION;
    } else if (lowerMsg.includes('safety') || lowerMsg.includes('permit') || lowerMsg.includes('oisd')) {
      responseText = MOCK_DATA.RESPONSES.SAFETY;
    } else if (lowerMsg.includes('vendor') || lowerMsg.includes('budget') || lowerMsg.includes('evaluation')) {
      responseText = MOCK_DATA.RESPONSES.VENDOR;
    }

    return {
      status: 'success',
      conversation_id: payload.conversation_id,
      model_used: payload.model,
      response_text: responseText
    };
  },

  /**
   * Upload a confidential document file to FastAPI OCR/RAG pipeline
   * Future endpoint: POST /documents/upload
   */
  async uploadDocument(file) {
    console.log('[API Placeholder] POST /documents/upload file:', file.name);
    await new Promise(resolve => setTimeout(resolve, 400));
    
    const ext = file.name.split('.').pop().toUpperCase();
    return {
      id: 'doc-' + Date.now(),
      title: file.name,
      type: ext || 'PDF',
      size: file.size ? (file.size / (1024 * 1024)).toFixed(1) + ' MB' : '1.5 MB',
      updated: 'Just now',
      pages: 12,
      active: true,
      category: 'Uploaded Document'
    };
  },

  /**
   * Fetch available documents list
   * Future endpoint: GET /documents
   */
  async getDocuments() {
    console.log('[API Placeholder] GET /documents');
    return state.documents;
  },

  /**
   * Fetch backend models list
   * Future endpoint: GET /models
   */
  async getModels() {
    console.log('[API Placeholder] GET /models');
    return CONFIG.MODELS;
  },

  /**
   * Trigger Word Document (.docx) report generation
   * Future endpoint: POST /documents/generate-word
   */
  async generateWordDoc(payload) {
    console.log('[API Placeholder] POST /documents/generate-word:', payload);
    await new Promise(resolve => setTimeout(resolve, 600));
    return {
      status: 'success',
      download_url: '/api/v1/downloads/MRPL_Report.docx'
    };
  },

  /**
   * Transcribe recorded audio blob via backend Whisper / STT model
   * Future endpoint: POST /api/v1/voice/transcribe
   */
  async transcribeAudio(audioBlob) {
    console.log('[API Placeholder] POST /api/v1/voice/transcribe (Blob size:', audioBlob ? audioBlob.size : 0, 'bytes)');
    await new Promise(resolve => setTimeout(resolve, 500));
    return {
      status: 'success',
      text: 'Summarize the latest unit inspection and safety compliance report.'
    };
  }
};

if (typeof window !== 'undefined') {
  window.api = api;
}
