/**
 * AGNI: Air-Gapped Neural Intelligence - Task Progress Block
 *
 * Renders a polished, technical processing-stage block during AI inference.
 * Replaces the simple "AGNI Thinking..." placeholder with a structured,
 * animated task-progress panel. Uses Anime.js for smooth state transitions.
 *
 * Design rules:
 *   COMPLETED   -> green   checkmark ✓
 *   IN PROGRESS -> orange  active dot ◉ (pulsed)
 *   PENDING     -> muted   empty circle ○
 *   ERROR       -> red     cross ✕
 */

(function () {
  'use strict';

  // ─── Request Classification ────────────────────────────────────────────────

  function classifyRequest(text, activeDocs) {
    var t = (text || '').toLowerCase();
    var hasDocs = activeDocs && activeDocs.length > 0;
    var hasImage = hasDocs && activeDocs.some(function (d) {
      var type = (d.type || '').toUpperCase();
      return type === 'JPG' || type === 'PNG' || type === 'JPEG' || type === 'WEBP' || type === 'TIFF' || type === 'BMP';
    });

    var detailedKeywords = [
      'review', 'analyse', 'analyze', 'detailed', 'thorough', 'comprehensive',
      'inspection', 'audit', 'findings', 'assessment', 'summary', 'report',
      'check', 'examine', 'evaluate', 'deep dive', 'full'
    ];
    var isDetailed = detailedKeywords.some(function (kw) { return t.indexOf(kw) !== -1; });

    if (hasDocs && hasImage) return 'image-analysis';
    if (hasDocs && isDetailed) return 'detailed-doc-review';
    if (hasDocs) return 'simple-doc-question';
    return 'general-chat';
  }

  // ─── Stage Definitions ────────────────────────────────────────────────────

  function buildStages(classification, activeDocs) {
    var hasDocs = activeDocs && activeDocs.length > 0;
    var docType = hasDocs ? (activeDocs[0].type || 'PDF').toUpperCase() : '';

    switch (classification) {
      case 'detailed-doc-review':
        if (docType === 'PDF') {
          return [
            'Request received',
            'PDF context loaded',
            'Document structure identified',
            'Extracting text content',
            'Analyzing relevant sections',
            'Identifying engineering findings',
            'Reviewing technical content',
            'Cross-referencing available context',
            'Preparing detailed assessment',
            'Generating response'
          ];
        }
        return [
          'Request received',
          'Document context loaded',
          'File structure identified',
          'Extracting document content',
          'Analyzing document structure',
          'Identifying relevant sections',
          'Reviewing technical content',
          'Checking safety observations',
          'Preparing detailed findings',
          'Generating response'
        ];

      case 'simple-doc-question':
        return [
          'Request received',
          'Document context loaded',
          'Retrieving relevant content',
          'Processing query',
          'Preparing response',
          'Generating response'
        ];

      case 'image-analysis':
        return [
          'Request received',
          'Image context loaded',
          'Processing visual content',
          'Interpreting document structure',
          'Identifying relevant information',
          'Performing technical analysis',
          'Preparing findings',
          'Generating response'
        ];

      case 'general-chat':
      default:
        return [
          'Request received',
          'Context prepared',
          'Processing request',
          'Retrieving relevant knowledge',
          'Formulating response',
          'Generating response'
        ];
    }
  }

  // ─── Timing ───────────────────────────────────────────────────────────────

  function stageDuration(index, total) {
    if (index < 2) return 360;
    if (index < total - 2) return 480 + (index * 35);
    return 680;
  }

  // ─── HTML Builders ────────────────────────────────────────────────────────

  function renderStageRow(label, stateStr, index) {
    var indicator, colorClass, ariaLabel;
    if (stateStr === 'completed') {
      indicator = '<span class="agni-tp-icon agni-tp-icon--done" aria-label="Completed">\u2713</span>';
      colorClass = 'agni-tp-stage--done';
      ariaLabel = 'Completed: ' + label;
    } else if (stateStr === 'active') {
      indicator = '<span class="agni-tp-icon agni-tp-icon--active" aria-label="In progress">\u25C9</span>';
      colorClass = 'agni-tp-stage--active';
      ariaLabel = 'In progress: ' + label;
    } else if (stateStr === 'error') {
      indicator = '<span class="agni-tp-icon agni-tp-icon--error" aria-label="Error">\u2715</span>';
      colorClass = 'agni-tp-stage--error';
      ariaLabel = 'Error: ' + label;
    } else {
      indicator = '<span class="agni-tp-icon agni-tp-icon--pending" aria-label="Pending">\u25CB</span>';
      colorClass = 'agni-tp-stage--pending';
      ariaLabel = 'Pending: ' + label;
    }
    return '<div class="agni-tp-stage ' + colorClass + '" data-stage-index="' + index + '" role="listitem" aria-label="' + ariaLabel + '">' + indicator + '<span class="agni-tp-label">' + label + '</span></div>';
  }

  function buildPanelHTML(stages, modelName) {
    var stagesHTML = stages.map(function (label, i) {
      return renderStageRow(label, i === 0 ? 'active' : 'pending', i);
    }).join('');

    return '<div class="agni-tp-panel">' +
      '<div class="agni-tp-header">' +
        '<div class="agni-tp-header-left">' +
          '<span class="agni-tp-brand">AGNI</span>' +
          '<span class="agni-tp-sep">|</span>' +
          '<span class="agni-tp-model">' + modelName + '</span>' +
          '<span class="agni-tp-badge">Air-Gapped RAG</span>' +
        '</div>' +
        '<span class="agni-tp-status-dot agni-tp-status-dot--active" aria-label="Processing"></span>' +
      '</div>' +
      '<div class="agni-tp-divider"></div>' +
      '<div class="agni-tp-stages" role="list" aria-label="Processing stages" aria-live="polite">' +
        stagesHTML +
      '</div>' +
      '<div class="agni-tp-divider"></div>' +
      '<div class="agni-tp-footer">' +
        '<span class="agni-tp-footer-text">Processing request</span>' +
        '<span class="agni-tp-footer-dots">' +
          '<span class="agni-tp-dot"></span>' +
          '<span class="agni-tp-dot"></span>' +
          '<span class="agni-tp-dot"></span>' +
        '</span>' +
      '</div>' +
    '</div>';
  }

  // ─── Controller ───────────────────────────────────────────────────────────

  function TaskProgressController(containerId, stages) {
    this.containerId = containerId;
    this.stages = stages;
    this.currentStageIndex = 0;
    this._timer = null;
    this._activeAnimeTargets = [];
    this._destroyed = false;
  }

  TaskProgressController.prototype._getEl = function (index) {
    var c = document.getElementById(this.containerId);
    if (!c) return null;
    return c.querySelector('[data-stage-index="' + index + '"]');
  };

  TaskProgressController.prototype._getFooterText = function () {
    var c = document.getElementById(this.containerId);
    if (!c) return null;
    return c.querySelector('.agni-tp-footer-text');
  };

  TaskProgressController.prototype._getStatusDot = function () {
    var c = document.getElementById(this.containerId);
    if (!c) return null;
    return c.querySelector('.agni-tp-status-dot');
  };

  TaskProgressController.prototype._stopAnime = function () {
    if (window.anime && this._activeAnimeTargets.length > 0) {
      try { window.anime.remove(this._activeAnimeTargets); } catch (_) {}
    }
    this._activeAnimeTargets = [];
  };

  TaskProgressController.prototype._pulseActive = function () {
    if (this._destroyed || !window.anime) return;
    var el = this._getEl(this.currentStageIndex);
    if (!el) return;

    var icon = el.querySelector('.agni-tp-icon--active');
    if (icon) {
      this._activeAnimeTargets.push(icon);
      try {
        window.anime({
          targets: icon,
          opacity: [1, 0.3, 1],
          scale: [1, 1.2, 1],
          duration: 950,
          easing: 'easeInOutSine',
          loop: true
        });
      } catch (_) {}
    }

    var dots = document.querySelectorAll('#' + this.containerId + ' .agni-tp-dot');
    if (dots.length > 0) {
      var dotsArr = Array.prototype.slice.call(dots);
      dotsArr.forEach(function (d) { this._activeAnimeTargets.push(d); }, this);
      try {
        window.anime({
          targets: dotsArr,
          opacity: [0.15, 1, 0.15],
          duration: 850,
          delay: window.anime.stagger(220),
          easing: 'easeInOutSine',
          loop: true
        });
      } catch (_) {}
    }
  };

  TaskProgressController.prototype.start = function () {
    this._pulseActive();
    this._scheduleNext(0);
  };

  TaskProgressController.prototype._scheduleNext = function (index) {
    if (this._destroyed) return;
    // Keep last stage active until API responds
    if (index >= this.stages.length - 1) return;
    var self = this;
    var delay = stageDuration(index, this.stages.length);
    this._timer = setTimeout(function () {
      if (!self._destroyed) self._advance();
    }, delay);
  };

  TaskProgressController.prototype._advance = function () {
    if (this._destroyed) return;
    this._stopAnime();
    var doneIdx = this.currentStageIndex;
    this.currentStageIndex++;
    var self = this;
    this._toDone(doneIdx, function () {
      if (self._destroyed) return;
      self._toActive(self.currentStageIndex);
      self._pulseActive();
      self._scheduleNext(self.currentStageIndex);
    });
  };

  TaskProgressController.prototype._toDone = function (index, cb) {
    var el = this._getEl(index);
    if (!el) { if (cb) cb(); return; }
    var icon = el.querySelector('.agni-tp-icon');

    el.classList.remove('agni-tp-stage--active', 'agni-tp-stage--pending', 'agni-tp-stage--error');
    el.classList.add('agni-tp-stage--done');
    el.setAttribute('aria-label', 'Completed: ' + this.stages[index]);

    if (icon) {
      icon.className = 'agni-tp-icon agni-tp-icon--done';
      icon.setAttribute('aria-label', 'Completed');
      icon.textContent = '\u2713';
    }

    if (window.anime && icon) {
      try {
        window.anime({
          targets: icon,
          scale: [0.5, 1.2, 1],
          opacity: [0, 1],
          duration: 260,
          easing: 'easeOutBack',
          complete: cb
        });
        return;
      } catch (_) {}
    }
    if (cb) cb();
  };

  TaskProgressController.prototype._toActive = function (index) {
    var el = this._getEl(index);
    if (!el) return;
    var icon = el.querySelector('.agni-tp-icon');

    el.classList.remove('agni-tp-stage--pending', 'agni-tp-stage--done', 'agni-tp-stage--error');
    el.classList.add('agni-tp-stage--active');
    el.setAttribute('aria-label', 'In progress: ' + (this.stages[index] || ''));

    if (icon) {
      icon.className = 'agni-tp-icon agni-tp-icon--active';
      icon.setAttribute('aria-label', 'In progress');
      icon.textContent = '\u25C9';
    }

    if (window.anime) {
      try {
        window.anime({
          targets: el,
          translateX: [-5, 0],
          opacity: [0.6, 1],
          duration: 200,
          easing: 'easeOutCubic'
        });
      } catch (_) {}
    }
  };

  TaskProgressController.prototype.signalDone = function (onComplete) {
    if (this._destroyed) { if (onComplete) onComplete(); return; }
    if (this._timer) { clearTimeout(this._timer); this._timer = null; }
    this._stopAnime();
    var self = this;
    var completeNext = function (i) {
      if (self._destroyed) return;
      if (i >= self.stages.length) {
        // Update footer
        var footer = self._getFooterText();
        if (footer) footer.textContent = 'Processing complete';
        var sd = self._getStatusDot();
        if (sd) {
          sd.classList.remove('agni-tp-status-dot--active');
          sd.classList.add('agni-tp-status-dot--done');
        }
        var dots = document.querySelectorAll('#' + self.containerId + ' .agni-tp-dot');
        if (window.anime && dots.length > 0) {
          try { window.anime({ targets: Array.prototype.slice.call(dots), opacity: 0, duration: 200 }); } catch (_) {}
        }
        setTimeout(function () {
          if (!self._destroyed && onComplete) onComplete();
        }, 300);
        return;
      }
      var delay = (i === self.currentStageIndex) ? 0 : 160;
      setTimeout(function () {
        if (self._destroyed) return;
        self._stopAnime();
        self._toDone(i, function () { completeNext(i + 1); });
      }, delay);
    };
    completeNext(this.currentStageIndex);
  };

  TaskProgressController.prototype.signalError = function (message) {
    if (this._destroyed) return;
    if (this._timer) { clearTimeout(this._timer); this._timer = null; }
    this._stopAnime();

    var el = this._getEl(this.currentStageIndex);
    if (el) {
      el.classList.remove('agni-tp-stage--active', 'agni-tp-stage--pending');
      el.classList.add('agni-tp-stage--error');
      var icon = el.querySelector('.agni-tp-icon');
      if (icon) { icon.className = 'agni-tp-icon agni-tp-icon--error'; icon.textContent = '\u2715'; }
      var label = el.querySelector('.agni-tp-label');
      if (label && message) label.textContent = message;
    }

    var footer = this._getFooterText();
    if (footer) { footer.textContent = 'Request failed'; footer.style.color = '#dc2626'; }

    var sd = this._getStatusDot();
    if (sd) {
      sd.classList.remove('agni-tp-status-dot--active');
      sd.classList.add('agni-tp-status-dot--error');
    }

    var dots = document.querySelectorAll('#' + this.containerId + ' .agni-tp-dot');
    dots.forEach(function (d) { d.style.opacity = '0'; });
  };

  TaskProgressController.prototype.destroy = function () {
    this._destroyed = true;
    if (this._timer) { clearTimeout(this._timer); this._timer = null; }
    this._stopAnime();
  };

  // ─── Public API ───────────────────────────────────────────────────────────

  var taskProgress = {
    _controllers: {},

    create: function (containerId, userText, activeDocs, modelName) {
      this.destroy(containerId);
      var classification = classifyRequest(userText, activeDocs);
      var stages = buildStages(classification, activeDocs);
      var html = buildPanelHTML(stages, modelName || 'Engineering Intelligence');
      var container = document.getElementById(containerId);
      if (container) container.innerHTML = html;
      var ctrl = new TaskProgressController(containerId, stages);
      this._controllers[containerId] = ctrl;
      ctrl.start();
      return ctrl;
    },

    signalDone: function (containerId, onComplete) {
      var ctrl = this._controllers[containerId];
      if (ctrl) ctrl.signalDone(onComplete);
      else if (onComplete) onComplete();
    },

    signalError: function (containerId, errorMessage) {
      var ctrl = this._controllers[containerId];
      if (ctrl) ctrl.signalError(errorMessage || 'Unable to complete request');
    },

    destroy: function (containerId) {
      var ctrl = this._controllers[containerId];
      if (ctrl) { ctrl.destroy(); delete this._controllers[containerId]; }
    },

    destroyAll: function () {
      var self = this;
      Object.keys(this._controllers).forEach(function (id) { self.destroy(id); });
    }
  };

  if (typeof window !== 'undefined') {
    window.taskProgress = taskProgress;
  }
})();
