/**
 * Prompt2Video AI — Models & Hardware Controller
 */

window.ModelsController = {
  async init() {
    this.setupButtons();
    await this.loadHardwareInfo();
    await this.loadModelStatus();
  },

  setupButtons() {
    const btnRecheck = document.getElementById('btn-recheck-models');
    if (btnRecheck) {
      btnRecheck.addEventListener('click', () => {
        this.loadModelStatus();
        this.loadHardwareInfo();
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

      // Update global header status
      const globalStatus = document.getElementById('global-status-text');
      if (globalStatus) {
        if (status.allReady) {
          globalStatus.textContent = 'Local AI Engine Ready (Offline)';
        } else {
          globalStatus.textContent = 'Models Downloading / Checking';
        }
      }

    } catch (err) {
      container.innerHTML = `<div style="color: var(--accent-red);">Failed to check models: ${err.message}</div>`;
    }
  }
};
