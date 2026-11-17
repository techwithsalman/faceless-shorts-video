const { app } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

/**
 * Returns whether the application is running in packaged production mode.
 */
function isPackaged() {
  return app ? app.isPackaged : false;
}

/**
 * Returns the backend directory containing scripts, styles, and templates.
 * In development: <repo_root>
 * In production: <app_install_dir>/resources/backend
 */
function getBackendDir() {
  if (isPackaged()) {
    const packagedBackend = path.join(process.resourcesPath, 'backend');
    if (fs.existsSync(packagedBackend)) {
      return packagedBackend;
    }
  }
  return path.resolve(__dirname, '..');
}

/**
 * Returns the absolute path to a specific backend script.
 */
function getScriptPath(scriptName) {
  const scriptInBackend = path.join(getBackendDir(), 'scripts', scriptName);
  if (fs.existsSync(scriptInBackend)) {
    return scriptInBackend;
  }
  // Fallback to dev scripts dir
  return path.join(path.resolve(__dirname, '..'), 'scripts', scriptName);
}

/**
 * Returns the writable user data directory.
 * Always inside %LOCALAPPDATA%\Prompt2VideoAI\ on Windows.
 */
function getUserDataDir() {
  const localAppData = process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local');
  const dir = path.join(localAppData, 'Prompt2VideoAI');
  if (!fs.existsSync(dir)) {
    try { fs.mkdirSync(dir, { recursive: true }); } catch (e) {}
  }
  return dir;
}

/**
 * Returns the application-managed Python runtime directory.
 * %LOCALAPPDATA%\Prompt2VideoAI\runtime\
 */
function getRuntimeDir() {
  return path.join(getUserDataDir(), 'runtime');
}

/**
 * Returns the expected path to the application-managed python.exe.
 */
function getRuntimePythonExe() {
  return path.join(getRuntimeDir(), 'Scripts', 'python.exe');
}

/**
 * Returns the default workspace directory for intermediate render assets.
 */
function getWorkspaceDir() {
  const dir = path.join(getUserDataDir(), 'workspace');
  if (!fs.existsSync(dir)) {
    try { fs.mkdirSync(dir, { recursive: true }); } catch (e) {}
  }
  return dir;
}

/**
 * Returns the default directory for finished MP4 renders.
 */
function getRendersDir() {
  const dir = path.join(getUserDataDir(), 'renders');
  if (!fs.existsSync(dir)) {
    try { fs.mkdirSync(dir, { recursive: true }); } catch (e) {}
  }
  return dir;
}

/**
 * Returns the model cache directory.
 * Checks D:\faceless-shorts-ai\cache first, then %LOCALAPPDATA%\Prompt2VideoAI\cache.
 */
function getModelCacheDir() {
  if (process.env.HF_HOME && fs.existsSync(process.env.HF_HOME)) {
    return process.env.HF_HOME;
  }
  const dDriveCache = 'D:\\faceless-shorts-ai\\cache';
  if (fs.existsSync(dDriveCache)) {
    return dDriveCache;
  }
  const defaultCache = path.join(getUserDataDir(), 'cache');
  if (!fs.existsSync(defaultCache)) {
    try { fs.mkdirSync(defaultCache, { recursive: true }); } catch (e) {}
  }
  return defaultCache;
}

/**
 * Returns the bin directory for local tools such as ffmpeg.
 */
function getBinDir() {
  const dir = path.join(getUserDataDir(), 'bin');
  if (!fs.existsSync(dir)) {
    try { fs.mkdirSync(dir, { recursive: true }); } catch (e) {}
  }
  return dir;
}

/**
 * Enriches the system PATH to include common FFmpeg and Git locations if missing.
 */
function getEnrichedPath() {
  let curPath = process.env.PATH || '';
  const localAppData = process.env.LOCALAPPDATA || '';
  const wingetPkg = path.join(localAppData, 'Microsoft', 'WinGet', 'Packages');
  
  const candidates = [
    getBinDir(),
    path.join(getRuntimeDir(), 'Scripts'),
    path.join(getRuntimeDir()),
    // Gyan.dev FFmpeg winget installations
    path.join(wingetPkg, 'Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe', 'ffmpeg-9.0.1-essentials_build', 'bin'),
    path.join(wingetPkg, 'Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe', 'ffmpeg-9.0.1-full_build', 'bin'),
    'C:\\ProgramData\\chocolatey\\bin'
  ];

  // Dynamically find any WinGet FFmpeg installation if directory version differs
  if (fs.existsSync(wingetPkg)) {
    try {
      const dirs = fs.readdirSync(wingetPkg);
      for (const d of dirs) {
        if (d.toLowerCase().includes('ffmpeg')) {
          const sub = path.join(wingetPkg, d);
          const inner = fs.readdirSync(sub);
          for (const inDir of inner) {
            const binP = path.join(sub, inDir, 'bin');
            if (fs.existsSync(path.join(binP, 'ffmpeg.exe'))) {
              candidates.push(binP);
            }
          }
        }
      }
    } catch (e) {}
  }

  for (const c of candidates) {
    if (fs.existsSync(c) && !curPath.toLowerCase().includes(c.toLowerCase())) {
      curPath = `${c}${path.delimiter}${curPath}`;
    }
  }
  return curPath;
}

module.exports = {
  isPackaged,
  getBackendDir,
  getScriptPath,
  getUserDataDir,
  getBinDir,
  getRuntimeDir,
  getRuntimePythonExe,
  getWorkspaceDir,
  getRendersDir,
  getModelCacheDir,
  getEnrichedPath
};
