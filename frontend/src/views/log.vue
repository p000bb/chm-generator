<template>
  <div class="log-page flex flex-col bg-white dark:bg-slate-900">
    <!-- 头部控制区域 -->
    <div
      class="bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 p-4 flex-shrink-0"
    >
      <div class="flex items-center justify-between">
        <h2
          class="text-xl font-semibold text-slate-900 dark:text-white flex items-center gap-2"
        >
          <Terminal class="h-5 w-5 text-blue-500 dark:text-cyan-500" />
          运行日志
        </h2>
        <div class="flex items-center gap-4">
          <!-- 搜索框 -->
          <div class="flex items-center gap-2">
            <div class="relative">
              <input
                ref="searchInputRef"
                v-model="searchKeyword"
                type="text"
                placeholder="输入关键字搜索日志..."
                class="bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md px-3 py-1 pr-8 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-cyan-500 w-64"
                @input="onSearchInput"
              />
              <button
                v-if="searchKeyword"
                @click="clearSearch"
                class="absolute right-2 top-1/2 transform -translate-y-1/2 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              >
                <X class="h-4 w-4" />
              </button>
            </div>
          </div>
          <!-- 筛选器 -->
          <div class="flex items-center gap-2">
            <label class="text-sm text-slate-700 dark:text-slate-300"
              >筛选:</label
            >
            <select
              v-model="selectedFilter"
              class="bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md px-3 py-1 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-cyan-500"
            >
              <option value="all">全部日志</option>
              <option
                v-for="script in availableScripts"
                :key="script"
                :value="script"
              >
                {{ script }}
              </option>
            </select>
          </div>
          <!-- 清空日志按钮 -->
          <button
            @click="clearPageLogsOnly"
            class="flex items-center gap-1 px-3 py-1 bg-red-500 dark:bg-red-500 hover:bg-red-600 dark:hover:bg-red-600 text-white text-sm rounded-md transition-colors"
          >
            <Trash2 class="h-4 w-4" />
            清空
          </button>
        </div>
      </div>
    </div>

    <!-- 日志显示区域 -->
    <div class="h-[calc(100vh-340px)] min-h-0 bg-white dark:bg-slate-900 p-4">
      <div
        ref="logContainer"
        class="h-full overflow-y-auto bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 font-mono text-sm max-w-full"
      >
        <div
          v-if="filteredLogs.length === 0"
          class="text-slate-500 dark:text-slate-400 text-center py-8"
        >
          暂无日志
        </div>
        <div
          v-for="(log, index) in filteredLogs"
          :key="index"
          :class="getLogItemClass(log.type)"
        >
          <div class="flex items-start gap-2 min-w-0">
            <span
              class="text-slate-500 dark:text-slate-400 text-xs font-mono flex-shrink-0 font-medium"
              >{{ log.timestamp }}</span
            >
            <span
              v-if="log.scriptName"
              class="text-blue-500 dark:text-cyan-400 text-xs font-mono flex-shrink-0 font-semibold"
              >[{{ log.scriptName }}]</span
            >
            <span
              class="flex-1 log-message"
              :class="getTextClass(log.type)"
              v-html="getHighlightedMessage(log.message, index)"
            ></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部状态栏 -->
    <div
      class="bg-slate-100 dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 px-4 py-2 flex-shrink-0"
    >
      <div
        class="flex items-center justify-between text-sm text-slate-700 dark:text-slate-300"
      >
        <div class="flex items-center gap-4">
          <span class="font-medium">总计: {{ logs.length }} 条日志</span>
          <span class="font-medium">显示: {{ filteredLogs.length }} 条</span>
          <span
            v-if="searchKeyword"
            class="text-yellow-600 dark:text-yellow-400 font-semibold"
          >
            搜索: "{{ searchKeyword }}" 找到 {{ searchResultCount }} 条匹配
          </span>
          <span
            v-if="!searchKeyword"
            class="text-slate-500 dark:text-slate-400 text-xs font-medium"
          >
            快捷键: Ctrl+F 搜索
          </span>
        </div>
        <div v-if="searchKeyword" class="flex items-center gap-2">
          <button
            @click="scrollToNextMatch"
            class="px-2 py-1 bg-yellow-500 dark:bg-yellow-500 hover:bg-yellow-600 dark:hover:bg-yellow-600 text-white text-xs rounded transition-colors"
            :disabled="searchResultCount === 0"
          >
            下一个
          </button>
          <button
            @click="scrollToPrevMatch"
            class="px-2 py-1 bg-yellow-500 dark:bg-yellow-500 hover:bg-yellow-600 dark:hover:bg-yellow-600 text-white text-xs rounded transition-colors"
            :disabled="searchResultCount === 0"
          >
            上一个
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { Terminal, Trash2, X } from "lucide-vue-next";
import {
  ref,
  computed,
  onMounted,
  onActivated,
  onDeactivated,
  nextTick,
} from "vue";
import { useMagicKeys, whenever } from "@vueuse/core";
import { confirm } from "@/utils/confirm";
import { message } from "@/utils/message";

