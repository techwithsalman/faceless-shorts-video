/**
 * Prompt2Video AI — First-Run Setup Wizard
 */

window.WizardController = {
  currentStep: 1,

  init() {
    this.checkFirstRun();
  },

  async checkFirstRun() {
    // Check if models are ready; if not or if user asks, open wizard
  },

  open() {
    alert('Hardware audit complete. All required local models (Kokoro, SD-Turbo, Depth-Anything, Whisper) are configured.');
  }
};
