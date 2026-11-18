let activeVideos = [];
let libraryVideos = [];
let isProcessing = false;
let pollInterval = null;
let nextBatchName = 'Batch-004';
let currentBatchDir = '';
let systemInfoData = null;

const BACKEND_URL = 'http://127.0.0.1:8765';

// DOM Elements
const fileInput = document.getElementById('file-input');
const dropzone = document.getElementById('dropzone');
const videoList = document.getElementById('video-list');
const emptyState = document.getElementById('empty-state');
const logBox = document.getElementById('log-box');
const uploadBox = document.getElementById('upload-progress-box');
const uploadFilename = document.getElementById('upload-filename');
const uploadPctLabel = document.getElementById('upload-pct-label');
const uploadFill = document.getElementById('upload-progress-fill');
const jobIdDisplay = document.getElementById('job-id-display');
const batchBanner = document.getElementById('batch-completed-banner');
const libraryPanel = document.getElementById('library-panel');
const libraryGrid = document.getElementById('library-grid');

// Lifecycle Initialization
window.addEventListener('DOMContentLoaded', async () => {
  appendLog('Connecting to Beyond History AI Clipper engine...');
  await pollBackendReady();
  await loadSystemDiagnostics();
  fetchUploadedVideos();
  updateStatus();
  startPolling();
});

async function pollBackendReady() {
  let attempts = 0;
  while (attempts < 20) {
    try {
      const res = await fetch(`${BACKEND_URL}/api/status`);
      if (res.ok) {
        appendLog('Connected to AI engine successfully.');
        const banner = document.getElementById('backend-offline-banner');
        if (banner) banner.style.display = 'none';
        return;
      }
    } catch (e) {
      // Waiting for backend to start
    }
    attempts++;
    await new Promise(r => setTimeout(r, 600));
  }

  appendLog('⚠️ AI Engine is not responding. First-time setup may be required on this PC.');
  const banner = document.getElementById('backend-offline-banner');
  if (banner) banner.style.display = 'flex';
}

function triggerEnvironmentSetup() {
  if (window.electronAPI && window.electronAPI.runEnvironmentSetup) {
    appendLog('Launching automated environment setup bootstrapper...');
    window.electronAPI.runEnvironmentSetup();
  } else {
    alert('Please run scripts/setup_clean_pc.bat to configure the environment.');
  }
}

async function retryBackendConnection() {
  appendLog('Retrying connection to backend...');
  const banner = document.getElementById('backend-offline-banner');
  if (banner) banner.style.display = 'none';
  await pollBackendReady();
  await loadSystemDiagnostics();
  fetchUploadedVideos();
  updateStatus();
}

// ----------------- DIAGNOSTICS & SETUP WIZARD -----------------

