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
import { spawn } from "child_process";

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

// 添加日志到文件
const addLogToFile = (logData: any) => {
  const logEntry = {
    id: `${Date.now()}-${Math.random()}`,
    timestamp: new Date().toISOString(),
    scriptName: logData.scriptName,
    type: logData.type,
    message: logData.data.trim().replace(/^\uFEFF/, ""),
  };

  // 写入日志文件
  writeLogToFile(logEntry);
};

// 写入日志到文件
const writeLogToFile = (logEntry: any) => {
  try {
    // 确保 config 目录存在
    const configDir = path.join(__dirname, "../../../config");
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }

    const logFilePath = path.join(configDir, "log.txt");

    // 格式化日志行
    const timestamp = new Date(logEntry.timestamp).toLocaleString();
    const scriptName = logEntry.scriptName || "SYSTEM";
    const type = logEntry.type.toUpperCase();
    const message = logEntry.message;

    // 创建格式化的日志行
    const logLine = `[${timestamp}] [${scriptName}] [${type}] ${message}\n`;

    // 追加写入日志文件
    fs.appendFileSync(logFilePath, logLine, "utf8");
  } catch (error) {
    console.error("写入日志文件失败:", error);
  }
};

// 写入实时日志到 cache/log.txt
const writeRealtimeLog = (logData: any) => {
  try {
    // 确保 cache 目录存在
    const cacheDir = path.join(__dirname, "../../../cache");
    if (!fs.existsSync(cacheDir)) {
      fs.mkdirSync(cacheDir, { recursive: true });
    }

    const logFilePath = path.join(cacheDir, "log.txt");

    // 格式化日志行
    const timestamp = new Date(logData.timestamp).toLocaleString();
    const scriptName = logData.scriptName || "SYSTEM";
    const type = logData.type.toUpperCase();
    const message = logData.data;

    // 处理多行消息，为每一行添加时间戳前缀
    const lines = message.split("\n");
    lines.forEach((line, index) => {
      if (line.trim()) {
        // 只处理非空行
        const logLine = `[${timestamp}] [${scriptName}] [${type}] ${line}\n`;
        fs.appendFileSync(logFilePath, logLine, "utf8");
      }
    });
  } catch (error) {
    console.error("写入实时日志文件失败:", error);
  }
};

// 清空实时日志文件
const clearRealtimeLog = () => {
  return new Promise<void>((resolve, reject) => {
    try {
      const cacheDir = path.join(__dirname, "../../../cache");
      const logFilePath = path.join(cacheDir, "log.txt");

      // 清空文件内容
      fs.writeFileSync(logFilePath, "", "utf8");
      console.log("实时日志文件已清空");
      resolve();
    } catch (error) {
      console.error("清空实时日志文件失败:", error);
      reject(error);
    }
  });
};

