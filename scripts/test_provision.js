const runtimeManager = require('../electron/runtime-manager');

async function testProvision() {
  console.log('Testing provisionRuntime()...');
  try {
    const res = await runtimeManager.provisionRuntime((p) => {
      console.log(`[PROGRESS] stage=${p.stage} percent=${p.percent}% msg="${p.message}"`);
    });
    console.log('Provision result:', res);
  } catch (err) {
    console.error('PROVISION FAILED:', err);
  }
}

testProvision();
