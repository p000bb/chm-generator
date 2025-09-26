# CHM文档生成工具 - 前端

> 专业的CHM帮助文档生成解决方案前端界面

## 📖 项目概述

这是CHM文档生成工具的前端部分，基于Electron + Vue 3 + TypeScript构建的现代化桌面应用程序。该工具专为国民技术微控制器产品设计，能够将芯片相关的技术文档、示例代码、应用笔记等资源自动整合，生成标准化的CHM帮助文档。

## ✨ 主要特性

- 🖥️ **跨平台支持** - 支持Windows、macOS、Linux
- ⚡ **现代化技术栈** - Vue 3 + TypeScript + Vite + Electron
- 🎨 **优雅的UI设计** - 基于Tailwind CSS的现代化界面
- 📱 **响应式布局** - 适配不同屏幕尺寸
- 🔧 **实时脚本管理** - 可视化脚本执行和监控
- 📊 **详细日志系统** - 实时查看执行状态和错误信息
- ⚙️ **灵活配置管理** - 支持芯片配置和路径管理
- 🔄 **热重载开发** - 快速开发和调试体验

## 🛠️ 技术栈

### 核心框架
- **Vue 3** - 渐进式JavaScript框架
- **TypeScript** - 类型安全的JavaScript超集
- **Vite** - 下一代前端构建工具
- **Electron** - 跨平台桌面应用框架

### UI & 样式
- **Tailwind CSS** - 实用优先的CSS框架
- **SCSS** - CSS预处理器
- **Lucide Vue Next** - 现代化图标库

### 开发工具
- **Vue Router** - 官方路由管理器
- **VueUse** - Vue组合式API工具集
- **Vue TSC** - Vue TypeScript编译器
- **Electron Builder** - 应用打包工具

## 📁 项目结构

```
frontend/
├── electron/                 # Electron主进程和预加载脚本
│   ├── main/                # 主进程代码
│   └── preload/             # 预加载脚本
├── src/                     # 前端源码
│   ├── components/          # 可复用组件
│   │   ├── CustomTitleBar.vue    # 自定义标题栏
│   │   ├── FileSelect.vue        # 文件选择组件
│   │   ├── MarkdownRender.vue    # Markdown渲染组件
│   │   └── ...
│   ├── views/               # 页面组件
│   │   ├── script/          # 脚本管理页面
│   │   ├── setting.vue      # 配置管理页面
│   │   └── log.vue          # 运行日志页面
│   ├── layout/              # 布局组件
│   ├── router/              # 路由配置
│   ├── utils/               # 工具函数
│   └── assets/              # 静态资源
├── public/                  # 公共资源
├── dist/                    # 构建输出目录
├── dist-electron/           # Electron构建输出
└── release/                 # 发布包目录
```

## 🚀 快速开始

### 环境要求

- **Node.js** >= 18.0.0
- **pnpm** >= 8.0.0 (推荐) 或 npm >= 9.0.0
- **Python** >= 3.8 (用于后端脚本执行)

### 安装依赖

```bash
# 使用pnpm (推荐)
pnpm install

# 或使用npm
npm install
```

### 开发模式

```bash
# 启动开发服务器
pnpm dev

# 或
npm run dev
```

开发服务器将在 `http://127.0.0.1:3344/` 启动，支持热重载。

### 构建应用

```bash
# 构建所有平台
pnpm build

# 构建Windows版本
pnpm build:win

# 构建macOS版本
pnpm build:mac

# 构建Linux版本
pnpm build:linux
```

### 预览构建结果

```bash
pnpm preview
```

## 📱 功能模块

### 1. 脚本管理页面 (`/script`)

主要的文档生成工作界面，包含：

- **输入源配置** - 选择包含芯片文档的源文件夹
- **芯片配置** - 填写芯片名称、版本等信息
- **输出目标** - 设置CHM文档输出位置
- **脚本选择** - 支持组合脚本和单独脚本两种模式
- **执行监控** - 实时查看脚本执行状态和进度

### 2. 配置管理页面 (`/setting`)

系统配置管理界面：

- **芯片配置管理** - 编辑基础配置和文档类型
- **路径配置** - 设置默认输入输出路径
- **翻译配置** - 管理技术术语翻译
- **系统设置** - 其他应用配置选项

### 3. 运行日志页面 (`/log`)

日志查看和管理：

- **实时日志** - 查看当前脚本执行输出
- **历史记录** - 查看所有执行历史
- **日志导出** - 导出日志文件
- **错误诊断** - 快速定位问题

## 🔧 开发指南

### 代码规范

- 使用TypeScript进行类型检查
- 遵循Vue 3 Composition API规范
- 使用ESLint和Prettier进行代码格式化
- 组件命名采用PascalCase
- 文件命名采用kebab-case

### 组件开发

```vue
<template>
  <div class="component-name">
    <!-- 组件模板 -->
  </div>
</template>

<script setup lang="ts">
// 组件逻辑
defineOptions({
  name: 'ComponentName'
})
</script>

<style scoped lang="scss">
// 组件样式
</style>
```

### 路由配置

```typescript
// src/router/index.ts
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '/script',
        name: 'Script',
        component: () => import('../views/script/index.vue'),
        meta: { title: '脚本管理' }
      }
    ]
  }
]
```

### Electron API调用

```typescript
// 调用主进程API
const result = await window.electronAPI.runPythonScript(
  scriptName,
  inputFolder,
  outputFolder,
  chipConfig
)
```

## 📦 构建配置

### Vite配置

- 支持Vue 3和TypeScript
- 配置了路径别名 `@` 和 `@config`
- 集成了Electron插件
- 支持Markdown文件作为资源

### Electron Builder配置

- 支持Windows (NSIS + Portable)
- 支持macOS (DMG)
- 支持Linux (AppImage)
- 自动打包Python环境和工具

## 🐛 调试

### VS Code调试

1. 安装VS Code扩展：
   - Vue Language Features (Volar)
   - TypeScript Vue Plugin (Volar)

2. 使用调试配置：
   - 按F5启动调试
   - 支持断点调试和变量查看

### 开发工具

- **Vue DevTools** - Vue组件调试
- **Electron DevTools** - Electron应用调试
- **Network面板** - 网络请求监控

**注意**：本前端应用需要配合Python后端脚本使用，请确保已正确配置Python环境和相关依赖。
