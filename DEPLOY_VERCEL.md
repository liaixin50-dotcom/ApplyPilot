# 部署ApplyPilot到Vercel

本指南将帮助你将ApplyPilot项目部署到Vercel平台，获得永久可访问的固定网址。

## 部署前准备

### 1. 创建GitHub仓库
1. 访问 [GitHub](https://github.com)
2. 点击右上角 "+" → "New repository"
3. 仓库名设为 "ApplyPilot"
4. 选择 "Public"（公开仓库）
5. 不要初始化README（因为已经有项目文件）
6. 点击 "Create repository"

### 2. 上传代码到GitHub
在本地项目目录执行以下命令：

```bash
# 初始化Git仓库
git init
git add .
git commit -m "Initial commit"

# 连接到GitHub仓库
git remote add origin https://github.com/你的用户名/ApplyPilot.git
git branch -M main
git push -u origin main
```

## 部署到Vercel

### 方法1：通过Vercel控制台（推荐）
1. 访问 [Vercel](https://vercel.com)
2. 使用GitHub账号登录
3. 点击 "New Project"
4. 导入你的ApplyPilot仓库
5. Vercel会自动检测配置：
   - 框架：Python
   - 构建命令：自动
   - 输出目录：自动
6. 点击 "Deploy"

### 方法2：使用Vercel CLI
1. 安装Vercel CLI：
   ```bash
   npm install -g vercel
   ```

2. 在项目根目录部署：
   ```bash
   vercel
   ```

3. 按照提示操作：
   - 登录Vercel账号
   - 选择项目设置
   - 确认部署

### 方法3：一键部署按钮
在你的README中添加以下按钮：

```markdown
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/你的用户名/ApplyPilot)
```

## 部署配置说明

### 配置文件
- `vercel.json` - Vercel部署配置
- `api/index.py` - 服务器端渲染的首页
- `requirements.txt` - Python依赖

### 环境变量
Vercel部署不需要特殊环境变量，所有功能都已内置。

## 访问你的网站

部署完成后，你会获得一个永久的Vercel URL：
- `https://applypilot.vercel.app`
- `https://applypilot-你的用户名.vercel.app`

## 自定义域名

如果你想使用自己的域名：
1. 在Vercel项目控制台点击 "Domains"
2. 添加你的域名（例如：applypilot.yourdomain.com）
3. 按照提示配置DNS记录：
   - 添加CNAME记录指向 `cname.vercel-dns.com`
   - 或添加A记录指向Vercel的IP地址

## 自动部署

每次向GitHub仓库的main分支推送代码时，Vercel会自动重新部署。

## 替代方案：Streamlit Cloud

如果你需要完整的Streamlit交互体验，建议使用Streamlit Cloud：

1. 访问 [Streamlit Cloud](https://share.streamlit.io)
2. 使用GitHub账号登录
3. 点击 "New app"
4. 选择你的仓库和文件：
   - Repository: 你的用户名/ApplyPilot
   - Branch: main
   - Main file path: `web_app/frontend/streamlit_app.py`
5. 点击 "Deploy"

## 故障排除

### 常见问题
1. **部署失败**：检查 `requirements.txt` 中的依赖是否正确
2. **页面无法访问**：检查Vercel项目设置中的构建输出
3. **自定义域名不工作**：检查DNS配置，可能需要等待DNS传播

### 技术支持
- Vercel文档：https://vercel.com/docs
- Streamlit Cloud文档：https://docs.streamlit.io/cloud
- ApplyPilot GitHub Issues：https://github.com/Pickle-Pixel/ApplyPilot/issues

## 更新日志
- 2026-06-06：创建Vercel部署指南
- 2026-06-06：添加一键部署配置