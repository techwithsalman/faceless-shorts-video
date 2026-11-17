const path = require('path');
const fs = require('fs');
const os = require('os');
const { exec, spawn, execFile } = require('child_process');
const {
  getRuntimeDir,
  getRuntimePythonExe,
  getEnrichedPath,
  getBackendDir
} = require('./path-resolver');

let cachedRuntimeStatus = null;

/**
 * Searches the Windows machine for base Python 3.10+ installations.
 */
async function findBasePython() {
  const localAppData = process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local');
  const userProfile = process.env.USERPROFILE || os.homedir();

  const candidates = [
    // Standard Windows Python installations
    path.join(localAppData, 'Programs', 'Python', 'Python311', 'python.exe'),
    path.join(localAppData, 'Programs', 'Python', 'Python312', 'python.exe'),
    path.join(localAppData, 'Programs', 'Python', 'Python310', 'python.exe'),
    'C:\\Program Files\\Python311\\python.exe',
    'C:\\Program Files\\Python312\\python.exe',
    'C:\\Program Files\\Python310\\python.exe',
    // Existing developer venv if present on dev machine
    path.join(userProfile, '.faceless-shorts', 'venv', 'Scripts', 'python.exe')
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      const ok = await testPythonExe(candidate);
      if (ok) return candidate;
    }
  }

  // Check PATH via where.exe
  const pathPy = await new Promise((resolve) => {
    exec('where.exe python', { env: { ...process.env, PATH: getEnrichedPath() }, timeout: 4000 }, (err, stdout) => {
      if (!err && stdout) {
        const lines = stdout.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
        for (const line of lines) {
          // Avoid the Windows Store placeholder shim (0-byte or redirects to store)
          if (!line.toLowerCase().includes('windowsapps')) {
            return resolve(line);
          }
        }
      }
      resolve(null);
    });
  });

  if (pathPy && fs.existsSync(pathPy)) {
    const ok = await testPythonExe(pathPy);
    if (ok) return pathPy;
  }

  // Check py.exe Windows launcher
  const pyLauncher = 'C:\\Windows\\py.exe';
  if (fs.existsSync(pyLauncher)) {
    const ok = await testPythonExe(`${pyLauncher} -3.11`);
    if (ok) return `${pyLauncher} -3.11`;
  }

  return null;
}

/**
 * Executes a basic Python smoke test.
 */
function testPythonExe(exeCmd) {
  return new Promise((resolve) => {
    if (fs.existsSync(exeCmd)) {
      execFile(exeCmd, ['-c', 'import sys; print(sys.version_info[0:2])'], { timeout: 5000 }, (err, stdout) => {
        if (!err && stdout && stdout.includes('3,')) {
          resolve(true);
        } else {
          resolve(false);
        }
      });
    } else {
      exec(`"${exeCmd}" -c "import sys; print(sys.version_info[0:2])"`, { timeout: 5000 }, (err, stdout) => {
        if (!err && stdout && stdout.includes('3,')) {
          resolve(true);
        } else {
          resolve(false);
        }
      });
    }
  });
}

/**
 * Verifies that the required neural inference dependencies are importable.
 */
function testDependencies(pythonExe) {
  return new Promise((resolve) => {
    const code = 'import torch, diffusers, kokoro_onnx, faster_whisper, transformers; print("DEPS_OK")';
    execFile(pythonExe, ['-c', code], {
      env: { ...process.env, PATH: getEnrichedPath() },
      timeout: 20000
    }, (err, stdout) => {
      if (!err && stdout && stdout.includes('DEPS_OK')) {
        resolve(true);
      } else {
        resolve(false);
      }
    });
  });
}

/**
 * Checks if FFmpeg is available and executable.
 */
function testFFmpeg() {
  return new Promise((resolve) => {
    exec('ffmpeg -version', {
      env: { ...process.env, PATH: getEnrichedPath() },
      timeout: 4000
    }, (err, stdout) => {
      if (!err && stdout && stdout.includes('ffmpeg version')) {
        resolve(true);
      } else {
        resolve(false);
      }
    });
  });
}

/**
 * Resolves the active, verified Python executable for Prompt2Video AI.
 * Priority:
 * 1. Application-managed runtime: %LOCALAPPDATA%\Prompt2VideoAI\runtime\Scripts\python.exe
 * 2. Pre-existing configured venv: %USERPROFILE%\.faceless-shorts\venv\Scripts\python.exe
 */
