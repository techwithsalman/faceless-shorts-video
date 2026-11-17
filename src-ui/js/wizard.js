/**
 * Prompt2Video AI — First-Run Setup Wizard Controller
 */

window.WizardController = {
  isProvisioning: false,
  unsubscribeProgress: null,

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
        ffmpegEl.textContent = status.ffmpegAvailable ? 'Ready (in PATH)' : 'Missing from PATH';
        ffmpegEl.style.color = status.ffmpegAvailable ? 'var(--accent-green)' : 'var(--accent-amber)';
      }

      const statusLabel = document.getElementById('wizard-status-label');
      const stepMsg = document.getElementById('wizard-step-message');
      const progressBar = document.getElementById('wizard-progress-bar');
      const percentEl = document.getElementById('wizard-status-percent');
      const btnStart = document.getElementById('btn-start-provision');

      if (status.ready) {
        if (statusLabel) statusLabel.textContent = 'Runtime Status: Verified & Ready';
        if (stepMsg) stepMsg.textContent = 'All local neural dependencies (PyTorch, Kokoro, Whisper, SD-Turbo) are active.';
        if (progressBar) progressBar.style.width = '100%';
        if (percentEl) percentEl.textContent = '100%';
        if (btnStart) btnStart.textContent = 'Re-Verify Runtime';
      } else {
        if (statusLabel) statusLabel.textContent = 'Runtime Status: Setup Required';
        if (stepMsg) stepMsg.textContent = 'Click "Initialize Python Runtime" to provision the offline AI engine.';
        if (progressBar) progressBar.style.width = '0%';
        if (percentEl) percentEl.textContent = '0%';
        if (btnStart) btnStart.textContent = 'Initialize Python Runtime';
      }
    } catch (err) {
      console.warn('Failed to refresh wizard details:', err);
    }
  },

  async startProvisioning() {
    if (this.isProvisioning) return;
    this.isProvisioning = true;

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
    }
    if (stepMsg) {
      stepMsg.textContent = 'Starting isolated environment setup...';
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
    const percent = data.percent || 0;
    const msg = data.message || '';

    const progressBar = document.getElementById('wizard-progress-bar');
    if (progressBar) {
      progressBar.style.width = `${percent}%`;
    }

    const percentEl = document.getElementById('wizard-status-percent');
    if (percentEl) {
      percentEl.textContent = `${percent}%`;
    }

    const stepMsg = document.getElementById('wizard-step-message');
    if (stepMsg && msg) {
      stepMsg.textContent = msg;
      stepMsg.style.color = 'var(--text-muted)';
    }
  }
};
