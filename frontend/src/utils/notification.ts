/**
 * 桌面通知工具
 */

// 检查浏览器是否支持通知
export const isNotificationSupported = () => {
  return "Notification" in window;
};

// 获取正确的图标路径
const getIconPath = () => {
  // 在 Electron 中，通知图标通常需要是 PNG 或 ICO 格式
  // SVG 格式可能不被所有系统支持
  if (import.meta.env.DEV) {
    return "/logo.svg";
  } else {
    // 生产环境：使用 ICO 格式的图标，这是 Windows 系统推荐的通知图标格式
    return "/icon.ico";
  }
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
    const iconPath = getIconPath();
    console.log("通知图标路径:", iconPath);
    console.log("当前环境:", import.meta.env.DEV ? "开发环境" : "生产环境");

    const notification = new Notification(title, {
      icon: iconPath, // 使用动态图标路径
      badge: iconPath,
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
  success: boolean = true,
  appName?: string
) => {
  const title = success ? "✅ 任务完成" : "❌ 任务异常";
  const body = success
    ? `脚本执行成功: ${appName}`
    : `脚本执行失败: ${appName}`;

  return showNotification(title, {
    body,
    icon: getIconPath(),
    tag: `task-${appName}`, // 每个应用使用不同的tag
    requireInteraction: false, // 任务完成通知需要用户交互
    silent: true,
  });
};

// 显示任务启动通知（已禁用）
export const showTaskStartNotification = (_appName: string) => {
  // 启动通知已禁用，不显示任何通知
  return null;
};