async function resolveActivePython() {
  const managedPython = getRuntimePythonExe();
  if (fs.existsSync(managedPython)) {
    const depsOk = await testDependencies(managedPython);
    if (depsOk) {
      return { executable: managedPython, isManaged: true, ready: true };
    }
  }

  // Check fallback dev venv
  const devVenv = path.join(process.env.USERPROFILE || '', '.faceless-shorts', 'venv', 'Scripts', 'python.exe');
  if (fs.existsSync(devVenv)) {
    const depsOk = await testDependencies(devVenv);
    if (depsOk) {
      return { executable: devVenv, isManaged: false, ready: true };
    }
  }

  return { executable: null, isManaged: false, ready: false };
}

/**
 * Returns comprehensive runtime and dependency health status.
 */
async function getRuntimeStatus(forceRefresh = false) {
  if (cachedRuntimeStatus && !forceRefresh) {
    return cachedRuntimeStatus;
  }

  const active = await resolveActivePython();
  const ffmpegOk = await testFFmpeg();
  const basePy = active.ready ? active.executable : await findBasePython();

  cachedRuntimeStatus = {
    ready: active.ready && ffmpegOk,
    pythonPath: active.executable,
    isManaged: active.isManaged,
    runtimeDir: getRuntimeDir(),
    ffmpegAvailable: ffmpegOk,
    basePythonFound: !!basePy,
    basePythonPath: basePy
  };

  return cachedRuntimeStatus;
}

/**
 * Provisions or repairs the isolated application runtime at %LOCALAPPDATA%\Prompt2VideoAI\runtime\.
 */
async function provisionRuntime(progressCallback = () => {}) {
  const runtimeDir = getRuntimeDir();
  const runtimePython = getRuntimePythonExe();

  progressCallback({ stage: 'search', percent: 10, message: 'Searching for Python 3.10+ installation...' });

  const basePython = await findBasePython();
  if (!basePython) {
    throw new Error(
      'Python 3.10 or 3.11 was not found on this computer. Please install Python from https://www.python.org or run "winget install Python.Python.3.11" in PowerShell.'
    );
  }

  progressCallback({ stage: 'venv', percent: 25, message: `Creating isolated runtime at ${runtimeDir}...` });

  // 1. Create venv if missing
  if (!fs.existsSync(runtimePython)) {
    await new Promise((resolve, reject) => {
      exec(`"${basePython}" -m venv "${runtimeDir}"`, { timeout: 30000 }, (err, stdout, stderr) => {
        if (err) return reject(new Error(`Failed to create virtual environment: ${stderr || err.message}`));
        resolve();
      });
    });
  }

  // 2. Fast-path: Check if developer venv has packages to share via .pth
  const devSitePackages = path.join(process.env.USERPROFILE || '', '.faceless-shorts', 'venv', 'Lib', 'site-packages');
  const targetSitePackages = path.join(runtimeDir, 'Lib', 'site-packages');

  if (fs.existsSync(devSitePackages) && fs.existsSync(targetSitePackages)) {
    progressCallback({ stage: 'linking', percent: 50, message: 'Configuring pre-installed neural packages...' });
    const pthFile = path.join(targetSitePackages, 'dev_packages.pth');
    try {
      fs.writeFileSync(pthFile, `${devSitePackages}\n`, 'ascii');
    } catch (e) {}
  }

  // 3. Verify packages or install from requirements.txt
  progressCallback({ stage: 'verify_deps', percent: 70, message: 'Verifying PyTorch, Kokoro, Whisper, and SD-Turbo imports...' });
  let depsOk = await testDependencies(runtimePython);

  if (!depsOk) {
    progressCallback({ stage: 'pip_install', percent: 75, message: 'Installing required neural dependencies (this may take a few minutes)...' });
    const reqPath = path.join(getBackendDir(), 'requirements.txt');
    if (fs.existsSync(reqPath)) {
      await new Promise((resolve, reject) => {
        const proc = spawn(runtimePython, ['-m', 'pip', 'install', '-r', reqPath], {
          env: { ...process.env, PATH: getEnrichedPath() }
        });
        proc.on('close', (code) => {
          if (code === 0) resolve();
          else reject(new Error(`pip install exited with code ${code}`));
        });
      });
    }
    depsOk = await testDependencies(runtimePython);
  }

  if (!depsOk) {
    throw new Error('Installed packages could not be verified. Please check network connection or system requirements.');
  }

  progressCallback({ stage: 'complete', percent: 100, message: 'Local AI Python Runtime verified and ready!' });
  cachedRuntimeStatus = null;
  return await getRuntimeStatus(true);
}

module.exports = {
  findBasePython,
  resolveActivePython,
  getRuntimeStatus,
  provisionRuntime,
  testFFmpeg
};
