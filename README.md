# telegram-forwarder-v20
Telegram channel forwarder with AI rewrite and smart album handling
# Telegram Forwarder v20 - Smart Album Rewrite

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/GUI-tkinter-green.svg" alt="GUI tkinter">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License MIT">
</p>

一个功能强大的 Telegram 频道消息转发工具，支持 AI 洗稿、智能相册处理、关键词过滤和替换。

## 📋 目录

- [功能特性](#功能特性)
- [截图](#截图)
- [安装](#安装)
- [配置](#配置)
- [使用指南](#使用指南)
- [AI 洗稿](#ai-洗稿)
- [高级功能](#高级功能)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [贡献](#贡献)
- [许可证](#许可证)

---

## 🌟 功能特性

### 核心功能
- ✅ **消息转发**：从公开频道转发消息到目标频道
- ✅ **相册处理**：按 `grouped_id` 智能分组转发相册
- ✅ **AI 洗稿**：支持 9 个 AI 平台（DeepSeek、OpenAI、Claude、Gemini、智谱 GLM、百川智能、通义千问、OpenRouter、Ollama）
- ✅ **关键词过滤**：包含/删除/替换关键词
- ✅ **消息链接解析**：支持 `https://t.me/xxx/123` 格式
- ✅ **配置持久化**：保存到 `config.ini`

### 智能相册洗稿模式
- 🎯 **智能模式（推荐）**：自动选择最佳洗稿方式
- 🚀 **简单模式**：快速转发相册后额外发送洗稿文案
- 🔄 **完整模式**：下载媒体重新上传（未实现，暂用简单模式）

---

## 📸 截图

> 💡 **提示**：你可以在这里添加程序运行截图（GUI 界面、转发效果等）

![主界面](screenshot_main.png)
![AI 洗稿配置](screenshot_ai.png)

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
git clone https://github.com/YOUR_USERNAME/telegram-forwarder-v20.git
cd telegram-forwarder-v20
```
本仓库内的所有文件下载在本地后点击：Start_Telegram_Forwarder_v20.bat

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
4. 填写应用信息：
   - **App title**: `Telegram Forwarder`
   - **Short name**: `forwarder`
   - **Platform**: `Desktop`
5. 点击 **"Create application"**
6. 复制 `api_id` 和 `api_hash`

### 2. 配置程序

启动程序后：

1. 切换到 **"API 配置"** 选项卡
2. 填写：
   - **API ID**: 你的 `api_id`（数字）
   - **API Hash**: 你的 `api_hash`（字符串）
   - **手机号**: 你的 Telegram 手机号（含国际区号，如 `+8613800138000`）
3. 点击 **"测试 API 连接"**
4. 如果成功，点击 **"保存到配置"**

如果不会操作，本软件已经默认配置了
---

## 📖 使用指南

### 基本转发

1. 切换到 **"转发"** 选项卡
2. 填写：
   - **源频道**: 公开频道用户名（如 `@source_channel`）或消息链接（`https://t.me/xxx/123`）
   - **目标频道**: 你的频道用户名（如 `@wumaav885`）
   - **起始消息 ID**: 从哪条消息开始转发（留空从最新开始）
   - **结束消息 ID**: 转发到哪条消息（留空转发所有）
3. 点击 **"开始转发"**

### 登录验证

首次使用需要登录 Telegram：
1. 点击 **"登录"** 按钮
2. 输入手机号和验证码
3. 如果账号有两步验证，输入密码

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
3. 选择 **AI 平台**（如下拉框中没有，手动填写 API URL 和模型名称）
4. 填写：
   - **API Key**: 你的 API Key
   - **API URL**: API 地址（大部分平台可自动填充）
   - **模型名称**: 使用的模型（可自动更新）
5. 点击 **"测试连接"**
6. 如果成功，点击 **"保存 AI 配置"**

### AI 洗稿提示词

程序使用以下提示词进行洗稿：

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

#### 包含关键词
- 用途：只转发包含特定关键词的消息
- 格式：关键词用逗号分隔（如 `AI,人工智能,机器学习`）
- 匹配：消息文案或媒体说明包含任一关键词即转发

#### 删除关键词
- 用途：删除文案中的特定词语
- 格式：关键词用逗号分隔（如 `广告,推广,点击链接`）
- 效果：从文案中移除这些词语（区分大小写）

#### 替换关键词
- 用途：替换文案中的词语
- 格式：`原词1=新词1,原词2=新词2`（如 `人工智能=AI,机器学习=ML`）
- 效果：将文案中的原词替换为新词

### 消息范围控制

- **起始消息 ID > 结束消息 ID**：程序自动交换
- **留空起始 ID**：从最新消息开始
- **留空结束 ID**：转发所有消息

### 隐藏发送者姓名

勾选 **"隐藏发送者姓名"** 后，转发的消息不会显示 "Forwarded from @username"。

---

## ❓ 常见问题

### 1. 登录没反应？
- 检查 API ID 和 API Hash 是否正确
- 检查网络连接（可能需要代理）
- 查看日志选项卡的错误信息

### 2. AI 洗稿不工作？
- 检查 API Key 是否正确
- 检查 API URL 是否填写正确
- 点击 **"测试连接"** 验证
- 查看日志中的 `[AI]` 标记信息

### 3. 相册转发重复？
- 这是已知问题：相册转发使用 `forward_messages()` 无法修改文案
- 当前方案：转发相册后额外发送一条洗稿文案（共 2 条消息）
- 未来计划：下载媒体重新上传（完整模式）

### 4. 程序闪退？
- 查看是否生成 `error_log.txt`
- 在命令行中运行，查看错误信息
- 检查 Python 和 telethon 版本

### 5. 如何更新程序？
```bash
cd telegram-forwarder-v20
git pull origin main
```

---

## 📅 更新日志

### v20 (2026-06-22)
- ✅ 添加智能相册洗稿模式（智能/简单/完整）
- ✅ 支持 9 个 AI 平台
- ✅ 自动模型更新
- ✅ 修复消息链接解析
- ✅ 优化事件循环架构

### v19 (2026-06-21)
- ✅ 添加 AI 洗稿功能
- ✅ 添加关键词过滤/替换
- ✅ 配置保存到 `config.ini`
- ✅ 修复登录问题

### v12 (2026-06-21)
- ✅ 基本转发功能
- ✅ 相册按 `grouped_id` 分组
- ✅ 消息范围控制
- ✅ 隐藏发送者姓名

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境搭建

```bash
git clone https://github.com/YOUR_USERNAME/telegram-forwarder-v20.git
cd telegram-forwarder-v20
pip install -r requirements.txt
python telegram_forwarder_v20.py
```

### 代码规范
- Python 3.8+ 兼容
- 使用 `black` 格式化代码
- 添加必要的注释

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram Python 框架
- [tkinter](https://docs.python.org/3/library/tkinter.html) - Python GUI 库
- 所有贡献者和使用者

---

## 📧 联系方式

- **Issues**: https://github.com/YOUR_USERNAME/telegram-forwarder-v20/issues
- **TG**: https://t.me/zzbzf1

---

<p align="center">
  ⭐ 如果这个项目对你有帮助，请给它一个 Star！ ⭐
</p>