async function loadSystemDiagnostics() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/system_info`);
    if (!res.ok) return;
    const data = await res.json();
    systemInfoData = data;

    // GPU
    const gpuLabel = document.getElementById('gpu-label');
    const diagGpu = document.getElementById('diag-gpu');
    const diagGpuStatus = document.getElementById('diag-gpu-status');

    if (data.gpu && data.gpu.available) {
      gpuLabel.innerText = `${data.gpu.name} (CUDA Active)`;
      diagGpu.innerText = `${data.gpu.name} (${data.gpu.vram_gb} GB VRAM — CUDA ${data.gpu.cuda_version || 'Active'})`;
      diagGpuStatus.className = 'diag-status ok';
      diagGpuStatus.innerText = '✓';
    } else {
      gpuLabel.innerText = 'CPU Fallback Active';
      diagGpu.innerText = 'No NVIDIA GPU (CPU Int8 Fallback Mode)';
      diagGpuStatus.className = 'diag-status warn';
      diagGpuStatus.innerText = '!';
    }

    // CPU & RAM
    document.getElementById('diag-cpu').innerText = `${data.cpu.name} (${data.cpu.threads} threads) • ${data.ram.total_gb} GB RAM (${data.ram.available_gb} GB free)`;

    // Disk
    document.getElementById('diag-disk').innerText = `Drive ${data.disk.drive} (${data.disk.free_gb} GB free space)`;

    // FFmpeg
    const diagFfmpeg = document.getElementById('diag-ffmpeg');
    const diagFfmpegStatus = document.getElementById('diag-ffmpeg-status');
    if (data.ffmpeg.installed) {
      diagFfmpeg.innerText = `Installed (${data.ffmpeg.path})`;
      diagFfmpegStatus.className = 'diag-status ok';
      diagFfmpegStatus.innerText = '✓';
    } else {
      diagFfmpeg.innerText = 'Missing FFmpeg executable';
      diagFfmpegStatus.className = 'diag-status warn';
      diagFfmpegStatus.innerText = '✕';
    }

    // Faster-Whisper Model
    const diagModel = document.getElementById('diag-model');
    const diagModelStatus = document.getElementById('diag-model-status');
    const modelBox = document.getElementById('model-download-box');

    if (data.model.installed) {
      diagModel.innerText = `Cached & Ready (${data.model.name})`;
      diagModelStatus.className = 'diag-status ok';
      diagModelStatus.innerText = '✓';
      modelBox.style.display = 'none';
    } else {
      diagModel.innerText = 'Not downloaded yet (Setup required)';
      diagModelStatus.className = 'diag-status warn';
      diagModelStatus.innerText = '!';
      modelBox.style.display = 'block';
      // If first run, auto show modal
      openSetupModal();
    }

    // Python
    document.getElementById('diag-python').innerText = `Python ${data.python.version} (${data.python.path})`;

    // Cache dir & Output dir
    if (document.getElementById('cache-path-input')) {
      document.getElementById('cache-path-input').value = data.cache_dir || '';
    }
    if (document.getElementById('output-path-input')) {
      document.getElementById('output-path-input').value = data.output_dir || '';
    }

  } catch (err) {
    console.warn('Could not load system diagnostics:', err);
  }
}

function openSetupModal() {
  document.getElementById('setup-modal').style.display = 'flex';
}

function closeSetupModal() {
  document.getElementById('setup-modal').style.display = 'none';
}

function openDiagnosticsModal() {
  loadSystemDiagnostics();
  openSetupModal();
}

async function chooseCacheFolder() {
  if (window.electronAPI && window.electronAPI.selectDirectory) {
    const dir = await window.electronAPI.selectDirectory();
    if (dir) {
      document.getElementById('cache-path-input').value = dir;
      try {
        await fetch(`${BACKEND_URL}/api/set_cache_dir`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: dir })
        });
        appendLog('Updated cache directory: ' + dir);
        loadSystemDiagnostics();
      } catch (e) {
        appendLog('Failed to save cache directory: ' + e);
      }
    }
  }
}

async function chooseOutputFolder() {
  if (window.electronAPI && window.electronAPI.selectDirectory) {
    const dir = await window.electronAPI.selectDirectory();
    if (dir) {
      document.getElementById('output-path-input').value = dir;
      try {
        await fetch(`${BACKEND_URL}/api/set_output_dir`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: dir })
        });
        appendLog('Updated output directory: ' + dir);
        fetchUploadedVideos();
      } catch (e) {
        appendLog('Failed to save output directory: ' + e);
      }
    }
  }
}

async function downloadModel() {
  const btn = document.getElementById('btn-download-model');
  const prog = document.getElementById('model-download-prog');
  btn.disabled = true;
  btn.innerText = 'Downloading Model...';
  prog.style.display = 'block';

  try {
    const res = await fetch(`${BACKEND_URL}/api/download_model`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      btn.innerText = '✓ Model Downloaded';
      prog.style.display = 'none';
      await loadSystemDiagnostics();
    } else {
      alert('Model download failed: ' + (data.error || 'Unknown error'));
      btn.disabled = false;
      btn.innerText = 'Retry Download';
    }
  } catch (err) {
    alert('Error connecting to download API: ' + err);
    btn.disabled = false;
    btn.innerText = 'Retry Download';
  }
}

async function runEngineTest() {
  const btn = document.getElementById('btn-test-engine');
  const resultDiv = document.getElementById('test-engine-result');
  btn.disabled = true;
  btn.innerText = 'Testing...';
  resultDiv.style.display = 'block';
  resultDiv.innerHTML = '<span style="color:var(--text-muted);">Running diagnostic verification on FFmpeg, Whisper, and inference hardware...</span>';

  try {
    const res = await fetch(`${BACKEND_URL}/api/test_engine`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      const icon = data.engine_ready ? '✅' : '⚠️';
      resultDiv.innerHTML = `
        <div style="font-weight:700; color:${data.engine_ready ? '#10b981' : '#f59e0b'}; margin-bottom:0.3rem;">
          ${icon} ${data.message}
        </div>
        <div style="font-size:0.75rem; color:#94a3b8;">
          • FFmpeg: ${data.ffmpeg_ok ? 'Available (' + data.ffmpeg_version + ')' : 'Missing'}<br>
          • Speech AI Engine: ${data.whisper_ok ? 'Faster-Whisper Loaded' : 'Unavailable'}<br>
          • Hardware Acceleration: ${data.device_mode}
        </div>
      `;
      appendLog(`[TEST] Diagnostic check completed: ${data.message}`);
    } else {
      resultDiv.innerHTML = `<span style="color:#ef4444;">❌ Engine test error: ${data.error || 'Unknown error'}</span>`;
    }
  } catch (err) {
    resultDiv.innerHTML = `<span style="color:#ef4444;">❌ Connection error during test: ${err}</span>`;
  } finally {
    btn.disabled = false;
    btn.innerText = '⚡ Test Engine';
  }
}

// ----------------- BATCH HISTORY -----------------

async function openHistoryModal() {
  const modal = document.getElementById('history-modal');
  const list = document.getElementById('history-list');
  modal.style.display = 'flex';
  list.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem; padding:1rem;">Loading batch history...</div>';

  try {
    const res = await fetch(`${BACKEND_URL}/api/history`);
    const data = await res.json();
    const batchesRes = await fetch(`${BACKEND_URL}/api/batches`);
    const batchesData = await batchesRes.json();

    list.innerHTML = '';

    const allBatches = batchesData.batches || [];
    if (!allBatches.length) {
      list.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem; padding:1rem;">No previous batches generated yet.</div>';
      return;
    }

    allBatches.reverse().forEach(b => {
      // Find matching report or history item
      const item = document.createElement('div');
      item.className = 'history-item';
      item.innerHTML = `
        <div>
          <div class="history-item-title">${b.name} <span style="font-size:0.75rem; color:var(--gold); font-weight:normal;">(${b.clip_count !== undefined ? b.clip_count + ' clips' : ''})</span></div>
          <div class="history-item-sub">Path: <code>${b.path}</code></div>
        </div>
        <button class="btn btn-secondary" style="font-size:0.8rem; padding:0.45rem 1rem;" onclick="openSpecificFolder('${encodeURIComponent(b.path)}')">
          📂 Open in Explorer
        </button>
      `;
      list.appendChild(item);
    });

  } catch (err) {
    list.innerHTML = `<div style="color:var(--danger); font-size:0.85rem;">Error loading history: ${err}</div>`;
  }
}

function closeHistoryModal() {
  document.getElementById('history-modal').style.display = 'none';
}

function openSpecificFolder(encodedPath) {
  const p = decodeURIComponent(encodedPath);
  if (window.electronAPI && window.electronAPI.openFolder) {
    window.electronAPI.openFolder(p);
  } else {
    fetch(`${BACKEND_URL}/api/open_folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: p })
    });
  }
}

