import {
  BrowserWindow,
  Menu,
  MenuItemConstructorOptions,
  app,
  dialog,
  ipcMain,
  shell,
} from "electron";

import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import fs from "fs";
import os from "node:os";
import path from "node:path";

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// The built directory structure
//
// ├─┬ dist-electron
// │ ├─┬ main
// │ │ └── index.js    > Electron-Main
// │ └─┬ preload
// │   └── index.mjs   > Preload-Scripts
// ├─┬ dist
// │ └── index.html    > Electron-Renderer
//
process.env.APP_ROOT = path.join(__dirname, "../..");

export const MAIN_DIST = path.join(process.env.APP_ROOT, "dist-electron");
export const RENDERER_DIST = path.join(process.env.APP_ROOT, "dist");
export const VITE_DEV_SERVER_URL = process.env.VITE_DEV_SERVER_URL;

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL
  ? path.join(process.env.APP_ROOT, "public")
  : RENDERER_DIST;

// Disable GPU Acceleration for Windows 7
if (os.release().startsWith("6.1")) app.disableHardwareAcceleration();

// Set application name for Windows 10+ notifications
if (process.platform === "win32") app.setAppUserModelId(app.getName());

if (!app.requestSingleInstanceLock()) {
  app.quit();
  process.exit(0);
}

let win: BrowserWindow | null = null;
const preload = path.join(__dirname, "../preload/index.mjs");
const indexHtml = path.join(RENDERER_DIST, "index.html");

// 创建开发环境右键菜单
function createContextMenu() {
  const template: MenuItemConstructorOptions[] = [
    {
      label: "开发者工具",
      click: () => {
        if (win) {
          win.webContents.toggleDevTools();
        }
      },
    },
    {
      label: "重新加载",
      click: () => {
        if (win) {
          win.reload();
        }
      },
    },
    {
      label: "强制重新加载",
      click: () => {
        if (win) {
          win.webContents.reloadIgnoringCache();
        }
      },
    },
    { type: "separator" },
    {
      label: "检查元素",
      click: () => {
        if (win) {
          win.webContents.inspectElement(0, 0);
        }
      },
    },
    {
      label: "查看页面源代码",
      click: () => {
        if (win) {
          // 通过开发者工具查看源代码
          win.webContents.openDevTools();
        }
      },
    },
    { type: "separator" },
    {
      label: "复制",
      role: "copy",
    },
    {
      label: "粘贴",
      role: "paste",
    },
    {
      label: "全选",
      role: "selectAll",
    },
  ];

  return Menu.buildFromTemplate(template);
}

async function createWindow() {
  win = new BrowserWindow({
    title: "应用管理器",
    icon: path.join(process.env.VITE_PUBLIC, "favicon.ico"),
    webPreferences: {
      preload,
      // Warning: Enable nodeIntegration and disable contextIsolation is not secure in production
      // nodeIntegration: true,

      // Consider using contextBridge.exposeInMainWorld
      // Read more on https://www.electronjs.org/docs/latest/tutorial/context-isolation
      // contextIsolation: false,
    },
  });

  // 去除菜单栏
  win.setMenuBarVisibility(false);

  // 只在开发环境添加右键菜单
  if (VITE_DEV_SERVER_URL) {
    // 设置右键菜单
    win.webContents.on("context-menu", (event, params) => {
      const contextMenu = createContextMenu();
      contextMenu.popup();
    });
  }

  if (VITE_DEV_SERVER_URL) {
    // #298
    win.loadURL(VITE_DEV_SERVER_URL);
    // Open devTool if the app is not packaged
    win.webContents.openDevTools();
  } else {
    win.loadFile(indexHtml);
  }

  // Test actively push message to the Electron-Renderer
  win.webContents.on("did-finish-load", () => {
    win?.webContents.send("main-process-message", new Date().toLocaleString());
  });

  // Make all links open with the browser, not with the application
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("https:")) shell.openExternal(url);
    return { action: "deny" };
  });
  // win.webContents.on('will-navigate', (event, url) => { }) #344
}

app.whenReady().then(() => {
  // 完全移除菜单
  Menu.setApplicationMenu(null);
  createWindow();
});

app.on("window-all-closed", () => {
  win = null;
  if (process.platform !== "darwin") app.quit();
});

app.on("second-instance", () => {
  if (win) {
    // Focus on the main window if the user tried to open another
    if (win.isMinimized()) win.restore();
    win.focus();
  }
});

app.on("activate", () => {
  const allWindows = BrowserWindow.getAllWindows();
  if (allWindows.length) {
    allWindows[0].focus();
  } else {
    createWindow();
  }
});

// 文件选择对话框
ipcMain.handle("dialog:selectFile", async (_, options) => {
  const result = await dialog.showOpenDialog(win!, {
    properties: ["openFile"],
    filters: options.filters || [{ name: "所有文件", extensions: ["*"] }],
  });
  return result;
});

// 文件夹选择对话框
ipcMain.handle("dialog:selectFolder", async () => {
  const result = await dialog.showOpenDialog(win!, {
    properties: ["openDirectory"],
  });
  return result;
});

// New window example arg: new windows url
ipcMain.handle("open-win", (_, arg) => {
  const childWindow = new BrowserWindow({
    webPreferences: {
      preload,
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  if (VITE_DEV_SERVER_URL) {
    childWindow.loadURL(`${VITE_DEV_SERVER_URL}#${arg}`);
  } else {
    childWindow.loadFile(indexHtml, { hash: arg });
  }
});

// 读取文件夹内容
ipcMain.handle("fs:readDirectory", async (_, dirPath: string) => {
  try {
    const items = fs.readdirSync(dirPath, { withFileTypes: true });
    return {
      success: true,
      folders: items
        .filter((item) => item.isDirectory())
        .map((item) => item.name),
      files: items.filter((item) => item.isFile()).map((item) => item.name),
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
      folders: [],
      files: [],
    };
  }
});
