/**
 * Prompt2Video AI — Master App Controller
 */

window.App = {
  state: {
    activeTab: 'create',
    prompt: '',
    title: '',
    duration: 30,
    aspectRatio: '9:16',
    resolution: '1080p',
    voice: 'bm_george',
    style: 'cinematic-documentary',
    outputDir: ''
  },

  async init() {
    this.setupTabs();
    this.setupCreateControls();
    await this.loadInitialSettings();
    
    // Initialize child controllers if available
    if (window.ModelsController) window.ModelsController.init();
    if (window.LibraryController) window.LibraryController.init();
    if (window.StudioController) window.StudioController.init();
  },

  setupTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        this.switchTab(target);
      });
    });
  },

  switchTab(tabName) {
    this.state.activeTab = tabName;
    document.querySelectorAll('.nav-tab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === tabName);
    });
    document.querySelectorAll('.tab-pane').forEach(pane => {
      pane.classList.toggle('active', pane.id === `tab-${tabName}`);
    });

    if (tabName === 'library' && window.LibraryController) {
      window.LibraryController.loadLibrary();
    }
  },

  setupCreateControls() {
    // Template pills
    document.querySelectorAll('.template-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const promptText = pill.dataset.prompt;
        const promptInput = document.getElementById('input-prompt');
        if (promptInput) {
          promptInput.value = promptText;
          promptInput.focus();
        }
      });
    });

    // Aspect ratio cards
    document.querySelectorAll('.ratio-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.ratio-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        this.state.aspectRatio = card.dataset.ratio;
      });
    });

    // Duration pills
    document.querySelectorAll('#duration-selector .pill-option').forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('#duration-selector .pill-option').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        this.state.duration = parseInt(pill.dataset.duration, 10);
      });
    });

    // Resolution pills
    document.querySelectorAll('#resolution-selector .pill-option').forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('#resolution-selector .pill-option').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        this.state.resolution = pill.dataset.res;
      });
    });

    // Folder selection
    const btnBrowse = document.getElementById('btn-browse-folder');
    if (btnBrowse) {
      btnBrowse.addEventListener('click', async () => {
        if (window.api && window.api.selectDirectory) {
          const selected = await window.api.selectDirectory(this.state.outputDir);
          if (selected) {
            this.state.outputDir = selected;
            const inputOut = document.getElementById('input-output-dir');
            if (inputOut) inputOut.value = selected;
            const display = document.getElementById('output-folder-display');
            if (display) display.textContent = selected;
          }
        }
      });
    }

    // Generate Button Click
    const btnGenerate = document.getElementById('btn-generate-video');
    if (btnGenerate) {
      btnGenerate.addEventListener('click', () => this.handleGenerate());
    }
  },

  async loadInitialSettings() {
    if (!window.api || !window.api.getSettings) return;
    try {
      const settings = await window.api.getSettings();
      if (settings.outputDir) {
        this.state.outputDir = settings.outputDir;
        const inputOut = document.getElementById('input-output-dir');
        if (inputOut) inputOut.value = settings.outputDir;
        const display = document.getElementById('output-folder-display');
        if (display) display.textContent = settings.outputDir;
      }
      if (settings.defaultVoice) {
        this.state.voice = settings.defaultVoice;
        const voiceSelect = document.getElementById('input-voice');
        if (voiceSelect) voiceSelect.value = settings.defaultVoice;
      }
    } catch (err) {
      console.warn('Failed to load settings:', err);
    }
  },

  async handleGenerate() {
    const promptInput = document.getElementById('input-prompt');
    const prompt = promptInput ? promptInput.value.trim() : '';

    if (!prompt) {
      alert('Please enter a video topic or prompt to begin.');
      if (promptInput) promptInput.focus();
      return;
    }

    const titleInput = document.getElementById('input-title');
    const title = titleInput ? titleInput.value.trim() : '';
    const voiceSelect = document.getElementById('input-voice');
    const voice = voiceSelect ? voiceSelect.value : this.state.voice;
    const styleSelect = document.getElementById('input-style');
    const style = styleSelect ? styleSelect.value : this.state.style;

    const options = {
      prompt,
      title,
      duration: this.state.duration,
      aspectRatio: this.state.aspectRatio,
      resolution: this.state.resolution,
      voice,
      style,
      outputDir: this.state.outputDir
    };

    // Switch to Production Studio tab
    this.switchTab('studio');

    // Trigger studio generation
    if (window.StudioController) {
      window.StudioController.startGeneration(options);
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  window.App.init();
});
