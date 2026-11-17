# Building Prompt2Video AI for Windows x64

This guide covers building the production Windows installer (`Prompt2Video-AI-Setup.exe`) and packaging the complete offline desktop application.

---

## 1. Prerequisites

Ensure the following tools are installed on your build machine:

- **Node.js**: `v20.x` or `v22.x`+ (`v24.x` supported)
- **npm**: `v10.x`+
- **Python**: `3.11.x` (64-bit)
- **FFmpeg**: Gyan.dev Windows build (included in PATH or local tools)
- **Git**: For source version control

---

## 2. Directory Structure

```
Prompt2Video-AI/
├── assets/
│   ├── icon.ico            # Windows application icon (16x16 to 256x256)
│   └── icon.png            # High-resolution PNG logo (512x512)
├── electron/
│   ├── main.js             # Electron main process & window lifecycle
│   ├── preload.js          # Secure contextBridge API for renderer
│   └── ipc-handlers.js     # Native IPC handlers (hardware, models, generation)
├── src-ui/
│   ├── index.html          # Main application interface
│   ├── css/
│   │   ├── style.css       # Core typography, dark palette & layout
│   │   └── components.css  # Buttons, cards, studio timeline & video player
│   └── js/
│       ├── app.js          # Main app & navigation controller
│       ├── studio.js       # Real-time production studio & event stream
│       ├── library.js      # Video player modal & file explorer actions
│       ├── models.js       # Hardware detection & local AI model status
│       └── wizard.js       # First-run hardware & model setup wizard
├── scripts/
│   ├── prompt2video.py     # Master offline video generation orchestrator
│   ├── local_llm.py        # Local script & scene planning engine
│   ├── voice.py            # Kokoro-82M ONNX voice synthesis
│   ├── words.py            # Faster-Whisper word-level subtitle alignment
│   ├── local_image.py      # SD-Turbo photorealistic visual generator
│   └── depth_estimator.py  # Depth-Anything 2.5D volumetric parallax
├── package.json            # Electron & electron-builder configuration
└── requirements.txt        # Python neural inference dependencies
```

---

## 3. Install Node.js Dependencies

In the project root:

```powershell
npm install
```

This installs `electron` and `electron-builder`.

---

## 4. Test in Development Mode

Run the application directly in development mode:

```powershell
npm start
```

Or execute directly with Electron:

```powershell
npx electron .
```

---

## 5. Build the Windows Installer (`.exe`)

Run the automated electron-builder packaging script:

```powershell
npm run dist
```

### Build Artifacts

Upon completion, `electron-builder` generates the following files in the `dist/` directory:

1. **`dist/Prompt2Video-AI-Setup.exe`**: The complete NSIS Windows installer.
2. **`dist/win-unpacked/`**: Portable unpacked binaries for instant execution without installation.

---

## 6. Installer Customization Options

Installer settings are defined in `package.json` under `"build"`:

```json
"build": {
  "appId": "com.prompt2video.ai",
  "productName": "Prompt2Video AI",
  "win": {
    "target": ["nsis"],
    "icon": "assets/icon.ico"
  },
  "nsis": {
    "oneClick": false,
    "allowToChangeInstallationDirectory": true,
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true,
    "shortcutName": "Prompt2Video AI",
    "artifactName": "Prompt2Video-AI-Setup.${ext}"
  },
  "directories": {
    "output": "dist"
  }
}
```

- **`oneClick: false`**: Provides a standard setup wizard allowing users to select their installation drive (e.g., C: or D: drive).
- **`createDesktopShortcut: true`**: Places a desktop shortcut with the Prompt2Video AI icon.
- **`allowToChangeInstallationDirectory: true`**: Enables custom directory selection for low-capacity C: drives.
