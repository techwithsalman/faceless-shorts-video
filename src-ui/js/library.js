/**
 * Prompt2Video AI — Video Library Controller
 */

window.LibraryController = {
  videos: [],
  selectedVideo: null,

  init() {
    this.setupButtons();
    this.loadLibrary();
  },

  setupButtons() {
    const btnRefresh = document.getElementById('btn-library-refresh');
    if (btnRefresh) {
      btnRefresh.addEventListener('click', () => this.loadLibrary());
    }

    const btnOpenFolder = document.getElementById('btn-library-open-folder');
    if (btnOpenFolder) {
      btnOpenFolder.addEventListener('click', () => {
        if (window.api && window.api.openPath) {
          const outDir = (window.App && window.App.state && window.App.state.outputDir) || '';
          window.api.openPath(outDir);
        }
      });
    }

    // Modal controls
    const btnCloseModal = document.getElementById('btn-close-modal');
    if (btnCloseModal) {
      btnCloseModal.addEventListener('click', () => this.closePlayerModal());
    }

    const modalBackdrop = document.getElementById('player-modal');
    if (modalBackdrop) {
      modalBackdrop.addEventListener('click', (e) => {
        if (e.target === modalBackdrop) this.closePlayerModal();
      });
    }

    const btnModalFolder = document.getElementById('btn-modal-open-folder');
    if (btnModalFolder) {
      btnModalFolder.addEventListener('click', () => {
        if (this.selectedVideo && window.api && window.api.openInFolder) {
          window.api.openInFolder(this.selectedVideo.path);
        }
      });
    }
  },

  async loadLibrary() {
    const container = document.getElementById('library-container');
    if (!container) return;

    if (!window.api || !window.api.getLibrary) {
      container.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">Library API unavailable.</div>';
      return;
    }

    container.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">Loading video library...</div>';

    try {
      const outDir = (window.App && window.App.state && window.App.state.outputDir) || '';
      const videos = await window.api.getLibrary(outDir);
      this.videos = videos || [];

      if (this.videos.length === 0) {
        container.innerHTML = `
          <div class="card" style="text-align: center; padding: 48px; grid-column: 1 / -1; color: var(--text-muted);">
            <svg style="width: 48px; height: 48px; fill: currentColor; margin-bottom: 12px; opacity: 0.5;" viewBox="0 0 24 24">
              <path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z"/>
            </svg>
            <h3>No Videos Generated Yet</h3>
            <p style="margin-top: 6px;">Head over to the Create tab to generate your first local AI video.</p>
          </div>
        `;
        return;
      }

      container.innerHTML = this.videos.map((item, idx) => {
        const title = item.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');
        const dateStr = item.createdAt ? new Date(item.createdAt).toLocaleDateString(undefined, {
          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        }) : '';

        const thumbHtml = item.thumbnail ? 
          `<img src="file:///${item.thumbnail.replace(/\\/g, '/')}" alt="Thumbnail">` :
          `<div style="color: var(--text-muted); font-size: 0.8rem;">1080×1920 MP4</div>`;

        return `
          <div class="library-item" data-index="${idx}">
            <div class="library-thumbnail">
              ${thumbHtml}
              <div class="library-play-overlay">
                <svg style="width: 20px; height: 20px; fill: currentColor;" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              </div>
            </div>
            <div class="library-item-body">
              <div class="library-item-title" title="${escapeHtml(title)}">${escapeHtml(title)}</div>
              <div class="library-item-meta">
                <span>${item.sizeMB || 0} MB</span>
                <span>${dateStr}</span>
              </div>
              <div class="library-item-actions">
                <button class="btn btn-secondary btn-small btn-show-folder" data-index="${idx}" style="flex: 1;">Show in Folder</button>
              </div>
            </div>
          </div>
        `;
      }).join('');

      // Add click listeners
      container.querySelectorAll('.library-item').forEach(card => {
        card.addEventListener('click', (e) => {
          if (e.target.closest('.btn-show-folder')) {
            const idx = parseInt(e.target.closest('.btn-show-folder').dataset.index, 10);
            const v = this.videos[idx];
            if (v && window.api && window.api.openInFolder) {
              window.api.openInFolder(v.path);
            }
            return;
          }
          const idx = parseInt(card.dataset.index, 10);
          this.openPlayerModal(this.videos[idx]);
        });
      });

    } catch (err) {
      container.innerHTML = `<div style="color: var(--accent-red); padding: 20px;">Failed to scan library: ${err.message}</div>`;
    }
  },

  openPlayerModal(video) {
    if (!video) return;
    this.selectedVideo = video;

    const modal = document.getElementById('player-modal');
    const player = document.getElementById('modal-video-element');
    const title = document.getElementById('modal-video-title');
    const info = document.getElementById('modal-video-info');

    const cleanPath = video.path.replace(/\\/g, '/');
    const fileUrl = cleanPath.startsWith('file://') ? cleanPath : `file:///${cleanPath}`;

    title.textContent = video.name;
    info.textContent = `${video.sizeMB} MB • ${video.path}`;
    player.src = fileUrl;

    modal.classList.add('active');
    player.play().catch(() => {});
  },

  closePlayerModal() {
    const modal = document.getElementById('player-modal');
    const player = document.getElementById('modal-video-element');
    if (player) {
      player.pause();
      player.src = '';
    }
    if (modal) modal.classList.remove('active');
    this.selectedVideo = null;
  }
};
