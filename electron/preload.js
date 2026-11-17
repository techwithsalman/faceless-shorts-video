const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // System & Hardware
  getHardwareInfo: () => ipcRenderer.invoke('system:get-hardware'),
  
  // AI Models
  getModelStatus: () => ipcRenderer.invoke('models:get-status'),
  verifyModels: () => ipcRenderer.invoke('models:verify'),

  // Generation
  generateVideo: (options) => ipcRenderer.invoke('video:generate', options),
  cancelVideo: () => ipcRenderer.invoke('video:cancel'),
  onVideoProgress: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('video:progress', handler);
    return () => ipcRenderer.removeListener('video:progress', handler);
  },
  onVideoLog: (callback) => {
    const handler = (event, log) => callback(log);
    ipcRenderer.on('video:log', handler);
    return () => ipcRenderer.removeListener('video:log', handler);
  },

  // Library
  getLibrary: (customDir) => ipcRenderer.invoke('library:get-videos', customDir),
  openInFolder: (filePath) => ipcRenderer.invoke('library:open-folder', filePath),
  openPath: (folderPath) => ipcRenderer.invoke('library:open-path', folderPath),
  deleteVideo: (filePath) => ipcRenderer.invoke('library:delete-video', filePath),

  // File & Dialogs
  selectDirectory: (defaultPath) => ipcRenderer.invoke('dialog:select-directory', defaultPath),

  // Settings
  getSettings: () => ipcRenderer.invoke('settings:get'),
  saveSettings: (settings) => ipcRenderer.invoke('settings:save', settings),

  // Platform info
  platform: process.platform,
  version: '1.0.0'
});
