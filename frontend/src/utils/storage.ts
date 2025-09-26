// 主题类型定义
export type Theme = "light" | "dark" | "system";

// 主题存储键名
const THEME_STORAGE_KEY = "theme";

// 默认主题
const DEFAULT_THEME: Theme = "system";

/**
 * 获取保存的主题
 * @returns 保存的主题，如果没有则返回默认主题
 */
export const getStoredTheme = (): Theme => {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored && ["light", "dark", "system"].includes(stored)) {
      return stored as Theme;
    }
  } catch (error) {
    console.warn("Failed to read theme from localStorage:", error);
  }
  return DEFAULT_THEME;
};

/**
 * 保存主题到localStorage
 * @param theme 要保存的主题
 */
export const setStoredTheme = (theme: Theme): void => {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch (error) {
    console.warn("Failed to save theme to localStorage:", error);
  }
};

/**
 * 清除主题存储
 */
export const clearStoredTheme = (): void => {
  try {
    localStorage.removeItem(THEME_STORAGE_KEY);
  } catch (error) {
    console.warn("Failed to clear theme from localStorage:", error);
  }
};

/**
 * 检查localStorage是否可用
 * @returns 是否可用
 */
export const isLocalStorageAvailable = (): boolean => {
  try {
    const test = "__localStorage_test__";
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch {
    return false;
  }
};