function openActiveBatchFolder() {
  if (currentBatchDir) {
    openSpecificFolder(encodeURIComponent(currentBatchDir));
  } else {
    openOutputDirectory();
  }
}

function openOutputDirectory() {
  if (window.electronAPI && window.electronAPI.openFolder) {
    window.electronAPI.openFolder('');
  } else {
    fetch(`${BACKEND_URL}/api/open_folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: '' })
    });
  }
}

// ----------------- VIDEO SOURCE SELECTION & UPLOAD -----------------

async function triggerNativeFilePicker() {
  if (window.electronAPI && window.electronAPI.selectVideoFiles) {
    const filePaths = await window.electronAPI.selectVideoFiles();
    if (filePaths && filePaths.length) {
      for (const p of filePaths) {
        await addLocalPathToActive(p);
      }
    }
  } else {
    fileInput.click();
  }
}

async function addLocalPathToActive(p) {
  appendLog('Adding local video: ' + p);
  try {
    const res = await fetch(`${BACKEND_URL}/api/select_local`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: p })
    });
    const data = await res.json();
    if (data.error) {
      appendLog('Failed to add local file: ' + data.error);
      alert(data.error);
    } else {
      appendLog(`Loaded: ${data.video.filename} [${data.video.width}x${data.video.height}]`);
      addVideoToActive(data.video);
      fetchUploadedVideos();
    }
  } catch (err) {
    appendLog('Error adding local file: ' + err);
  }
}

function fetchUploadedVideos() {
  fetch(`${BACKEND_URL}/api/uploaded_videos`)
    .then(r => r.json())
    .then(data => {
      libraryVideos = data.library_videos || [];
      document.getElementById('library-count-label').innerText = libraryVideos.length;
      renderLibrary();

      if (data.next_batch) {
        updateNextBatchName(data.next_batch);
      }

      if (data.active_videos !== undefined) {
        activeVideos = data.active_videos;
        renderVideoList();
      }
    })
    .catch(err => console.log('Could not fetch existing videos:', err));
}

function updateNextBatchName(name) {
  nextBatchName = name;
  document.getElementById('header-next-batch').innerText = name;
  document.querySelectorAll('.next-batch-label').forEach(el => el.innerText = name);
}

// Drag & Drop
['dragenter', 'dragover'].forEach(eventName => {
  dropzone.addEventListener(eventName, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add('dragover');
  });
});

['dragleave', 'dragend', 'drop'].forEach(eventName => {
  dropzone.addEventListener(eventName, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('dragover');
  });
});

dropzone.addEventListener('drop', (e) => {
  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
    handleFiles(e.dataTransfer.files);
  }
});

fileInput.addEventListener('change', (e) => {
  if (e.target.files && e.target.files.length) {
    handleFiles(e.target.files);
    fileInput.value = '';
  }
});

document.getElementById('btn-add-local').addEventListener('click', () => {
  const p = document.getElementById('local-path-input').value.trim();
  if (!p) return;
  addLocalPathToActive(p).then(() => {
    document.getElementById('local-path-input').value = '';
  });
});

function toggleLibrary() {
  if (libraryPanel.style.display === 'block') {
    libraryPanel.style.display = 'none';
  } else {
    libraryPanel.style.display = 'block';
    renderLibrary();
  }
}

function renderLibrary() {
  libraryGrid.innerHTML = '';
  if (!libraryVideos.length) {
    libraryGrid.innerHTML = '<div style="font-size:0.75rem; color:var(--text-muted); grid-column:span 2;">No uploaded videos in library yet.</div>';
    return;
  }
  libraryVideos.forEach(v => {
    const isAdded = activeVideos.some(x => x.path === v.path);
    const item = document.createElement('div');
    item.className = 'library-item';
    item.innerHTML = `
      <div class="library-item-name" title="${v.filename}">${v.filename}</div>
      <div style="font-size:0.72rem; color:var(--text-muted); display:flex; justify-content:space-between;">
        <span>⏱ ${Math.floor(v.duration / 60)}m ${Math.floor(v.duration % 60)}s</span>
        <span>💾 ${v.size_mb} MB</span>
      </div>
      <button class="btn ${isAdded ? 'btn-secondary' : 'btn-success'}" style="padding:0.3rem; font-size:0.75rem;" onclick="toggleVideoFromLibrary('${encodeURIComponent(v.path)}')" ${isAdded ? 'disabled' : ''}>
        ${isAdded ? '✓ Added to Batch' : '+ Add to Batch'}
      </button>
    `;
    libraryGrid.appendChild(item);
  });
}

function toggleVideoFromLibrary(encodedPath) {
  const p = decodeURIComponent(encodedPath);
  const v = libraryVideos.find(x => x.path === p);
  if (v) {
    addVideoToActive(v);
    renderLibrary();
  }
}

function handleFiles(files) {
  const fileList = Array.from(files);
  if (!fileList.length) return;
  appendLog('Received ' + fileList.length + ' file(s) for upload.');
  uploadQueue(fileList, 0);
}

function uploadQueue(files, index) {
  if (index >= files.length) {
    uploadBox.style.display = 'none';
    fetchUploadedVideos();
    return;
  }
  const file = files[index];
  uploadSingleFile(file, () => {
    uploadQueue(files, index + 1);
  });
}

function uploadSingleFile(file, onComplete) {
  const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
  appendLog('Uploading ' + file.name + ' (' + sizeMb + ' MB)...');

  uploadBox.style.display = 'block';
  uploadFilename.innerText = file.name + ' (' + sizeMb + ' MB)';
  uploadPctLabel.innerText = '0%';
  uploadFill.style.width = '0%';

  const formData = new FormData();
  formData.append('file', file, file.name);

  const xhr = new XMLHttpRequest();
  xhr.open('POST', `${BACKEND_URL}/api/upload`, true);

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      const pct = Math.round((e.loaded / e.total) * 100);
      uploadFill.style.width = pct + '%';
      uploadPctLabel.innerText = pct + '% (' + (e.loaded / (1024*1024)).toFixed(1) + ' / ' + sizeMb + ' MB)';
    }
  };

  xhr.onload = () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      try {
        const data = JSON.parse(xhr.responseText);
        if (data.video) {
          appendLog('Upload successful: ' + data.video.filename + ' [' + data.video.width + 'x' + data.video.height + ']');
          addVideoToActive(data.video);
        } else if (data.error) {
          appendLog('Upload failed: ' + data.error);
          alert('Upload failed: ' + data.error);
        }
      } catch (err) {
        appendLog('Server response parse error: ' + err);
      }
    } else {
      appendLog('Upload HTTP error ' + xhr.status + ': ' + xhr.responseText);
      alert('Upload failed with status ' + xhr.status);
    }
    if (onComplete) onComplete();
  };

  xhr.onerror = () => {
    appendLog('Network error during upload of ' + file.name);
    alert('Network error during video upload. Please check server.');
    if (onComplete) onComplete();
  };

  xhr.send(formData);
}

function addVideoToActive(v) {
  if (activeVideos.some(x => x.path === v.path)) {
    return;
  }
  activeVideos.push(v);
  renderVideoList();
  fetch(`${BACKEND_URL}/api/add_to_batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: v.path })
  });
}

