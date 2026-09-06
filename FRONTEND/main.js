const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
    const win = new BrowserWindow({
        width: 1440,
        height: 900,
        minWidth: 1100,
        minHeight: 700,
        title: "MRPL AI WORKBENCH - Secure Enterprise AI Workspace",
        autoHideMenuBar: true,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    win.loadFile('index.html');

    // Reset and enforce 100% zoom factor on page load and reload
    const resetZoomToHundred = () => {
        win.webContents.setZoomFactor(1.0);
        win.webContents.setZoomLevel(0);
    };

    win.webContents.on('dom-ready', resetZoomToHundred);
    win.webContents.on('did-finish-load', resetZoomToHundred);

    // Handle zoom shortcuts (Ctrl/Cmd + '=', '+', '-', '0') and reloads seamlessly
    win.webContents.on('before-input-event', (event, input) => {
        if (input.type === 'keyDown' && (input.control || input.meta)) {
            const currentZoom = win.webContents.getZoomFactor();

            if (input.key === '=' || input.key === '+' || input.code === 'Equal' || input.code === 'NumpadAdd') {
                event.preventDefault();
                const nextZoom = Math.min(Number((currentZoom + 0.1).toFixed(2)), 3.0);
                win.webContents.setZoomFactor(nextZoom);
            } else if (input.key === '-' || input.key === '_' || input.code === 'Minus' || input.code === 'NumpadSubtract') {
                event.preventDefault();
                const nextZoom = Math.max(Number((currentZoom - 0.1).toFixed(2)), 0.3);
                win.webContents.setZoomFactor(nextZoom);
            } else if (input.key === '0' || input.code === 'Digit0' || input.code === 'Numpad0') {
                event.preventDefault();
                resetZoomToHundred();
            } else if (input.key.toLowerCase() === 'r') {
                event.preventDefault();
                resetZoomToHundred();
                win.webContents.reload();
            }
        } else if (input.type === 'keyDown' && input.key === 'F5') {
            event.preventDefault();
            resetZoomToHundred();
            win.webContents.reload();
        }
    });
}

app.whenReady().then(() => {
    createWindow();
    
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});