defineOptions({
  name: "Log",
});

// #region 日志管理功能
// 接口类型定义
interface LogEntry {
  id: string;
  timestamp: string;
  scriptName?: string;
  type: "stdout" | "stderr" | "system";
  message: string;
}

// 响应式数据
const logs = ref<LogEntry[]>([]);
const logContainer = ref<HTMLElement>();
const isAutoScroll = ref(true);
let refreshTimer: NodeJS.Timeout | null = null;
let lastFileSize = 0;
let scrollTimer: NodeJS.Timeout | null = null;

// 计算属性
const availableScripts = computed(() => {
  const scripts = new Set<string>();
  logs.value.forEach((log) => {
    if (log.scriptName) {
      scripts.add(log.scriptName);
    }
  });
  return Array.from(scripts).sort();
});

const addSystemLog = (message: string) => {
  const logEntry: LogEntry = {
    id: `${Date.now()}-${Math.random()}`,
    timestamp: new Date().toLocaleTimeString(),
    type: "system",
    message,
  };

  logs.value.push(logEntry);

  if (isAutoScroll.value) {
    nextTick(() => {
      scrollToBottom();
    });
  }
};

const scrollToBottom = () => {
  if (logContainer.value) {
    logContainer.value.scrollTo({
      top: logContainer.value.scrollHeight,
      behavior: "smooth",
    });
  }
};

const debouncedScrollToBottom = () => {
  if (scrollTimer) {
    clearTimeout(scrollTimer);
  }
  scrollTimer = setTimeout(() => {
    if (isAutoScroll.value) {
      scrollToBottom();
    }
  }, 100); // 100ms 防抖延迟
};
// #endregion

// #region 搜索功能
// 响应式数据
const searchKeyword = ref("");
const currentMatchIndex = ref(0);
const searchInputRef = ref<HTMLInputElement>();

// 计算属性
const filteredLogs = computed(() => {
  let filtered = logs.value;

  // 按脚本筛选
  if (selectedFilter.value !== "all") {
    filtered = filtered.filter(
      (log) => log.scriptName === selectedFilter.value
    );
  }

  // 按关键字搜索
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase();
    filtered = filtered.filter(
      (log) =>
        log.message.toLowerCase().includes(keyword) ||
        (log.scriptName && log.scriptName.toLowerCase().includes(keyword))
    );
  }

  return filtered;
});

const searchResultCount = computed(() => {
  if (!searchKeyword.value.trim()) return 0;
  const keyword = searchKeyword.value.toLowerCase();
  return logs.value.filter(
    (log) =>
      log.message.toLowerCase().includes(keyword) ||
      (log.scriptName && log.scriptName.toLowerCase().includes(keyword))
  ).length;
});

// 方法
const onSearchInput = () => {
  currentMatchIndex.value = 0;
};

const clearSearch = () => {
  searchKeyword.value = "";
  currentMatchIndex.value = 0;
};

