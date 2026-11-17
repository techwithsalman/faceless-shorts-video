/**
 * Prompt2Video AI — Models, Runtime & Hardware Controller
 */

window.ModelsController = {
  async init() {
    this.setupButtons();
    await this.loadHardwareInfo();
    await this.loadRuntimeStatus();
    await this.loadModelStatus();
  },

  setupButtons() {
    const btnRecheck = document.getElementById('btn-recheck-models');
    if (btnRecheck) {
      btnRecheck.addEventListener('click', () => {
        this.loadModelStatus();
        this.loadRuntimeStatus(true);
        this.loadHardwareInfo();
      });
    }

    const btnRecheckRuntime = document.getElementById('btn-recheck-runtime');
    if (btnRecheckRuntime) {
      btnRecheckRuntime.addEventListener('click', () => {
        this.loadRuntimeStatus(true);
      });
    }

    const btnProvisionRuntime = document.getElementById('btn-provision-runtime');
    if (btnProvisionRuntime) {
      btnProvisionRuntime.addEventListener('click', () => {
        if (window.WizardController) {
          window.WizardController.open();
        }
      });
    }

    const btnWizard = document.getElementById('btn-open-wizard');
    if (btnWizard) {
      btnWizard.addEventListener('click', () => {
        if (window.WizardController) {
          window.WizardController.open();
        }
      });
    }
  },

  async loadHardwareInfo() {
    if (!window.api || !window.api.getHardwareInfo) return;

    try {
      const hw = await window.api.getHardwareInfo();
      const cpuInput = document.getElementById('hw-cpu');
      if (cpuInput) cpuInput.value = `${hw.cpu} (${hw.cores} Logical Cores)`;

      const ramInput = document.getElementById('hw-ram');
      if (ramInput) ramInput.value = `${hw.totalRamGB} GB Total (${hw.freeRamGB} GB Free)`;

      const gpuInput = document.getElementById('hw-gpu');
      if (gpuInput) gpuInput.value = hw.gpu || 'Integrated Graphics';

      const drivesList = document.getElementById('hw-drives-list');
      if (drivesList && hw.drives && hw.drives.length > 0) {
        drivesList.innerHTML = hw.drives.map(d => `
          <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid var(--border-subtle);">
            <span>Drive <strong>${d.Name}:</strong></span>
            <span><strong>${d.FreeGB} GB Free</strong> (of ${Math.round((d.FreeGB + d.UsedGB) * 10) / 10} GB)</span>
          </div>
        `).join('');
      }
    } catch (err) {
      console.warn('Failed to load hardware specs:', err);
    }
  },

  async loadRuntimeStatus(forceRefresh = false) {
    if (!window.api || !window.api.getRuntimeStatus) return;

    try {
      const status = await window.api.getRuntimeStatus(forceRefresh);
      
      const pathInput = document.getElementById('runtime-python-path');
      if (pathInput) {
        pathInput.value = status.pythonPath || 'No Python Runtime Configured';
      }

      const badge = document.getElementById('runtime-status-badge');
      const desc = document.getElementById('runtime-status-desc');
      if (badge && desc) {
        if (status.ready) {
          badge.className = 'badge badge-success';
          badge.textContent = 'Isolated & Ready';
          desc.textContent = status.isManaged ? 'Application-managed isolated venv' : 'Configured local environment';
        } else {
          badge.className = 'badge badge-warning';
          badge.textContent = 'Setup Required';
          desc.textContent = status.basePythonFound ? 'Base Python found — runtime needs provisioning' : 'Python 3.10+ needed';
        }
      }

      // Dependencies
      const setDep = (id, ok, textOk, textFail) => {
        const el = document.getElementById(id);
        if (el) {
          el.textContent = ok ? textOk : textFail;
          el.style.color = ok ? 'var(--accent-green)' : 'var(--accent-amber)';
        }
      };

      setDep('dep-torch-status', status.ready, 'Verified (CPU/CUDA ready)', 'Not verified');
      setDep('dep-kokoro-status', status.ready, 'Verified (ONNX ready)', 'Not verified');
      setDep('dep-whisper-status', status.ready, 'Verified (Faster-Whisper ready)', 'Not verified');
      setDep('dep-ffmpeg-status', status.ffmpegAvailable, 'Available in System PATH', 'Missing from PATH');

      if (window.App && window.App.updateRuntimeUI) {
        window.App.updateRuntimeUI(status);
      }
    } catch (err) {
      console.warn('Failed to load runtime status:', err);
    }
  },

  async loadModelStatus() {
    const container = document.getElementById('models-checklist');
    if (!container) return;

    if (!window.api || !window.api.getModelStatus) {
      container.innerHTML = '<div style="color: var(--text-muted);">Model status API unavailable.</div>';
      return;
    }

    try {
      const status = await window.api.getModelStatus();
      const models = [
        status.kokoro,
        status.sdTurbo,
        status.depthAnything,
        status.whisper,
        status.qwen
      ].filter(Boolean);

      container.innerHTML = models.map(m => {
        const isReady = m.installed;
        const badgeClass = isReady ? 'badge-success' : 'badge-warning';
        const badgeText = isReady ? 'Installed & Ready' : 'Download Needed';

        return `
          <div class="model-check-item">
            <div class="model-info-block">
              <h4>${m.name}</h4>
              <p>${m.type} • ${m.size} • 100% Offline</p>
            </div>
            <div>
              <span class="badge ${badgeClass}">${badgeText}</span>
            </div>
          </div>
        `;
      }).join('');

    } catch (err) {
      container.innerHTML = `<div style="color: var(--accent-red);">Failed to check models: ${err.message}</div>`;
    }
  }
};
