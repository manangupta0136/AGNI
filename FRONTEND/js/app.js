/**
 * MRPL AI WORKBENCH - Application Controller & Event Wiring
 * 
 * Orchestrates event handling, interactive prompt cards, sidebar toggles,
 * working file upload pipeline, and mock streaming response loop.
 */

(function () {
  'use strict';

  let currentStreamingTimer = null;

  document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
  });

  function initializeApp() {
    try {
      const { webFrame } = require('electron');
      webFrame.setZoomFactor(1.0);
      webFrame.setZoomLevel(0);
    } catch (e) {
      // Ignore if not in Electron renderer
    }
    ui.applyTheme(state.theme);
    ui.renderModels();
    ui.renderDocuments();
    ui.renderContextChips();
    ui.renderMessages();
    setupEventListeners();
  }

  function setupEventListeners() {
    // Sidebar Toggle (Hamburger Button)
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    if (sidebarToggleBtn) sidebarToggleBtn.addEventListener('click', toggleSidebar);

    // Theme Toggle Buttons
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const headerThemeBtn = document.getElementById('header-theme-toggle');
    if (themeToggleBtn) themeToggleBtn.addEventListener('click', () => state.toggleTheme());
    if (headerThemeBtn) headerThemeBtn.addEventListener('click', () => state.toggleTheme());

    // State Subscriptions
    state.subscribe((event, data) => {
      if (event === 'themeChange') ui.applyTheme(data);
      if (event === 'sidebarToggle') applySidebarState(data);
      if (event === 'drawerToggle') applyDrawerState(data);
      if (event === 'modelChange') ui.renderModels();
      if (event === 'documentToggle' || event === 'documentAdd' || event === 'searchChange') {
        ui.renderDocuments();
      }
    });

    // New Chat Buttons
    const newChatBtn = document.getElementById('new-chat-btn');
    const headerNewChatBtn = document.getElementById('header-new-chat-btn');
    if (newChatBtn) newChatBtn.addEventListener('click', startNewChat);
    if (headerNewChatBtn) headerNewChatBtn.addEventListener('click', startNewChat);

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
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsBtn = document.getElementById('close-settings-modal');
    if (settingsBtn && settingsModal) settingsBtn.addEventListener('click', () => settingsModal.classList.remove('hidden'));
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

    // Clear Chat Action
    const clearChatBtn = document.getElementById('clear-chat-btn');
    if (clearChatBtn) clearChatBtn.addEventListener('click', startNewChat);

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
      const newDoc = await api.uploadDocument(file);
      state.addDocument(newDoc);
      ui.showToast(`Indexed Document: "${newDoc.title}" (${newDoc.size})`);
    }

    if (uploadModal) uploadModal.classList.add('hidden');
    if (modalFileInput) modalFileInput.value = '';
    if (sidebarFileInput) sidebarFileInput.value = '';
  }

  function toggleSidebar() {
    state.toggleSidebar();
  }

  function applySidebarState(collapsed) {
    const sidebar = document.getElementById('app-sidebar');
    const toggleBtnIcon = document.querySelector('#sidebar-toggle-btn svg');
    if (sidebar) {
      if (collapsed) {
        sidebar.classList.add('sidebar-closed');
      } else {
        sidebar.classList.remove('sidebar-closed');
      }
    }
    if (toggleBtnIcon) {
      toggleBtnIcon.style.transform = collapsed ? 'rotate(90deg)' : 'rotate(0deg)';
    }
  }

  function applyDrawerState(open) {
    const drawer = document.getElementById('right-context-drawer');
    if (drawer) {
      if (open) {
        drawer.classList.remove('translate-x-full');
      } else {
        drawer.classList.add('translate-x-full');
      }
    }
  }

  function startNewChat() {
    if (state.isStreaming) stopStreaming();
    state.messages = [];
    ui.renderMessages();
    ui.showToast('Cleared conversation buffer.');
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

    const userMsg = {
      id: 'msg-' + Date.now(),
      sender: 'user',
      text: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    state.messages.push(userMsg);
    ui.renderMessages();

    // Call API placeholder to get response payload
    const requestPayload = state.buildChatRequest(text);
    const apiResult = await api.sendMessage(requestPayload);

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
      modelName: activeModel ? activeModel.name : 'MRPL AI',
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
  window.MRPLApp = {
    switchModel: (modelId) => state.setModel(modelId),
    toggleDocumentSelection: (docId) => state.toggleDocument(docId),
    toggleSidebar,
    toggleTheme: () => state.toggleTheme(),
    startNewChat,
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

  function handleSendMessageWithPrompt(text) {
    const userMsg = {
      id: 'msg-' + Date.now(),
      sender: 'user',
      text: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    state.messages.push(userMsg);
    ui.renderMessages();
    api.sendMessage(state.buildChatRequest(text)).then(res => streamAIResponse(res.response_text));
  }

})();
