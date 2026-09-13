/**
 * AGNI: Air-Gapped Neural Intelligence - State Management & Reload Persistence
 * 
 * Manages runtime state for theme, sidebar layout, selected models,
 * document context selection, active chat sessions, and message logs.
 * Provides versioned, renderer-safe localStorage persistence.
 */

const STORAGE_KEY = 'agni_app_state_v1';
const SCHEMA_VERSION = 1;

class AppState {
  constructor() {
    this.version = SCHEMA_VERSION;
    this.theme = localStorage.getItem('mrpl_theme') || CONFIG.DEFAULT_THEME;
    this.sidebarCollapsed = false;
    this.contextDrawerOpen = false;
    this.activeModelId = 'engineering-intelligence';
    this.searchQuery = '';
    this.isStreaming = false;
    this.currentChatId = 'chat-001';
    
    // Deep clone initial fallback data
    this.documents = JSON.parse(JSON.stringify(MOCK_DATA.INITIAL_DOCUMENTS || []));
    this.conversations = JSON.parse(JSON.stringify(MOCK_DATA.INITIAL_CONVERSATIONS || []));
    this.messagesBySession = {};
    this.messages = [];
    
    this.listeners = [];

    // Hydrate state from localStorage safely
    this.loadState();
  }

  subscribe(listener) {
    this.listeners.push(listener);
  }

  notify(event, data) {
    this.listeners.forEach(fn => fn(event, data, this));
  }

  /**
   * Safely load and hydrate state from localStorage with defensive parsing
   */
  loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;

      const data = JSON.parse(raw);
      if (!data || typeof data !== 'object') return;
      if (data.version !== SCHEMA_VERSION) return; // Ignore incompatible old schema

      if (data.theme && (data.theme === 'light' || data.theme === 'dark')) {
        this.theme = data.theme;
      }
      if (typeof data.sidebarCollapsed === 'boolean') {
        this.sidebarCollapsed = data.sidebarCollapsed;
      }
      if (typeof data.contextDrawerOpen === 'boolean') {
        this.contextDrawerOpen = data.contextDrawerOpen;
      }
      if (data.activeModelId) {
        this.activeModelId = data.activeModelId;
      }
      if (data.currentChatId) {
        this.currentChatId = data.currentChatId;
      }
      if (Array.isArray(data.documents) && data.documents.length > 0) {
        this.documents = data.documents;
      }
      if (Array.isArray(data.conversations) && data.conversations.length > 0) {
        this.conversations = data.conversations;
      }
      if (data.messagesBySession && typeof data.messagesBySession === 'object') {
        const cleanedSessionMessages = {};
        for (const sessionId in data.messagesBySession) {
          if (Array.isArray(data.messagesBySession[sessionId])) {
            // Filter out transient thinking or streaming states before hydrating
            cleanedSessionMessages[sessionId] = data.messagesBySession[sessionId].filter(m => !m.isThinking && !m.isStreaming);
          }
        }
        this.messagesBySession = cleanedSessionMessages;
      }

