const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow = null;
let pythonProcess = null;
const BACKEND_PORT = 8765;

function findPythonExecutable() {
  const candidates = [
    'C:\\Users\\HP\\.faceless-shorts\\venv\\Scripts\\python.exe',
    path.join(os.homedir(), '.faceless-shorts', 'venv', 'Scripts', 'python.exe'),
    path.join(process.resourcesPath, 'python', 'python.exe'),
    path.join(process.resourcesPath, 'venv', 'Scripts', 'python.exe'),
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python311', 'python.exe'),
    path.join(process.env.ProgramFiles || '', 'Python311', 'python.exe'),
    path.join(__dirname, '..', '..', '.faceless-shorts', 'venv', 'Scripts', 'python.exe'),
    'python.exe',
    'python'
  ];

  for (const c of candidates) {
    if (c && fs.existsSync(c)) {
      return c;
    }
  }
  return 'python';
}

function findServerScript() {
  const candidates = app.isPackaged
    ? [
        path.join(process.resourcesPath, 'scripts', 'clipper_server.py'),
        path.join(__dirname, 'scripts', 'clipper_server.py'),
        path.join(__dirname, '..', 'scripts', 'clipper_server.py')
      ]
    : [
        path.join(__dirname, '..', 'scripts', 'clipper_server.py'),
        path.join(process.resourcesPath, 'scripts', 'clipper_server.py'),
        path.join(__dirname, 'scripts', 'clipper_server.py')
      ];

  for (const c of candidates) {
    if (fs.existsSync(c)) {
      return c;
    }
  }
  return app.isPackaged
    ? path.join(process.resourcesPath, 'scripts', 'clipper_server.py')
    : path.join(__dirname, '..', 'scripts', 'clipper_server.py');
}

function checkBackendHealth(port, callback) {
  const req = http.get(`http://127.0.0.1:${port}/api/status`, (res) => {
    if (res.statusCode === 200) {
      callback(true);
    } else {
      callback(false);
    }
  });
  req.on('error', () => callback(false));
  req.setTimeout(1000, () => {
    req.destroy();
    callback(false);
  });
}

function startPythonBackend() {
  checkBackendHealth(BACKEND_PORT, (isRunning) => {
    if (isRunning) {
      console.log(`[MAIN] Python backend is already running on port ${BACKEND_PORT}`);
      return;
    }

    const pythonExe = findPythonExecutable();
    const serverScript = findServerScript();
    const projectRoot = app.isPackaged ? process.resourcesPath : path.resolve(__dirname, '..');

    console.log(`[MAIN] Launching Python backend: ${pythonExe} ${serverScript} ${BACKEND_PORT}`);

    const envVars = { ...process.env, PYTHONUNBUFFERED: '1' };
    if (process.env.PORTABLE_EXECUTABLE_DIR && !envVars.CLIPPER_OUTPUT_DIR) {
      envVars.CLIPPER_OUTPUT_DIR = path.join(process.env.PORTABLE_EXECUTABLE_DIR, 'AI-Video-Clips');
    }

    try {
      pythonProcess = spawn(pythonExe, [serverScript, String(BACKEND_PORT)], {
        cwd: projectRoot,
        env: envVars,
        windowsHide: true
      });

      pythonProcess.stdout.on('data', (data) => {
        const str = data.toString();
        if (str.includes('[JOB-LOG]') || str.includes('BATCH') || str.includes('ERROR')) {
          console.log(`[BACKEND STDOUT] ${str.trim()}`);
        }
      });

      pythonProcess.stderr.on('data', (data) => {
        console.error(`[BACKEND STDERR] ${data.toString().trim()}`);
      });

      pythonProcess.on('exit', (code) => {
        console.log(`[MAIN] Python backend exited with code ${code}`);
        pythonProcess = null;
      });
    } catch (err) {
      console.error('[MAIN] Failed to spawn Python backend:', err);
    }
  });
}

function stopPythonBackend() {
  if (pythonProcess) {
    console.log('[MAIN] Terminating Python backend...');
    try {
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', pythonProcess.pid, '/f', '/t']);
      } else {
        pythonProcess.kill('SIGINT');
      }
    } catch (e) {
      console.error('[MAIN] Error terminating python process:', e);
    }
    pythonProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 880,
    minWidth: 1080,
    minHeight: 700,
    backgroundColor: '#0c0e12',
    icon: path.join(__dirname, 'assets', 'icon.png'),
    title: 'AI Long Video Clipper — Beyond History Studio',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false
    }
  });

  mainWindow.setMenuBarVisibility(false);

  mainWindow.loadFile(path.join(__dirname, 'src', 'index.html'));

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC Handlers
ipcMain.handle('select-video-files', async () => {
  if (!mainWindow) return [];
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Select Video Files for AI Long Video Clipper',
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'Video Files', extensions: ['mp4', 'mov', 'mkv', 'avi', 'webm'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  });
  if (result.canceled) return [];
  return result.filePaths;
});

ipcMain.handle('select-directory', async () => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Select Model / Cache Directory',
    properties: ['openDirectory', 'createDirectory']
  });
  if (result.canceled || !result.filePaths.length) return null;
  return result.filePaths[0];
});

ipcMain.handle('open-folder', async (event, folderPath) => {
  try {
    if (!folderPath) {
      if (process.env.PORTABLE_EXECUTABLE_DIR) {
        folderPath = path.join(process.env.PORTABLE_EXECUTABLE_DIR, 'AI-Video-Clips');
      } else {
        folderPath = path.join(__dirname, '..', 'AI-Video-Clips');
      }
    }
    if (fs.existsSync(folderPath)) {
      await shell.openPath(folderPath);
      return { success: true };
    }
    return { success: false, error: 'Path does not exist' };
  } catch (err) {
    return { success: false, error: err.message };
  }
});

ipcMain.handle('get-system-info', async () => {
  const cpus = os.cpus();
  return {
    platform: os.platform(),
    arch: os.arch(),
    cpuModel: cpus.length ? cpus[0].model : 'Multi-core CPU',
    cpuThreads: cpus.length,
    totalMemGb: (os.totalmem() / (1024 ** 3)).toFixed(1),
    freeMemGb: (os.freemem() / (1024 ** 3)).toFixed(1)
  };
});

ipcMain.handle('get-backend-port', () => BACKEND_PORT);
ipcMain.handle('minimize-window', () => mainWindow && mainWindow.minimize());
ipcMain.handle('maximize-window', () => {
  if (!mainWindow) return;
  if (mainWindow.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow.maximize();
  }
});
ipcMain.handle('close-window', () => mainWindow && mainWindow.close());

app.whenReady().then(() => {
  startPythonBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  stopPythonBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  stopPythonBackend();
});
