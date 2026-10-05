# Telegram 转发工具 v20 · Telegram Forwarder v20

> Telegram 频道消息转发工具：AI 洗稿 + 智能相册处理 + 关键词过滤替换，Windows 一键运行。

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/GUI-tkinter-green.svg" alt="GUI tkinter">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License MIT">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

<p align="center">
  <a href="https://github.com/yuanze68-cell/telegram-forwarder-v20/releases">下载最新版</a> ·
  <a href="#-功能特性">功能特性</a> ·
  <a href="#-安装">安装</a> ·
  <a href="#-使用指南">使用指南</a> ·
  <a href="#-常见问题">常见问题</a>
</p>

**关键词**：Telegram 转发 · TG 频道转发 · telegram forwarder · telethon · 频道消息搬运 · AI 洗稿 · 相册转发 · 关键词替换 · 定时批量转发 · 多账号

---

## 📋 目录

- [功能特性](#-功能特性)
- [截图](#-截图)
- [下载](#-下载)
- [安装](#-安装)
- [配置](#-配置)
- [使用指南](#-使用指南)
- [AI 洗稿](#-ai-洗稿)
- [高级功能](#-高级功能)
- [常见问题](#-常见问题)
- [更新日志](#-更新日志)
- [贡献](#-贡献)
- [许可证](#-许可证)

---

## 🌟 功能特性

### 核心功能
- ✅ **消息转发**：从公开频道转发消息到目标频道，支持 `https://t.me/xxx/123` 链接解析
- ✅ **相册处理**：按 `grouped_id` 智能分组转发相册
- ✅ **AI 洗稿**：支持 9 个 AI 平台（DeepSeek、OpenAI、Claude、Gemini、智谱 GLM、百川智能、通义千问、OpenRouter、Ollama）
- ✅ **关键词过滤**：包含 / 删除 / 替换关键词
- ✅ **消息范围控制**：按起始 / 结束消息 ID 精确转发
- ✅ **配置持久化**：保存到 `config.ini`
- ✅ **多账号 / 多目标 / 批量任务 / 定时任务 / 克隆评论区**

### 智能相册洗稿模式
- 🎯 **智能模式（推荐）**：自动选择最佳洗稿方式
- 🚀 **简单模式**：快速转发相册后额外发送洗稿文案
- 🔄 **完整模式**：下载媒体重新上传（未实现，暂用简单模式）

---

## 📸 截图

> 💡 把程序截图放进仓库根目录并命名为 `screenshot_main.png` / `screenshot_ai.png`，下面两行才会显示；
> 没有截图就先删掉这两行，**不要留坏图**（坏图会降低仓库质量评分）。

<!-- 有截图后再取消注释：
![主界面](screenshot_main.png)
![AI 洗稿配置](screenshot_ai.png)
-->

---

## ⬇️ 下载

- **EXE 版（推荐，无需装 Python）**：见 [Releases](https://github.com/yuanze68-cell/telegram-forwarder-v20/releases)
- **源码版**：`git clone` 本仓库后运行 `Start_Telegram_Forwarder_v20.bat`

---

## 💻 安装

### 方法 1：直接运行（推荐）

#### 1. 安装 Python 3.8+
- 下载：https://www.python.org/downloads/
- ✅ 勾选 "Add Python to PATH"

#### 2. 安装依赖
```bash
pip install telethon
```

#### 3. 下载项目
```bash
git clone https://github.com/yuanze68-cell/telegram-forwarder-v20.git
cd telegram-forwarder-v20
```

#### 4. 运行程序
**Windows:**
```bash
Start_Telegram_Forwarder_v20.bat
```
**macOS / Linux:**
```bash
python3 telegram_forwarder_v20.py
```

---

### 方法 2：打包为 EXE（高级用户）

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "TelegramForwarder" telegram_forwarder_v20.py
```
生成的 EXE 在 `dist\` 目录。

---

## ⚙️ 配置

### 1. 获取 Telegram API 凭证
1. 访问 https://my.telegram.org
2. 登录你的 Telegram 账号
3. 点击 **"API development tools"**
4. 填写应用信息（App title：`Telegram Forwarder`；Short name：`forwarder`；Platform：`Desktop`）
5. 点击 **"Create application"**
6. 复制 `api_id` 和 `api_hash`

### 2. 配置程序
1. 切换到 **"API 配置"** 选项卡
2. 填写 **API ID** / **API Hash** / **手机号**（含国际区号，如 `+8613800138000`）
3. 点击 **"测试 API 连接"**，成功后 **"保存到配置"**

> ⚠️ 请务必使用自己的 API 凭证，不要使用他人泄露的 api_id / api_hash。

---

## 📖 使用指南

### 基本转发
1. 切换到 **"转发"** 选项卡
2. 填写：
   - **源频道**：公开频道用户名（如 `@source_channel`）或消息链接（`https://t.me/xxx/123`）
   - **目标频道**：你的频道用户名（如 `@your_channel`）
   - **起始消息 ID**：从哪条开始（留空从最新开始）
   - **结束消息 ID**：转发到哪条（留空转发所有）
3. 点击 **"开始转发"**

### 登录验证
首次使用需要登录 Telegram：点 **"登录"** → 输入手机号和验证码 → 有两步验证的再输入密码。

---

## 🤖 AI 洗稿

### 支持的 AI 平台

| 平台 | 模型示例 | API Key 获取地址 |
|------|---------|-----------------|
| **DeepSeek** | `deepseek-chat` | https://platform.deepseek.com/ |
| **OpenAI** | `gpt-3.5-turbo` | https://platform.openai.com/ |
| **Claude** | `claude-3-opus-20240229` | https://console.anthropic.com/ |
| **Gemini** | `gemini-1.5-pro` | https://aistudio.google.com/ |
| **智谱 GLM** | `glm-4-flash` | https://open.bigmodel.cn/ |
| **百川智能** | `Baichuan4-Turbo` | https://api.baichuan-ai.com/ |
| **通义千问** | `qwen-turbo` | https://dashscope.aliyun.com/ |
| **OpenRouter** | `openai/gpt-3.5-turbo` | https://openrouter.ai/ |
| **Ollama** | `llama3` | 本地部署 |

### 配置 AI 洗稿
1. 切换到 **"AI 洗稿"** 选项卡
2. 勾选 **"启用 AI 洗稿"**
3. 选择 **AI 平台**（下拉框没有就手动填 API URL 和模型名）
4. 填写 **API Key** / **API URL** / **模型名称**
5. 点击 **"测试连接"**，成功后 **"保存 AI 配置"**

### 默认提示词
```
请改写以下 Telegram 消息文案，要求：
1. 保持原意和核心信息
2. 用不同的表达方式重写
3. 避免改变专业术语和关键数据
4. 输出洗稿后的文案，不要添加任何解释

原文案：
{caption}
```

---

## 🔧 高级功能

### 关键词过滤
- **包含关键词**：只转发包含这些词的消息，逗号分隔（如 `AI,人工智能,机器学习`）
- **删除关键词**：从文案中移除这些词，逗号分隔（如 `广告,推广,点击链接`）
- **替换关键词**：`原词1=新词1,原词2=新词2`（如 `人工智能=AI,机器学习=ML`）

### 消息范围控制
- **起始 ID > 结束 ID**：程序自动交换
- **留空起始 ID**：从最新消息开始
- **留空结束 ID**：转发所有消息

### 隐藏发送者姓名
勾选 **"隐藏发送者姓名"** 后，转发消息不显示 "Forwarded from @username"。

---

## ❓ 常见问题

**1. 登录没反应？** 检查 API ID / API Hash、网络（可能需代理），看「日志」选项卡。

**2. AI 洗稿不工作？** 检查 API Key 与 URL，点「测试连接」验证，看日志里的 `[AI]` 标记。

**3. 相册转发重复？** 已知限制：`forward_messages()` 无法改相册文案，当前方案是转发后补一条洗稿文案（共 2 条）。

**4. 程序闪退？** 查看目录下 `error_log.txt`，或在命令行运行看报错。

**5. 如何更新？**
```bash
cd telegram-forwarder-v20
git pull origin main
```

---

## 📅 更新日志

### v20 (2026-06-22)
- ✅ 智能相册洗稿模式（智能/简单/完整）
- ✅ 支持 9 个 AI 平台
- ✅ 自动模型更新
- ✅ 修复消息链接解析
- ✅ 优化事件循环架构

### v19 (2026-06-21)
- ✅ AI 洗稿、关键词过滤 / 替换、配置保存

### v12 (2026-06-21)
- ✅ 基本转发、相册分组、消息范围控制、隐藏发送者

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

```bash
git clone https://github.com/yuanze68-cell/telegram-forwarder-v20.git
cd telegram-forwarder-v20
pip install -r requirements.txt
python telegram_forwarder_v20.py
```

- Python 3.8+ 兼容
- 使用 `black` 格式化代码
- 添加必要的注释

---

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

> ⚠️ 当前仓库还没有 `LICENSE` 文件，但徽章写的是 MIT。请补一个 MIT 的 `LICENSE` 文件
> （GitHub 仓库页 → Add file → Create new file → 文件名填 `LICENSE` → 选 "MIT License" 模板），
> 否则会影响项目的可信度与收录。

---

## 🙏 致谢

- [Telethon](https://github.com/LonamiWebs/Telethon) — Telegram Python 框架
- [tkinter](https://docs.python.org/3/library/tkinter.html) — Python GUI 库
- 所有贡献者和使用者

---

## 📧 联系方式

- **Issues**: https://github.com/yuanze68-cell/telegram-forwarder-v20/issues
- **Telegram**: https://t.me/zzbzf1

---

<p align="center">
  ⭐ 如果这个项目对你有帮助，请给它一个 Star！ ⭐
</p>
