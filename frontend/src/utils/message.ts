import { createApp, type App } from "vue";
import Message from "@/components/Message.vue";

//#region 类型定义
export type MessageType = "success" | "error" | "warning" | "info";

export interface MessageOptions {
  type: MessageType;
  message: string;
  duration?: number;
}
//#endregion

//#region 消息管理器
class MessageManager {
  private container: HTMLElement | null = null;
  private messages: App[] = [];

  private createContainer() {
    if (!this.container) {
      this.container = document.createElement("div");
      this.container.className = "message-container";
      this.container.style.cssText = `
        position: fixed;
        top: 0;
        right: 0;
        z-index: 9999;
        pointer-events: none;
      `;
      document.body.appendChild(this.container);
    }
    return this.container;
  }

  private removeMessage(app: App) {
    const index = this.messages.indexOf(app);
    if (index > -1) {
      this.messages.splice(index, 1);
    }
    app.unmount();
  }

  show(options: MessageOptions) {
    const container = this.createContainer();

    // 创建消息实例
    const messageApp = createApp(Message, {
      ...options,
      onClose: () => {
        this.removeMessage(messageApp);
      },
    });

    // 挂载到容器
    const messageElement = document.createElement("div");
    messageElement.style.pointerEvents = "auto";
    messageElement.style.marginBottom = "8px";
    container.appendChild(messageElement);

    messageApp.mount(messageElement);
    this.messages.push(messageApp);

    return messageApp;
  }

  success(message: string, duration?: number) {
    return this.show({ type: "success", message, duration });
  }

  error(message: string, duration?: number) {
    return this.show({ type: "error", message, duration });
  }

  warning(message: string, duration?: number) {
    return this.show({ type: "warning", message, duration });
  }

  info(message: string, duration?: number) {
    return this.show({ type: "info", message, duration });
  }

  clear() {
    this.messages.forEach((app) => {
      app.unmount();
    });
    this.messages = [];
  }
}

// 创建全局实例
const messageManager = new MessageManager();

// 导出方法
export const message = {
  success: (msg: string, duration?: number) =>
    messageManager.success(msg, duration),
  error: (msg: string, duration?: number) =>
    messageManager.error(msg, duration),
  warning: (msg: string, duration?: number) =>
    messageManager.warning(msg, duration),
  info: (msg: string, duration?: number) => messageManager.info(msg, duration),
  clear: () => messageManager.clear(),
};

export default message;
//#endregion
