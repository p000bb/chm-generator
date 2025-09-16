/**
 * 桌面通知工具
 */

// 检查浏览器是否支持通知
export const isNotificationSupported = () => {
  return "Notification" in window;
};

// 请求通知权限
export const requestNotificationPermission = async (): Promise<boolean> => {
  if (!isNotificationSupported()) {
    console.warn("浏览器不支持桌面通知");
    return false;
  }

  if (Notification.permission === "granted") {
    return true;
  }

  if (Notification.permission === "denied") {
    console.warn("用户已拒绝桌面通知权限");
    return false;
  }

  try {
    const permission = await Notification.requestPermission();
    return permission === "granted";
  } catch (error) {
    console.error("请求通知权限失败:", error);
    return false;
  }
};

// 显示通知
export const showNotification = (
  title: string,
  options?: NotificationOptions
) => {
  if (!isNotificationSupported() || Notification.permission !== "granted") {
    console.warn("无法显示桌面通知，权限未授予");
    return null;
  }

  try {
    const notification = new Notification(title, {
      icon: "/logo.svg", // 使用应用图标
      badge: "/logo.svg",
      tag: "app-notification", // 使用相同tag替换之前的通知
      requireInteraction: false, // 不需要用户交互
      silent: false, // 允许声音
      ...options,
    });

    // 自动关闭通知（5秒后）
    setTimeout(() => {
      notification.close();
    }, 5000);

    // 点击通知时聚焦到应用窗口
    notification.onclick = () => {
      window.focus();
      notification.close();
    };

    return notification;
  } catch (error) {
    console.error("显示通知失败:", error);
    return null;
  }
};

// 显示任务完成通知
export const showTaskCompleteNotification = (
  appName: string,
  success: boolean = true
) => {
  const title = success ? "任务完成" : "任务异常";
  const body = success
    ? `${appName} 已成功运行完毕`
    : `${appName} 运行出现异常`;

  return showNotification(title, {
    body,
    icon: "/logo.svg",
    tag: `task-${appName}`, // 每个应用使用不同的tag
    requireInteraction: true, // 任务完成通知需要用户交互
    silent: false,
  });
};

// 显示任务启动通知（已禁用）
export const showTaskStartNotification = (appName: string) => {
  // 启动通知已禁用，不显示任何通知
  return null;
};