function removeVideo(idx) {
  const v = activeVideos[idx];
  if (!v) return;
  activeVideos.splice(idx, 1);
  renderVideoList();
  renderLibrary();
  fetch(`${BACKEND_URL}/api/remove_video`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: v.path })
  });
}

function renderVideoList() {
  videoList.innerHTML = '';
  document.getElementById('active-count-label').innerText = activeVideos.length + ' Selected';
  if (!activeVideos.length) {
    emptyState.style.display = 'block';
    return;
  }
  emptyState.style.display = 'none';

  activeVideos.forEach((v, idx) => {
    const item = document.createElement('div');
    item.className = 'video-item';
    item.innerHTML = `
      <div class="video-item-header">
        <div class="video-item-title" title="${v.filename}">${v.filename}</div>
        <button class="btn-remove" onclick="removeVideo(${idx})">× Remove</button>
      </div>
      <video class="video-item-preview" controls src="${BACKEND_URL}/stream/${encodeURIComponent(v.path)}"></video>
      <div class="video-item-meta">
        <span>⏱ ${Math.floor(v.duration / 60)}m ${Math.floor(v.duration % 60)}s</span>
        <span>📐 ${v.width}x${v.height} (${v.aspect_ratio})</span>
        <span>💾 ${v.size_mb} MB</span>
      </div>
    `;
    videoList.appendChild(item);
  });
}

