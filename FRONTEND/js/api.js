/**
 * AGNI: Air-Gapped Neural Intelligence - FastAPI Integration API Layer
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
   * Endpoint: POST /api/v1/documents/upload?username=...
   */
  async uploadDocument(file, username = 'rekha') {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const url = `${CONFIG.API_BASE_URL}/documents/upload?username=${encodeURIComponent(username)}`;

      const res = await fetch(url, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        return await res.json();
      }
      const detail = await res.text().catch(() => '');
      console.warn(`[API] Upload endpoint returned ${res.status}: ${detail}. Falling back to local doc registration.`);
    } catch (err) {
      console.warn('[API] Could not post file to backend upload endpoint:', err);
    }

    const ext = file.name ? file.name.split('.').pop().toUpperCase() : 'PDF';
    return {
      id: 'doc-' + Date.now(),
      title: file.name || 'Uploaded Document',
      type: ext || 'PDF',
      size: file.size ? (file.size / (1024 * 1024)).toFixed(1) + ' MB' : '1.5 MB',
      updated: 'Just now',
      pages: Math.max(1, Math.floor(((file.size || 50000) / 50000))),
      active: true,
      category: 'Uploaded Document'
    };
  },

  /**
   * Fetch available documents list
   * Endpoint: GET /api/v1/documents?username=...
   */
  async getDocuments(username = 'rekha') {
    try {
      const res = await fetch(`${CONFIG.API_BASE_URL}/documents?username=${encodeURIComponent(username)}`);
      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      console.warn('[API] Could not fetch documents from backend endpoint:', err);
    }
    return state.documents;
  },

  /**
   * Delete an uploaded document from backend store
   * Endpoint: DELETE /api/v1/documents/{docId}
   */
  async deleteDocument(docId) {
    try {
      const res = await fetch(`${CONFIG.API_BASE_URL}/api/v1/documents/${docId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      console.warn('[API] Could not delete document on backend endpoint:', err);
    }
    return { status: 'success', deleted_id: docId };
  },

  /**
   * Fetch backend models list
   * Endpoint: GET /api/v1/models
   */
  async getModels() {
    try {
      const res = await fetch(`${CONFIG.API_BASE_URL}/models`);
      if (res.ok) {
        return await res.json();
      }
    } catch (err) {
      console.warn('Backend models fetch fallback:', err);
    }
    return CONFIG.MODELS;
  },

  /**
   * Trigger Word Document (.docx) report generation
   * Endpoint: POST /api/v1/documents/generate-word
   */
  async generateWordDoc(payload) {
    const res = await fetch(`${CONFIG.API_BASE_URL}/documents/generate-word`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || { title: 'MRPL Technical Audit' })
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => '');
      throw new Error(`Word report generation failed (${res.status}): ${detail}`);
    }

    return res.json();
  },

  /**
   * Air-gap network audit status check
   * Endpoint: GET /api/v1/system/network-status
   */
  async getNetworkStatus() {
    const res = await fetch(`${CONFIG.API_BASE_URL}/system/network-status`);
    if (!res.ok) {
      throw new Error(`Network audit check failed (${res.status})`);
    }
    return res.json();
  },

  /**
   * Fetch agent tasks and steps for conversation
   * Endpoint: GET /api/v1/tasks/{conversation_id}
   */
  async getTasks(conversationId) {
    try {
      const res = await fetch(`${CONFIG.API_BASE_URL}/tasks/${encodeURIComponent(conversationId)}`);
      if (res.ok) return await res.json();
    } catch (err) {
      console.warn('Tasks fetch fallback:', err);
    }
    return { tasks: [] };
  },

  /**
   * Fetch model auto-selection routing decisions
   * Endpoint: GET /api/v1/routing/decisions
   */
  async getRoutingDecisions() {
    try {
      const res = await fetch(`${CONFIG.API_BASE_URL}/routing/decisions`);
      if (res.ok) return await res.json();
    } catch (err) {
      console.warn('Routing decisions fetch fallback:', err);
    }
    return [];
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
