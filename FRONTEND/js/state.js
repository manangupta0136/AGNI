/**
 * MRPL AI WORKBENCH - State Management
 * 
 * Manages runtime state for theme, sidebar layout, selected models,
 * document context selection, active chat session, and message logs.
 */

class AppState {
  constructor() {
    this.theme = localStorage.getItem('mrpl_theme') || CONFIG.DEFAULT_THEME;
    this.sidebarCollapsed = false;
    this.contextDrawerOpen = false;
    this.activeModelId = 'engineering-intelligence';
    this.searchQuery = '';
    this.isStreaming = false;
    this.currentChatId = 'chat-001';
    
    // Deep clone initial data
    this.documents = JSON.parse(JSON.stringify(MOCK_DATA.INITIAL_DOCUMENTS));
    this.conversations = JSON.parse(JSON.stringify(MOCK_DATA.INITIAL_CONVERSATIONS));
    this.messages = [];
    
    this.listeners = [];
  }

  subscribe(listener) {
    this.listeners.push(listener);
  }

  notify(event, data) {
    this.listeners.forEach(fn => fn(event, data, this));
  }

  setTheme(newTheme) {
    this.theme = newTheme;
    localStorage.setItem('mrpl_theme', newTheme);
    this.notify('themeChange', this.theme);
  }

  toggleTheme() {
    this.setTheme(this.theme === 'light' ? 'dark' : 'light');
  }

  toggleSidebar() {
    this.sidebarCollapsed = !this.sidebarCollapsed;
    this.notify('sidebarToggle', this.sidebarCollapsed);
  }

  toggleDrawer() {
    this.contextDrawerOpen = !this.contextDrawerOpen;
    this.notify('drawerToggle', this.contextDrawerOpen);
  }

  setModel(modelId) {
    this.activeModelId = modelId;
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
      this.notify('documentToggle', { docId, active: doc.active });
    }
  }

  addDocument(docObj) {
    this.documents.unshift(docObj);
    this.notify('documentAdd', docObj);
  }

  getActiveDocuments() {
    return this.documents.filter(d => d.active);
  }

  getSelectedModel() {
    return CONFIG.MODELS.find(m => m.id === this.activeModelId) || CONFIG.MODELS[1];
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
