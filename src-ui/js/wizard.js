/**
 * Prompt2Video AI — First-Run Setup Wizard Controller
 */

window.WizardController = {
  isProvisioning: false,
  unsubscribeProgress: null,
  highestPercent: 0,

  init() {
    this.setupListeners();
  },

  setupListeners() {
    const modal = document.getElementById('wizard-modal');
    const btnClose = document.getElementById('btn-close-wizard');
    const btnCancel = document.getElementById('btn-cancel-wizard');
    const btnStart = document.getElementById('btn-start-provision');

    if (btnClose) {
      btnClose.addEventListener('click', () => this.close());
    }
    if (btnCancel) {
      btnCancel.addEventListener('click', () => this.close());
    }

    if (btnStart) {
      btnStart.addEventListener('click', () => this.startProvisioning());
    }

    // Close on backdrop click
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal && !this.isProvisioning) {
          this.close();
        }
      });
    }

    // Listen for progress events from IPC
    if (window.api && window.api.onRuntimeProgress) {
      this.unsubscribeProgress = window.api.onRuntimeProgress((data) => {
        this.updateProgress(data);
      });
    }
  },

  async open() {
    const modal = document.getElementById('wizard-modal');
    if (!modal) return;

    modal.classList.add('active');
    await this.refreshDetails();
  },

  close() {
    const modal = document.getElementById('wizard-modal');
    if (modal) {
      modal.classList.remove('active');
    }
  },

  setCheckItem(id, status, text) {
    const el = document.getElementById(id);
    if (!el) return;
    const icon = el.querySelector('.chk-icon');
    if (status === 'ok') {
      if (icon) icon.textContent = '🟢';
      el.style.color = 'var(--accent-green)';
    } else if (status === 'active') {
      if (icon) icon.textContent = '⏳';
      el.style.color = 'var(--accent-cyan)';
    } else if (status === 'fail') {
      if (icon) icon.textContent = '❌';
      el.style.color = 'var(--accent-red)';
    } else {
      if (icon) icon.textContent = '⚪';
      el.style.color = 'var(--text-muted)';
    }
    if (text) {
      el.childNodes[1].textContent = ` ${text}`;
    }
  },

  async refreshDetails() {
    if (!window.api || !window.api.getRuntimeStatus) return;

    try {
      const status = await window.api.getRuntimeStatus();
      
      const pathEl = document.getElementById('wizard-runtime-path');
      if (pathEl) {
        pathEl.textContent = status.runtimeDir || '%LOCALAPPDATA%\\Prompt2VideoAI\\runtime';
      }

      const basePyEl = document.getElementById('wizard-base-python');
      if (basePyEl) {
        basePyEl.textContent = status.basePythonFound
          ? `Found (${status.basePythonPath || 'System Python'})`
          : 'Not found (Python 3.10+ required)';
        basePyEl.style.color = status.basePythonFound ? 'var(--accent-green)' : 'var(--accent-amber)';
      }

      const ffmpegEl = document.getElementById('wizard-ffmpeg-status');
      if (ffmpegEl) {
        ffmpegEl.textContent = status.ffmpegAvailable ? 'Ready (in PATH)' : 'Configuring...';
        ffmpegEl.style.color = status.ffmpegAvailable ? 'var(--accent-green)' : 'var(--accent-amber)';
      }

      const statusLabel = document.getElementById('wizard-status-label');
      const stepMsg = document.getElementById('wizard-step-message');
      const progressBar = document.getElementById('wizard-progress-bar');
      const percentEl = document.getElementById('wizard-status-percent');
      const btnStart = document.getElementById('btn-start-provision');

      if (status.ready) {
        this.highestPercent = 100;
        if (statusLabel) statusLabel.textContent = 'Runtime Status: Verified & Ready';
        if (stepMsg) stepMsg.textContent = 'All local neural dependencies (PyTorch, Kokoro, Whisper, Diffusers, FFmpeg) are verified.';
        if (progressBar) progressBar.style.width = '100%';
        if (percentEl) percentEl.textContent = '100%';
        if (btnStart) btnStart.textContent = 'Re-Verify Runtime';

        this.setCheckItem('chk-base-py', 'ok', 'Base Python 3.10+');
        this.setCheckItem('chk-venv', 'ok', 'Isolated Venv');
        this.setCheckItem('chk-ffmpeg', 'ok', 'FFmpeg Media Engine');
        this.setCheckItem('chk-torch', 'ok', 'PyTorch (CUDA/CPU)');
        this.setCheckItem('chk-kokoro', 'ok', 'Kokoro Voice (ONNX)');
        this.setCheckItem('chk-whisper', 'ok', 'Faster-Whisper');
        this.setCheckItem('chk-transformers', 'ok', 'Transformers');
        this.setCheckItem('chk-diffusers', 'ok', 'Diffusers (SD-Turbo)');
      } else {
        this.highestPercent = 0;
        if (statusLabel) statusLabel.textContent = 'Runtime Status: Setup Required';
        if (stepMsg) stepMsg.textContent = 'Click "Initialize Python Runtime" to provision the offline AI engine.';
        if (progressBar) progressBar.style.width = '0%';
        if (percentEl) percentEl.textContent = '0%';
        if (btnStart) btnStart.textContent = 'Initialize Python Runtime';

        this.setCheckItem('chk-base-py', status.basePythonFound ? 'ok' : 'wait');
        this.setCheckItem('chk-venv', 'wait');
        this.setCheckItem('chk-ffmpeg', status.ffmpegAvailable ? 'ok' : 'wait');
        this.setCheckItem('chk-torch', 'wait');
        this.setCheckItem('chk-kokoro', 'wait');
        this.setCheckItem('chk-whisper', 'wait');
        this.setCheckItem('chk-transformers', 'wait');
        this.setCheckItem('chk-diffusers', 'wait');
      }
    } catch (err) {
      console.warn('Failed to refresh wizard details:', err);
    }
  },

  async startProvisioning() {
    if (this.isProvisioning) return;
    this.isProvisioning = true;
    this.highestPercent = 0;

    const btnStart = document.getElementById('btn-start-provision');
    const btnCancel = document.getElementById('btn-cancel-wizard');
    const statusLabel = document.getElementById('wizard-status-label');
    const stepMsg = document.getElementById('wizard-step-message');

    if (btnStart) {
      btnStart.setAttribute('disabled', 'disabled');
      btnStart.textContent = 'Provisioning Runtime...';
    }
    if (btnCancel) {
      btnCancel.setAttribute('disabled', 'disabled');
    }
    if (statusLabel) {
      statusLabel.textContent = 'Provisioning in progress...';
      statusLabel.style.color = 'var(--text-primary)';
    }
    if (stepMsg) {
      stepMsg.textContent = 'Starting isolated environment setup...';
      stepMsg.style.color = 'var(--text-muted)';
    }

    try {
      const res = await window.api.provisionRuntime();
      
      this.updateProgress({
        percent: 100,
        message: 'Local AI Python Runtime verified and ready!'
      });

      if (statusLabel) {
        statusLabel.textContent = 'Runtime Setup Complete!';
        statusLabel.style.color = 'var(--accent-green)';
      }

      this.setCheckItem('chk-base-py', 'ok');
      this.setCheckItem('chk-venv', 'ok');
      this.setCheckItem('chk-ffmpeg', 'ok');
      this.setCheckItem('chk-torch', 'ok');
      this.setCheckItem('chk-kokoro', 'ok');
      this.setCheckItem('chk-whisper', 'ok');
      this.setCheckItem('chk-transformers', 'ok');
      this.setCheckItem('chk-diffusers', 'ok');

      // Refresh global app state & models
      if (window.App && window.App.checkRuntimeHealth) {
        await window.App.checkRuntimeHealth(true);
      }
      if (window.ModelsController && window.ModelsController.loadRuntimeStatus) {
        await window.ModelsController.loadRuntimeStatus(true);
      }

      if (btnStart) {
        btnStart.textContent = 'Runtime Ready ✓';
      }

      setTimeout(() => {
        this.close();
      }, 1500);

    } catch (err) {
      console.error('Provisioning failed:', err);
      if (statusLabel) {
        statusLabel.textContent = 'Setup Encountered an Issue';
        statusLabel.style.color = 'var(--accent-red)';
      }
      if (stepMsg) {
        stepMsg.textContent = `Error: ${err.message || 'Failed to provision runtime.'}`;
        stepMsg.style.color = 'var(--accent-red)';
      }
      if (btnStart) {
        btnStart.removeAttribute('disabled');
        btnStart.textContent = 'Retry Setup';
      }
    } finally {
      this.isProvisioning = false;
      if (btnCancel) {
        btnCancel.removeAttribute('disabled');
      }
    }
  },

  updateProgress(data) {
    if (!data) return;
    const incomingPct = data.percent !== undefined ? data.percent : 0;
    this.highestPercent = Math.max(this.highestPercent, incomingPct);
    const msg = data.message || '';

    const progressBar = document.getElementById('wizard-progress-bar');
    if (progressBar) {
      progressBar.style.width = `${this.highestPercent}%`;
    }

    const percentEl = document.getElementById('wizard-status-percent');
    if (percentEl) {
      percentEl.textContent = `${this.highestPercent}%`;
    }

    const stepMsg = document.getElementById('wizard-step-message');
    if (stepMsg && msg) {
      stepMsg.textContent = msg;
      stepMsg.style.color = 'var(--text-muted)';
    }

    // Map stages to checklist items
    const s = data.stage;
    if (s === 'search') this.setCheckItem('chk-base-py', 'active');
    else if (s === 'venv') {
      this.setCheckItem('chk-base-py', 'ok');
      this.setCheckItem('chk-venv', 'active');
    }
    else if (s === 'linking' || s === 'ffmpeg') {
      this.setCheckItem('chk-venv', 'ok');
      this.setCheckItem('chk-ffmpeg', 'active');
    }
    else if (s === 'torch') this.setCheckItem('chk-torch', 'active');
    else if (s === 'torch_ok') this.setCheckItem('chk-torch', 'ok');
    else if (s === 'kokoro') this.setCheckItem('chk-kokoro', 'active');
    else if (s === 'kokoro_ok') this.setCheckItem('chk-kokoro', 'ok');
    else if (s === 'whisper') this.setCheckItem('chk-whisper', 'active');
    else if (s === 'whisper_ok') this.setCheckItem('chk-whisper', 'ok');
    else if (s === 'transformers') this.setCheckItem('chk-transformers', 'active');
    else if (s === 'transformers_ok') this.setCheckItem('chk-transformers', 'ok');
    else if (s === 'diffusers') this.setCheckItem('chk-diffusers', 'active');
    else if (s === 'diffusers_ok') this.setCheckItem('chk-diffusers', 'ok');
    else if (s === 'ffmpeg_ok') this.setCheckItem('chk-ffmpeg', 'ok');
  }
};
