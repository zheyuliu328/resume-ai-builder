const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow;
let pythonProcess;

// 启动Python后端服务
function startPythonBackend() {
    const rootDir = path.join(__dirname, '..');
    const backendPath = path.join(rootDir, 'backend', 'api_server.py');
    pythonProcess = spawn('python3', [backendPath], { cwd: rootDir });
    
    pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        titleBarStyle: 'hiddenInset',
        backgroundColor: '#f3f4f6'
    });

    mainWindow.loadFile('index.html');

    mainWindow.webContents.on('did-finish-load', () => {
        mainWindow.webContents.setZoomFactor(1);
        mainWindow.webContents.setVisualZoomLevelLimits(1, 1).catch((error) => {
            console.warn('Failed to lock zoom level:', error);
        });
    });

    mainWindow.webContents.on('before-input-event', (event, input) => {
        // 拦截 Ctrl/Cmd + +/-/0/= 缩放快捷键
        const isModifier = input.control || input.meta;
        const isZoomKey = ['+', '-', '=', '0', '_', 'plus', 'minus', 'numadd', 'numsub'].includes(input.key) 
                       || input.key === '=';
        if (isModifier && isZoomKey) {
            event.preventDefault();
        }
    });
    
    // 开发模式打开DevTools
    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools();
    }
}

app.whenReady().then(() => {
    // 等待2秒让Python后端启动
    startPythonBackend();
    setTimeout(createWindow, 2000);
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
