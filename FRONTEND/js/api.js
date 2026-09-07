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
   * Endpoint: POST /api/v1/chat
   */
  async sendMessage(payload) {
    const res = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.CHAT}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => '');
      throw new Error(`Chat request failed (${res.status}): ${detail}`);
    }

    return res.json();
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
   * Transcribe recorded audio blob via backend STT model
   * Endpoint: POST /api/v1/transcribe (multipart/form-data, field "file")
   */
  async transcribeAudio(audioBlob) {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');

    const res = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.TRANSCRIBE}`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => '');
      throw new Error(`Transcription failed (${res.status}): ${detail}`);
    }

    return res.json();
  },

  /**
   * Synthesize speech audio from text via backend TTS model
   * Endpoint: POST /api/v1/speak (JSON body { text }) -> audio/wav bytes
   * Returns a playable object URL for use in an <audio> element.
   */
  async synthesizeSpeech(text) {
    const res = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.SPEAK}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => '');
      throw new Error(`Speech synthesis failed (${res.status}): ${detail}`);
    }

    const audioBlob = await res.blob();
    return URL.createObjectURL(audioBlob);
  }
};

if (typeof window !== 'undefined') {
  window.api = api;
}
