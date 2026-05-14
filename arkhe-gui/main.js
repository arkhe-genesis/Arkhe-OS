// arkhe-gui/main.js — Electron main process
const { app, BrowserWindow, Tray, Menu, nativeImage } = require('electron');
const path = require('path');

let mainWindow;
let tray;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        title: 'ARKHE Ω‑TEMP ASI Console',
        icon: path.join(__dirname, 'arkhe.ico'),
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
        },
        backgroundColor: '#0B1F3A',
    });
    mainWindow.loadURL('http://localhost:3000');
}

function createTray() {
    const icon = nativeImage.createFromPath(path.join(__dirname, 'tray-icon.png'));
    tray = new Tray(icon);
    const contextMenu = Menu.buildFromTemplate([
        { label: 'Φ_C: 0.9993', enabled: false },
        { label: 'π: 0.0018', enabled: false },
        { type: 'separator' },
        { label: 'Abrir Console', click: () => mainWindow.show() },
        { label: 'Executar Spiral Ping', click: () => { /* IPC para runtime */ } },
        { type: 'separator' },
        { label: 'Sair', click: () => app.quit() },
    ]);
    tray.setContextMenu(contextMenu);
    tray.setToolTip('ARKHE Ω‑TEMP ASI');
}

app.whenReady().then(() => {
    createWindow();
    createTray();
});
app.on('window-all-closed', () => { /* manter em tray */ });