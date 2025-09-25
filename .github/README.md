# GitHub Actions 使用说明

## 工作流说明

### 1. build.yml - 构建工作流
- **触发条件**: 推送标签 (v*) 或手动触发
- **功能**: 在 Windows、macOS、Linux 三个平台上构建 Electron 应用
- **输出**: 各平台的构建产物作为 artifacts

### 2. release.yml - 发布工作流
- **触发条件**: 推送标签 (v*)
- **功能**: 下载所有平台的构建产物并创建 GitHub Release

## 使用方法

### 1. 手动触发构建
1. 进入 GitHub 仓库的 Actions 页面
2. 选择 "Build and Release" 工作流
3. 点击 "Run workflow" 按钮
4. 选择分支并点击 "Run workflow"

### 2. 通过标签发布
1. 创建并推送版本标签：
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. GitHub Actions 会自动：
   - 构建所有平台的应用
   - 创建 GitHub Release
   - 上传构建产物

### 3. 本地开发
```bash
# 安装依赖
pnpm install

# 开发模式
cd frontend
pnpm run dev

# 构建特定平台
pnpm run build:win    # Windows
pnpm run build:mac    # macOS
pnpm run build:linux  # Linux
```

## 注意事项

1. **macOS 构建**: 需要在 macOS 运行器上完成，GitHub Actions 提供免费的 macOS 运行器
2. **代码签名**: macOS 和 Windows 应用可能需要代码签名证书
3. **依赖缓存**: 使用 pnpm 缓存加速构建过程
4. **工作区**: 项目使用 pnpm 工作区管理多个包