const getHighlightedMessage = (text: string, logIndex: number) => {
  if (!searchKeyword.value.trim()) {
    return text;
  }
  return highlightSearchKeyword(text, logIndex);
};

const highlightSearchKeyword = (text: string, logIndex: number) => {
  const keyword = searchKeyword.value;
  const regex = new RegExp(`(${keyword})`, "gi");
  const isCurrentActiveLog = logIndex === currentMatchIndex.value;
  const highlightClass = isCurrentActiveLog
    ? "bg-yellow-500 dark:bg-yellow-500 text-white px-1 rounded font-bold shadow-sm"
    : "bg-yellow-400 dark:bg-yellow-400/70 text-white px-1 rounded font-semibold";

  return text.replace(regex, `<mark class="${highlightClass}">$1</mark>`);
};

const scrollToNextMatch = () => {
  const matches = filteredLogs.value;
  if (matches.length === 0) return;

  currentMatchIndex.value = (currentMatchIndex.value + 1) % matches.length;
  scrollToMatch(currentMatchIndex.value);
};

const scrollToPrevMatch = () => {
  const matches = filteredLogs.value;
  if (matches.length === 0) return;

  currentMatchIndex.value =
    currentMatchIndex.value === 0
      ? matches.length - 1
      : currentMatchIndex.value - 1;
  scrollToMatch(currentMatchIndex.value);
};

