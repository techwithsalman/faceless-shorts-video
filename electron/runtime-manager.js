const path = require('path');
const fs = require('fs');
const os = require('os');
const { exec, spawn, execFile } = require('child_process');
const {
  getRuntimeDir,
  getRuntimePythonExe,
  getEnrichedPath,
  getBackendDir,
  getBinDir,
  getScriptPath
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
      if (ok) return { executable: candidate, args: [] };
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
    if (ok) return { executable: pathPy, args: [] };
  }

  // Check py.exe Windows launcher
  const pyLauncher = 'C:\\Windows\\py.exe';
  if (fs.existsSync(pyLauncher)) {
    for (const v of ['-3.11', '-3.12', '-3.10', '-3']) {
      const ok = await testPythonExe(pyLauncher, [v]);
      if (ok) return { executable: pyLauncher, args: [v] };
    }
  }

  return null;
}

/**
 * Executes a basic Python smoke test.
 */
function testPythonExe(exeCmd, extraArgs = []) {
  return new Promise((resolve) => {
    const args = [...extraArgs, '-c', 'import sys; print(sys.version_info[0:2])'];
    if (fs.existsSync(exeCmd)) {
      execFile(exeCmd, args, { timeout: 8000 }, (err, stdout) => {
        if (!err && stdout && stdout.includes('3,')) {
          resolve(true);
        } else {
          resolve(false);
        }
      });
    } else {
      const fullCmd = extraArgs.length > 0 ? `"${exeCmd}" ${extraArgs.join(' ')}` : `"${exeCmd}"`;
      exec(`${fullCmd} -c "import sys; print(sys.version_info[0:2])"`, { timeout: 8000 }, (err, stdout) => {
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
 * Checks if the runtime already has a valid .verified.json marker.
 */
function checkVerifiedMarker(pythonExe) {
  const runtimeDir = getRuntimeDir();
  const markerPath = path.join(runtimeDir, '.verified.json');
  if (!fs.existsSync(markerPath)) return null;

  try {
    const raw = fs.readFileSync(markerPath, 'utf-8');
    const data = JSON.parse(raw);
    if (data.all_ready === true && data.python_exe && fs.existsSync(data.python_exe)) {
      return data;
    }
  } catch (e) {}
  return null;
}

/**
 * Verifies that the required neural inference dependencies are importable using verify_environment.py.
 */
function verifyDependencies(pythonExe, progressCallback = () => {}) {
  return new Promise((resolve) => {
    const verifyScript = getScriptPath('verify_environment.py');
    const proc = spawn(pythonExe, [verifyScript], {
      env: { ...process.env, PATH: getEnrichedPath() }
    });

    let stdoutBuffer = '';
    let stderrBuffer = '';
    let completedMarker = null;

    proc.stdout.on('data', (chunk) => {
      const text = chunk.toString('utf-8');
      stdoutBuffer += text;
      const lines = text.split(/\r?\n/);
      for (const line of lines) {
        if (line.includes('__P2V_VERIFY__')) {
          try {
            const jsonPart = line.substring(line.indexOf('__P2V_VERIFY__') + '__P2V_VERIFY__'.length);
            const data = JSON.parse(jsonPart);
            if (data.percent !== undefined) {
              progressCallback({
                stage: data.stage || 'verify',
                percent: data.percent,
                message: data.message || 'Verifying neural dependencies...'
              });
            }
            if (data.marker) {
              completedMarker = data.marker;
            }
          } catch (e) {}
        }
      }
    });

    proc.stderr.on('data', (chunk) => {
      stderrBuffer += chunk.toString('utf-8');
    });

    proc.on('close', (code) => {
      if (code === 0) {
        resolve({ ok: true, marker: completedMarker, stdout: stdoutBuffer });
      } else {
        resolve({ ok: false, error: stderrBuffer || stdoutBuffer || `Verifier exited with code ${code}` });
      }
    });

    proc.on('error', (err) => {
      resolve({ ok: false, error: err.message });
    });
  });
}

/**
 * Searches for FFmpeg across all standard Windows locations and tool paths.
 */
function findFFmpegExe() {
  const localAppData = process.env.LOCALAPPDATA || '';
  const wingetPkg = path.join(localAppData, 'Microsoft', 'WinGet', 'Packages');

  const candidates = [
    path.join(getBinDir(), 'ffmpeg.exe'),
    path.join(getRuntimeDir(), 'Scripts', 'ffmpeg.exe'),
    // imageio_ffmpeg bundled binaries
    path.join(getRuntimeDir(), 'Lib', 'site-packages', 'imageio_ffmpeg', 'binaries', 'ffmpeg-win-x86_64-v9.0.2.exe'),
    // WinGet installations
    path.join(wingetPkg, 'Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe', 'ffmpeg-9.0.1-essentials_build', 'bin', 'ffmpeg.exe'),
    path.join(wingetPkg, 'Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe', 'ffmpeg-9.0.1-full_build', 'bin', 'ffmpeg.exe'),
    'C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe'
  ];

  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }

  // Check dynamically inside WinGet Packages
  if (fs.existsSync(wingetPkg)) {
    try {
      const dirs = fs.readdirSync(wingetPkg);
      for (const d of dirs) {
        if (d.toLowerCase().includes('ffmpeg')) {
          const sub = path.join(wingetPkg, d);
          const inner = fs.readdirSync(sub);
          for (const inDir of inner) {
            const exeP = path.join(sub, inDir, 'bin', 'ffmpeg.exe');
            if (fs.existsSync(exeP)) return exeP;
          }
        }
      }
    } catch (e) {}
  }

  return null;
}

/**
 * Configures and verifies local FFmpeg availability.
 */
async function configureFFmpeg(progressCallback = () => {}) {
  const binDir = getBinDir();
  const targetBinExe = path.join(binDir, 'ffmpeg.exe');
  const targetScriptsExe = path.join(getRuntimeDir(), 'Scripts', 'ffmpeg.exe');

  if (fs.existsSync(targetBinExe) && fs.existsSync(targetScriptsExe)) {
    return targetBinExe;
  }

  const existingExe = findFFmpegExe();
  if (existingExe && fs.existsSync(existingExe)) {
    progressCallback({ stage: 'ffmpeg', percent: 45, message: `Configuring local FFmpeg from ${path.basename(existingExe)}...` });
    try {
      if (!fs.existsSync(targetBinExe)) fs.copyFileSync(existingExe, targetBinExe);
      if (!fs.existsSync(targetScriptsExe)) fs.copyFileSync(existingExe, targetScriptsExe);
      return targetBinExe;
    } catch (e) {}
  }

  return existingExe || null;
}

/**
 * Checks if FFmpeg is available and executable.
 */
function testFFmpeg() {
  return new Promise((resolve) => {
    exec('ffmpeg -version', {
      env: { ...process.env, PATH: getEnrichedPath() },
      timeout: 5000
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
 */
async function resolveActivePython() {
  const managedPython = getRuntimePythonExe();
  if (fs.existsSync(managedPython)) {
    // Check marker file for instant resolution
    const marker = checkVerifiedMarker(managedPython);
    if (marker) {
      return { executable: managedPython, isManaged: true, ready: true, marker };
    }

    // Quick verification
    const testOk = await testPythonExe(managedPython);
    if (testOk) {
      return { executable: managedPython, isManaged: true, ready: true };
    }
  }

  // Check fallback dev venv
  const devVenv = path.join(process.env.USERPROFILE || '', '.faceless-shorts', 'venv', 'Scripts', 'python.exe');
  if (fs.existsSync(devVenv)) {
    const testOk = await testPythonExe(devVenv);
    if (testOk) {
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
  const basePyPath = basePy ? (basePy.executable || basePy) : null;

  cachedRuntimeStatus = {
    ready: active.ready && ffmpegOk,
    pythonPath: active.executable,
    isManaged: active.isManaged,
    runtimeDir: getRuntimeDir(),
    ffmpegAvailable: ffmpegOk,
    ffmpegPath: findFFmpegExe(),
    basePythonFound: !!basePyPath,
    basePythonPath: basePyPath,
    marker: active.marker || checkVerifiedMarker(active.executable)
  };

  return cachedRuntimeStatus;
}

/**
 * Provisions or repairs the isolated application runtime at %LOCALAPPDATA%\Prompt2VideoAI\runtime\.
 */
async function provisionRuntime(progressCallback = () => {}) {
  const runtimeDir = getRuntimeDir();
  const runtimePython = getRuntimePythonExe();

  progressCallback({ stage: 'search', percent: 5, message: 'Detecting local Python 3.10+ runtime...' });

  const basePythonObj = await findBasePython();
  if (!basePythonObj) {
    throw new Error(
      'Python 3.10, 3.11, or 3.12 was not found on this computer. Please install Python from https://www.python.org or run "winget install Python.Python.3.11" in PowerShell.'
    );
  }

  const baseExe = basePythonObj.executable;
  const baseArgs = basePythonObj.args || [];

  progressCallback({ stage: 'venv', percent: 15, message: `Creating isolated runtime at ${runtimeDir}...` });

  // 1. Create venv if missing
  if (!fs.existsSync(runtimePython)) {
    await new Promise((resolve, reject) => {
      const venvArgs = [...baseArgs, '-m', 'venv', runtimeDir];
      let errBuf = '';
      const proc = spawn(baseExe, venvArgs);

      proc.stderr.on('data', (c) => { errBuf += c.toString('utf-8'); });
      proc.on('close', (code) => {
        if (code === 0 && fs.existsSync(runtimePython)) {
          resolve();
        } else {
          reject(new Error(`Failed to create virtual environment: ${errBuf || `Exit code ${code}`}`));
        }
      });
      proc.on('error', (err) => reject(new Error(`Failed to spawn base Python: ${err.message}`)));
    });
  }

  // 2. Fast-path: Check if developer venv has packages to share via .pth
  const devSitePackages = path.join(process.env.USERPROFILE || '', '.faceless-shorts', 'venv', 'Lib', 'site-packages');
  const targetSitePackages = path.join(runtimeDir, 'Lib', 'site-packages');

  if (fs.existsSync(devSitePackages) && fs.existsSync(targetSitePackages)) {
    progressCallback({ stage: 'linking', percent: 35, message: 'Configuring pre-installed neural packages...' });
    const pthFile = path.join(targetSitePackages, 'dev_packages.pth');
    try {
      fs.writeFileSync(pthFile, `${devSitePackages}\n`, 'ascii');
    } catch (e) {}
  }

  // 3. Configure local FFmpeg binaries
  progressCallback({ stage: 'ffmpeg', percent: 45, message: 'Configuring audio/video processing engine (FFmpeg)...' });
  await configureFFmpeg(progressCallback);

  // 4. Install / Verify neural packages
  progressCallback({ stage: 'pip_check', percent: 50, message: 'Checking neural packages (PyTorch, Kokoro, Whisper, Diffusers)...' });
  
  // Test dependencies via verify_environment.py
  let verifyResult = await verifyDependencies(runtimePython, progressCallback);

  if (!verifyResult.ok) {
    progressCallback({ stage: 'pip_install', percent: 60, message: 'Installing required neural dependencies from requirements.txt...' });
    const reqPath = path.join(getBackendDir(), 'requirements.txt');
    
    if (fs.existsSync(reqPath)) {
      await new Promise((resolve, reject) => {
        let stderrBuf = '';
        let stdoutBuf = '';
        let currentPct = 60;

        const proc = spawn(runtimePython, ['-m', 'pip', 'install', '-r', reqPath], {
          env: { ...process.env, PATH: getEnrichedPath() }
        });

        proc.stdout.on('data', (chunk) => {
          const text = chunk.toString('utf-8');
          stdoutBuf += text;
          const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
          for (const line of lines) {
            if (line.startsWith('Collecting ') || line.startsWith('Downloading ') || line.startsWith('Installing ')) {
              currentPct = Math.min(84, currentPct + 1);
              progressCallback({
                stage: 'pip_progress',
                percent: currentPct,
                message: line.substring(0, 80)
              });
            }
          }
        });

        proc.stderr.on('data', (chunk) => {
          stderrBuf += chunk.toString('utf-8');
        });

        proc.on('close', (code) => {
          if (code === 0) resolve();
          else reject(new Error(`Package installation failed (code ${code}): ${stderrBuf.slice(-400) || stdoutBuf.slice(-400)}`));
        });

        proc.on('error', (err) => reject(new Error(`Failed to execute pip: ${err.message}`)));
      });
    }

    // After installation, configure FFmpeg again in case imageio-ffmpeg was just installed
    await configureFFmpeg(progressCallback);

    // Re-verify dependencies
    progressCallback({ stage: 'reverify', percent: 85, message: 'Verifying installed neural libraries...' });
    verifyResult = await verifyDependencies(runtimePython, progressCallback);
  }

  if (!verifyResult.ok) {
    throw new Error(`Neural dependencies could not be verified: ${verifyResult.error || 'Check system requirements.'}`);
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
  testFFmpeg,
  findFFmpegExe,
  configureFFmpeg,
  verifyDependencies
};
