const { dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');
const { spawn, exec } = require('child_process');
const {
  isPackaged,
  getBackendDir,
  getScriptPath,
  getUserDataDir,
  getRuntimeDir,
  getRuntimePythonExe,
  getWorkspaceDir,
  getRendersDir,
  getModelCacheDir,
  getEnrichedPath
} = require('./path-resolver');
const {
  findBasePython,
  resolveActivePython,
  getRuntimeStatus,
  provisionRuntime,
  testFFmpeg
} = require('./runtime-manager');

let activeChildProcess = null;

function registerIpcHandlers(ipcMain, mainWindow) {
  const userDataDir = getUserDataDir();
  const settingsFile = path.join(userDataDir, 'settings.json');

  // 1. Hardware Info
  ipcMain.handle('system:get-hardware', async () => {
    const cpus = os.cpus();
    const cpuModel = cpus && cpus.length > 0 ? cpus[0].model.trim() : 'Unknown CPU';
    const cpuCores = cpus ? cpus.length : 1;
    const totalMemGB = Math.round((os.totalmem() / (1024 ** 3)) * 10) / 10;
    const freeMemGB = Math.round((os.freemem() / (1024 ** 3)) * 10) / 10;
    const platform = `${os.type()} ${os.release()} (${os.arch()})`;

    // Run powershell query for GPU and Disks
    const details = await new Promise((resolve) => {
      const psCmd = `powershell -NoProfile -Command "
        $gpu = (Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join ', ';
        $drives = Get-PSDrive -PSProvider FileSystem | ForEach-Object { @{ Name = $_.Name; FreeGB = [math]::Round($_.Free / 1GB, 1); UsedGB = [math]::Round($_.Used / 1GB, 1) } } | ConvertTo-Json -Compress;
        Write-Output ('GPU:::' + $gpu);
        Write-Output ('DRIVES:::' + $drives);
      "`;

      exec(psCmd, { timeout: 6000 }, (err, stdout) => {
        let gpu = 'Integrated Graphics';
        let drives = [];
        if (!err && stdout) {
          const lines = stdout.split('\n');
          for (const line of lines) {
            if (line.startsWith('GPU:::')) {
              gpu = line.replace('GPU:::', '').trim();
            } else if (line.startsWith('DRIVES:::')) {
              try {
                const parsed = JSON.parse(line.replace('DRIVES:::', '').trim());
                drives = Array.isArray(parsed) ? parsed : [parsed];
              } catch (e) {}
            }
          }
        }
        resolve({ gpu, drives });
      });
    });

    return {
      cpu: cpuModel,
      cores: cpuCores,
      totalRamGB: totalMemGB,
      freeRamGB: freeMemGB,
      gpu: details.gpu || 'Integrated Graphics',
      platform,
      drives: details.drives || []
    };
  });

  // 2. Python Runtime Status & Provisioning
  ipcMain.handle('runtime:get-status', async (event, forceRefresh) => {
    return await getRuntimeStatus(forceRefresh);
  });

  ipcMain.handle('runtime:provision', async () => {
    return await provisionRuntime((progress) => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('runtime:progress', progress);
      }
    });
  });

  // 3. Model & Runtime Status
  ipcMain.handle('models:get-status', async () => {
    const runtimeStatus = await getRuntimeStatus();
    const cacheD = getModelCacheDir();
    const cacheHubD = path.join(cacheD, 'hub');
    const cacheUser = path.join(process.env.USERPROFILE || '', '.cache', 'huggingface', 'hub');

    const checkDirExists = (pattern) => {
      const pathsToCheck = [cacheD, cacheHubD, cacheUser];
      for (const dir of pathsToCheck) {
        if (fs.existsSync(dir)) {
          try {
            const files = fs.readdirSync(dir);
            if (files.some(f => f.toLowerCase().includes(pattern.toLowerCase()))) return true;
          } catch (e) {}
        }
      }
      return false;
    };

    const userKokoro = path.join(process.env.USERPROFILE || '', '.faceless-shorts', 'kokoro', 'kokoro-v1.0.onnx');
    const appKokoro = path.join(userDataDir, 'models', 'kokoro', 'kokoro-v1.0.onnx');
    const localKokoro = path.join(getBackendDir(), 'models', 'kokoro', 'kokoro-v1.0.onnx');
    const hasKokoro = fs.existsSync(userKokoro) || fs.existsSync(appKokoro) || fs.existsSync(localKokoro);

    const hasSdTurbo = checkDirExists('sd-turbo');
    const hasDepthAnything = checkDirExists('depth-anything');
    const hasWhisper = checkDirExists('whisper') || fs.existsSync(path.join(cacheHubD, 'models--Systran--faster-whisper-small.en'));
    const hasQwen = checkDirExists('qwen2.5-0.5b') || checkDirExists('qwen');

    const allModelsReady = hasKokoro && hasSdTurbo && hasDepthAnything && hasWhisper;

    return {
      runtime: runtimeStatus,
      python: {
        installed: runtimeStatus.ready,
        path: runtimeStatus.pythonPath,
        isManaged: runtimeStatus.isManaged
      },
      kokoro: {
        name: 'Kokoro-82M TTS',
        installed: hasKokoro,
        type: 'Voice Synthesis (ONNX)',
        size: '~320 MB',
        path: userKokoro
      },
      sdTurbo: {
        name: 'SD-Turbo',
        installed: hasSdTurbo,
        type: 'Photorealistic Visual Generator',
        size: '~2.1 GB',
        location: cacheD
      },
      depthAnything: {
        name: 'Depth-Anything V2',
        installed: hasDepthAnything,
        type: '2.5D Volumetric Parallax',
        size: '~380 MB',
        location: cacheD
      },
      whisper: {
        name: 'Faster-Whisper (Base.en)',
        installed: hasWhisper,
        type: 'Word-Level Subtitle Alignment',
        size: '~140 MB',
        location: cacheD
      },
      qwen: {
        name: 'Qwen2.5-0.5B-Instruct',
        installed: hasQwen,
        type: 'Local Script & Scene Planner',
        size: '~600 MB',
        location: cacheD
      },
      allReady: allModelsReady && runtimeStatus.ready
    };
  });

  // 4. Settings
  ipcMain.handle('settings:get', async () => {
    const defaults = {
      outputDir: getRendersDir(),
      defaultDuration: 30,
      defaultAspectRatio: '9:16',
      defaultResolution: '1080p',
      defaultVoice: 'bm_george',
      defaultStyle: 'cinematic-documentary',
      cacheDir: getModelCacheDir()
    };

    if (fs.existsSync(settingsFile)) {
      try {
        const raw = fs.readFileSync(settingsFile, 'utf-8');
        return { ...defaults, ...JSON.parse(raw) };
      } catch (e) {
        return defaults;
      }
    }
    return defaults;
  });

  ipcMain.handle('settings:save', async (event, settings) => {
    try {
      fs.writeFileSync(settingsFile, JSON.stringify(settings, null, 2), 'utf-8');
      return true;
    } catch (e) {
      return false;
    }
  });

  // 5. Folder selection dialog
  ipcMain.handle('dialog:select-directory', async (event, defaultPath) => {
    const result = await dialog.showOpenDialog(mainWindow, {
      title: 'Select Output Directory',
      defaultPath: defaultPath || getRendersDir(),
      properties: ['openDirectory', 'createDirectory']
    });
    if (!result.canceled && result.filePaths.length > 0) {
      return result.filePaths[0];
    }
    return null;
  });

  // 6. Video Generation
  ipcMain.handle('video:generate', async (event, options) => {
    if (activeChildProcess) {
      return { success: false, error: 'A video generation task is already running.' };
    }

    const runtimeStatus = await getRuntimeStatus();
    if (!runtimeStatus.ready || !runtimeStatus.pythonPath) {
      return {
        success: false,
        error: 'Local AI Python Runtime is not configured. Please open Settings -> Python Runtime Setup to initialize.'
      };
    }

    const pythonExe = runtimeStatus.pythonPath;
    const scriptPath = getScriptPath('prompt2video.py');
    const backendDir = getBackendDir();
    const userData = getUserDataDir();
    const rendersDir = options.outputDir || getRendersDir();
    const modelCache = getModelCacheDir();

    const duration = options.duration || 30;
    const aspectRatio = options.aspectRatio || '9:16';
    const resolution = options.resolution || '1080p';
    const voice = options.voice || 'bm_george';
    const style = options.style || 'cinematic-documentary';

    const args = [
      scriptPath,
      '--prompt', options.prompt,
      '--duration', String(duration),
      '--aspect-ratio', aspectRatio,
      '--resolution', resolution,
      '--voice', voice,
      '--style', style,
      '--output', rendersDir,
      '--ipc-json'
    ];

    return new Promise((resolve) => {
      let finalResult = null;
      let lastErrorMessage = '';

      const env = {
        ...process.env,
        PATH: getEnrichedPath(),
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        P2V_PYTHON_EXE: pythonExe,
        P2V_BACKEND_DIR: backendDir,
        P2V_USER_DATA: userData,
        HF_HOME: modelCache,
        TORCH_HOME: path.join(modelCache, 'torch'),
        TRANSFORMERS_CACHE: modelCache
      };

      activeChildProcess = spawn(pythonExe, args, {
        cwd: userData,
        env,
        windowsHide: true
      });

      activeChildProcess.stdout.on('data', (chunk) => {
        const text = chunk.toString('utf-8');
        const lines = text.split(/\r?\n/);
        for (const line of lines) {
          if (!line.trim()) continue;
          if (line.includes('__P2V_EVENT__')) {
            try {
              const rawJson = line.substring(line.indexOf('__P2V_EVENT__') + '__P2V_EVENT__'.length).replace(/^:/, '');
              const eventData = JSON.parse(rawJson);
              if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send('video:progress', eventData);
              }
              if (eventData.type === 'complete' || eventData.event === 'done') {
                finalResult = eventData;
              } else if (eventData.type === 'error' || eventData.event === 'error') {
                lastErrorMessage = eventData.message || 'Generation error occurred.';
              }
            } catch (err) {
              console.error('Failed to parse IPC event:', err);
            }
          } else {
            if (mainWindow && !mainWindow.isDestroyed()) {
              mainWindow.webContents.send('video:log', line);
            }
          }
        }
      });

      activeChildProcess.stderr.on('data', (chunk) => {
        const text = chunk.toString('utf-8');
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('video:log', text);
        }
      });

      activeChildProcess.on('close', (code) => {
        activeChildProcess = null;
        if (code === 0 && finalResult) {
          resolve({ success: true, ...finalResult });
        } else if (code === 0) {
          resolve({ success: true, message: 'Video generation completed.' });
        } else {
          resolve({
            success: false,
            error: lastErrorMessage || `Process exited with code ${code}. Check logs for details.`
          });
        }
      });

      activeChildProcess.on('error', (err) => {
        activeChildProcess = null;
        resolve({ success: false, error: err.message });
      });
    });
  });

  // 7. Cancel Generation
  ipcMain.handle('video:cancel', async () => {
    if (!activeChildProcess) return false;
    const pid = activeChildProcess.pid;
    try {
      if (process.platform === 'win32') {
        exec(`taskkill /PID ${pid} /T /F`);
      } else {
        activeChildProcess.kill('SIGINT');
      }
      activeChildProcess = null;
      return true;
    } catch (e) {
      activeChildProcess = null;
      return false;
    }
  });

  // 8. Video Library
  ipcMain.handle('library:get-videos', async (event, customDir) => {
    const rendersDir = customDir || getRendersDir();
    if (!fs.existsSync(rendersDir)) return [];

    const items = [];
    const scanDir = (dir, depth = 0) => {
      if (depth > 2) return;
      try {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);
          if (entry.isDirectory()) {
            scanDir(fullPath, depth + 1);
          } else if (entry.isFile() && entry.name.toLowerCase().endsWith('.mp4')) {
            const stats = fs.statSync(fullPath);
            const sizeMB = Math.round((stats.size / (1024 * 1024)) * 10) / 10;
            
            // Check for contact sheet / thumbnail image
            let thumbnail = null;
            const parentDir = path.dirname(fullPath);
            const possibleThumbnails = [
              path.join(parentDir, 'contact_sheet.jpg'),
              path.join(parentDir, 'contact_sheet.png'),
              path.join(parentDir, `${path.basename(entry.name, '.mp4')}-contact.jpg`),
              path.join(parentDir, 'scene_01.png'),
              path.join(parentDir, 'scene_01.jpg')
            ];
            for (const t of possibleThumbnails) {
              if (fs.existsSync(t)) {
                thumbnail = t;
                break;
              }
            }

            items.push({
              name: entry.name,
              path: fullPath,
              dir: parentDir,
              sizeMB,
              createdAt: stats.birthtime || stats.mtime,
              thumbnail
            });
          }
        }
      } catch (e) {}
    };

    scanDir(rendersDir);
    items.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    return items;
  });

  // 9. Open file / folder
  ipcMain.handle('library:open-folder', async (event, filePath) => {
    if (filePath && fs.existsSync(filePath)) {
      shell.showItemInFolder(filePath);
      return true;
    }
    return false;
  });

  ipcMain.handle('library:open-path', async (event, folderPath) => {
    if (folderPath && fs.existsSync(folderPath)) {
      shell.openPath(folderPath);
      return true;
    }
    return false;
  });

  ipcMain.handle('library:delete-video', async (event, filePath) => {
    if (filePath && fs.existsSync(filePath)) {
      try {
        fs.unlinkSync(filePath);
        return true;
      } catch (e) {
        return false;
      }
    }
    return false;
  });
}

module.exports = { registerIpcHandlers };
