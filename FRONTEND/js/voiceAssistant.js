/**
 * MRPL AI WORKBENCH - Voice Assistant Integration Engine
 * 
 * Modular, frontend-only Speech Recognition & Audio Input Controller.
 * Provides clean event callbacks (onTranscript, onRecordingStart, onRecordingStop, onError)
 * for future backend STT API integration while seamlessly populating the frontend chatbox.
 */

class VoiceAssistant {
  constructor() {
    this.isRecording = false;
    this.recognition = null;
    this.mediaRecorder = null;
    this.audioChunks = [];
    
    // Callback registries
    this.listeners = {
      start: [],
      stop: [],
      transcript: [],
      error: []
    };

    this.initSpeechRecognition();
  }

  /**
   * Initialize browser / Electron Speech Recognition if supported
   */
  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      try {
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onstart = () => {
          this.isRecording = true;
          this.emit('start');
        };

        this.recognition.onresult = (event) => {
          let interimTranscript = '';
          let finalTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const transcriptChunk = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              finalTranscript += transcriptChunk;
            } else {
              interimTranscript += transcriptChunk;
            }
          }

          const combinedText = finalTranscript || interimTranscript;
          if (combinedText) {
            this.emit('transcript', {
              text: combinedText,
              isFinal: Boolean(finalTranscript)
            });
          }
        };

        this.recognition.onerror = (event) => {
          console.warn('[Voice Assistant] Speech Recognition error:', event.error);
          let message = 'Voice input error occurred.';
          if (event.error === 'not-allowed' || event.error === 'permission-denied') {
            message = 'Microphone permission denied. Please allow microphone access.';
          } else if (event.error === 'no-speech') {
            message = 'No speech detected. Please speak clearly.';
          } else if (event.error === 'network') {
            message = 'Speech recognition service offline.';
          }
          this.emit('error', { message, code: event.error });
          this.stop();
        };

        this.recognition.onend = () => {
          if (this.isRecording) {
            this.isRecording = false;
            this.emit('stop');
          }
        };
      } catch (err) {
        console.warn('[Voice Assistant] Failed to instantiate SpeechRecognition:', err);
        this.recognition = null;
      }
    }
  }

  /**
   * Check if speech recognition or microphone capture is supported
   */
  isSupported() {
    return Boolean(this.recognition || (navigator.mediaDevices && navigator.mediaDevices.getUserMedia));
  }

  /**
   * Register event callbacks
   */
  onRecordingStart(fn) { this.listeners.start.push(fn); }
  onRecordingStop(fn) { this.listeners.stop.push(fn); }
  onTranscript(fn) { this.listeners.transcript.push(fn); }
  onError(fn) { this.listeners.error.push(fn); }

  emit(event, payload) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(fn => fn(payload));
    }
  }

  /**
   * Start voice recording & speech recognition
   */
  async start() {
    if (this.isRecording) return;

    if (this.recognition) {
      try {
        this.recognition.start();
      } catch (err) {
        console.warn('[Voice Assistant] Recognition start error:', err);
        this.isRecording = true;
        this.emit('start');
      }
      return;
    }

    // Fallback: Use MediaRecorder if Web Speech API is missing in Electron
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.audioChunks = [];
        this.mediaRecorder = new MediaRecorder(stream);

        this.mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) this.audioChunks.push(e.data);
        };

        this.mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
          if (window.api && window.api.transcribeAudio) {
            try {
              const res = await window.api.transcribeAudio(audioBlob);
              if (res && res.text) {
                this.emit('transcript', { text: res.text, isFinal: true });
              }
            } catch (err) {
              console.error('[Voice Assistant] Audio transcription error:', err);
            }
          }
          stream.getTracks().forEach(track => track.stop());
          this.isRecording = false;
          this.emit('stop');
        };

        this.mediaRecorder.start();
        this.isRecording = true;
        this.emit('start');

        // Immediate feedback indicator for fallback audio stream
        this.emit('transcript', { 
          text: '[Listening... Speak clearly into your microphone]', 
          isFinal: false 
        });

      } catch (err) {
        console.error('[Voice Assistant] getUserMedia failed:', err);
        this.emit('error', { 
          message: 'Microphone access denied or unavailable.', 
          code: 'permission_denied' 
        });
      }
    } else {
      this.emit('error', { 
        message: 'Speech input is not supported in this environment.', 
        code: 'unsupported' 
      });
    }
  }

  /**
   * Stop voice recording
   */
  stop() {
    if (!this.isRecording) return;

    this.isRecording = false;

    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (err) {
        console.warn('[Voice Assistant] Error stopping recognition:', err);
      }
    }

    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop();
      } catch (err) {
        console.warn('[Voice Assistant] Error stopping MediaRecorder:', err);
      }
    }

    this.emit('stop');
  }

  /**
   * Toggle recording state
   */
  toggle() {
    if (this.isRecording) {
      this.stop();
    } else {
      this.start();
    }
  }
}

// Export global instance
if (typeof window !== 'undefined') {
  window.VoiceAssistant = VoiceAssistant;
  window.voiceAssistant = new VoiceAssistant();
}
