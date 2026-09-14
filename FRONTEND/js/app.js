/**
 * AGNI: Air-Gapped Neural Intelligence - Application Controller & Event Wiring
 * 
 * Orchestrates event handling, interactive prompt cards, sidebar toggles,
 * document context pipeline, persistence hydration, and streaming response loop.
 */

(function () {
  'use strict';

  let currentStreamingTimer = null;

  document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
  });

  async function initializeApp() {
    try {
      const { webFrame } = require('electron');
      webFrame.setZoomFactor(1.0);
      webFrame.setZoomLevel(0);
    } catch (e) {
      // Ignore if not in Electron renderer
    }

    // 1. Restore Theme, Sidebar & Drawer layout without animation flash on startup
    ui.applyTheme(state.theme);
    applySidebarState(state.sidebarCollapsed, true);
    applyDrawerState(state.contextDrawerOpen, true);

    // 2. Fetch and merge backend documents with local selection state & custom uploads
    try {
      const backendDocs = await api.getDocuments();
      if (Array.isArray(backendDocs) && backendDocs.length > 0) {
        state.mergeBackendDocuments(backendDocs);
      }
    } catch (err) {
      console.warn('[Init] Syncing documents with backend failed:', err);
    }

    // 3. Render restored state components
    ui.renderNavigation();
    ui.renderQuickActions();
    ui.renderRightPanels();
    ui.renderModels();
    ui.renderDocuments(true);
    ui.renderContextChips(true);
    ui.renderMessages(true);
    ui.switchView(state.activeNav);

    setupEventListeners();
  }

  function setupEventListeners() {
    // Sidebar Toggle (Hamburger Button)
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    if (sidebarToggleBtn) sidebarToggleBtn.addEventListener('click', toggleSidebar);

    // Theme Toggle Button (Top-Right Header)
    const headerThemeBtn = document.getElementById('header-theme-toggle');
    if (headerThemeBtn) headerThemeBtn.addEventListener('click', () => state.toggleTheme());

    // State Subscriptions
    state.subscribe((event, data) => {
      if (event === 'themeChange') ui.applyTheme(data);
      if (event === 'sidebarToggle') applySidebarState(data);
      if (event === 'drawerToggle') applyDrawerState(data);
      if (event === 'navChange') ui.switchView(data);
      if (event === 'modelChange') {
        ui.renderModels();
        ui.renderRightPanels();
      }
      if (event === 'documentToggle' || event === 'documentAdd' || event === 'documentDelete' || event === 'searchChange') {
        ui.renderDocuments();
      }
      if (event === 'sessionChange' || event === 'messagesCleared') {
        ui.renderMessages(true);
      }
    });

    // New Chat Button (Sidebar)
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) newChatBtn.addEventListener('click', startNewChat);

    // Clear Messages Button (Main Header)
    const clearChatBtn = document.getElementById('clear-chat-btn');
    if (clearChatBtn) clearChatBtn.addEventListener('click', clearChat);

    // Composer Form & Input Handlers
    const chatForm = document.getElementById('chat-composer-form');
    const userInput = document.getElementById('user-input-textarea');
    const sendBtn = document.getElementById('send-message-btn');
    const stopBtn = document.getElementById('stop-generation-btn');

    if (chatForm) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        handleSendMessage();
      });
    }

    if (userInput) {
      userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 180) + 'px';
        updateSendButtonState();
      });

      userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          if (userInput.value.trim() && !state.isStreaming) {
            handleSendMessage();
          }
        }
      });
    }

    if (stopBtn) {
      stopBtn.addEventListener('click', stopStreaming);
    }

    // Voice Assistant Control Wiring
    const voiceBtn = document.getElementById('voice-assistant-btn');
    if (window.voiceAssistant) {
      if (voiceBtn) {
        voiceBtn.addEventListener('click', () => {
          if (!window.voiceAssistant.isSupported()) {
            ui.showToast('Voice input is not supported in this environment.');
            ui.setVoiceAssistantState('error');
            return;
          }
          window.voiceAssistant.toggle();
        });
      }

      window.voiceAssistant.onRecordingStart(() => {
        ui.setVoiceAssistantState('recording');
      });

      window.voiceAssistant.onRecordingStop(() => {
        ui.setVoiceAssistantState('idle');
      });

      window.voiceAssistant.onTranscript(({ text }) => {
        if (userInput) {
          userInput.value = text;
          userInput.style.height = 'auto';
          userInput.style.height = Math.min(userInput.scrollHeight, 180) + 'px';
          updateSendButtonState();
        }
      });

      window.voiceAssistant.onError(({ message }) => {
        ui.setVoiceAssistantState('idle');
        ui.showToast(message || 'Voice input error');
      });
    }

    // Document Search Filter Input
    const docSearchInput = document.getElementById('doc-search-input');
    if (docSearchInput) {
      docSearchInput.addEventListener('input', (e) => {
        state.setSearchQuery(e.target.value);
      });
    }

    // Context Drawer Toggles
    const drawerToggleBtn = document.getElementById('context-drawer-toggle');
    const closeDrawerBtn = document.getElementById('close-drawer-btn');
    if (drawerToggleBtn) drawerToggleBtn.addEventListener('click', () => state.toggleDrawer());
    if (closeDrawerBtn) closeDrawerBtn.addEventListener('click', () => state.toggleDrawer());

    // ==========================================
    // DOCUMENT UPLOAD PIPELINE
    // ==========================================
    const uploadBtn = document.getElementById('upload-doc-btn');
    const uploadModal = document.getElementById('upload-modal');
    const closeModalBtn = document.getElementById('close-upload-modal');
    const cancelModalBtn = document.getElementById('cancel-upload-btn');
    const confirmUploadBtn = document.getElementById('confirm-upload-btn');
    const modalFileInput = document.getElementById('modal-file-input');
    const sidebarFileInput = document.getElementById('sidebar-file-input');
    const uploadDropzone = document.getElementById('upload-dropzone');

    // Trigger file selection or modal
    if (uploadBtn) {
      uploadBtn.addEventListener('click', () => {
        if (sidebarFileInput) {
          sidebarFileInput.click();
        } else if (uploadModal) {
          uploadModal.classList.remove('hidden');
        }
      });
    }

    if (uploadDropzone && modalFileInput) {
      uploadDropzone.addEventListener('click', () => modalFileInput.click());

      // Drag and drop support
      uploadDropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadDropzone.classList.add('border-[#3F641C]', 'bg-[#EEF5E5]/50');
      });

      uploadDropzone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadDropzone.classList.remove('border-[#3F641C]', 'bg-[#EEF5E5]/50');
      });

      uploadDropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadDropzone.classList.remove('border-[#3F641C]', 'bg-[#EEF5E5]/50');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          handleFilesUploaded(e.dataTransfer.files);
        }
      });
    }

    if (modalFileInput) {
      modalFileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
          handleFilesUploaded(e.target.files);
        }
      });
    }

    if (sidebarFileInput) {
      sidebarFileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
          handleFilesUploaded(e.target.files);
        }
      });
    }

    if (closeModalBtn) closeModalBtn.addEventListener('click', () => uploadModal.classList.add('hidden'));
    if (cancelModalBtn) cancelModalBtn.addEventListener('click', () => uploadModal.classList.add('hidden'));
    
    if (confirmUploadBtn) {
      confirmUploadBtn.addEventListener('click', () => {
        if (modalFileInput && modalFileInput.files.length > 0) {
          handleFilesUploaded(modalFileInput.files);
        } else {
          // Demo fallback document
          handleFilesUploaded([{ name: 'Unit_4_Hydrocarbon_Audit.pdf', size: 1850000 }]);
        }
      });
    }

    // Settings Modal
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsBtn = document.getElementById('close-settings-modal');
    if (closeSettingsBtn && settingsModal) closeSettingsBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));

    // Interactive Prompt Cards
    const promptCards = document.querySelectorAll('.prompt-suggestion-card');
    promptCards.forEach(card => {
      card.addEventListener('click', () => {
        const promptText = card.getAttribute('data-prompt');
        if (promptText && !state.isStreaming) {
          if (userInput) userInput.value = promptText;
          handleSendMessage();
        }
      });
    });

    // Ctrl + Mouse Wheel Zoom handling
    window.addEventListener('wheel', (e) => {
      if (e.ctrlKey) {
        e.preventDefault();
        try {
          const { webFrame } = require('electron');
          const currentZoom = webFrame.getZoomFactor();
          const delta = e.deltaY < 0 ? 0.1 : -0.1;
          const nextZoom = Math.min(Math.max(Number((currentZoom + delta).toFixed(2)), 0.3), 3.0);
          webFrame.setZoomFactor(nextZoom);
        } catch (err) {
          // Ignore if not running under Electron renderer
        }
      }
    }, { passive: false });
  }

  async function handleFilesUploaded(fileList) {
    const uploadModal = document.getElementById('upload-modal');
    const modalFileInput = document.getElementById('modal-file-input');
    const sidebarFileInput = document.getElementById('sidebar-file-input');

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
      try {
        const newDoc = await api.uploadDocument(file);
        state.addDocument(newDoc);
        ui.showToast(`Indexed Document: "${newDoc.title}" (${newDoc.size})`);
      } catch (err) {
        console.error('[Upload] Error uploading file:', file.name, err);
        ui.showToast(`Failed to upload "${file.name}": ${err.message || 'Upload error'}`);
      }
    }

    if (uploadModal) uploadModal.classList.add('hidden');
    if (modalFileInput) modalFileInput.value = '';
    if (sidebarFileInput) sidebarFileInput.value = '';
  }

  function toggleSidebar() {
    state.toggleSidebar();
  }

  function applySidebarState(collapsed, initialHydrate = false) {
    const sidebar = document.getElementById('app-sidebar');
    const toggleBtnIcon = document.querySelector('#sidebar-toggle-btn svg');
    if (sidebar) {
      if (initialHydrate) {
        sidebar.style.transition = 'none';
      }
      if (collapsed) {
        sidebar.classList.add('sidebar-closed');
      } else {
        sidebar.classList.remove('sidebar-closed');
      }
      if (initialHydrate) {
        // Re-enable transition after initial render frame
        requestAnimationFrame(() => {
          sidebar.style.transition = '';
        });
      }
    }
    if (toggleBtnIcon) {
      toggleBtnIcon.style.transform = collapsed ? 'rotate(90deg)' : 'rotate(0deg)';
    }
  }

  function applyDrawerState(open, initialHydrate = false) {
    const drawer = document.getElementById('right-context-drawer');
    if (drawer) {
      if (initialHydrate) {
        drawer.style.transition = 'none';
      }
      if (open) {
        drawer.classList.remove('translate-x-full');
      } else {
        drawer.classList.add('translate-x-full');
      }
      if (initialHydrate) {
        requestAnimationFrame(() => {
          drawer.style.transition = '';
        });
      }
    }
  }

  function startNewChat() {
    if (state.isStreaming) stopStreaming();
    state.startNewSession('New Session');
    ui.renderMessages(true);
    ui.showToast('Started new chat session.');
  }

  function clearChat() {
    if (state.isStreaming) stopStreaming();
    state.clearCurrentMessages();
    ui.renderMessages(true);
    ui.showToast('Cleared conversation history.');
  }

  async function handleSendMessage() {
    if (window.voiceAssistant && window.voiceAssistant.isRecording) {
      window.voiceAssistant.stop();
    }

    const userInput = document.getElementById('user-input-textarea');
    if (!userInput) return;

    const text = userInput.value.trim();
    if (!text || state.isStreaming) return;

    userInput.value = '';
    userInput.style.height = 'auto';

    const activeDocs = state.getActiveDocuments().map(d => ({
      id: d.id,
      title: d.title,
      type: d.type,
      size: d.size
    }));

    const userMsg = {
      id: 'msg-' + Date.now(),
      sender: 'user',
      text: text,
      attachedDocs: activeDocs,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    state.messages.push(userMsg);
    state.saveMessages(); // Persist user message immediately

    // Add temporary AI thinking/loading message
    const activeModel = state.getSelectedModel();
    const loadingText = activeDocs.length > 0 ? 'Analyzing document context...' : 'AGNI Thinking...';
    const loadingMsg = {
      id: 'loading-msg',
      sender: 'ai',
      text: loadingText,
      modelName: activeModel ? activeModel.name : 'Engineering Intelligence',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isThinking: true
    };
    state.messages.push(loadingMsg);
    ui.renderMessages();

    // Immediately enter loading/streaming state to prevent duplicate submissions
    state.isStreaming = true;
    updateSendButtonState();

    const requestPayload = state.buildChatRequest(text);
    let apiResult;
    try {
      apiResult = await api.sendMessage(requestPayload);
    } catch (err) {
      console.error('[Chat] sendMessage failed:', err);
      state.messages = state.messages.filter(m => !m.isThinking);
      ui.showToast('Could not reach backend: ' + (err.message || 'Server error'));
      state.isStreaming = false;
      updateSendButtonState();
      ui.renderMessages();
      return;
    }

    state.messages = state.messages.filter(m => !m.isThinking);
    streamAIResponse(apiResult.response_text);
  }

  function streamAIResponse(fullResponseText) {
    state.isStreaming = true;
    updateSendButtonState();

    const aiMsgId = 'ai-msg-' + Date.now();
    const activeModel = state.getSelectedModel();

    const aiMsg = {
      id: aiMsgId,
      sender: 'ai',
      text: '',
      modelName: activeModel ? activeModel.name : 'Engineering Intelligence',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isStreaming: true
    };

    state.messages.push(aiMsg);
    ui.renderMessages();

    let charIndex = 0;
    const chunkSize = 5;
    const intervalMs = 18;

    currentStreamingTimer = setInterval(() => {
      charIndex += chunkSize;
      const currentSubtext = fullResponseText.slice(0, charIndex);

      const msgObj = state.messages.find(m => m.id === aiMsgId);
      if (msgObj) msgObj.text = currentSubtext;

      const msgNode = document.getElementById(`content-${aiMsgId}`);
      if (msgNode) {
        msgNode.innerHTML = ui.parseMarkdown(currentSubtext) + '<span class="streaming-cursor"></span>';
      }

      ui.scrollToBottom();

      if (charIndex >= fullResponseText.length) {
        finishStreaming(aiMsgId, fullResponseText);
      }
    }, intervalMs);
  }

  function finishStreaming(aiMsgId, fullText) {
    if (currentStreamingTimer) clearInterval(currentStreamingTimer);
    currentStreamingTimer = null;

    const msgObj = state.messages.find(m => m.id === aiMsgId);
    if (msgObj) msgObj.isStreaming = false;

    const msgNode = document.getElementById(`content-${aiMsgId}`);
    if (msgNode) {
      msgNode.innerHTML = ui.parseMarkdown(fullText);
    }

    state.isStreaming = false;
    updateSendButtonState();

    // Persist final assistant response to state
    state.saveMessages();

    ui.renderMessages();
    ui.scrollToBottom();
  }

  function stopStreaming() {
    if (currentStreamingTimer) {
      clearInterval(currentStreamingTimer);
      currentStreamingTimer = null;
    }
    const lastMsg = state.messages[state.messages.length - 1];
    if (lastMsg && lastMsg.sender === 'ai') {
      lastMsg.isStreaming = false;
    }
    state.isStreaming = false;
    updateSendButtonState();
    state.saveMessages();
    ui.renderMessages();
    ui.showToast('Generation stopped.');
  }

  function updateSendButtonState() {
    const sendBtn = document.getElementById('send-message-btn');
    const stopBtn = document.getElementById('stop-generation-btn');
    const userInput = document.getElementById('user-input-textarea');

    if (state.isStreaming) {
      if (sendBtn) sendBtn.classList.add('hidden');
      if (stopBtn) stopBtn.classList.remove('hidden');
    } else {
      if (sendBtn) {
        sendBtn.classList.remove('hidden');
        sendBtn.disabled = !userInput || !userInput.value.trim();
      }
      if (stopBtn) stopBtn.classList.add('hidden');
    }
  }

  // PUBLIC WINDOW API EXPORTS
  const AppExports = {
    navigate: (navId) => state.setActiveNav(navId),
    triggerQuickAction: (promptText) => {
      if (!state.isStreaming) {
        state.setActiveNav('chat');
        const userInput = document.getElementById('user-input-textarea');
        if (userInput) userInput.value = promptText;
        handleSendMessage();
      }
    },
    selectSession: (sessionId) => {
      state.currentChatId = sessionId;
      state.messages = state.messagesBySession[sessionId] || [];
      state.saveState();
      state.setActiveNav('chat');
      ui.renderMessages(true);
    },
    switchModel: (modelId) => state.setModel(modelId),
    toggleDocumentSelection: (docId) => state.toggleDocument(docId),
    deleteDocument: async (docId) => {
      const doc = state.documents.find(d => d.id === docId);
      const title = doc ? doc.title : 'Document';
      state.deleteDocument(docId);
      try {
        await api.deleteDocument(docId);
        ui.showToast(`Deleted "${title}"`);
      } catch (err) {
        console.warn('Failed to delete document from backend:', err);
      }
    },
    toggleSidebar,
    toggleTheme: () => state.toggleTheme(),
    startNewChat,
    clearChat,
    regenerate: () => {
      if (state.messages.length > 0) {
        const lastUserMsg = state.messages.filter(m => m.sender === 'user').pop();
        if (lastUserMsg && !state.isStreaming) {
          handleSendMessageWithPrompt(lastUserMsg.text);
        }
      }
    },
    copyText: (msgId) => {
      const msg = state.messages.find(m => m.id === msgId);
      if (msg) {
        navigator.clipboard.writeText(msg.text);
        ui.showToast('Copied text to clipboard');
      }
    },
    feedback: (type) => {
      ui.showToast(type === 'up' ? 'Feedback recorded: Helpful' : 'Feedback recorded: Inaccurate');
    }
  };

  window.AGNIApp = AppExports;
  window.MRPLApp = AppExports;

  function handleSendMessageWithPrompt(text) {
    const activeDocs = state.getActiveDocuments().map(d => ({
      id: d.id,
      title: d.title,
      type: d.type,
      size: d.size
    }));

    const userMsg = {
      id: 'msg-' + Date.now(),
      sender: 'user',
      text: text,
      attachedDocs: activeDocs,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    state.messages.push(userMsg);
    state.saveMessages();

    const activeModel = state.getSelectedModel();
    const loadingText = activeDocs.length > 0 ? 'Analyzing document context...' : 'AGNI Thinking...';
    const loadingMsg = {
      id: 'loading-msg',
      sender: 'ai',
      text: loadingText,
      modelName: activeModel ? activeModel.name : 'Engineering Intelligence',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isThinking: true
    };
    state.messages.push(loadingMsg);
    ui.renderMessages();

    state.isStreaming = true;
    updateSendButtonState();

    api.sendMessage(state.buildChatRequest(text))
      .then(res => {
        state.messages = state.messages.filter(m => !m.isThinking);
        streamAIResponse(res.response_text);
      })
      .catch(err => {
        console.error('[Chat] sendMessage failed:', err);
        state.messages = state.messages.filter(m => !m.isThinking);
        state.isStreaming = false;
        updateSendButtonState();
        ui.renderMessages();
        ui.showToast('Could not reach backend. Is the server running?');
      });
  }

})();
