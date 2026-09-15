/**
 * AGNI: Air-Gapped Neural Intelligence - Voice Assistant Integration Engine
 *
 * Push-to-talk-free voice input: click the mic once, speak, and both the
 * live transcript and the eventual send happen automatically —
 *   1. While recording, the growing audio is periodically re-transcribed
 *      (via the backend's faster-whisper endpoint) so the chat textbox
 *      fills in as you talk, the same way a live captioning view would.
 *   2. A simple volume-based silence detector watches the mic; once you've
 *      spoken and then paused for SILENCE_DURATION_MS, recording stops on
 *      its own — no button press needed.
 *   3. On stop, one last (full, most accurate) transcription runs and is
 *      emitted as { isFinal: true, autoSend: true } — app.js uses that flag
 *      to submit the message itself instead of waiting for the send button.
 *
 * Deliberately does NOT use window.SpeechRecognition/webkitSpeechRecognition
 * — Electron's bundled Chromium always exposes that constructor, so a naive
 * `if (SpeechRecognition)` check looks "supported" everywhere, but it's a
 * cloud service (Chromium streams audio to Google's servers to recognize
 * it). On this air-gapped/offline setup that request has nowhere to go and
 * fails silently. Recording always goes through MediaRecorder + the local,
 * fully offline backend model instead (faster-whisper, see
 * BACKEND/voice_command/stt.py via POST /api/v1/transcribe).
 */

class VoiceAssistant {
  constructor() {
    this.isRecording = false;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;

    // Volume-based silence detection
    this.audioContext = null;
    this.analyser = null;
    this.volumeCheckTimer = null;
    this.hasDetectedSpeech = false;
    this.lastSpeechTime = 0;
    this.recordingStartTime = 0;

    // Periodic "live fill" re-transcription while recording
    this.interimTimer = null;
    this.interimInFlight = false;

    this.listeners = {
      start: [],
      processing: [],
      stop: [],
      transcript: [],
      error: []
    };
  }

