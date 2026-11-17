/**
 * Test script to verify Electron backend resolution and runtime readiness
 */
const path = require('path');
const fs = require('fs');
const { spawnSync } = require('child_process');

const pathResolver = require('../electron/path-resolver');
const runtimeManager = require('../electron/runtime-manager');

async function runTests() {
  console.log('====================================================');
  console.log(' PROMPT2VIDEO AI — BACKEND & RUNTIME VERIFICATION');
  console.log('====================================================\n');

  // 1. Path Resolver Checks
  console.log('1. Checking Path Resolver:');
  console.log('   - isPackaged():', pathResolver.isPackaged());
  console.log('   - getBackendDir():', pathResolver.getBackendDir());
  console.log('   - getScriptPath("prompt2video.py"):', pathResolver.getScriptPath('prompt2video.py'));
  console.log('   - getUserDataDir():', pathResolver.getUserDataDir());
  console.log('   - getRuntimeDir():', pathResolver.getRuntimeDir());
  console.log('   - getRuntimePythonExe():', pathResolver.getRuntimePythonExe());
  console.log('   - getModelCacheDir():', pathResolver.getModelCacheDir());
  console.log('   - Script exists:', fs.existsSync(pathResolver.getScriptPath('prompt2video.py')));
  console.log('   - Runtime Python exists:', fs.existsSync(pathResolver.getRuntimePythonExe()));

  // 2. Runtime Manager Checks
  console.log('\n2. Checking Runtime Manager:');
  const basePy = await runtimeManager.findBasePython();
  console.log('   - Base Python found:', basePy);

  const ffmpegOk = await runtimeManager.testFFmpeg();
  console.log('   - FFmpeg available:', ffmpegOk);

  const activePy = await runtimeManager.resolveActivePython();
  console.log('   - Active Python resolved:', activePy);

  const status = await runtimeManager.getRuntimeStatus();
  console.log('   - Full Runtime Status:', JSON.stringify(status, null, 2));

  // 3. Smoke Test Python Execution
  console.log('\n3. Smoke Testing prompt2video.py with Active Python:');
  if (status.ready && status.pythonPath) {
    const scriptPath = pathResolver.getScriptPath('prompt2video.py');
    const res = spawnSync(status.pythonPath, [scriptPath, '--help'], {
      env: {
        ...process.env,
        PATH: pathResolver.getEnrichedPath(),
        P2V_PYTHON_EXE: status.pythonPath,
        P2V_BACKEND_DIR: pathResolver.getBackendDir(),
        P2V_USER_DATA: pathResolver.getUserDataDir()
      },
      encoding: 'utf-8'
    });

    console.log('   - Exit code:', res.status);
    console.log('   - Output preview:\n', res.stdout.substring(0, 300));
    if (res.status === 0) {
      console.log('\n>>> SUCCESS: prompt2video.py executed cleanly with isolated runtime! <<<');
    } else {
      console.error('\n>>> ERROR: prompt2video.py failed:\n', res.stderr);
      process.exit(1);
    }
  } else {
    console.warn('   - Runtime not ready yet. Ready status:', status.ready);
  }
}

runTests().catch(err => {
  console.error('Fatal test error:', err);
  process.exit(1);
});