function startNewBatchWorkflow() {
  if (isProcessing) {
    alert('Cannot start a new batch while processing is currently running.');
    return;
  }
  appendLog('Initializing clean workspace for new batch...');
  fetch(`${BACKEND_URL}/api/new_batch`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      if (data.status === 'success') {
        activeVideos = [];
        currentBatchDir = '';
        renderVideoList();
        renderLibrary();
        batchBanner.style.display = 'none';
        document.getElementById('results-card').style.display = 'none';
        document.getElementById('progress-fill').style.width = '0%';
        document.getElementById('progress-pct').innerText = '0%';
        document.getElementById('progress-stage').innerText = 'Ready — 0%';
        jobIdDisplay.innerText = 'Job ID: Ready for ' + (data.next_batch || 'New Batch');
        if (data.next_batch) updateNextBatchName(data.next_batch);
        appendLog('Clean workspace initialized. Ready for ' + (data.next_batch || 'new batch') + '.');
      } else {
        alert('Failed to reset for new batch: ' + (data.error || 'Unknown error'));
      }
    })
    .catch(err => {
      alert('Communication error: ' + err);
    });
}

// ----------------- CONTROLS & BATCH EXECUTION -----------------

function adjustCount(id, delta) {
  const el = document.getElementById(id);
  let val = parseInt(el.innerText) + delta;
  if (val < 0) val = 0;
  if (val > 50) val = 50; // Flexible up to 50 clips per video
  el.innerText = val;
}

