/**
 * AGNI: Air-Gapped Neural Intelligence - UI Rendering & DOM Helpers
 * 
 * Provides crisp SVG icon templates, Markdown parsing, document list renderers,
 * model switchers, message list viewports, toast alerts, theme toggling,
 * and Anime.js micro-interaction controllers for voice and processing states.
 */

const ui = {
  // SVG Icon Registry (Enterprise Industrial Design System)
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
    openFile: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>`,
    speaker: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5L6 9H2v6h4l5 4V5z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072M18.364 5.636a9 9 0 010 12.728"/></svg>`,
    speakerLoading: `<svg class="w-3.5 h-3.5 shrink-0 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>`,
    lock: `<svg class="w-3.5 h-3.5 text-[#3F641C] dark:text-[#A8D66D] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>`,
    send: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>`,
    stop: `<svg class="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>`,
    settings: `<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>`,
    copy: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>`,
    refresh: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>`,
    thumbUp: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"/></svg>`,
    thumbDown: `<svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v5a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"/></svg>`,
    mic: `<svg class="w-3.5 h-3.5 shrink-0 text-[#3F641C] dark:text-[#A8D66D]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg>`,
    micActive: `<svg class="w-3.5 h-3.5 text-red-600 dark:text-red-400 shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M12 14a3 3 0 003-3V5a3 3 0 10-6 0v6a3 3 0 003 3zm5-3a1 1 0 10-2 0 5 5 0 01-10 0 1 1 0 10-2 0 7 7 0 006 6.92V20H9a1 1 0 100 2h6a1 1 0 100-2h-2v-2.08A7 7 0 0017 11z"/></svg>`,
    micOff: `<svg class="w-3.5 h-3.5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18"/></svg>`,
    home: `<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 00-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>`,
    chat: `<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>`,
    fileText: `<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>`,
    database: `<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21 3.582 4 8 4s8-1.79 8-4"/></svg>`,
    cpu: `<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M3 9h2m-2 6h2m14-6h2m-2 6h2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/></svg>`,
    tool: `<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>`,
    clock: `<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`,
    fileSearch: `<svg class="w-4 h-4 shrink-0 text-[#3F641C] dark:text-[#A8D66D]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"/></svg>`,
    terminal: `<svg class="w-4 h-4 shrink-0 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>`,
    barChart: `<svg class="w-4 h-4 shrink-0 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>`,
    eye: `<svg class="w-4 h-4 shrink-0 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>`,
    fileCheck: `<svg class="w-4 h-4 shrink-0 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`
  },

  // Anime.js active animation references
  _voiceRingsAnim: null,
  _voiceEqAnim: null,
  _thinkingAnim: null,

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

  // NOTE: there used to be a renderModels() here targeting a
  // '#model-list-container' element that doesn't exist anywhere in
  // index.html — a dead no-op on every call, including its
  // updateHeaderModelBadge() call at the end, which never ran either. The
  // real, visible model switcher lives in the right panel (see
  // renderRightPanels() below), which now also carries the header-badge
  // update since that's the code path that actually executes.

  renderDocuments(initialHydrate = false) {
    const container = document.getElementById('document-list-container');
    const docCountBadge = document.getElementById('selected-docs-count');
    if (!container) return;

    if (state.documents.length === 0) {
      if (docCountBadge) docCountBadge.textContent = '0 Selected';
      container.innerHTML = `
        <div class="text-center py-6 px-2 text-xs text-[#5C6654] dark:text-[#AEB5A6]">
          <p class="font-medium text-[#20251D] dark:text-[#E8EBDD]">No documents uploaded yet</p>
          <p class="mt-1 text-[11px] leading-relaxed">Click <strong>+ Upload Document</strong> above to add files for AGNI to analyze.</p>
        </div>
      `;
      this.renderContextChips(initialHydrate);
      this.renderDrawerDocuments();
      return;
    }

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
      this.renderContextChips(initialHydrate);
      this.renderDrawerDocuments();
      return;
    }

    container.innerHTML = filteredDocs.map(d => this.documentCardHtml(d)).join('');

    this.renderContextChips(initialHydrate);
    this.renderDrawerDocuments();
  },

  /** Shared document-card markup used by both the sidebar list and the
   * full Documents workspace view, so the two never drift apart. */
  documentCardHtml(d) {
    return `
      <div
        id="doc-card-${d.id}"
        class="flex items-center justify-between p-2 rounded-md cursor-pointer border text-xs transition-all duration-150 relative group ${
          d.active
            ? 'bg-[#EEF5E5]/70 dark:bg-[#1F2B18]/70 border-[#3F641C] dark:border-[#88B83E] font-medium shadow-2xs'
            : 'bg-white dark:bg-[#171B19] border-[#D6DDC9] dark:border-[#34422B] hover:bg-[#F9FAF6] dark:hover:bg-[#1C201E]'
        }"
        onclick="window.MRPLApp.toggleDocumentSelection('${d.id}')"
      >
        <div class="flex items-center space-x-2 min-w-0 pr-1 flex-1">
          <input
            type="checkbox"
            ${d.active ? 'checked' : ''}
            class="w-3.5 h-3.5 text-[#3F641C] accent-[#3F641C] rounded border-[#D6DDC9] dark:border-[#34422B] focus:ring-[#3F641C] cursor-pointer shrink-0"
            onclick="event.stopPropagation(); window.MRPLApp.toggleDocumentSelection('${d.id}')"
          />
          ${this.getFileIcon(d.type)}
          <div class="min-w-0 flex-1">
            <p class="text-xs text-[#20251D] dark:text-[#E8EBDD] truncate" title="${d.title}">${d.title}</p>
            <p class="text-[10px] text-[#5C6654] dark:text-[#AEB5A6] truncate">${d.size} • ${d.category}</p>
          </div>
        </div>
        <button
          type="button"
          onclick="event.stopPropagation(); window.MRPLApp.deleteDocument('${d.id}')"
          class="p-1 text-[#5C6654] hover:text-red-600 dark:hover:text-red-400 rounded cursor-pointer shrink-0 transition-colors"
          title="Delete document"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
        </button>
      </div>
    `;
  },

  renderContextChips(initialHydrate = false) {
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

    const chipClass = initialHydrate ? 'inline-flex' : 'attachment-chip-enter inline-flex';

    container.innerHTML = activeDocs.map(d => `
      <span class="${chipClass} items-center space-x-1.5 text-xs bg-[#EEF5E5] dark:bg-[#1F2B18] text-[#20251D] dark:text-[#E8EBDD] px-2.5 py-1 rounded-md border border-[#C3D9AA] dark:border-[#34422B] shadow-2xs">
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

    if (!initialHydrate && window.anime && typeof window.anime === 'function') {
      try {
        window.anime({
          targets: '.attachment-chip-enter',
          translateY: [4, 0],
          opacity: [0, 1],
          duration: 200,
          easing: 'easeOutCubic',
          delay: window.anime.stagger(40)
        });
      } catch (err) {
        // Fallback CSS handles animation
      }
    }
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
        <p class="text-[11px] text-[#5C6654] dark:text-[#AEB5A6] mt-1">Qdrant Chunk Index: Ready</p>
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

  updateHeaderChatTitle() {
    const titleNode = document.getElementById('current-chat-title');
    if (titleNode) {
      const conv = state.conversations.find(c => c.id === state.currentChatId);
      titleNode.textContent = conv ? conv.title : 'Refinery Maintenance & Safety Audit';
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

  // Matches an absolute local filesystem path (macOS/Linux style, starting
  // with "/") ending in a document extension the backend's generation tools
  // (pdf_tool/docx_tool/pptx_tool) or an uploaded attachment can produce —
  // used to offer a real "Open file" button instead of leaving the user to
  // copy/paste a path into Finder manually. Tried in order: backtick-
  // delimited and bracketed-tool-result forms first (both tolerate spaces
  // in the filename), then a bare-path fallback that stops at whitespace.
  FILE_PATH_PATTERNS: [
    /`(\/[^`]+\.(?:pptx|docx|pdf|xlsx|csv))`/gi,
    /\bat:?\s+(\/[^\]\n]+\.(?:pptx|docx|pdf|xlsx|csv))\]/gi,
    /(\/[^\s`'"()\[\]<>]+\.(?:pptx|docx|pdf|xlsx|csv))\b/gi,
  ],

  extractFilePaths(text) {
    if (!text || typeof text !== 'string') return [];
    const found = [];
    for (const re of this.FILE_PATH_PATTERNS) {
      re.lastIndex = 0;
      let match;
      while ((match = re.exec(text)) !== null) {
        found.push(match[1]);
      }
    }
    return [...new Set(found)];
  },

  // Round-trips a filesystem path through base64 so it can sit safely inside
  // an inline onclick="..." HTML attribute regardless of quotes, backslashes,
  // or unicode characters in the path — decoded on the other end in app.js.
  encodePathForAttr(path) {
    try {
      return btoa(unescape(encodeURIComponent(path)));
    } catch (e) {
      return btoa(path.replace(/[^\x00-\xFF]/g, '_'));
    }
  },

  renderMessages(initialHydrate = false) {
    const container = document.getElementById('chat-messages-container');
    const emptyState = document.getElementById('welcome-empty-state');
    if (!container) return;

    this.updateHeaderChatTitle();

    // Filter out transient items before rendering
    const validMessages = (state.messages || []).filter(m => m && m.text !== undefined);

    if (validMessages.length === 0) {
      container.classList.add('hidden');
      if (emptyState) emptyState.classList.remove('hidden');
      return;
    }

    if (emptyState) emptyState.classList.add('hidden');
    container.classList.remove('hidden');

    const chipClass = initialHydrate ? 'inline-flex' : 'attachment-chip-enter inline-flex';

    container.innerHTML = validMessages.map(m => {
      if (m.sender === 'user') {
        return `
          <div class="flex justify-end mb-5">
            <div class="max-w-2xl bg-[#EEF5E5] dark:bg-[#1F2B18] text-[#20251D] dark:text-[#E8EBDD] rounded-lg p-3.5 shadow-xs border border-[#C3D9AA] dark:border-[#34422B]">
              <p class="text-xs leading-relaxed whitespace-pre-wrap font-sans">${this.escapeHtml(m.text)}</p>
              ${m.attachedDocs && m.attachedDocs.length > 0 ? `
                <div class="mt-2.5 pt-2.5 border-t border-[#C3D9AA] dark:border-[#34422B]/70 flex flex-wrap gap-2">
                  ${m.attachedDocs.map(doc => `
                    <div class="${chipClass} items-center space-x-2 p-2 rounded-md bg-white/90 dark:bg-[#171B19]/90 border border-[#C3D9AA] dark:border-[#34422B] text-xs shadow-2xs">
                      ${this.getFileIcon(doc.type)}
                      <div class="min-w-0">
                        <p class="text-xs font-semibold text-[#20251D] dark:text-[#E8EBDD] truncate max-w-[220px]" title="${this.escapeHtml(doc.title)}">${this.escapeHtml(doc.title)}</p>
                        <p class="text-[10px] text-[#5C6654] dark:text-[#AEB5A6]">${doc.type || 'PDF'} ${doc.size ? '• ' + doc.size : ''} • Attached</p>
                      </div>
                    </div>
                  `).join('')}
                </div>
              ` : ''}
              <div class="text-[10px] text-[#5C6654] dark:text-[#AEB5A6] mt-1.5 text-right font-mono">${m.timestamp}</div>
            </div>
          </div>
        `;
      } else if (m.isThinking) {
        const hasDocCtx = m.attachedDocs && m.attachedDocs.length > 0;
        if (hasDocCtx) {
          // Document request → taskProgress.js will populate this container
          return `
            <div class="mb-5" id="thinking-container-${m.id}">
              <div id="task-progress-host-${m.id}">
                <!-- task-progress block injected by taskProgress.js -->
              </div>
            </div>
          `;
        }
        // Text-only request → simple classic thinking card
        return `
          <div class="mb-5" id="thinking-container-${m.id}">
            <div class="thinking-card-pulse bg-white dark:bg-[#1C201E] border border-[#D6DDC9] dark:border-[#2D3827] rounded-lg p-4 shadow-xs">
              <div class="flex items-center justify-between pb-2 mb-2 border-b border-[#EAEFE2] dark:border-[#2D3827]">
                <div class="flex items-center space-x-2">
                  <span class="text-xs font-extrabold text-[#3F641C] dark:text-[#A8D66D] tracking-tight uppercase">AGNI</span>
                  <span class="text-[#D6DDC9] dark:text-[#34422B]">|</span>
                  <span class="text-[11px] font-semibold text-[#20251D] dark:text-[#E8EBDD]">${m.modelName}</span>
                  <span class="text-[10px] bg-[#EEF5E5] text-[#3F641C] dark:bg-[#1F2B18] dark:text-[#A8D66D] font-mono px-2 py-0.5 rounded border border-[#C3D9AA] dark:border-[#34422B]">
                    Air-Gapped RAG
                  </span>
                </div>
                <span class="text-[10px] text-[#5C6654] dark:text-[#AEB5A6] font-mono">${m.timestamp}</span>
              </div>
              <div class="flex items-center space-x-2 py-1">
                <span class="w-2 h-2 rounded-full bg-[#3F641C] dark:bg-[#A8D66D] animate-ping shrink-0"></span>
                <span class="thinking-text-fade text-xs font-semibold text-[#3F641C] dark:text-[#A8D66D]">AGNI Thinking...</span>
              </div>
            </div>
          </div>
        `;
      } else {
        const formattedContent = this.parseMarkdown(m.text) + (m.isStreaming ? '<span class="streaming-cursor"></span>' : '');
        const filePaths = m.isStreaming ? [] : this.extractFilePaths(m.text);
        return `
          <div class="mb-5">
            <div class="bg-white dark:bg-[#1C201E] border border-[#D6DDC9] dark:border-[#2D3827] rounded-lg p-4 shadow-xs">
              <div class="flex items-center justify-between pb-2 mb-3 border-b border-[#EAEFE2] dark:border-[#2D3827]">
                <div class="flex items-center space-x-2">
                  <span class="text-xs font-extrabold text-[#3F641C] dark:text-[#A8D66D] tracking-tight uppercase">AGNI</span>
                  <span class="text-[#D6DDC9] dark:text-[#34422B]">|</span>
                  <span class="text-[11px] font-semibold text-[#20251D] dark:text-[#E8EBDD]">${m.modelName}</span>
                  <span class="text-[10px] bg-[#EEF5E5] text-[#3F641C] dark:bg-[#1F2B18] dark:text-[#A8D66D] font-mono px-2 py-0.5 rounded border border-[#C3D9AA] dark:border-[#34422B]">
                    Air-Gapped RAG
                  </span>
                </div>
                <span class="text-[10px] text-[#5C6654] dark:text-[#AEB5A6] font-mono">${m.timestamp}</span>
              </div>

              <div id="content-${m.id}" class="prose-ai text-xs text-[#20251D] dark:text-[#E8EBDD] leading-relaxed">
                ${formattedContent}
              </div>

              ${filePaths.length > 0 ? `
                <div class="flex flex-wrap gap-2 mt-3 pt-3 border-t border-[#EAEFE2] dark:border-[#2D3827]">
                  ${filePaths.map(p => `
                    <button
                      type="button"
                      onclick="window.MRPLApp.openGeneratedFile('${this.encodePathForAttr(p)}')"
                      class="px-2.5 py-1 rounded border border-[#C3D9AA] dark:border-[#34422B] bg-[#EEF5E5] dark:bg-[#1F2B18] text-[#3F641C] dark:text-[#A8D66D] hover:bg-[#DCEBC7] dark:hover:bg-[#28351F] cursor-pointer flex items-center space-x-1.5 transition-colors text-xs font-medium"
                      title="${this.escapeHtml(p)}"
                    >
                      ${this.icons.openFile}
                      <span>Open ${this.escapeHtml(p.split('/').pop())}</span>
                    </button>
                  `).join('')}
                </div>
              ` : ''}

              ${!m.isStreaming ? `
                <div class="flex items-center justify-between pt-3 mt-3 border-t border-[#EAEFE2] dark:border-[#2D3827] text-xs text-[#5C6654] dark:text-[#AEB5A6]">
                  <div class="flex items-center space-x-2">
                    <button 
                      type="button" 
                      onclick="window.MRPLApp.copyText('${m.id}')"
                      class="px-2.5 py-1 rounded border border-[#D6DDC9] dark:border-[#34422B] hover:bg-[#EEF5E5] dark:hover:bg-[#1F2B18] hover:text-[#3F641C] dark:hover:text-[#A8D66D] cursor-pointer flex items-center space-x-1.5 transition-colors"
                    >
                      ${this.icons.copy}
                      <span>Copy</span>
                    </button>
                    <button
                      type="button"
                      onclick="window.MRPLApp.regenerate()"
                      class="px-2.5 py-1 rounded border border-[#D6DDC9] dark:border-[#34422B] hover:bg-[#EEF5E5] dark:hover:bg-[#1F2B18] hover:text-[#3F641C] dark:hover:text-[#A8D66D] cursor-pointer flex items-center space-x-1.5 transition-colors"
                    >
                      ${this.icons.refresh}
                      <span>Regenerate</span>
                    </button>
                    <button
                      type="button"
                      id="speak-btn-${m.id}"
                      onclick="window.MRPLApp.speakMessage('${m.id}')"
                      class="px-2.5 py-1 rounded border border-[#D6DDC9] dark:border-[#34422B] hover:bg-[#EEF5E5] dark:hover:bg-[#1F2B18] hover:text-[#3F641C] dark:hover:text-[#A8D66D] cursor-pointer flex items-center space-x-1.5 transition-colors"
                      title="Read this response aloud (Piper, on-device)"
                    >
                      ${this.icons.speaker}
                      <span>Speak</span>
                    </button>
                  </div>
                  <div class="flex items-center space-x-3">
                    <button type="button" onclick="window.MRPLApp.feedback('up')" class="hover:text-[#3F641C] dark:hover:text-[#A8D66D] cursor-pointer flex items-center space-x-1 transition-colors" title="Helpful response">
                      ${this.icons.thumbUp}
                      <span>Helpful</span>
                    </button>
                    <button type="button" onclick="window.MRPLApp.feedback('down')" class="hover:text-red-600 cursor-pointer flex items-center space-x-1 transition-colors" title="Inaccurate response">
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

    const codeBlocks = [];

    // Extract code blocks first to protect them from HTML escaping and paragraph injection
    let text = md.replace(/```(\w+)?\s*\n([\s\S]*?)```/g, (match, lang, code) => {
      const idx = codeBlocks.length;
      codeBlocks.push({
        lang: lang || 'CODE',
        code: this.escapeHtml(code.trimEnd()),
      });
      return `___AGNI_CODE_BLOCK_${idx}___`;
    });

    let html = this.escapeHtml(text);

    // Inline code `code`
    html = html.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded bg-[#EEF5E5] dark:bg-[#1F2B18] font-mono text-[11px] text-[#3F641C] dark:text-[#A8D66D] border border-[#C3D9AA] dark:border-[#34422B]">$1</code>');

    // Headings
    html = html.replace(/^### (.*$)/gim, '<h3 class="text-sm font-bold text-[#3F641C] dark:text-[#A8D66D] mt-3 mb-1.5 border-b border-[#D6DDC9] dark:border-[#34422B] pb-1">$1</h3>');
    html = html.replace(/^#### (.*$)/gim, '<h4 class="text-xs font-semibold text-[#20251D] dark:text-[#E8EBDD] mt-2.5 mb-1">$1</h4>');

    // GitHub alerts [!IMPORTANT]
    html = html.replace(/&gt; \[!IMPORTANT\]\n&gt; (.*$)/gim, '<div class="my-2 p-2.5 bg-[#EEF5E5] dark:bg-[#1F2B18] border-l-4 border-[#3F641C] dark:border-[#88B83E] rounded-r text-xs text-[#20251D] dark:text-[#E8EBDD] font-medium">⚠️ $1</div>');

    // Bold & Italics
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

    // Paragraphs
    html = html.replace(/\n\n/g, '</p><p class="mt-2">');

    // Restore Code blocks with pristine styling
    codeBlocks.forEach((cb, idx) => {
      const codeMarkup = `</p><div class="my-3 rounded-md border border-[#34422B] bg-[#151819] text-[#E8EBDD] overflow-hidden">
        <div class="flex items-center justify-between px-3 py-1.5 bg-[#171B19] font-mono text-[11px] text-[#A8D66D] border-b border-[#34422B]">
          <span>${cb.lang}</span>
          <button type="button" onclick="navigator.clipboard.writeText(this.parentNode.nextElementSibling.innerText)" class="hover:text-white cursor-pointer">Copy</button>
        </div>
        <pre class="p-3 overflow-x-auto text-xs font-mono"><code>${cb.code}</code></pre>
      </div><p class="mt-2">`;
      html = html.replace(`___AGNI_CODE_BLOCK_${idx}___`, codeMarkup);
    });

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

  /**
   * Voice Assistant 6-State Visual & Animation Controller
   */
  setVoiceAssistantState(state) {
    const micBtn = document.getElementById('voice-assistant-btn');
    const statusBadge = document.getElementById('voice-status-indicator');
    const rings = document.querySelectorAll('.voice-ring');
    const eqBars = document.querySelectorAll('.eq-bar');

    if (!micBtn) return;

    const animeAvailable = window.anime && typeof window.anime === 'function';

    if (state === 'recording') {
      micBtn.innerHTML = this.icons.micActive;
      micBtn.title = 'Listening... Click to stop speech input';
      micBtn.ariaLabel = 'Stop voice input';
      micBtn.classList.add('bg-red-100', 'dark:bg-red-950/60', 'border-red-400', 'dark:border-red-700');
      micBtn.classList.remove('hover:bg-[#EEF5E5]', 'dark:hover:bg-[#1F2B18]');

      if (statusBadge) statusBadge.classList.remove('hidden');

      if (animeAvailable) {
        window.anime({
          targets: micBtn,
          scale: [1, 1.12, 1],
          duration: 250,
          easing: 'easeOutQuad'
        });

        if (rings.length > 0) {
          window.anime.remove(rings);
          this._voiceRingsAnim = window.anime({
            targets: rings,
            scale: [0.8, 1.85],
            opacity: [0.75, 0],
            duration: 1600,
            delay: window.anime.stagger(450),
            loop: true,
            easing: 'easeOutSine'
          });
        }

        if (eqBars.length > 0) {
          window.anime.remove(eqBars);
          this._voiceEqAnim = window.anime({
            targets: eqBars,
            scaleY: [0.2, 1.0],
            duration: 400,
            delay: window.anime.stagger(120),
            direction: 'alternate',
            loop: true,
            easing: 'easeInOutQuad'
          });
        }
      }
    } else if (state === 'processing') {
      micBtn.innerHTML = this.icons.mic;
      micBtn.title = 'Processing voice transcript...';
      if (statusBadge) {
        statusBadge.classList.remove('hidden');
        const textNode = statusBadge.querySelector('span:nth-child(2)');
        if (textNode) textNode.textContent = 'AGNI Transcribing voice audio...';
      }
      this.cleanupVoiceAnimations();
    } else if (state === 'error') {
      micBtn.innerHTML = this.icons.micOff;
      micBtn.title = 'Voice input unavailable or permission denied';
      micBtn.ariaLabel = 'Voice input unavailable';
      micBtn.classList.remove('bg-red-100', 'dark:bg-red-950/60', 'border-red-400', 'dark:border-red-700');
      
      if (statusBadge) statusBadge.classList.add('hidden');
      this.cleanupVoiceAnimations();

      setTimeout(() => {
        this.setVoiceAssistantState('idle');
      }, 2500);
    } else {
      micBtn.innerHTML = this.icons.mic;
      micBtn.title = 'Voice Assistant (Click to start speech input)';
      micBtn.ariaLabel = 'Start voice input';
      micBtn.classList.remove('bg-red-100', 'dark:bg-red-950/60', 'border-red-400', 'dark:border-red-700');
      micBtn.classList.add('hover:bg-[#EEF5E5]', 'dark:hover:bg-[#1F2B18]');

      if (statusBadge) statusBadge.classList.add('hidden');
      this.cleanupVoiceAnimations();

      if (animeAvailable && rings.length > 0) {
        window.anime({
          targets: rings,
          scale: 0.8,
          opacity: 0,
          duration: 200,
          easing: 'easeOutQuad'
        });
      }
    }
  },

  cleanupVoiceAnimations() {
    const rings = document.querySelectorAll('.voice-ring');
    const eqBars = document.querySelectorAll('.eq-bar');

    if (window.anime && typeof window.anime === 'function') {
      if (rings.length > 0) window.anime.remove(rings);
      if (eqBars.length > 0) window.anime.remove(eqBars);
    }

    rings.forEach(r => {
      r.style.transform = 'scale(0.8)';
      r.style.opacity = '0';
    });
  },

  /**
   * Render Vertical Sidebar Navigation Links
   */
  renderNavigation() {
    const container = document.getElementById('sidebar-nav-container');
    if (!container) return;

    const navItems = CONFIG.NAV_ITEMS || [];
    const activeNav = state.activeNav || 'chat';

    container.innerHTML = navItems.map(item => {
      const isActive = item.id === activeNav;
      const iconSvg = this.icons[item.icon] || this.icons.chat;
      return `
        <button 
          type="button" 
          onclick="window.MRPLApp.navigate('${item.id}')"
          class="w-full flex items-center space-x-2.5 px-3 py-2 rounded-md text-xs font-medium cursor-pointer transition-all duration-150 text-left border-l-3 ${
            isActive 
              ? 'nav-item-active bg-[#EEF5E5] dark:bg-[#1F2B18] text-[#20251D] dark:text-[#E8EBDD] border-[#3F641C] dark:border-[#88B83E]' 
              : 'border-transparent text-[#5C6654] dark:text-[#AEB5A6] hover:bg-[#F4F5F0] dark:hover:bg-[#1F2522] hover:text-[#20251D] dark:hover:text-[#E8EBDD]'
          }"
        >
          <span class="${isActive ? 'text-[#3F641C] dark:text-[#A8D66D]' : 'text-[#8A9581] dark:text-[#6E7B68]'}">${iconSvg}</span>
          <span class="truncate flex-1">${item.label}</span>
        </button>
      `;
    }).join('');
  },

  /**
   * Render Horizontal Quick Action Cards
   */
  renderQuickActions() {
    const container = document.getElementById('quick-action-cards-container');
    if (!container) return;

    const actions = CONFIG.QUICK_ACTIONS || [];
    container.innerHTML = actions.map(act => `
      <button 
        type="button"
        onclick="window.MRPLApp.triggerQuickAction('${act.prompt}')"
        class="quick-action-card p-3 bg-white dark:bg-[#161B19] border border-[#D6DDC9] dark:border-[#283623] hover:border-[#3F641C] dark:hover:border-[#88B83E] rounded-md text-xs text-left cursor-pointer transition-all shadow-2xs group flex flex-col justify-between"
      >
        <div class="flex items-center justify-between mb-1.5">
          <span class="p-1.5 rounded bg-[#EEF5E5] dark:bg-[#1F2B18] text-[#3F641C] dark:text-[#A8D66D] border border-[#C3D9AA] dark:border-[#34422B] shrink-0">
            ${this.icons[act.icon] || this.icons.fileSearch}
          </span>
          <span class="text-[10px] text-[#8A9581] dark:text-[#6E7B68] font-mono group-hover:text-[#3F641C] dark:group-hover:text-[#A8D66D]">Run →</span>
        </div>
        <div>
          <h4 class="font-bold text-[#20251D] dark:text-[#E8EBDD] group-hover:text-[#3F641C] dark:group-hover:text-[#A8D66D] truncate text-xs">${act.title}</h4>
          <p class="text-[11px] text-[#5C6654] dark:text-[#AEB5A6] mt-0.5 line-clamp-2">${act.desc}</p>
        </div>
      </button>
    `).join('');
  },

  /**
   * Render Right Information / System Panels
   */
  renderRightPanels() {
    // Keeps the "Model: <name>" badge in the workspace sub-header in sync —
    // this used to live inside a dead renderModels() function that never
    // actually ran (see the note above), so the badge never updated at all.
    this.updateHeaderModelBadge();

    // 1. Model Orchestrator Panel
    const modelsContainer = document.getElementById('right-panel-models-list');
    if (modelsContainer) {
      modelsContainer.innerHTML = CONFIG.MODELS.map(m => {
        const isActive = m.id === state.activeModelId;
        return `
          <div 
            onclick="window.MRPLApp.switchModel('${m.id}')"
            class="p-2.5 rounded-md border text-xs cursor-pointer transition-all duration-150 ${
              isActive 
                ? 'bg-[#EEF5E5]/80 dark:bg-[#1F2B18]/80 border-[#3F641C] dark:border-[#88B83E] shadow-2xs' 
                : 'bg-white dark:bg-[#161B19] border-[#D6DDC9] dark:border-[#283623] hover:bg-[#F9FAF6] dark:hover:bg-[#1F2522]'
            }"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-1.5 min-w-0">
                <span class="w-2 h-2 rounded-full ${isActive ? 'bg-[#3F641C] dark:bg-[#88B83E] animate-pulse' : 'bg-gray-400'} shrink-0"></span>
                <span class="font-bold text-[#20251D] dark:text-[#E8EBDD] truncate text-xs">${m.name}</span>
              </div>
              <span class="font-mono text-[9px] px-1.5 py-0.5 rounded ${isActive ? 'bg-[#3F641C] text-white' : 'bg-[#EEF5E5] dark:bg-[#1F2B18] text-[#3F641C] dark:text-[#A8D66D]'}">${m.code}</span>
            </div>
            <p class="text-[10px] text-[#5C6654] dark:text-[#AEB5A6] mt-1 font-mono">${m.backendModel} • ${m.badge}</p>
          </div>
        `;
      }).join('');
    }

    // 2. Agent Tools Panel
    const toolsContainer = document.getElementById('right-panel-tools-list');
    if (toolsContainer) {
      const tools = CONFIG.AGENT_TOOLS || [];
      toolsContainer.innerHTML = tools.map(t => `
        <div class="flex items-center justify-between p-2 rounded bg-white dark:bg-[#161B19] border border-[#D6DDC9] dark:border-[#283623] text-xs">
          <div class="min-w-0 pr-1">
            <p class="font-semibold text-[#20251D] dark:text-[#E8EBDD] truncate text-[11px]">${t.name}</p>
            <p class="text-[10px] text-[#5C6654] dark:text-[#AEB5A6] truncate">${t.desc}</p>
          </div>
          <span class="text-[9px] font-bold font-mono px-1.5 py-0.5 rounded bg-[#EEF5E5] text-[#3F641C] dark:bg-[#1F2B18] dark:text-[#A8D66D] border border-[#C3D9AA] dark:border-[#34422B] shrink-0">
            ${t.status}
          </span>
        </div>
      `).join('');
    }

    // 3. System Status Panel
    const statusContainer = document.getElementById('right-panel-status-list');
    if (statusContainer) {
      const statuses = CONFIG.SYSTEM_STATUS || [];
      statusContainer.innerHTML = statuses.map(s => `
        <div class="flex items-center justify-between text-[11px] p-1.5 border-b border-[#D6DDC9]/60 dark:border-[#283623] last:border-0">
          <span class="text-[#5C6654] dark:text-[#AEB5A6] font-medium">${s.label}:</span>
          <span class="font-semibold font-mono text-[#3F641C] dark:text-[#A8D66D]">${s.value}</span>
        </div>
      `).join('');
    }
  },

  /** Model card with a real install-status badge, used by the Model Hub
   * workspace view. `liveInfo` is the matching entry from api.getModels()
   * once it resolves (has `.installed_locally`); undefined while loading
   * or if the fetch failed, in which case we show a neutral state instead
   * of guessing. */
  modelCardHtml(m, liveInfo) {
    let badge;
    if (!liveInfo || typeof liveInfo.installed_locally !== 'boolean') {
      badge = `<span class="text-[10px] bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300 px-2 py-0.5 rounded border border-gray-300 dark:border-gray-700 font-semibold">Checking…</span>`;
    } else if (liveInfo.installed_locally) {
      badge = `<span class="text-[10px] bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 px-2 py-0.5 rounded border border-emerald-300 font-semibold">Installed</span>`;
    } else {
      badge = `<span class="text-[10px] bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 px-2 py-0.5 rounded border border-amber-300 font-semibold" title="Run: ollama pull ${m.backendModel}">Not Pulled</span>`;
    }
    const isActive = m.id === state.activeModelId;
    return `
      <div id="model-card-${m.id}" class="p-4 rounded-md border ${isActive ? 'border-[#3F641C] dark:border-[#88B83E] bg-[#F9FAF6] dark:bg-[#1F2B18]/40' : 'border-[#D6DDC9] dark:border-[#283623] bg-[#F9FAF6] dark:bg-[#171B19]'} flex items-center justify-between">
        <div class="min-w-0 pr-3">
          <div class="flex items-center space-x-2 flex-wrap gap-y-1">
            <span class="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#EEF5E5] dark:bg-[#1F2B18] text-[#3F641C] dark:text-[#A8D66D] border border-[#C3D9AA] dark:border-[#34422B]">${m.code}</span>
            <h4 class="font-bold text-xs text-[#20251D] dark:text-[#E8EBDD]">${m.name}</h4>
            ${badge}
          </div>
          <p class="text-xs text-[#5C6654] dark:text-[#AEB5A6] mt-1">${m.description}</p>
          <p class="text-[11px] font-mono text-[#3F641C] dark:text-[#A8D66D] mt-1">Backend: ${m.backendModel}</p>
        </div>
        <button type="button" onclick="window.MRPLApp.switchModel('${m.id}')" class="px-3 py-1 ${isActive ? 'bg-[#EEF5E5] dark:bg-[#1F2B18] text-[#3F641C] dark:text-[#A8D66D] border border-[#3F641C] dark:border-[#88B83E]' : 'bg-[#3F641C] hover:bg-[#304D16] text-white'} text-xs font-semibold rounded cursor-pointer shrink-0">
          ${isActive ? 'Selected' : 'Select Model'}
        </button>
      </div>
    `;
  },

  /** Fetches real Ollama install status and re-renders the Model Hub cards
   * in place once it resolves — cards start in a neutral "Checking…" state
   * so there's no flash of a wrong "Not Pulled" badge before data arrives. */
  async loadModelInstallStatus() {
    try {
      const models = await api.getModels();
      const container = document.getElementById('models-view-list');
      if (!container || !Array.isArray(models)) return; // view was navigated away from, or fetch fell all the way back
      const byId = new Map(models.map(m => [m.id, m]));
      container.innerHTML = CONFIG.MODELS.map(m => this.modelCardHtml(m, byId.get(m.id))).join('');
    } catch (err) {
      console.warn('[UI] Could not load model install status:', err);
    }
  },

  /** Fetches the real local Qdrant collection stats and fills in the
   * Knowledge Base view's metric tiles, replacing the "Loading…" placeholder. */
  async loadKnowledgeStats() {
    const container = document.getElementById('knowledge-stats-container');
    if (!container) return;
    try {
      const stats = await api.getRagStatus();
      if (stats.status === 'ready' || stats.status === 'empty') {
        container.innerHTML = `
          <div class="p-3 bg-[#EEF5E5] dark:bg-[#1F2B18] border border-[#C3D9AA] dark:border-[#34422B] rounded text-xs">
            <span class="text-[10px] font-mono uppercase text-[#3F641C] dark:text-[#A8D66D] font-bold block">Total Chunks</span>
            <span class="text-lg font-extrabold text-[#20251D] dark:text-[#E8EBDD]">${(stats.chunk_count || 0).toLocaleString()}</span>
          </div>
          <div class="p-3 bg-[#EEF5E5] dark:bg-[#1F2B18] border border-[#C3D9AA] dark:border-[#34422B] rounded text-xs">
            <span class="text-[10px] font-mono uppercase text-[#3F641C] dark:text-[#A8D66D] font-bold block">Embedding Model</span>
            <span class="text-xs font-semibold text-[#20251D] dark:text-[#E8EBDD]">${this.escapeHtml(stats.embedding_model || 'BAAI/bge-small-en-v1.5')}</span>
          </div>
          <div class="p-3 bg-[#EEF5E5] dark:bg-[#1F2B18] border border-[#C3D9AA] dark:border-[#34422B] rounded text-xs">
            <span class="text-[10px] font-mono uppercase text-[#3F641C] dark:text-[#A8D66D] font-bold block">Vector Store</span>
            <span class="text-xs font-semibold text-[#20251D] dark:text-[#E8EBDD]">${this.escapeHtml(stats.vector_db || 'Qdrant (local)')}</span>
          </div>
          ${stats.status === 'empty' ? `<div class="sm:col-span-3 text-[11px] text-amber-700 dark:text-amber-400 mt-1">${this.escapeHtml(stats.message || 'No documents indexed yet.')}</div>` : ''}
        `;
      } else {
        container.innerHTML = `
          <div class="sm:col-span-3 p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 rounded text-xs text-amber-800 dark:text-amber-300">
            Could not reach the RAG status endpoint. ${this.escapeHtml(stats.message || 'Is the backend running?')}
          </div>
        `;
      }
    } catch (err) {
      console.warn('[UI] Could not load knowledge base stats:', err);
    }
  },

  /** Fetches live Ollama/database/RAG status for the Settings view. */
  async loadSettingsStatus() {
    const el = document.getElementById('settings-live-status');
    if (!el) return;
    try {
      const [sys, rag] = await Promise.all([api.getSystemStatus(), api.getRagStatus()]);
      const lines = [];
      if (sys) {
        const modelsList = sys.ollama_models || [];
        lines.push(`Ollama: ${modelsList.length > 0 ? `${modelsList.length} model(s) installed (${modelsList.join(', ')})` : 'not reachable'}`);
        const db = sys.database;
        lines.push(`Database: ${db && db.status === 'connected' ? `connected (${db.active_db}, ${db.latency_ms}ms)` : (db ? db.status : 'unavailable')}`);
        lines.push(`Indexed documents: ${sys.indexed_documents_count ?? 'n/a'}`);
      } else {
        lines.push(`Backend unreachable at ${CONFIG.API_BASE_URL}`);
      }
      if (rag) {
        lines.push(`RAG knowledge base: ${rag.status === 'ready' ? `${rag.chunk_count} chunks indexed` : (rag.status === 'empty' ? 'no documents indexed yet' : (rag.message || rag.status))}`);
      }
      el.innerHTML = lines.map(l => `<div>${this.escapeHtml(l)}</div>`).join('');
    } catch (err) {
      el.textContent = 'Could not reach backend status endpoints.';
      console.warn('[UI] Settings status load failed:', err);
    }
  },

  /**
   * Switch View in Central Workspace based on Nav ID
   */
  switchView(navId) {
    this.renderNavigation();
    
    // Switch main workspace content views
    const chatWorkspace = document.getElementById('workspace-chat-view');
    const otherViewsContainer = document.getElementById('workspace-other-views');
    const viewTitleNode = document.getElementById('current-chat-title');

    if (!chatWorkspace) return;

    if (navId === 'chat' || navId === 'home') {
      chatWorkspace.classList.remove('hidden');
      if (otherViewsContainer) otherViewsContainer.classList.add('hidden');
    } else {
      chatWorkspace.classList.add('hidden');
      if (otherViewsContainer) {
        otherViewsContainer.classList.remove('hidden');
        this.renderOtherViewContent(navId, otherViewsContainer);
      }
    }
  },

  renderOtherViewContent(navId, container) {
    let title = 'Section';
    let contentHtml = '';

    switch (navId) {
      case 'documents': {
        title = 'Document Context & OCR Index';
        const docs = state.documents || [];
        contentHtml = `
          <div class="space-y-4 max-w-4xl mx-auto py-4">
            <div class="bg-white dark:bg-[#161B19] border border-[#D6DDC9] dark:border-[#283623] rounded-lg p-5">
              <div class="flex items-center justify-between mb-2">
                <h3 class="text-sm font-extrabold text-[#20251D] dark:text-[#E8EBDD] uppercase tracking-wider">Document Context Management</h3>
                <button type="button" onclick="document.getElementById('sidebar-file-input').click()" class="px-3 py-1.5 bg-[#3F641C] hover:bg-[#304D16] text-white text-xs font-semibold rounded cursor-pointer flex items-center space-x-1.5 shrink-0">
                  ${this.icons.upload}
                  <span>Upload Document</span>
                </button>
              </div>
              <p class="text-xs text-[#5C6654] dark:text-[#AEB5A6] leading-relaxed mb-4">Upload and select confidential refinery documents (PDF, DOCX, TXT) for offline OCR and Qdrant RAG indexing. Checking a document makes it part of the active chat context.</p>
              <div id="documents-view-list" class="space-y-2">
                ${docs.length === 0
                  ? `<div class="text-center py-6 text-xs text-[#5C6654] dark:text-[#AEB5A6]">No documents uploaded yet. Click <strong>Upload Document</strong> above to add one.</div>`
                  : docs.map(d => this.documentCardHtml(d)).join('')}
              </div>
            </div>
          </div>
        `;
        break;
      }

      case 'knowledge':
        title = 'Qdrant Vector Store';
        contentHtml = `
          <div class="space-y-4 max-w-4xl mx-auto py-4">
            <div class="bg-white dark:bg-[#161B19] border border-[#D6DDC9] dark:border-[#283623] rounded-lg p-5">
              <h3 class="text-sm font-extrabold text-[#20251D] dark:text-[#E8EBDD] uppercase tracking-wider mb-2">On-Premise Vector Database Metrics</h3>
              <p class="text-xs text-[#5C6654] dark:text-[#AEB5A6] leading-relaxed mb-4">Local embedded Qdrant instance, air-gapped on PSU infrastructure — no server process, no network calls.</p>
              <div id="knowledge-stats-container" class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div class="p-3 bg-[#EEF5E5] dark:bg-[#1F2B18] border border-[#C3D9AA] dark:border-[#34422B] rounded text-xs col-span-3">
                  <span class="text-xs font-semibold text-[#5C6654] dark:text-[#AEB5A6]">Loading live index status…</span>
                </div>
              </div>
            </div>
          </div>
        `;
        this.loadKnowledgeStats();
        break;

      case 'models':
        title = 'Local Model Hub & GPU Cluster';
        contentHtml = `
          <div class="space-y-4 max-w-4xl mx-auto py-4">
            <div class="bg-white dark:bg-[#161B19] border border-[#D6DDC9] dark:border-[#283623] rounded-lg p-5">
              <h3 class="text-sm font-extrabold text-[#20251D] dark:text-[#E8EBDD] uppercase tracking-wider mb-2">Configured On-Premise LLM Models</h3>
              <div id="models-view-list" class="space-y-3 mt-4">
                ${CONFIG.MODELS.map(m => this.modelCardHtml(m)).join('')}
              </div>
            </div>
          </div>
        `;
        this.loadModelInstallStatus();
        break;

      case 'tools':
        title = 'Agent Execution Tools';
        contentHtml = `
          <div class="space-y-4 max-w-4xl mx-auto py-4">
            <div class="bg-white dark:bg-[#161B19] border border-[#D6DDC9] dark:border-[#283623] rounded-lg p-5">
              <h3 class="text-sm font-extrabold text-[#20251D] dark:text-[#E8EBDD] uppercase tracking-wider mb-2">On-Premise Industrial Agent Tools</h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
                ${CONFIG.AGENT_TOOLS.map(t => `
                  <div class="p-3 rounded-md border border-[#D6DDC9] dark:border-[#283623] bg-[#F9FAF6] dark:bg-[#171B19]">
                    <div class="flex items-center justify-between">
                      <h4 class="font-bold text-xs text-[#20251D] dark:text-[#E8EBDD]">${t.name}</h4>
                      <span class="text-[9px] font-bold font-mono px-1.5 py-0.5 rounded bg-[#EEF5E5] text-[#3F641C] dark:bg-[#1F2B18] dark:text-[#A8D66D] border border-[#C3D9AA] dark:border-[#34422B]">${t.status}</span>
                    </div>
                    <p class="text-[11px] text-[#5C6654] dark:text-[#AEB5A6] mt-1">${t.desc}</p>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
        `;
        break;

      case 'history':
        title = 'Task & Chat History';
        contentHtml = `
          <div class="space-y-4 max-w-4xl mx-auto py-4">
            <div class="bg-white dark:bg-[#161B19] border border-[#D6DDC9] dark:border-[#283623] rounded-lg p-5">
              <h3 class="text-sm font-extrabold text-[#20251D] dark:text-[#E8EBDD] uppercase tracking-wider mb-2">Recent Sessions</h3>
              <div class="space-y-2 mt-4">
                ${state.conversations.length === 0
                  ? `<div class="text-center py-6 text-xs text-[#5C6654] dark:text-[#AEB5A6]">No past sessions yet. Click <strong>New Chat Session</strong> in the sidebar to start one.</div>`
                  : state.conversations.map(c => `
                  <div onclick="window.MRPLApp.selectSession('${c.id}')" class="p-3 rounded border border-[#D6DDC9] dark:border-[#283623] bg-[#F9FAF6] dark:bg-[#171B19] hover:bg-[#EEF5E5] dark:hover:bg-[#1F2B18] cursor-pointer flex items-center justify-between">
                    <div>
                      <h4 class="font-semibold text-xs text-[#20251D] dark:text-[#E8EBDD]">${this.escapeHtml(c.title)}</h4>
                      <p class="text-[11px] text-[#5C6654] dark:text-[#AEB5A6]">${this.escapeHtml(c.subtitle || '')}</p>
                    </div>
                    <span class="text-[10px] font-mono text-[#8A9581] dark:text-[#6E7B68]">${this.escapeHtml(c.date || '')}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
        `;
        break;

      case 'settings':
        title = 'System Configuration';
        contentHtml = `
          <div class="space-y-4 max-w-4xl mx-auto py-4">
            <div class="bg-white dark:bg-[#161B19] border border-[#D6DDC9] dark:border-[#283623] rounded-lg p-5">
              <h3 class="text-sm font-extrabold text-[#20251D] dark:text-[#E8EBDD] uppercase tracking-wider mb-2">FastAPI & Ollama System Settings</h3>
              <div class="space-y-3 text-xs mt-4">
                <div>
                  <label class="block text-[11px] font-semibold text-[#5C6654] dark:text-[#AEB5A6] mb-1">FastAPI Backend Endpoint URL</label>
                  <input type="text" value="${CONFIG.API_BASE_URL}" class="w-full px-3 py-1.5 bg-[#F9FAF6] dark:bg-[#171B19] border border-[#D6DDC9] dark:border-[#283623] rounded font-mono text-xs text-[#20251D] dark:text-[#E8EBDD]" readonly />
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-[#5C6654] dark:text-[#AEB5A6] mb-1">Security Model</label>
                  <div class="p-3 bg-[#EEF5E5] dark:bg-[#1F2B18] border border-[#C3D9AA] dark:border-[#34422B] rounded text-xs text-[#3F641C] dark:text-[#A8D66D] font-mono">
                    Air-Gapped PSU Enterprise Infrastructure (Strictly Offline)
                  </div>
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-[#5C6654] dark:text-[#AEB5A6] mb-1">Live Backend Status</label>
                  <div id="settings-live-status" class="p-3 bg-[#EEF5E5] dark:bg-[#1F2B18] border border-[#C3D9AA] dark:border-[#34422B] rounded text-xs text-[#3F641C] dark:text-[#A8D66D] font-mono">
                    Checking Ollama, database, and RAG connectivity…
                  </div>
                </div>
              </div>
            </div>
          </div>
        `;
        this.loadSettingsStatus();
        break;
    }

    container.innerHTML = contentHtml;
  }
};

if (typeof window !== 'undefined') {
  window.ui = ui;
}