  /** Whether this environment can record audio at all. */
  isSupported() {
    return Boolean(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  }

  onRecordingStart(fn) { this.listeners.start.push(fn); }
  /** Fired the instant recording stops, before the final transcription
   * finishes — use this to show a "transcribing..." indicator. */
  onProcessing(fn) { this.listeners.processing.push(fn); }
  /** Fired once the voice turn is fully done (final transcript delivered,
   * or it failed) — use this to return the UI to idle. */
  onRecordingStop(fn) { this.listeners.stop.push(fn); }
  onTranscript(fn) { this.listeners.transcript.push(fn); }
  onError(fn) { this.listeners.error.push(fn); }

  emit(event, payload) {
    (this.listeners[event] || []).forEach(fn => fn(payload));
  }

  async start() {
    if (this.isRecording) return;

    if (!this.isSupported()) {
      this.emit('error', {
        message: 'Speech input is not supported in this environment.',
        code: 'unsupported'
      });
      return;
    }

    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      console.error('[Voice Assistant] getUserMedia failed:', err);
      this.emit('error', {
        message: 'Microphone access denied or unavailable.',
        code: 'permission_denied'
      });
      return;
    }

    this.stream = stream;
    this.audioChunks = [];
    this.hasDetectedSpeech = false;
    this.recordingStartTime = Date.now();
    this.lastSpeechTime = this.recordingStartTime;

    this._startSilenceWatcher(stream);

    this.mediaRecorder = new MediaRecorder(stream);
    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) this.audioChunks.push(e.data);
    };
    this.mediaRecorder.onstop = () => this._handleRecorderStopped();
    // A timeslice makes ondataavailable fire periodically instead of only
    // once at the very end, which is what lets _runInterimTranscription()
    // below re-transcribe "everything captured so far" while still talking.
    this.mediaRecorder.start(250);

    this.isRecording = true;
    this.emit('start');

    this.interimTimer = setInterval(
      () => this._runInterimTranscription(),
      VoiceAssistant.INTERIM_INTERVAL_MS
    );
  }

  /** Volume-only silence/voice-activity watcher — no speech content is
   * inspected here, just RMS level, purely to decide when to auto-stop. */
  _startSilenceWatcher(stream) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return; // no auto-stop on very old environments; manual re-click still stops it

    this.audioContext = new AudioContextClass();
    const source = this.audioContext.createMediaStreamSource(stream);
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 512;
    source.connect(this.analyser);

    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);

    this.volumeCheckTimer = setInterval(() => {
      this.analyser.getByteTimeDomainData(dataArray);

      let sumSquares = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const centered = (dataArray[i] - 128) / 128;
        sumSquares += centered * centered;
      }
      const rms = Math.sqrt(sumSquares / dataArray.length);
      const now = Date.now();

      if (rms > VoiceAssistant.SILENCE_RMS_THRESHOLD) {
        this.hasDetectedSpeech = true;
        this.lastSpeechTime = now;
      }

      const elapsedSinceStart = now - this.recordingStartTime;
      const elapsedSinceSpeech = now - this.lastSpeechTime;

      if (elapsedSinceStart > VoiceAssistant.MAX_RECORDING_MS) {
        this.stop(); // safety cap regardless of speech/silence
      } else if (
        this.hasDetectedSpeech &&
        elapsedSinceStart > VoiceAssistant.MIN_RECORDING_MS &&
        elapsedSinceSpeech > VoiceAssistant.SILENCE_DURATION_MS
      ) {
        this.stop();
      }
    }, 100);
  }

  _stopSilenceWatcher() {
    if (this.volumeCheckTimer) {
      clearInterval(this.volumeCheckTimer);
      this.volumeCheckTimer = null;
    }
    if (this.audioContext) {
      this.audioContext.close().catch(() => {});
      this.audioContext = null;
    }
    this.analyser = null;
  }

  /** Re-transcribes everything captured so far (from the very start of the
   * recording) so the textbox visibly fills in while the user keeps
   * talking. Skips a cycle rather than queuing if the previous call is
   * still in flight, so slower transcription just updates less often
   * instead of piling up requests. */
  async _runInterimTranscription() {
    if (this.interimInFlight || !this.isRecording || this.audioChunks.length === 0) return;
    if (!(window.api && window.api.transcribeAudio)) return;

    this.interimInFlight = true;
    try {
      const snapshot = new Blob(this.audioChunks, { type: 'audio/webm' });
      const res = await window.api.transcribeAudio(snapshot);
      const text = ((res && res.text) || '').trim();
      // Recording may have stopped while this request was in flight — the
      // final transcript from _handleRecorderStopped() always wins, so
      // drop a late interim result rather than let it overwrite it.
      if (text && this.isRecording) {
        this.emit('transcript', { text, isFinal: false, autoSend: false });
      }
    } catch (err) {
      console.warn('[Voice Assistant] Interim transcription skipped:', err.message || err);
    } finally {
      this.interimInFlight = false;
    }
  }

  async _handleRecorderStopped() {
    this._stopSilenceWatcher();
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    const finalBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
    this.audioChunks = [];

    if (finalBlob.size > 0 && window.api && window.api.transcribeAudio) {
      try {
        const res = await window.api.transcribeAudio(finalBlob);
        const text = ((res && res.text) || '').trim();
        if (text) {
          this.emit('transcript', { text, isFinal: true, autoSend: true });
        }
      } catch (err) {
        console.error('[Voice Assistant] Final transcription error:', err);
        this.emit('error', {
          message: 'Voice transcription failed. Is the backend running?',
          code: 'transcription_failed'
        });
      }
    }

    this.emit('stop');
  }

  /** Stops recording — called either by the silence watcher or by the user
   * clicking the mic again. Either way the flow is identical from here:
   * emit 'processing', run the final transcription, then auto-send it. */
  stop() {
    if (!this.isRecording) return;
    this.isRecording = false;

    if (this.interimTimer) {
      clearInterval(this.interimTimer);
      this.interimTimer = null;
    }

    this.emit('processing');

    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop(); // onstop -> _handleRecorderStopped()
      } catch (err) {
        console.warn('[Voice Assistant] Error stopping MediaRecorder:', err);
        this._handleRecorderStopped();
      }
    } else {
      this._handleRecorderStopped();
    }
  }

  toggle() {
    if (this.isRecording) this.stop();
    else this.start();
  }
}

// Tuning constants — kept as static fields (not magic numbers inline) since
// mic sensitivity and acceptable pause length vary by hardware/environment.
VoiceAssistant.SILENCE_RMS_THRESHOLD = 0.02;  // volume floor treated as "silence"; raise if it never stops, lower if it cuts you off
VoiceAssistant.SILENCE_DURATION_MS = 1600;    // how long a pause must last to end the turn
VoiceAssistant.MIN_RECORDING_MS = 500;        // ignore silence checks for this long after clicking the mic
VoiceAssistant.MAX_RECORDING_MS = 60000;      // hard cap so a stuck silence-detector can't record forever
VoiceAssistant.INTERIM_INTERVAL_MS = 1300;    // how often to re-transcribe the growing clip while talking

// Export global instance
if (typeof window !== 'undefined') {
  window.VoiceAssistant = VoiceAssistant;
  window.voiceAssistant = new VoiceAssistant();
}
