<template>
  <div class="log-page flex flex-col bg-slate-900">
    <!-- 头部控制区域 -->
    <div class="bg-slate-800 border-b border-slate-700 p-4 flex-shrink-0">
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold text-white flex items-center gap-2">
          <Terminal class="h-5 w-5 text-cyan-500" />
          运行日志
        </h2>
        <div class="flex items-center gap-4">
          <!-- 筛选器 -->
          <div class="flex items-center gap-2">
            <label class="text-sm text-slate-300">筛选:</label>
            <select
              v-model="selectedFilter"
              class="bg-slate-700 border border-slate-600 rounded-md px-3 py-1 text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
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
            class="flex items-center gap-1 px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded-md transition-colors"
          >
            <Trash2 class="h-4 w-4" />
            清空
          </button>
        </div>
      </div>
    </div>

    <!-- 日志显示区域 -->
    <div class="h-[calc(100vh-305px)] min-h-0 bg-slate-900 p-4">
      <div
        ref="logContainer"
        class="h-full overflow-y-auto bg-slate-800 rounded-lg border border-slate-700 p-4 font-mono text-sm max-w-full"
      >
        <div
          v-if="filteredLogs.length === 0"
          class="text-slate-500 text-center py-8"
        >
          暂无日志
        </div>
        <div
          v-for="(log, index) in filteredLogs"
          :key="index"
          :class="[
            'mb-2 px-3 py-2 rounded-md border break-all',
            getLogClass(log.type),
          ]"
        >
          <div class="flex items-start gap-2 min-w-0">
            <span class="text-slate-400 text-xs font-mono flex-shrink-0">{{
              log.timestamp
            }}</span>
            <span
              v-if="log.scriptName"
              class="text-cyan-400 text-xs font-mono flex-shrink-0"
              >[{{ log.scriptName }}]</span
            >
            <span class="flex-1 log-message" :class="getTextClass(log.type)">{{
              log.message
            }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部状态栏 -->
    <div class="bg-slate-800 border-t border-slate-700 px-4 py-2 flex-shrink-0">
      <div class="flex items-center justify-between text-sm text-slate-400">
        <span>总计: {{ logs.length }} 条日志</span>
        <span>显示: {{ filteredLogs.length }} 条</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { Terminal, Trash2 } from "lucide-vue-next";
import {
  ref,
  computed,
  onMounted,
  onUnmounted,
  onActivated,
  onDeactivated,
  nextTick,
} from "vue";

defineOptions({
  name: "Log",
});

// 日志接口定义
interface LogEntry {
  id: string;
  timestamp: string;
  scriptName?: string;
  type: "stdout" | "stderr" | "system";
  message: string;
}

// 响应式数据
const logs = ref<LogEntry[]>([]);
const selectedFilter = ref("all");
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

const filteredLogs = computed(() => {
  if (selectedFilter.value === "all") {
    return logs.value;
  } else {
    return logs.value.filter((log) => log.scriptName === selectedFilter.value);
  }
});

// 日志处理方法
const addLog = (logData: any) => {
  const { scriptName, type, data: message, timestamp } = logData;

  const logEntry: LogEntry = {
    id: `${Date.now()}-${Math.random()}`,
    timestamp: new Date(timestamp).toLocaleTimeString(),
    scriptName,
    type,
    message: message.trim().replace(/^\uFEFF/, ""),
  };

  logs.value.push(logEntry);

  // 自动滚动到底部
  if (isAutoScroll.value) {
    nextTick(() => {
      scrollToBottom();
    });
  }
};

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

// 防抖滚动函数
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

// 样式方法
const getLogClass = (type: string) => {
  switch (type) {
    case "stdout":
      return "bg-slate-800/50 border-l-4 border-green-500 hover:bg-slate-800/70";
    case "stderr":
      return "bg-slate-800/50 border-l-4 border-red-500 hover:bg-slate-800/70";
    case "system":
      return "bg-slate-800/50 border-l-4 border-blue-500 hover:bg-slate-800/70";
    default:
      return "bg-slate-800/50 hover:bg-slate-800/70";
  }
};

const getTextClass = (type: string) => {
  switch (type) {
    case "stdout":
      return "text-green-200";
    case "stderr":
      return "text-red-200";
    case "system":
      return "text-blue-200";
    default:
      return "text-slate-200";
  }
};

// Python 输出处理函数
const handlePythonOutput = (event: any) => {
  const data = event.detail || event;
  console.log("日志页面收到 Python 输出:", data);
  addLog(data);
};

// 初始化页面日志（不加载历史）
const initPageLogs = () => {
  logs.value = [];
  addSystemLog("日志系统已启动");
};

// 清空页面日志（只清空页面显示）
const clearPageLogsOnly = () => {
  logs.value = [];
  addSystemLog("页面日志已清空");
};

// 清空页面日志显示（只清空页面，不影响文件）
const clearPageLogs = () => {
  logs.value = [];
  addSystemLog("开始新的脚本执行");
};

// 读取实时日志文件
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
      console.log(`文件变化，开始解析 ${lines.length} 行日志`);

      lines.forEach((line, index) => {
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
                console.log(`解析成功第${index + 1}行:`, {
                  timestamp,
                  scriptName,
                  type,
                  message,
                });
              }
            }
          }
        } else {
          console.log(
            `跳过第${index + 1}行（格式不匹配）:`,
            line.substring(0, 50)
          );
        }
      });

      console.log(`成功加载 ${logs.value.length} 条实时日志`);

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

// 生命周期
onMounted(() => {
  console.log("日志页面挂载");
  // 初始化页面日志
  initPageLogs();
  // 加载实时日志
  loadRealtimeLogs();
});

onUnmounted(() => {
  console.log("日志页面卸载");
});

onActivated(() => {
  console.log("日志页面激活");
  // 重新加载实时日志
  loadRealtimeLogs();
  addSystemLog("日志页面已激活");

  // 开始定时检查文件变化
  refreshTimer = setInterval(() => {
    loadRealtimeLogs();
  }, 500); // 每500毫秒检查一次文件变化
});

onDeactivated(() => {
  console.log("日志页面停用");
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
  background: #1e293b;
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

/* 确保页面本身不出现滚动条 */
.h-screen {
  overflow: hidden;
}

/* 强制长文本换行 */
.log-message {
  word-break: break-all;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  max-width: 100%;
}
</style>