// 执行 Python 脚本
ipcMain.handle(
  "python:runScript",
  async (
    _,
    scriptName: string,
    inputFolder: string,
    outputFolder: string,
    chipConfig: any
  ) => {
    return new Promise(async (resolve, reject) => {
      // 构建 Python 主脚本路径
      let scriptPath;
      let projectPythonPath;

      if (process.env.NODE_ENV === "production") {
        // 生产环境：使用打包后的路径
        scriptPath = path.join(process.resourcesPath, "python", "main.py");
        projectPythonPath = path.join(process.resourcesPath, "python", "interpreter", "python.exe");
      } else {
        // 开发环境：使用开发路径
        scriptPath = path.join(__dirname, "../../..", "python", "main.py");
        projectPythonPath = path.join(__dirname, "../../../python/interpreter/python.exe");
      }

      // 检查脚本文件是否存在
      if (!fs.existsSync(scriptPath)) {
        reject(new Error(`Python 脚本不存在: ${scriptPath}`));
        return;
      }

      // 记录脚本开始执行的系统日志
      addSystemLog(`开始执行脚本: ${scriptName}`);

      // 启动 Python 进程
      // 智能选择 Python 解释器路径
      let pythonCommand;

      if (fs.existsSync(projectPythonPath)) {
        pythonCommand = projectPythonPath;
        console.log(`使用项目内 Python 解释器: ${pythonCommand}`);
      } else {
        // 回退到系统 Python
        pythonCommand = process.platform === "win32" ? "python" : "python3";
        console.log(`使用系统 Python 解释器: ${pythonCommand}`);
      }

      // 统一通过 main.py 调用，传递脚本名称和参数
      // 将芯片配置转换为 JSON 字符串
      const chipConfigJson = JSON.stringify(chipConfig);
      const scriptArgs = [
        scriptPath, // main.py 的路径
        scriptName, // 脚本名称
        inputFolder, // 输入文件夹
        outputFolder, // 输出文件夹
        chipConfigJson, // 芯片配置JSON
      ];

      console.log(`脚本参数: ${scriptArgs.join(" ")}`);
      console.log(`芯片配置: ${chipConfigJson}`);

      const pythonProcess = spawn(pythonCommand, scriptArgs, {
        env: {
          ...process.env,
          PYTHONIOENCODING: "utf-8",
          PYTHONUTF8: "1",
          PYTHONUNBUFFERED: "1", // 禁用 Python 输出缓冲，实现实时输出
        },
      });

      let output = "";
      let errorOutput = "";

      // 监听标准输出
      pythonProcess.stdout?.on("data", (data) => {
        const text = data.toString("utf8");
        output += text;
        console.log(`[${scriptName}] stdout:`, text);

        const logData = {
          scriptName,
          type: "stdout",
          data: text,
          timestamp: new Date().toISOString(),
        };

        // 写入历史日志文件
        addLogToFile(logData);

        // 写入实时日志文件
        writeRealtimeLog(logData);
      });

      // 监听错误输出
      pythonProcess.stderr?.on("data", (data) => {
        const text = data.toString("utf8");
        errorOutput += text;
        console.error(`[${scriptName}] stderr:`, text);

        const logData = {
          scriptName,
          type: "stderr",
          data: text,
          timestamp: new Date().toISOString(),
        };

        // 写入历史日志文件
        addLogToFile(logData);

        // 写入实时日志文件
        writeRealtimeLog(logData);
      });

      // 监听进程结束
      pythonProcess.on("close", (code) => {
        console.log(`[${scriptName}] 进程结束，退出码: ${code}`);

        // 记录脚本执行完成的系统日志
        if (code === 0) {
          addSystemLog(`脚本执行完成: ${scriptName} (退出码: ${code})`);
          resolve({
            success: true,
            output: output,
            code: code,
          });
        } else {
          addSystemLog(`脚本执行失败: ${scriptName} (退出码: ${code})`);
          resolve({
            success: false,
            output: output,
            error: errorOutput,
            code: code,
          });
        }
      });

      // 监听进程错误
      pythonProcess.on("error", (error) => {
        console.error(`[${scriptName}] 进程错误:`, error);
        addSystemLog(`脚本启动失败: ${scriptName} - ${error.message}`);
        reject(new Error(`启动 Python 脚本失败: ${error.message}`));
      });
    });
  }
);

// 清空实时日志文件
ipcMain.handle("logs:clearRealtime", async () => {
  try {
    await clearRealtimeLog();
    return { success: true };
  } catch (error) {
    console.error("清空实时日志失败:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
});

// 获取实时日志文件内容
ipcMain.handle("logs:getRealtimeFile", async () => {
  try {
    const cacheDir = path.join(__dirname, "../../../cache");
    const logFilePath = path.join(cacheDir, "log.txt");

    if (fs.existsSync(logFilePath)) {
      const content = fs.readFileSync(logFilePath, "utf8");
      return {
        success: true,
        content: content,
        filePath: logFilePath,
      };
    } else {
      return {
        success: false,
        content: "",
        filePath: logFilePath,
        error: "实时日志文件不存在",
      };
    }
  } catch (error) {
    console.error("读取实时日志文件失败:", error);
    return {
      success: false,
      content: "",
      filePath: "",
      error: error instanceof Error ? error.message : String(error),
    };
  }
});

// 添加系统日志
const addSystemLog = (message: string) => {
  const logData = {
    scriptName: "SYSTEM",
    type: "system",
    data: message,
    timestamp: new Date().toISOString(),
  };
  addLogToFile(logData);
};

// 应用启动时记录系统日志
addSystemLog("CHM文档生成工具启动");

// 应用关闭时记录系统日志
app.on("before-quit", () => {
  addSystemLog("CHM文档生成工具关闭");
});

// 窗口关闭时记录系统日志
app.on("window-all-closed", () => {
  addSystemLog("所有窗口已关闭");
});
