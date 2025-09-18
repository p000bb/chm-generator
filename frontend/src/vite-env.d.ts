/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

interface Window {
  // expose in the `electron/preload/index.ts`
  ipcRenderer: import("electron").IpcRenderer;
  electronAPI: {
    selectFile: (options: {
      filters: Array<{ name: string; extensions: string[] }>;
    }) => Promise<{ canceled: boolean; filePaths: string[] }>;
    selectFolder: () => Promise<{ canceled: boolean; filePaths: string[] }>;
    readDirectory: (path: string) => Promise<{
      success: boolean;
      folders: string[];
      files: string[];
      error?: string;
    }>;
    getConfig: () => Promise<{
      inputFolder: string;
      outputFolder: string;
      scripts: any[];
    }>;
    saveConfig: (config: any) => Promise<{ success: boolean }>;
    runPythonScript: (
      scriptName: string,
      inputFolder: string,
      outputFolder: string,
      chipConfig: any
    ) => Promise<{
      success: boolean;
      output: string;
      error?: string;
      code: number;
    }>;
    getRealtimeLogFile: () => Promise<{
      success: boolean;
      content: string;
      filePath: string;
      error?: string;
    }>;
    clearLogFile: () => Promise<{
      success: boolean;
      error?: string;
    }>;
    clearRealtimeLog: () => Promise<{
      success: boolean;
      error?: string;
    }>;
  };
}