      this.messages = this.messagesBySession[this.currentChatId] || [];

    } catch (err) {
      console.warn('[State] Failed to load persisted state, using initial defaults:', err);
    }
  }

  /**
   * Persist current state snapshot to localStorage
   */
  saveState() {
    try {
      // Sync current active messages buffer to session map, excluding transient items
      const cleanMessages = (this.messages || []).filter(m => !m.isThinking && !m.isStreaming);
      this.messagesBySession[this.currentChatId] = cleanMessages;

      const payload = {
        version: SCHEMA_VERSION,
        theme: this.theme,
        sidebarCollapsed: this.sidebarCollapsed,
        contextDrawerOpen: this.contextDrawerOpen,
        activeModelId: this.activeModelId,
        currentChatId: this.currentChatId,
        documents: this.documents,
        conversations: this.conversations,
        messagesBySession: this.messagesBySession,
        updatedAt: new Date().toISOString()
      };

      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
      localStorage.setItem('mrpl_theme', this.theme);
    } catch (err) {
      console.warn('[State] Failed to save state to localStorage:', err);
    }
  }

  setTheme(newTheme) {
    this.theme = newTheme;
    this.saveState();
    this.notify('themeChange', this.theme);
  }

  toggleTheme() {
    this.setTheme(this.theme === 'light' ? 'dark' : 'light');
  }

  toggleSidebar() {
    this.sidebarCollapsed = !this.sidebarCollapsed;
    this.saveState();
    this.notify('sidebarToggle', this.sidebarCollapsed);
  }

  toggleDrawer() {
    this.contextDrawerOpen = !this.contextDrawerOpen;
    this.saveState();
    this.notify('drawerToggle', this.contextDrawerOpen);
  }

  setModel(modelId) {
    this.activeModelId = modelId;
    this.saveState();
    this.notify('modelChange', this.activeModelId);
  }

  setSearchQuery(query) {
    this.searchQuery = query.toLowerCase();
    this.notify('searchChange', this.searchQuery);
  }

  toggleDocument(docId) {
    const doc = this.documents.find(d => d.id === docId);
    if (doc) {
      doc.active = !doc.active;
      this.saveState();
      this.notify('documentToggle', { docId, active: doc.active });
    }
  }

  addDocument(docObj) {
    this.documents.unshift(docObj);
    this.saveState();
    this.notify('documentAdd', docObj);
  }

  deleteDocument(docId) {
    this.documents = this.documents.filter(d => d.id !== docId);
    this.saveState();
    this.notify('documentDelete', docId);
  }

  /**
   * Intelligently merge backend document list while keeping local active states & custom uploads
   */
  mergeBackendDocuments(backendDocs) {
    if (!Array.isArray(backendDocs) || backendDocs.length === 0) return;

    const existingMap = new Map(this.documents.map(d => [d.id, d]));

    backendDocs.forEach(bDoc => {
      if (existingMap.has(bDoc.id)) {
        // Keep active checkbox state
        const localDoc = existingMap.get(bDoc.id);
        bDoc.active = localDoc.active;
      }
      existingMap.set(bDoc.id, bDoc);
    });

    this.documents = Array.from(existingMap.values());
    this.saveState();
  }

  getActiveDocuments() {
    return this.documents.filter(d => d.active);
  }

  getSelectedModel() {
    return CONFIG.MODELS.find(m => m.id === this.activeModelId) || CONFIG.MODELS[1];
  }

  /**
   * Create and switch to a new active chat session
   */
  startNewSession(title = 'New Session') {
    const newSessionId = 'chat-' + Date.now();
    const newConversation = {
      id: newSessionId,
      title: title,
      subtitle: 'New AI Chat Session',
      date: 'Just now',
      active: true,
      modelId: this.activeModelId
    };

    // Mark previous conversations inactive
    this.conversations.forEach(c => c.active = false);
    this.conversations.unshift(newConversation);

    this.currentChatId = newSessionId;
    this.messagesBySession[newSessionId] = [];
    this.messages = [];

    this.saveState();
    this.notify('sessionChange', newSessionId);
  }

  /**
   * Clear active session messages
   */
  clearCurrentMessages() {
    this.messages = [];
    this.messagesBySession[this.currentChatId] = [];
    this.saveState();
    this.notify('messagesCleared', this.currentChatId);
  }

  /**
   * Explicitly save message timeline
   */
  saveMessages() {
    this.saveState();
  }

  buildChatRequest(userMessageText) {
    return {
      message: userMessageText,
      model: this.getSelectedModel().backendModel,
      conversation_id: this.currentChatId,
      document_ids: this.getActiveDocuments().map(d => d.id),
      stream: true
    };
  }
}

// Create global state instance
const state = new AppState();

if (typeof window !== 'undefined') {
  window.state = state;
}
