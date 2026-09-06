/**
 * MRPL AI WORKBENCH - UI Rendering & DOM Helpers
 * 
 * Provides crisp SVG icon templates, Markdown parsing, document list renderers,
 * model switchers, message list viewports, toast alerts, and theme toggling.
 */

const ui = {
  // SVG Icon Registry (Industrial & Enterprise Design System)
  icons: {
    logo: `<svg class="w-5 h-5 text-[#3F641C] dark:text-[#A8D66D] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>`,
    plus: `<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>`,
    sun: `<svg class="w-4 h-4 text-amber-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>`,
    moon: `<svg class="w-4 h-4 text-[#3F641C] dark:text-[#A8D66D] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>`,
    menu: `<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>`,
    search: `<svg class="w-3.5 h-3.5 text-[#5C6654] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>`,
    upload: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>`,
    filePdf: `<svg class="w-3.5 h-3.5 text-red-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>`,
    fileXlsx: `<svg class="w-3.5 h-3.5 text-emerald-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>`,
    fileDocx: `<svg class="w-3.5 h-3.5 text-[#3F641C] dark:text-[#88B83E] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>`,
    fileZip: `<svg class="w-3.5 h-3.5 text-amber-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v1a2 2 0 01-2 2M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/></svg>`,
    lock: `<svg class="w-3.5 h-3.5 text-[#3F641C] dark:text-[#A8D66D] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>`,
    send: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>`,
    stop: `<svg class="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>`,
    settings: `<svg class="w-4 h-4 text-[#5C6654] hover:text-[#20251D] dark:hover:text-[#E8EBDD] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>`,
    copy: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>`,
    refresh: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>`,
    thumbUp: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"/></svg>`,
    thumbDown: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v5a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"/></svg>`,
    mic: `<svg class="w-3.5 h-3.5 shrink-0 text-[#3F641C] dark:text-[#A8D66D]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg>`,
    micActive: `<svg class="w-3.5 h-3.5 text-red-600 dark:text-red-400 animate-pulse shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M12 14a3 3 0 003-3V5a3 3 0 10-6 0v6a3 3 0 003 3zm5-3a1 1 0 10-2 0 5 5 0 01-10 0 1 1 0 10-2 0 7 7 0 006 6.92V20H9a1 1 0 100 2h6a1 1 0 100-2h-2v-2.08A7 7 0 0017 11z"/></svg>`,
    micOff: `<svg class="w-3.5 h-3.5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18"/></svg>`
  },

  applyTheme(theme) {
    const root = document.documentElement;
    const themeIconContainers = document.querySelectorAll('.theme-icon-slot');
    const themeLabels = document.querySelectorAll('.theme-label-slot');

    if (theme === 'dark') {
      root.classList.add('dark');
      themeIconContainers.forEach(el => el.innerHTML = this.icons.sun);
      themeLabels.forEach(el => el.textContent = 'Light Theme');
    } else {
      root.classList.remove('dark');
      themeIconContainers.forEach(el => el.innerHTML = this.icons.moon);
      themeLabels.forEach(el => el.textContent = 'Dark Theme');
    }
  },

  renderModels() {
    const container = document.getElementById('model-list-container');
    if (!container) return;

    container.innerHTML = CONFIG.MODELS.map(m => {
      const isActive = m.id === state.activeModelId;
      return `
        <button 
          type="button" 
          onclick="window.MRPLApp.switchModel('${m.id}')"
          class="w-full text-left p-2.5 rounded-md border transition-all duration-150 flex items-start space-x-2.5 cursor-pointer relative group ${
            isActive 
              ? 'bg-[#EEF5E5] dark:bg-[#1F2B18] text-[#20251D] dark:text-[#E8EBDD] border-[#3F641C] dark:border-[#88B83E] font-medium shadow-2xs' 
              : 'bg-white text-[#20251D] dark:bg-[#171B19] dark:text-[#E8EBDD] border-[#D6DDC9] dark:border-[#34422B] hover:bg-[#F9FAF6] dark:hover:bg-[#1C201E]'
          }"
        >
          <span class="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0 ${
            isActive 
              ? 'bg-[#3F641C] text-white dark:bg-[#3F641C] dark:text-white' 
              : 'bg-[#EEF5E5] text-[#3F641C] dark:bg-[#1F2B18] dark:text-[#A8D66D]'
          }">${m.code}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold truncate">${m.name}</span>
              ${isActive ? '<span class="w-2 h-2 rounded-full bg-[#3F641C] dark:bg-[#88B83E] shrink-0 ml-1"></span>' : ''}
            </div>
            <p class="text-[11px] text-[#5C6654] dark:text-[#AEB5A6] truncate mt-0.5">${m.badge}</p>
          </div>
        </button>
      `;
    }).join('');

    this.updateHeaderModelBadge();
  },

  renderDocuments() {
    const container = document.getElementById('document-list-container');
    const docCountBadge = document.getElementById('selected-docs-count');
    if (!container) return;

    const filteredDocs = state.documents.filter(d => 
      d.title.toLowerCase().includes(state.searchQuery)
    );

    const activeCount = state.getActiveDocuments().length;
    if (docCountBadge) docCountBadge.textContent = `${activeCount} Selected`;

    if (filteredDocs.length === 0) {
      container.innerHTML = `
        <div class="text-center py-4 text-xs text-[#5C6654] dark:text-[#AEB5A6]">
          No matching documents found
        </div>
      `;
      return;
    }

    container.innerHTML = filteredDocs.map(d => `
      <div 
        class="flex items-center justify-between p-2 rounded-md cursor-pointer border text-xs transition-colors relative ${
          d.active 
            ? 'bg-[#EEF5E5]/70 dark:bg-[#1F2B18]/70 border-[#3F641C] dark:border-[#88B83E] font-medium' 
            : 'bg-white dark:bg-[#171B19] border-[#D6DDC9] dark:border-[#34422B] hover:bg-[#F9FAF6] dark:hover:bg-[#1C201E]'
        }"
        onclick="window.MRPLApp.toggleDocumentSelection('${d.id}')"
      >
        <div class="flex items-center space-x-2 min-w-0 pr-1">
          <input 
            type="checkbox" 
            ${d.active ? 'checked' : ''} 
            class="w-3.5 h-3.5 text-[#3F641C] accent-[#3F641C] rounded border-[#D6DDC9] dark:border-[#34422B] focus:ring-[#3F641C] cursor-pointer shrink-0"
            onclick="event.stopPropagation(); window.MRPLApp.toggleDocumentSelection('${d.id}')"
          />
          ${this.getFileIcon(d.type)}
          <div class="min-w-0">
            <p class="text-xs text-[#20251D] dark:text-[#E8EBDD] truncate" title="${d.title}">${d.title}</p>
            <p class="text-[10px] text-[#5C6654] dark:text-[#AEB5A6] truncate">${d.size} • ${d.category}</p>
          </div>
        </div>
      </div>
    `).join('');

    this.renderContextChips();
    this.renderDrawerDocuments();
  },

  renderContextChips() {
    const container = document.getElementById('attached-context-chips');
    if (!container) return;

    const activeDocs = state.getActiveDocuments();

    if (activeDocs.length === 0) {
      container.innerHTML = `
        <span class="text-xs text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/50 px-2.5 py-1 rounded border border-amber-200 dark:border-amber-800 inline-flex items-center space-x-1.5">
          <span>⚠️</span>
          <span>No documents selected for context lookup</span>
        </span>
      `;
      return;
    }

    container.innerHTML = activeDocs.map(d => `
      <span class="inline-flex items-center space-x-1.5 text-xs bg-[#EEF5E5] dark:bg-[#1F2B18] text-[#20251D] dark:text-[#E8EBDD] px-2.5 py-1 rounded-md border border-[#C3D9AA] dark:border-[#34422B] shadow-2xs">
        ${this.getFileIcon(d.type)}
        <span class="truncate max-w-[160px] font-medium text-[#3F641C] dark:text-[#A8D66D]" title="${d.title}">${d.title}</span>
        <button 
          type="button" 
          onclick="window.MRPLApp.toggleDocumentSelection('${d.id}')"
          class="font-bold text-[#5C6654] hover:text-red-700 dark:hover:text-red-400 ml-1 cursor-pointer"
          title="Remove from chat context"
        >
          ×
        </button>
      </span>
    `).join('');
  },

  renderDrawerDocuments() {
    const container = document.getElementById('drawer-active-docs-list');
    if (!container) return;

    const activeDocs = state.getActiveDocuments();
    if (activeDocs.length === 0) {
      container.innerHTML = '<p class="text-xs text-[#5C6654] dark:text-[#AEB5A6]">No active documents selected for vector index.</p>';
      return;
    }

    container.innerHTML = activeDocs.map(d => `
      <div class="p-3 bg-[#F9FAF6] dark:bg-[#1C201E] rounded-md border border-[#D6DDC9] dark:border-[#34422B]">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold font-mono px-1.5 py-0.5 rounded bg-[#EEF5E5] text-[#3F641C] dark:bg-[#1F2B18] dark:text-[#A8D66D] border border-[#C3D9AA] dark:border-[#34422B]">${d.type}</span>
          <span class="text-[11px] text-[#5C6654] dark:text-[#AEB5A6]">${d.size} • ${d.pages} pages</span>
        </div>
        <p class="text-xs font-semibold text-[#20251D] dark:text-[#E8EBDD] mt-2 truncate">${d.title}</p>
        <p class="text-[11px] text-[#5C6654] dark:text-[#AEB5A6] mt-1">ChromaDB Chunk Index: Ready</p>
      </div>
    `).join('');
  },

  updateHeaderModelBadge() {
    const model = state.getSelectedModel();
    const badge = document.getElementById('header-active-model-name');
    if (badge && model) {
      badge.textContent = model.name;
    }
  },

  getFileIcon(type) {
    switch (type) {
      case 'PDF': return this.icons.filePdf;
      case 'XLSX': return this.icons.fileXlsx;
      case 'DOCX': return this.icons.fileDocx;
      case 'ZIP': return this.icons.fileZip;
      default: return this.icons.filePdf;
    }
  },

  renderMessages() {
    const container = document.getElementById('chat-messages-container');
    const emptyState = document.getElementById('welcome-empty-state');
    if (!container) return;

    if (state.messages.length === 0) {
      container.classList.add('hidden');
      if (emptyState) emptyState.classList.remove('hidden');
      return;
    }

    if (emptyState) emptyState.classList.add('hidden');
    container.classList.remove('hidden');

    container.innerHTML = state.messages.map(m => {
      if (m.sender === 'user') {
        return `
          <div class="flex justify-end mb-5">
            <div class="max-w-2xl bg-[#EEF5E5] dark:bg-[#1F2B18] text-[#20251D] dark:text-[#E8EBDD] rounded-lg p-3.5 shadow-xs border border-[#C3D9AA] dark:border-[#34422B]">
              <p class="text-xs leading-relaxed whitespace-pre-wrap font-sans">${this.escapeHtml(m.text)}</p>
              <div class="text-[10px] text-[#5C6654] dark:text-[#AEB5A6] mt-1.5 text-right font-mono">${m.timestamp}</div>
            </div>
          </div>
        `;
      } else {
        const formattedContent = this.parseMarkdown(m.text) + (m.isStreaming ? '<span class="streaming-cursor"></span>' : '');
        return `
          <div class="mb-5">
            <div class="bg-white dark:bg-[#1C201E] border border-[#D6DDC9] dark:border-[#2D3827] rounded-lg p-4 shadow-xs">
              <div class="flex items-center justify-between pb-2 mb-3 border-b border-[#EAEFE2] dark:border-[#2D3827]">
                <div class="flex items-center space-x-2">
                  <span class="text-xs font-bold text-[#3F641C] dark:text-[#A8D66D] tracking-tight uppercase">${m.modelName}</span>
                  <span class="text-[10px] bg-[#F9FAF6] text-[#5C6654] dark:bg-[#171B19] dark:text-[#AEB5A6] font-mono px-2 py-0.5 rounded border border-[#D6DDC9] dark:border-[#34422B]">
                    Offline RAG Pipeline
                  </span>
                </div>
                <span class="text-[10px] text-[#5C6654] dark:text-[#AEB5A6] font-mono">${m.timestamp}</span>
              </div>
              
              <div id="content-${m.id}" class="prose-ai text-xs text-[#20251D] dark:text-[#E8EBDD] leading-relaxed">
                ${formattedContent}
              </div>

              ${!m.isStreaming ? `
                <div class="flex items-center justify-between pt-3 mt-3 border-t border-[#EAEFE2] dark:border-[#2D3827] text-xs text-[#5C6654] dark:text-[#AEB5A6]">
                  <div class="flex items-center space-x-2">
                    <button 
                      type="button" 
                      onclick="window.MRPLApp.copyText('${m.id}')"
                      class="px-2.5 py-1 rounded border border-[#D6DDC9] dark:border-[#34422B] hover:bg-[#EEF5E5] dark:hover:bg-[#1F2B18] hover:text-[#3F641C] dark:hover:text-[#A8D66D] cursor-pointer flex items-center space-x-1.5"
                    >
                      ${this.icons.copy}
                      <span>Copy</span>
                    </button>
                    <button 
                      type="button" 
                      onclick="window.MRPLApp.regenerate()"
                      class="px-2.5 py-1 rounded border border-[#D6DDC9] dark:border-[#34422B] hover:bg-[#EEF5E5] dark:hover:bg-[#1F2B18] hover:text-[#3F641C] dark:hover:text-[#A8D66D] cursor-pointer flex items-center space-x-1.5"
                    >
                      ${this.icons.refresh}
                      <span>Regenerate</span>
                    </button>
                  </div>
                  <div class="flex items-center space-x-3">
                    <button type="button" onclick="window.MRPLApp.feedback('up')" class="hover:text-[#3F641C] dark:hover:text-[#A8D66D] cursor-pointer flex items-center space-x-1" title="Helpful response">
                      ${this.icons.thumbUp}
                      <span>Helpful</span>
                    </button>
                    <button type="button" onclick="window.MRPLApp.feedback('down')" class="hover:text-red-600 cursor-pointer flex items-center space-x-1" title="Inaccurate response">
                      ${this.icons.thumbDown}
                      <span>Inaccurate</span>
                    </button>
                  </div>
                </div>
              ` : ''}
            </div>
          </div>
        `;
      }
    }).join('');

    this.scrollToBottom();
  },

  scrollToBottom() {
    const viewport = document.getElementById('chat-scroll-viewport');
    if (viewport) {
      viewport.scrollTop = viewport.scrollHeight;
    }
  },

  parseMarkdown(md) {
    if (!md) return '';

    let html = this.escapeHtml(md);

    // Code blocks ```
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, function (match, lang, code) {
      return `<div class="my-3 rounded-md border border-[#34422B] bg-[#151819] text-[#E8EBDD] overflow-hidden">
        <div class="flex items-center justify-between px-3 py-1.5 bg-[#171B19] font-mono text-[11px] text-[#A8D66D] border-b border-[#34422B]">
          <span>${lang || 'CODE'}</span>
          <button type="button" onclick="navigator.clipboard.writeText(this.parentNode.nextElementSibling.innerText)" class="hover:text-white cursor-pointer">Copy</button>
        </div>
        <pre class="p-3 overflow-x-auto text-xs font-mono"><code>${code}</code></pre>
      </div>`;
    });

    // Inline code `code`
    html = html.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded bg-[#EEF5E5] dark:bg-[#1F2B18] font-mono text-[11px] text-[#3F641C] dark:text-[#A8D66D] border border-[#C3D9AA] dark:border-[#34422B]">$1</code>');

    // Headings
    html = html.replace(/^### (.*$)/gim, '<h3 class="text-sm font-bold text-[#3F641C] dark:text-[#A8D66D] mt-3 mb-1.5 border-b border-[#D6DDC9] dark:border-[#34422B] pb-1">$1</h3>');
    html = html.replace(/^#### (.*$)/gim, '<h4 class="text-xs font-semibold text-[#20251D] dark:text-[#E8EBDD] mt-2.5 mb-1">$1</h4>');

    // GitHub alerts [!IMPORTANT]
    html = html.replace(/&gt; \[!IMPORTANT\]\n&gt; (.*$)/gim, '<div class="my-2 p-2.5 bg-[#EEF5E5] dark:bg-[#1F2B18] border-l-4 border-[#3F641C] dark:border-[#88B83E] rounded-r text-xs text-[#20251D] dark:text-[#E8EBDD] font-medium">⚠️ $1</div>');

    // Bold & Italics
    html = html.replace(/\*\*([^*]+)\*\`/g, '<strong>$1</strong>');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Blockquotes
    html = html.replace(/^&gt; (.*$)/gim, '<blockquote class="border-l-3 border-[#3F641C] dark:border-[#88B83E] pl-3 my-2 bg-[#EEF5E5] dark:bg-[#1F2B18] p-2 text-xs italic">$1</blockquote>');

    // Tables
    html = html.replace(/\|(.+)\|/g, function (match) {
      const rows = match.split('\n').filter(r => r.trim());
      if (rows.length === 0) return match;

      let tableHtml = '<div class="overflow-x-auto my-3"><table class="w-full text-xs border-collapse border border-[#D6DDC9] dark:border-[#34422B] rounded">';
      rows.forEach((row, idx) => {
        if (row.includes('---')) return;
        const cells = row.split('|').filter((c, i, a) => i > 0 && i < a.length - 1);
        const tag = idx === 0 ? 'th' : 'td';
        const cellBg = idx === 0 ? 'bg-[#EEF5E5] text-[#20251D] dark:bg-[#1F2B18] dark:text-[#A8D66D] font-bold' : '';
        tableHtml += `<tr>${cells.map(c => `<${tag} class="p-2 border border-[#D6DDC9] dark:border-[#34422B] ${cellBg}">${c.trim()}</${tag}>`).join('')}</tr>`;
      });
      tableHtml += '</table></div>';
      return tableHtml;
    });

    // Unordered lists (- item)
    html = html.replace(/^\s*-\s+(.*$)/gim, '<li class="ml-4 list-disc">$1</li>');

    // Source links [Source: ...]
    html = html.replace(/\[Source: ([^\]]+)\]/g, '<span class="inline-block font-mono text-[10px] bg-[#EEF5E5] text-[#3F641C] dark:bg-[#1F2B18] dark:text-[#A8D66D] border border-[#C3D9AA] dark:border-[#34422B] px-2 py-0.5 rounded my-1 mr-1">📄 Source: $1</span>');

    html = html.replace(/\n\n/g, '</p><p class="mt-2">');

    return `<p>${html}</p>`;
  },

  escapeHtml(str) {
    return (str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 z-50 bg-[#151819] text-[#E8EBDD] text-xs px-3.5 py-2 rounded shadow-lg border border-[#34422B] flex items-center space-x-2';
    toast.innerHTML = `<span class="text-[#A8D66D]">ℹ️</span><span>${message}</span>`;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, 2200);
  },

  setVoiceAssistantState(state) {
    const micBtn = document.getElementById('voice-assistant-btn');
    const statusBadge = document.getElementById('voice-status-indicator');

    if (!micBtn) return;

    if (state === 'recording') {
      micBtn.innerHTML = this.icons.micActive;
      micBtn.title = 'Listening... Click to stop voice input';
      micBtn.ariaLabel = 'Stop voice input';
      micBtn.classList.add('bg-red-100', 'dark:bg-red-950/60', 'border-red-400', 'dark:border-red-700');
      micBtn.classList.remove('hover:bg-[#EEF5E5]', 'dark:hover:bg-[#1F2B18]');

      if (statusBadge) {
        statusBadge.classList.remove('hidden');
      }
    } else if (state === 'error') {
      micBtn.innerHTML = this.icons.micOff;
      micBtn.title = 'Voice input unavailable or permission denied';
      micBtn.ariaLabel = 'Voice input unavailable';
      micBtn.classList.remove('bg-red-100', 'dark:bg-red-950/60', 'border-red-400', 'dark:border-red-700');
      
      if (statusBadge) {
        statusBadge.classList.add('hidden');
      }
    } else {
      micBtn.innerHTML = this.icons.mic;
      micBtn.title = 'Voice Assistant (Click to start speech input)';
      micBtn.ariaLabel = 'Start voice input';
      micBtn.classList.remove('bg-red-100', 'dark:bg-red-950/60', 'border-red-400', 'dark:border-red-700');
      micBtn.classList.add('hover:bg-[#EEF5E5]', 'dark:hover:bg-[#1F2B18]');

      if (statusBadge) {
        statusBadge.classList.add('hidden');
      }
    }
  }
};

if (typeof window !== 'undefined') {
  window.ui = ui;
}
