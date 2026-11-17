const { dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');
const { spawn, exec } = require('child_process');

let activeChildProcess = null;

function findPythonExe() {
  const candidates = [
    path.join(process.env.USERPROFILE || '', '.faceless-shorts', 'venv', 'Scripts', 'python.exe'),
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python311', 'python.exe'),
    path.join(process.env.USERPROFILE || '', 'AppData', 'Local', 'Programs', 'Python', 'Python311', 'python.exe'),
    'python.exe',
    'python'
  ];

  for (const p of candidates) {
    if (p.includes('\\') || p.includes('/')) {
      if (fs.existsSync(p)) return p;
    } else {
      return p;
    }
  }
  return 'python';
}

function findFFmpegExe() {
  // Check if ffmpeg is accessible
  return 'ffmpeg';
}

function registerIpcHandlers(ipcMain, mainWindow) {
  const projectRoot = path.resolve(__dirname, '..');
  const userDataDir = path.join(process.env.APPDATA || process.env.USERPROFILE || '', 'Prompt2VideoAI');
  if (!fs.existsSync(userDataDir)) {
    try { fs.mkdirSync(userDataDir, { recursive: true }); } catch (e) {}
  }
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

  // 2. Model Status
  ipcMain.handle('models:get-status', async () => {
    const modelsDir = path.join(projectRoot, 'models');
    const kokoroDir = path.join(modelsDir, 'kokoro');
    const userKokoro = path.join(process.env.USERPROFILE || '', '.faceless-shorts', 'kokoro', 'kokoro-v1.0.onnx');
    const kokoroOnnx = path.join(kokoroDir, 'kokoro-v0_19.onnx');

    const cacheD = 'D:\\faceless-shorts-ai\\cache';
    const cacheHubD = 'D:\\faceless-shorts-ai\\cache\\hub';
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

    const hasKokoro = fs.existsSync(userKokoro) || fs.existsSync(kokoroOnnx);
    const hasSdTurbo = checkDirExists('sd-turbo');
    const hasDepthAnything = checkDirExists('depth-anything');
    const hasWhisper = checkDirExists('whisper') || fs.existsSync(path.join(cacheHubD, 'models--Systran--faster-whisper-small.en'));
    const hasQwen = checkDirExists('qwen2.5-0.5b') || checkDirExists('qwen');

    const pythonPath = findPythonExe();
    const hasPython = fs.existsSync(pythonPath);

    return {
      python: { installed: hasPython, path: pythonPath },
      kokoro: {
        name: 'Kokoro-82M TTS',
        installed: hasKokoro,
        type: 'Voice Synthesis (ONNX)',
        size: '~320 MB',
        path: kokoroOnnx
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
      allReady: hasKokoro && hasSdTurbo && hasDepthAnything && hasWhisper
    };
  });

  // 3. Settings
  ipcMain.handle('settings:get', async () => {
    const defaults = {
      outputDir: path.join(projectRoot, 'renders'),
      defaultDuration: 30,
      defaultAspectRatio: '9:16',
      defaultResolution: '1080p',
      defaultVoice: 'bm_george',
      defaultStyle: 'cinematic-documentary',
      cacheDir: fs.existsSync('D:\\faceless-shorts-ai\\cache') ? 'D:\\faceless-shorts-ai\\cache' : path.join(projectRoot, 'cache')
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

  // 4. Folder selection dialog
  ipcMain.handle('dialog:select-directory', async (event, defaultPath) => {
    const result = await dialog.showOpenDialog(mainWindow, {
      title: 'Select Output Directory',
      defaultPath: defaultPath || projectRoot,
      properties: ['openDirectory', 'createDirectory']
    });
    if (!result.canceled && result.filePaths.length > 0) {
      return result.filePaths[0];
    }
    return null;
  });

  // 5. Video Generation
  ipcMain.handle('video:generate', async (event, options) => {
    if (activeChildProcess) {
      return { success: false, error: 'A video generation task is already running.' };
    }

    const pythonExe = findPythonExe();
    const scriptPath = path.join(projectRoot, 'scripts', 'prompt2video.py');

    const duration = options.duration || 30;
    const aspectRatio = options.aspectRatio || '9:16';
    const resolution = options.resolution || '1080p';
    const voice = options.voice || 'bm_george';
    const style = options.style || 'cinematic-documentary';
    const outputDir = options.outputDir || path.join(projectRoot, 'renders');

    const args = [
      scriptPath,
      '--prompt', options.prompt,
      '--duration', String(duration),
      '--aspect-ratio', aspectRatio,
      '--resolution', resolution,
      '--voice', voice,
      '--style', style,
      '--output-dir', outputDir,
      '--ipc-json'
    ];

    if (options.title) {
      args.push('--title', options.title);
    }

    return new Promise((resolve) => {
      let finalResult = null;
      let lastErrorMessage = '';

      const env = {
        ...process.env,
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
        HF_HOME: 'D:\\faceless-shorts-ai\\cache'
      };

      activeChildProcess = spawn(pythonExe, args, {
        cwd: projectRoot,
        env,
        windowsHide: true
      });

      activeChildProcess.stdout.on('data', (chunk) => {
        const text = chunk.toString('utf-8');
        const lines = text.split(/\r?\n/);
        for (const line of lines) {
          if (!line.trim()) continue;
          if (line.startsWith('__P2V_EVENT__:')) {
            try {
              const eventData = JSON.parse(line.substring('__P2V_EVENT__:'.length));
              mainWindow.webContents.send('video:progress', eventData);
              if (eventData.type === 'complete') {
                finalResult = eventData;
              } else if (eventData.type === 'error') {
                lastErrorMessage = eventData.message || 'Generation error occurred.';
              }
            } catch (err) {
              console.error('Failed to parse IPC event:', err);
            }
          } else {
            mainWindow.webContents.send('video:log', line);
          }
        }
      });

      activeChildProcess.stderr.on('data', (chunk) => {
        const text = chunk.toString('utf-8');
        mainWindow.webContents.send('video:log', text);
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

  // 6. Cancel Generation
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

  // 7. Video Library
  ipcMain.handle('library:get-videos', async (event, customDir) => {
    const rendersDir = customDir || path.join(projectRoot, 'renders');
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

  // 8. Open file / folder
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
