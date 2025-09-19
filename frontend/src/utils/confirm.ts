import { createApp, type App } from "vue";
import Confirm from "@/components/Confirm.vue";

//#region 类型定义
export type ConfirmType = "warning" | "error" | "info" | "question";

export interface ConfirmOptions {
  title?: string;
  message: string;
  type?: ConfirmType;
  confirmText?: string;
  cancelText?: string;
  showCancel?: boolean;
  closeOnOverlay?: boolean;
}

export interface ConfirmResult {
  confirmed: boolean;
  cancelled: boolean;
}
//#endregion

//#region 确认对话框管理器
class ConfirmManager {
  private container: HTMLElement | null = null;
  private currentConfirm: App | null = null;

  private createContainer() {
    if (!this.container) {
      this.container = document.createElement("div");
      this.container.className = "confirm-container";
      this.container.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 10000;
        pointer-events: none;
      `;
      document.body.appendChild(this.container);
    }
    return this.container;
  }

  private removeConfirm(app: App) {
    if (this.currentConfirm === app) {
      this.currentConfirm = null;
    }
    app.unmount();
  }

  show(options: ConfirmOptions): Promise<ConfirmResult> {
    return new Promise((resolve) => {
      // 如果已有确认对话框，先关闭
      if (this.currentConfirm) {
        this.currentConfirm.unmount();
        this.currentConfirm = null;
      }

      const container = this.createContainer();

      // 创建确认对话框实例
      const confirmApp = createApp(Confirm, {
        ...options,
        onConfirm: () => {
          this.removeConfirm(confirmApp);
          resolve({ confirmed: true, cancelled: false });
        },
        onCancel: () => {
          this.removeConfirm(confirmApp);
          resolve({ confirmed: false, cancelled: true });
        },
        onClose: () => {
          this.removeConfirm(confirmApp);
        },
      });

      // 挂载到容器
      const confirmElement = document.createElement("div");
      confirmElement.style.pointerEvents = "auto";
      container.appendChild(confirmElement);

      confirmApp.mount(confirmElement);
      this.currentConfirm = confirmApp;
    });
  }

  // 快捷方法
  confirm(message: string, title?: string): Promise<ConfirmResult> {
    return this.show({
      message,
      title: title || "确认操作",
      type: "question",
    });
  }

  warning(message: string, title?: string): Promise<ConfirmResult> {
    return this.show({
      message,
      title: title || "警告",
      type: "warning",
    });
  }

  error(message: string, title?: string): Promise<ConfirmResult> {
    return this.show({
      message,
      title: title || "错误",
      type: "error",
    });
  }

  info(message: string, title?: string): Promise<ConfirmResult> {
    return this.show({
      message,
      title: title || "提示",
      type: "info",
    });
  }

  // 删除确认
  delete(message: string, title?: string): Promise<ConfirmResult> {
    return this.show({
      message,
      title: title || "删除确认",
      type: "error",
      confirmText: "删除",
      cancelText: "取消",
    });
  }

  // 保存确认
  save(message: string, title?: string): Promise<ConfirmResult> {
    return this.show({
      message,
      title: title || "保存确认",
      type: "info",
      confirmText: "保存",
      cancelText: "取消",
    });
  }

  // 关闭所有确认对话框
  closeAll() {
    if (this.currentConfirm) {
      this.currentConfirm.unmount();
      this.currentConfirm = null;
    }
  }
}

// 创建全局实例
const confirmManager = new ConfirmManager();

// 导出方法
export const confirm = {
  // 基础方法
  show: (options: ConfirmOptions) => confirmManager.show(options),
  confirm: (message: string, title?: string) =>
    confirmManager.confirm(message, title),
  warning: (message: string, title?: string) =>
    confirmManager.warning(message, title),
  error: (message: string, title?: string) =>
    confirmManager.error(message, title),
  info: (message: string, title?: string) =>
    confirmManager.info(message, title),

  // 快捷方法
  delete: (message: string, title?: string) =>
    confirmManager.delete(message, title),
  save: (message: string, title?: string) =>
    confirmManager.save(message, title),

  // 工具方法
  closeAll: () => confirmManager.closeAll(),
};

export default confirm;
//#endregion