const scrollToMatch = (index: number) => {
  const matches = filteredLogs.value;
  if (index >= 0 && index < matches.length) {
    const logElement = logContainer.value?.children[index] as HTMLElement;
    if (logElement) {
      logElement.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }
};

const focusSearchInput = () => {
  if (searchInputRef.value) {
    searchInputRef.value.focus();
    searchInputRef.value.select();
  }
};
// #endregion

// #region 筛选功能
// 响应式数据
const selectedFilter = ref("all");
// #endregion

// #region 样式功能
// 方法
const getLogItemClass = (type: string) => {
  const baseClass = "mb-2 px-3 py-2 rounded-md border break-all";
  const typeClass = getLogClass(type);
  return `${baseClass} ${typeClass}`;
};

const getLogClass = (type: string) => {
  switch (type) {
    case "stdout":
      return "bg-slate-100 dark:bg-slate-700/50 border-l-4 border-green-500 dark:border-green-500 hover:bg-slate-200 dark:hover:bg-slate-700/70";
    case "stderr":
      return "bg-slate-100 dark:bg-slate-700/50 border-l-4 border-red-500 dark:border-red-500 hover:bg-slate-200 dark:hover:bg-slate-700/70";
    case "system":
      return "bg-slate-100 dark:bg-slate-700/50 border-l-4 border-blue-500 dark:border-cyan-500 hover:bg-slate-200 dark:hover:bg-slate-700/70";
    default:
      return "bg-slate-100 dark:bg-slate-700/50 hover:bg-slate-200 dark:hover:bg-slate-700/70";
  }
};

const getTextClass = (type: string) => {
  switch (type) {
    case "stdout":
      return "text-green-600 dark:text-green-400";
    case "stderr":
      return "text-red-600 dark:text-red-400";
    case "system":
      return "text-blue-600 dark:text-cyan-400";
    default:
      return "text-slate-900 dark:text-slate-100";
  }
};
// #endregion

// #region 页面控制功能
// 方法
const initPageLogs = () => {
  logs.value = [];
  addSystemLog("日志系统已启动");
};

const clearPageLogsOnly = async () => {
  // 显示确认对话框
  const result = await confirm.warning(
    "确定要清空所有日志吗？此操作不可撤销。",
    "清空日志确认"
  );
  if (!result.confirmed) {
    return;
  }

  try {
    // 清空cache/log.txt文件
    const result = await window.electronAPI.clearLogFile();
    if (result.success) {
      // 清空页面显示
      logs.value = [];
      addSystemLog("日志文件和页面显示已清空");
      message.success("日志清空成功");
    } else {
      addSystemLog(`清空日志文件失败: ${result.error}`);
      message.error(`清空日志文件失败: ${result.error}`);
    }
  } catch (error) {
    console.error("清空日志文件时发生错误:", error);
    addSystemLog("清空日志文件时发生错误");
    message.error("清空日志文件时发生错误");
  }
};
// #endregion

// #region 日志文件处理功能
// 方法
const loadRealtimeLogs = async () => {
  try {
    const result = await window.electronAPI.getRealtimeLogFile();
    if (result.success) {
      // 检查文件大小是否变化
      const currentFileSize = result.content.length;
      if (currentFileSize === lastFileSize) {
        return; // 文件没有变化，不刷新
      }
      lastFileSize = currentFileSize;

      // 清空当前日志
      logs.value = [];

      // 解析日志内容
      const lines = result.content.split("\n").filter((line) => line.trim());

      lines.forEach((line) => {
        // 简单解析日志行格式: [timestamp] [scriptName] [type] message
        if (line.startsWith("[") && line.includes("] [")) {
          // 找到第一个 ] 的位置
          const firstBracketEnd = line.indexOf("] [");
          if (firstBracketEnd > 0) {
            const timestamp = line.substring(1, firstBracketEnd);

            // 找到第二个 ] 的位置
            const secondBracketStart = firstBracketEnd + 3;
            const secondBracketEnd = line.indexOf("] [", secondBracketStart);
            if (secondBracketEnd > secondBracketStart) {
              const scriptName = line.substring(
                secondBracketStart,
                secondBracketEnd
              );

              // 找到第三个 ] 的位置
              const thirdBracketStart = secondBracketEnd + 3;
              const thirdBracketEnd = line.indexOf("] ", thirdBracketStart);
              if (thirdBracketEnd > thirdBracketStart) {
                const type = line.substring(thirdBracketStart, thirdBracketEnd);
                const message = line.substring(thirdBracketEnd + 2);

                // 直接添加到日志数组
                const logEntry: LogEntry = {
                  id: `${Date.now()}-${Math.random()}`,
                  timestamp: new Date(timestamp).toLocaleTimeString(),
                  scriptName,
                  type: type.toLowerCase() as "stdout" | "stderr" | "system",
                  message: message.trim(),
                };
                logs.value.push(logEntry);
              }
            }
          }
        }
      });

      // 解析完成后防抖滚动到底部
      nextTick(() => {
        debouncedScrollToBottom();
      });
    } else {
      console.error("读取实时日志文件失败:", result.error);
    }
  } catch (error) {
    console.error("读取实时日志文件时发生错误:", error);
  }
};
// #endregion

// #region 快捷键功能
// 使用VueUse的useMagicKeys监听快捷键
const keys = useMagicKeys();

// 监听Ctrl+F快捷键
whenever(keys.ctrl_f, () => {
  focusSearchInput();
});

// #endregion

// 生命周期
onMounted(() => {
  // 初始化页面日志
  initPageLogs();
  // 加载实时日志
  loadRealtimeLogs();
});

onActivated(() => {
  // 重新加载实时日志
  loadRealtimeLogs();
  // 开始定时检查文件变化
  refreshTimer = setInterval(() => {
    loadRealtimeLogs();
  }, 500); // 每500毫秒检查一次文件变化
});

onDeactivated(() => {
  // 停止定时刷新
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
  // 清理滚动定时器
  if (scrollTimer) {
    clearTimeout(scrollTimer);
    scrollTimer = null;
  }
});
</script>

<style scoped>
/* 自定义滚动条样式 - 只应用于日志容器 */
.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.dark .overflow-y-auto::-webkit-scrollbar-track {
  background: #1e293b;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.dark .overflow-y-auto::-webkit-scrollbar-thumb {
  background: #475569;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.dark .overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

/* 确保页面本身不出现滚动条 */
.h-screen {
  overflow: auto;
}

/* 强制长文本换行 */
.log-message {
  word-break: break-all;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  max-width: 100%;
}
</style>