function getTargetDurations() {
  const targets = {};
  if (document.getElementById('chk-30').checked) targets[30] = parseInt(document.getElementById('cnt-30').innerText);
  if (document.getElementById('chk-45').checked) targets[45] = parseInt(document.getElementById('cnt-45').innerText);
  if (document.getElementById('chk-60').checked) targets[60] = parseInt(document.getElementById('cnt-60').innerText);
  if (document.getElementById('chk-90').checked) targets[90] = parseInt(document.getElementById('cnt-90').innerText);
  if (document.getElementById('chk-120').checked) targets[120] = parseInt(document.getElementById('cnt-120').innerText);
  return targets;
}

function startBatch() {
  if (!activeVideos.length) {
    alert('Please add or upload at least one video to process in this batch.');
    return;
  }
  const durations = getTargetDurations();
  if (!Object.values(durations).some(v => v > 0)) {
    alert('Please select at least one duration preset with count > 0.');
    return;
  }

  const format = document.querySelector('input[name="format"]:checked').value;
  const burnSubs = document.getElementById('chk-burn-subtitles').checked;

  const payload = {
    video_paths: activeVideos.map(v => v.path),
    target_durations: durations,
    output_format: format,
    burn_subtitles: burnSubs
  };

  appendLog('Dispatching start request to engine...');
  fetch(`${BACKEND_URL}/api/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) {
      alert('Start error: ' + data.error);
      appendLog('Start error: ' + data.error);
    } else {
      isProcessing = true;
      document.getElementById('btn-start').disabled = true;
      document.getElementById('btn-pause').disabled = false;
      document.getElementById('btn-cancel').disabled = false;
      jobIdDisplay.innerText = 'Job ID: ' + (data.job_id || 'Active');
      appendLog('Clipper Job Started: ' + (data.job_id || ''));
      startPolling();
    }
  })
  .catch(err => {
    alert('Communication error: ' + err);
    appendLog('Communication error: ' + err);
  });
}

function pauseBatch() {
  fetch(`${BACKEND_URL}/api/pause`, { method: 'POST' }).then(() => {
    document.getElementById('btn-pause').style.display = 'none';
    document.getElementById('btn-resume').style.display = 'inline-flex';
    document.getElementById('btn-resume').disabled = false;
  });
}

function resumeBatch() {
  fetch(`${BACKEND_URL}/api/resume`, { method: 'POST' }).then(() => {
    document.getElementById('btn-resume').style.display = 'none';
    document.getElementById('btn-pause').style.display = 'inline-flex';
    document.getElementById('btn-pause').disabled = false;
  });
}

function cancelBatch() {
  if (!confirm('Are you sure you want to cancel the active batch?')) return;
  fetch(`${BACKEND_URL}/api/cancel`, { method: 'POST' });
}

function startPolling() {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(updateStatus, 1500);
}

function updateStatus() {
  fetch(`${BACKEND_URL}/api/status`)
    .then(r => r.json())
    .then(data => {
      document.getElementById('progress-fill').style.width = data.overall_percent + '%';
      document.getElementById('progress-pct').innerText = Math.round(data.overall_percent) + '%';
      document.getElementById('progress-stage').innerText = data.current_detail || data.current_stage || 'Ready — 0%';

      if (data.next_batch) {
        updateNextBatchName(data.next_batch);
      }

      if (data.job_id) {
        jobIdDisplay.innerText = 'Job ID: ' + data.job_id + ' [' + data.state.toUpperCase() + ']';
      }

      if (data.logs && data.logs.length) {
        logBox.innerText = data.logs.join('\n');
        logBox.scrollTop = logBox.scrollHeight;
      }

      if (data.state === 'running') {
        isProcessing = true;
        batchBanner.style.display = 'none';
        document.getElementById('btn-start').disabled = true;
        document.getElementById('btn-pause').disabled = false;
        document.getElementById('btn-pause').style.display = 'inline-flex';
        document.getElementById('btn-resume').style.display = 'none';
        document.getElementById('btn-cancel').disabled = false;
      } else if (data.state === 'paused') {
        document.getElementById('btn-pause').style.display = 'none';
        document.getElementById('btn-resume').style.display = 'inline-flex';
        document.getElementById('btn-resume').disabled = false;
      } else if (data.state === 'completed') {
        isProcessing = false;
        document.getElementById('btn-start').disabled = false;
        document.getElementById('btn-pause').disabled = true;
        document.getElementById('btn-pause').style.display = 'inline-flex';
        document.getElementById('btn-resume').style.display = 'none';
        document.getElementById('btn-cancel').disabled = true;

        batchBanner.style.display = 'flex';
        if (data.batch_result) {
          currentBatchDir = data.batch_result.batch_dir;
          document.getElementById('banner-title').innerText = '🎉 ' + (data.batch_result.batch_id || 'Batch') + ' Completed Successfully!';
          document.getElementById('banner-subtitle').innerText = 'Generated ' + data.batch_result.total_clips + ' clips in ' + data.batch_result.elapsed_seconds + 's. Folder: ' + data.batch_result.batch_dir;
          renderResults(data.batch_result);
        }
      } else if (data.state === 'cancelled' || data.state === 'error' || data.state === 'idle') {
        isProcessing = false;
        document.getElementById('btn-start').disabled = false;
        document.getElementById('btn-pause').disabled = true;
        document.getElementById('btn-pause').style.display = 'inline-flex';
        document.getElementById('btn-resume').style.display = 'none';
        document.getElementById('btn-cancel').disabled = true;
      }
    })
    .catch(err => console.log('Status polling error:', err));
}

function renderResults(res) {
  const card = document.getElementById('results-card');
  const gallery = document.getElementById('results-gallery');
  const summary = document.getElementById('results-summary');

  card.style.display = 'block';
  summary.innerHTML = `<strong>Batch ${res.batch_id}</strong>: Generated <strong>${res.total_clips}</strong> clips in ${res.elapsed_seconds}s. Folder: <code>${res.batch_dir}</code>`;
  gallery.innerHTML = '';

  for (const [vname, clips] of Object.entries(res.results)) {
    for (const c of clips) {
      const videoSrc = c.vertical_mp4 || c.landscape_mp4;
      const cardEl = document.createElement('div');
      cardEl.className = 'clip-card';
      cardEl.innerHTML = `
        <video class="clip-player" controls poster="${BACKEND_URL}/stream/${encodeURIComponent(c.contact_sheet || '')}" src="${BACKEND_URL}/stream/${encodeURIComponent(videoSrc)}"></video>
        <div class="clip-card-body">
          <div class="clip-card-title">${c.clip_id} (${c.duration}s)</div>
          <div class="clip-scores">
            <span class="score-chip highlight">Score: ${c.score}/100</span>
            <span class="score-chip">Hook: ${c.hook_score}</span>
            <span class="score-chip">Density: ${c.density_score}</span>
            <span class="score-chip">Closure: ${c.closure_score}</span>
          </div>
          <div class="clip-transcript">"${c.text}"</div>
          <div class="clip-actions">
            ${c.vertical_mp4 ? `<a class="btn-action" href="${BACKEND_URL}/stream/${encodeURIComponent(c.vertical_mp4)}" download>⬇ Vertical</a>` : ''}
            ${c.landscape_mp4 ? `<a class="btn-action" href="${BACKEND_URL}/stream/${encodeURIComponent(c.landscape_mp4)}" download>⬇ Landscape</a>` : ''}
            ${c.srt_path ? `<a class="btn-action" href="${BACKEND_URL}/stream/${encodeURIComponent(c.srt_path)}" download>⬇ SRT</a>` : ''}
            <button class="btn-action" onclick="openSpecificFolder('${encodeURIComponent(res.batch_dir)}')">📂 Folder</button>
          </div>
        </div>
      `;
      gallery.appendChild(cardEl);
    }
  }
}

function appendLog(msg) {
  const t = new Date().toLocaleTimeString();
  logBox.innerText += `\n[${t}] ${msg}`;
  logBox.scrollTop = logBox.scrollHeight;
}
