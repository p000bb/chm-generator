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
  };
}
