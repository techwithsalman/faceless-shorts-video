/**
 * Prompt2Video AI — Production Studio Controller
 */

window.StudioController = {
  activeRunId: null,
  activeOutputDir: null,
  scenes: [],
  isGenerating: false,

  init() {
    this.setupListeners();
    this.setupButtons();
  },

  setupListeners() {
    if (!window.api) return;

    window.api.onVideoProgress((event) => {
      this.handleProgressEvent(event);
    });

    window.api.onVideoLog((logLine) => {
      this.appendLogLine(logLine);
    });
  },

  setupButtons() {
    const btnCancel = document.getElementById('btn-cancel-generation');
    if (btnCancel) {
      btnCancel.addEventListener('click', async () => {
        if (confirm('Are you sure you want to cancel the active video generation?')) {
          this.appendLogLine('[System] Cancelling generation task...', 'log-warn');
          if (window.api && window.api.cancelVideo) {
            await window.api.cancelVideo();
          }
          this.isGenerating = false;
          btnCancel.style.display = 'none';
          document.getElementById('studio-subtitle').textContent = 'Generation cancelled by user.';
        }
      });
    }

    const btnOpenFolder = document.getElementById('btn-open-active-folder');
    if (btnOpenFolder) {
      btnOpenFolder.addEventListener('click', () => {
        if (this.activeOutputDir && window.api && window.api.openPath) {
          window.api.openPath(this.activeOutputDir);
        }
      });
    }
  },

  startGeneration(options) {
    this.isGenerating = true;
    this.scenes = [];
    
    // Update Header
    document.getElementById('studio-title').textContent = options.title || 'Generating Video...';
    document.getElementById('studio-subtitle').textContent = `Prompt: "${options.prompt.substring(0, 100)}..."`;
    
    const btnCancel = document.getElementById('btn-cancel-generation');
    if (btnCancel) btnCancel.style.display = 'inline-flex';

    const btnOpenFolder = document.getElementById('btn-open-active-folder');
    if (btnOpenFolder) btnOpenFolder.style.display = 'none';

    // Reset stages
    for (let i = 1; i <= 6; i++) {
      const step = document.getElementById(`stage-${i}`);
      if (step) {
        step.classList.remove('active', 'completed');
      }
    }

    // Reset progress
    this.updateProgress(2, 'Initializing AI engine...');

    // Clear scenes grid
    const scenesGrid = document.getElementById('studio-scenes-grid');
    if (scenesGrid) {
      scenesGrid.innerHTML = `
        <div class="scene-card" style="text-align: center; padding: 40px; color: var(--text-muted); grid-column: 1 / -1;">
          <div class="status-dot pulsing" style="margin: 0 auto 12px auto;"></div>
          Architecting story script and scenes...
        </div>
      `;
    }

    this.appendLogLine(`[Start] Beginning generation for prompt: ${options.prompt}`, 'log-info');

    // Trigger generation via IPC
    window.api.generateVideo(options).then((res) => {
      this.isGenerating = false;
      if (btnCancel) btnCancel.style.display = 'none';
      if (btnOpenFolder) btnOpenFolder.style.display = 'inline-flex';

      if (res.success) {
        this.updateProgress(100, 'Complete! Video rendered successfully.');
        document.getElementById('studio-subtitle').textContent = `Video finished! Saved at ${res.video_path || this.activeOutputDir}`;
        this.appendLogLine(`[Success] Video ready: ${res.video_path || ''}`, 'log-success');
        
        // Mark all stages completed
        for (let i = 1; i <= 6; i++) {
          const step = document.getElementById(`stage-${i}`);
          if (step) {
            step.classList.remove('active');
            step.classList.add('completed');
          }
        }
      } else {
        this.appendLogLine(`[Error] Generation failed: ${res.error || 'Unknown error'}`, 'log-error');
        document.getElementById('studio-subtitle').textContent = `Error: ${res.error || 'Generation failed.'}`;
      }
    }).catch(err => {
      this.isGenerating = false;
      if (btnCancel) btnCancel.style.display = 'none';
      this.appendLogLine(`[Error] Execution exception: ${err.message}`, 'log-error');
    });
  },

  handleProgressEvent(event) {
    if (!event || !event.type) return;

    switch (event.type) {
      case 'start':
        this.activeRunId = event.run_id;
        this.activeOutputDir = event.output_dir;
        this.appendLogLine(`[Engine] Run initialized: ${event.run_id}`, 'log-info');
        break;

      case 'stage':
        this.setActiveStage(event.stage_num);
        this.updateProgress(event.stage_num * 15, event.title);
        this.appendLogLine(`[Stage ${event.stage_num}/6] ${event.title}`, 'log-info');
        break;

      case 'script_ready':
        document.getElementById('studio-title').textContent = event.title;
        this.renderInitialScenes(event.script.scenes || []);
        this.updateProgress(18, `Script ready: ${event.scenes_count} scenes planned`);
        break;

      case 'voice_ready':
        this.updateProgress(28, `Narration voiceover generated (${Math.round(event.duration)}s)`);
        break;

      case 'subtitles_ready':
        this.updateProgress(35, `Subtitles aligned (${event.words_count} words synchronized)`);
        break;

      case 'scene_image':
        this.updateSceneImage(event.scene_index, event.image_path);
        const imgProgress = 35 + Math.round((event.scene_index / (event.total_scenes || 5)) * 30);
        this.updateProgress(imgProgress, `Visual generated: Scene ${event.scene_index}/${event.total_scenes}`);
        break;

      case 'scene_depth':
        this.updateSceneDepth(event.scene_index, event.depth_path);
        const depthProgress = 65 + Math.round((event.scene_index / (event.total_scenes || 5)) * 15);
        this.updateProgress(depthProgress, `2.5D depth calculated: Scene ${event.scene_index}`);
        break;

      case 'render_progress':
        const renderPct = 80 + Math.round((event.percent || 0) * 0.2);
        this.updateProgress(renderPct, `Rendering video frames: ${event.percent}% (Frame ${event.frame}/${event.total_frames})`);
        break;

      case 'complete':
        this.updateProgress(100, 'Video generated successfully!');
        break;

      case 'error':
        this.appendLogLine(`[Error] ${event.message}`, 'log-error');
        break;
    }
  },

  setActiveStage(stageNum) {
    for (let i = 1; i <= 6; i++) {
      const step = document.getElementById(`stage-${i}`);
      if (!step) continue;
      if (i < stageNum) {
        step.classList.remove('active');
        step.classList.add('completed');
      } else if (i === stageNum) {
        step.classList.add('active');
        step.classList.remove('completed');
      } else {
        step.classList.remove('active', 'completed');
      }
    }
  },

  updateProgress(percent, label) {
    const p = Math.min(100, Math.max(0, percent));
    const fill = document.getElementById('studio-progress-fill');
    if (fill) fill.style.width = `${p}%`;
    const pctLabel = document.getElementById('studio-progress-percent');
    if (pctLabel) pctLabel.textContent = `${p}%`;
    const statusLabel = document.getElementById('studio-progress-label');
    if (statusLabel && label) statusLabel.textContent = label;
  },

  renderInitialScenes(scenes) {
    this.scenes = scenes;
    const grid = document.getElementById('studio-scenes-grid');
    if (!grid) return;

    if (!scenes || scenes.length === 0) {
      grid.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">No scenes parsed.</div>';
      return;
    }

    grid.innerHTML = scenes.map((scene, idx) => {
      const sceneNum = idx + 1;
      return `
        <div class="scene-card" id="scene-card-${sceneNum}">
          <div class="scene-preview-container" id="scene-preview-${sceneNum}">
            <div class="scene-placeholder">
              <span class="status-dot pulsing"></span>
              Generating Visual...
            </div>
          </div>
          <div class="scene-card-body">
            <span class="scene-badge">Scene ${sceneNum}</span>
            <div class="scene-narrator">${escapeHtml(scene.narrator || '')}</div>
            <div class="scene-visual-prompt"><strong>Prompt:</strong> ${escapeHtml(scene.visual_prompt || '')}</div>
          </div>
        </div>
      `;
    }).join('');
  },

  updateSceneImage(sceneIndex, imagePath) {
    const preview = document.getElementById(`scene-preview-${sceneIndex}`);
    if (preview && imagePath) {
      // Format file url safely
      const cleanPath = imagePath.replace(/\\/g, '/');
      const fileUrl = cleanPath.startsWith('file://') ? cleanPath : `file:///${cleanPath}`;
      preview.innerHTML = `<img class="scene-preview-img" src="${fileUrl}" alt="Scene ${sceneIndex} Visual">`;
    }
  },

  updateSceneDepth(sceneIndex, depthPath) {
    const card = document.getElementById(`scene-card-${sceneIndex}`);
    if (card) {
      let badge = card.querySelector('.depth-badge');
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'scene-badge depth-badge';
        badge.style.backgroundColor = 'rgba(16, 185, 129, 0.15)';
        badge.style.color = 'var(--accent-green)';
        badge.style.marginLeft = '6px';
        badge.textContent = '2.5D Parallax Ready';
        card.querySelector('.scene-badge').after(badge);
      }
    }
  },

  appendLogLine(text, styleClass = '') {
    const box = document.getElementById('studio-console-log');
    if (!box) return;

    const div = document.createElement('div');
    div.className = `log-line ${styleClass}`;
    div.textContent = text;
    box.appendChild(div);

    // Auto-scroll
    box.scrollTop = box.scrollHeight;
  }
};

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
