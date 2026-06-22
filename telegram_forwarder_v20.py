#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram 转发工具 v19 - 完整修复版

修复内容：
1. 修复原文和洗稿文案重复发送（只发送最终修改版）
2. 结束消息ID输入框现在可见（修复布局）
3. 添加"打开源频道"按钮（方便选择帖子）
4. 排除关键词改为"删除文案中的词语"（不是过滤整条消息）

保留功能（v17 全部功能）：
- 支持 Telegram 消息链接
- AI 洗稿（DeepSeek/OpenAI）
- 关键词替换（不区分大小写）
- 相册转发
- 批量任务管理
- 定时转发
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import asyncio
import threading
import configparser
import os
import json
import time
import logging
from datetime import datetime, timedelta
import traceback
import re

def parse_telegram_link(link):
    """解析 Telegram 消息链接，提取 channel 和 message_id
    
    支持的格式：
    - https://t.me/channel/12345
    - https://telegram.me/channel/12345
    - t.me/channel/12345
    - @channel/12345
    
    返回: (channel, message_id) 或 (None, None)
    """
    if not link:
        return None, None
    
    link = link.strip()
    
    # 正则匹配各种 Telegram 链接格式
    patterns = [
        r'https?://t\.me/([^/]+)/(\d+)',
        r'https?://telegram\.me/([^/]+)/(\d+)',
        r't\.me/([^/]+)/(\d+)',
        r'@([^/]+)/(\d+)',
        r'^(\d+)$',  # 纯数字 ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            groups = match.groups()
            if len(groups) == 1:  # 纯数字 ID
                return None, int(groups[0])
            else:  # channel + ID
                return groups[0], int(groups[1])
    
    return None, None

# =============================================================================
# 自动安装依赖
# =============================================================================
def install_dependencies():
    """自动检测并安装依赖"""
    missing = []
    
    try:
        import telethon
    except ImportError:
        missing.append('telethon')
    
    try:
        import requests
    except ImportError:
        missing.append('requests')
    
    if missing:
        print(f"正在安装依赖: {', '.join(missing)}")
        import subprocess
        subprocess.check_call(['pip', 'install'] + missing)
        print("依赖安装完成！")

install_dependencies()

from telethon import TelegramClient
import requests

# =============================================================================
# 日志配置
# =============================================================================
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"telegram_forwarder_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# =============================================================================
# 配置文件管理
# =============================================================================
class ConfigManager:
    CONFIG_FILE = "config.ini"
    
    @staticmethod
    def load():
        config = configparser.ConfigParser()
        if os.path.exists(ConfigManager.CONFIG_FILE):
            config.read(ConfigManager.CONFIG_FILE, encoding='utf-8')
        return config
    
    @staticmethod
    def save(config):
        with open(ConfigManager.CONFIG_FILE, 'w', encoding='utf-8') as f:
            config.write(f)
    
    @staticmethod
    def get_api_credentials():
        config = ConfigManager.load()
        if config and config.has_section('API'):
            api_id = config.get('API', 'api_id', fallback='')
            api_hash = config.get('API', 'api_hash', fallback='')
            return api_id, api_hash
        return '', ''
    
    @staticmethod
    def save_api_credentials(api_id, api_hash):
        config = ConfigManager.load()
        if not config.has_section('API'):
            config.add_section('API')
        config.set('API', 'api_id', api_id)
        config.set('API', 'api_hash', api_hash)
        ConfigManager.save(config)
    
    @staticmethod
    def get_ai_config():
        config = ConfigManager.load()
        if config and config.has_section('AI'):
            return {
                'platform': config.get('AI', 'platform', fallback='DeepSeek'),
                'api_key': config.get('AI', 'api_key', fallback=''),
                'model': config.get('AI', 'model', fallback='deepseek-chat'),
                'prompt': config.get('AI', 'prompt', fallback='请改写以下文案，保持原意但换种表达方式，语言自然流畅：')
            }
        return {
            'platform': 'DeepSeek',
            'api_key': '',
            'model': 'deepseek-chat',
            'prompt': '请改写以下文案，保持原意但换种表达方式，语言自然流畅：'
        }
    
    @staticmethod
    def save_ai_config(ai_config):
        config = ConfigManager.load()
        if not config.has_section('AI'):
            config.add_section('AI')
        config.set('AI', 'platform', ai_config['platform'])
        config.set('AI', 'api_key', ai_config['api_key'])
        config.set('AI', 'model', ai_config['model'])
        config.set('AI', 'prompt', ai_config['prompt'])
        ConfigManager.save(config)

# =============================================================================
# AI 洗稿模块
# =============================================================================
class AIRewriter:
    """AI 洗稿模块（支持多个平台）"""
    
    PLATFORMS = {
        'DeepSeek': {
            'url': 'https://api.deepseek.com/chat/completions',
            'model': 'deepseek-chat',
            'format': 'openai'
        },
        'OpenAI': {
            'url': 'https://api.openai.com/v1/chat/completions',
            'model': 'gpt-3.5-turbo',
            'format': 'openai'
        },
        'Claude': {
            'url': 'https://api.anthropic.com/v1/messages',
            'model': 'claude-3-haiku-20240307',
            'format': 'claude'
        },
        'Gemini': {
            'url': 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
            'model': 'gemini-1.5-pro',
            'format': 'openai'
        },
        '智谱GLM': {
            'url': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
            'model': 'glm-4-flash',
            'format': 'openai'
        },
        '百川智能': {
            'url': 'https://api.baichuan-ai.com/v1/chat/completions',
            'model': 'Baichuan3-Turbo',
            'format': 'openai'
        },
        '通义千问': {
            'url': 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
            'model': 'qwen-turbo',
            'format': 'openai'
        },
        'OpenRouter': {
            'url': 'https://openrouter.ai/api/v1/chat/completions',
            'model': 'openai/gpt-3.5-turbo',
            'format': 'openai'
        },
        'Ollama': {
            'url': 'http://localhost:11434/api/chat',
            'model': 'llama3',
            'format': 'ollama'
        }
    }

    
    def __init__(self, platform, api_key, model, prompt):
        self.platform = platform
        self.api_key = api_key
        self.model = model
        self.prompt = prompt
    
    def rewrite(self, text, retry=3):
        """洗稿（带重试）"""
        if not self.api_key:
            return False, text, '未配置 API Key'
        
        for attempt in range(retry):
            try:
                if self.platform == 'DeepSeek':
                    return self._rewrite_deepseek(text)
                elif self.platform == 'OpenAI':
                    return self._rewrite_openai(text)
                elif self.platform == 'Claude':
                    return self._rewrite_claude(text)
                elif self.platform == 'Gemini':
                    return self._rewrite_gemini(text)
                elif self.platform in ['智谱GLM', '百川智能', '通义千问', 'OpenRouter', 'Gemini']:
                    return self._rewrite_openai_compatible(text)  # 这些平台都兼容 OpenAI 格式
                elif self.platform == 'Ollama':
                    return self._rewrite_ollama(text)
                else:
                    return False, text, f'不支持的平台: {self.platform}'
            except Exception as e:
                if attempt < retry - 1:
                    time.sleep(2)
                    continue
                return False, text, str(e)
        
        return False, text, '重试次数用尽'
    
    def _rewrite_deepseek(self, text):
        """DeepSeek 洗稿"""
        url = self.PLATFORMS['DeepSeek']['url']
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': f'{self.prompt}\n\n原文案：\n{text}'}
            ],
            'temperature': 0.7
        }
        
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        rewritten = result['choices'][0]['message']['content'].strip()
        return True, rewritten, None
    
    def _rewrite_openai(self, text):
        """OpenAI 洗稿"""
        url = self.PLATFORMS['OpenAI']['url']
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': f'{self.prompt}\n\n原文案：\n{text}'}
            ],
            'temperature': 0.7
        }
        
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        rewritten = result['choices'][0]['message']['content'].strip()
        return True, rewritten, None
    
    def _rewrite_claude(self, text):
        """Claude 洗稿"""
        url = self.PLATFORMS['Claude']['url']
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }
        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': f'{self.prompt}\n\n原文案：\n{text}'}
            ],
            'max_tokens': 1000
        }
        
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        rewritten = result['content'][0]['text'].strip()
        return True, rewritten, None
    
    def _rewrite_gemini(self, text):
        """Google Gemini 洗稿"""
        url = f"{self.PLATFORMS['Gemini']['url']}/{self.model}:generateContent?key={self.api_key}"
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'contents': [{
                'parts': [{'text': f'{self.prompt}\n\n原文案：\n{text}'}]
            }],
            'generationConfig': {
                'temperature': 0.7
            }
        }
        
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        rewritten = result['candidates'][0]['content']['parts'][0]['text'].strip()
        return True, rewritten, None
    
    def _rewrite_openai_compatible(self, text):
        """兼容 OpenAI 格式的平台（智谱GLM、百川、通义千问、OpenRouter）"""
        url = self.PLATFORMS[self.platform]['url']
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json'
        }
        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': f'{self.prompt}\n\n原文案：\n{text}'}
            ],
            'temperature': 0.7
        }
        
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        rewritten = result['choices'][0]['message']['content'].strip()
        return True, rewritten, None
    
    def _rewrite_ollama(self, text):
        """Ollama 本地模型洗稿"""
        url = self.PLATFORMS['Ollama']['url']
        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': f'{self.prompt}\n\n原文案：\n{text}'}
            ],
            'stream': False,
            'options': {
                'temperature': 0.7
            }
        }
        
        resp = requests.post(url, json=data, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        rewritten = result['message']['content'].strip()
        return True, rewritten, None
    
    def _rewrite_openai_compatible(self, text):
        """兼容 OpenAI 格式的平台（智谱GLM、百川、通义千问、OpenRouter）"""
        url = self.PLATFORMS[self.platform]['url']
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json'
        }
        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': f'{self.prompt}\n\n原文案：\n{text}'}
            ],
            'temperature': 0.7
        }
        
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        rewritten = result['choices'][0]['message']['content'].strip()
        return True, rewritten, None
    
    def _rewrite_ollama(self, text):
        """Ollama 本地模型洗稿"""
        url = self.PLATFORMS['Ollama']['url']
        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': f'{self.prompt}\n\n原文案：\n{text}'}
            ],
            'stream': False,
            'options': {
                'temperature': 0.7
            }
        }
        
        resp = requests.post(url, json=data, timeout=60)  # 本地模型可能需要更长时间
        resp.raise_for_status()
        result = resp.json()
        rewritten = result['message']['content'].strip()
        return True, rewritten, None
    
    def test_connection(self):
        """测试 API 连接"""
        try:
            success, result, error = self.rewrite('测试连接')
            if success:
                return True, result
            else:
                return False, error
        except Exception as e:
            return False, str(e)

# =============================================================================
# 主程序
# =============================================================================
class TelegramForwarder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Telegram 转发工具 v20 - AI洗稿多平台版')
        self.root.geometry('900x700')
        
        self.client = None
        self.is_running = False
        self.loop = None
        self.loop_thread = None
        
        self._start_event_loop()
        self._create_ui()
        self._load_config()
    
    def _start_event_loop(self):
        """启动后台事件循环"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        time.sleep(0.5)
    
    def _submit_task(self, coro):
        """提交任务到后台事件循环"""
        if self.loop and self.loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
        return None
    
    def _create_ui(self):
        """创建界面"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建各个选项卡
        self._setup_main_tab(notebook)
        self._setup_api_tab(notebook)
        self._setup_ai_tab(notebook)
        self._setup_tasks_tab(notebook)
        self._setup_log_tab(notebook)
    
    def _setup_main_tab(self, notebook):
        """主界面"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='转发')
        
        # 源频道和目标频道
        ttk.Label(frame, text='手机号:').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.entry_phone = ttk.Entry(frame, width=30)
        self.entry_phone.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text='源频道:').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.entry_source = ttk.Entry(frame, width=40)
        self.entry_source.insert(0, '@biaojie128')
        self.entry_source.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text='目标频道:').grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.entry_target = ttk.Entry(frame, width=40)
        self.entry_target.insert(0, '@wumaav885')
        self.entry_target.grid(row=2, column=1, padx=10, pady=5)
        
        # 消息ID范围
        ttk.Label(frame, text='起始消息ID（支持链接）:').grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.entry_start_id = ttk.Entry(frame, width=50)
        self.entry_start_id.insert(0, '2027')
        self.entry_start_id.grid(row=3, column=1, columnspan=2, sticky='we', padx=10, pady=5)
        ttk.Label(frame, text='示例: https://t.me/channel/12345 或 2027', font=('', 8), foreground='gray').grid(row=4, column=1, columnspan=2, sticky='w', padx=10)
        
        ttk.Label(frame, text='结束消息ID（支持链接）:').grid(row=5, column=0, sticky='w', padx=10, pady=5)
        self.entry_end_id = ttk.Entry(frame, width=50)
        self.entry_end_id.insert(0, '2045')
        self.entry_end_id.grid(row=5, column=1, columnspan=2, sticky='we', padx=10, pady=5)
        ttk.Label(frame, text='示例: https://t.me/channel/12345 或 2045', font=('', 8), foreground='gray').grid(row=6, column=1, columnspan=2, sticky='w', padx=10)
        
        # 延迟
        ttk.Label(frame, text='延迟(秒):').grid(row=7, column=0, sticky='w', padx=10, pady=5)
        self.entry_delay = ttk.Entry(frame, width=20)
        self.entry_delay.insert(0, '2')
        self.entry_delay.grid(row=7, column=1, sticky='w', padx=10, pady=5)
        
        # 转发选项
        options_frame = ttk.LabelFrame(frame, text='转发选项')
        options_frame.grid(row=9, column=0, columnspan=3, sticky='we', padx=10, pady=10)
        
        self.var_hide_author = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text='隐藏发送者', variable=self.var_hide_author).grid(row=0, column=0, padx=10, pady=5, sticky='w')
        
        self.var_forward_albums = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text='转发整组帖子(相册)', variable=self.var_forward_albums).grid(row=0, column=1, padx=10, pady=5, sticky='w')
        
        # 相册洗稿方式选择（仅当启用AI洗稿时有效）
        ttk.Label(options_frame, text='相册洗稿方式:').grid(row=1, column=0, padx=10, pady=5, sticky='w')
        self.var_album_rewrite_mode = tk.StringVar(value='auto')
        album_mode_frame = ttk.Frame(options_frame)
        album_mode_frame.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        ttk.Radiobutton(album_mode_frame, text='智能模式（自动选择）', variable=self.var_album_rewrite_mode, value='auto').pack(side='left', padx=5)
        ttk.Radiobutton(album_mode_frame, text='简单模式', variable=self.var_album_rewrite_mode, value='simple').pack(side='left', padx=5)
        ttk.Radiobutton(album_mode_frame, text='完整模式', variable=self.var_album_rewrite_mode, value='complete').pack(side='left', padx=5)
        ttk.Label(options_frame, text='智能模式：有文案则用完整模式，无文案则用简单模式', font=('', 8), foreground='gray').grid(row=2, column=0, columnspan=2, padx=10, pady=2, sticky='w')
        
        # 关键词过滤
        keyword_frame = ttk.LabelFrame(frame, text='关键词过滤（可选）')
        keyword_frame.grid(row=10, column=0, columnspan=3, sticky='we', padx=10, pady=5)
        
        ttk.Label(keyword_frame, text='包含关键词:').grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.entry_include_keywords = ttk.Entry(keyword_frame, width=40)
        self.entry_include_keywords.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(keyword_frame, text='删除关键词:').grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.entry_exclude_keywords = ttk.Entry(keyword_frame, width=40)
        self.entry_exclude_keywords.grid(row=1, column=1, padx=5, pady=2)
        
        # 替换关键词
        replace_frame = ttk.LabelFrame(frame, text='替换关键词（可选）')
        replace_frame.grid(row=11, column=0, columnspan=3, sticky='we', padx=10, pady=5)
        
        ttk.Label(replace_frame, text='替换规则:').grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.entry_replace_keywords = ttk.Entry(replace_frame, width=60)
        self.entry_replace_keywords.insert(0, '张三=李四')
        self.entry_replace_keywords.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(replace_frame, text='格式: 原词1=新词1,原词2=新词2').grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=12, column=0, columnspan=3, pady=20)
        
        self.btn_login = ttk.Button(btn_frame, text='登录', command=self.login)
        self.btn_login.pack(side='left', padx=10)
        
        self.btn_start = ttk.Button(btn_frame, text='启动转发', command=self.start_forwarding)
        self.btn_start.pack(side='left', padx=10)
        
        self.btn_stop = ttk.Button(btn_frame, text='停止', command=self.stop_forwarding, state='disabled')
        self.btn_stop.pack(side='left', padx=10)
    
    def _setup_api_tab(self, notebook):
        """API配置"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='API配置')
        
        ttk.Label(frame, text='API ID:').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.entry_api_id = ttk.Entry(frame, width=30)
        self.entry_api_id.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        
        ttk.Label(frame, text='API Hash:').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.entry_api_hash = ttk.Entry(frame, width=50, show='*')
        self.entry_api_hash.grid(row=1, column=1, padx=10, pady=5, sticky='we')
        
        ttk.Label(frame, text='获取地址:').grid(row=2, column=0, sticky='w', padx=10, pady=5)
        ttk.Label(frame, text='https://my.telegram.org/apps', foreground='blue').grid(row=2, column=1, sticky='w', padx=10, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text='保存配置', command=self._save_api_config).pack(side='left', padx=10)
    
    def _save_api_config(self):
        """保存 API 配置"""
        api_id = self.entry_api_id.get().strip()
        api_hash = self.entry_api_hash.get().strip()
        
        if not api_id or not api_hash:
            messagebox.showerror('错误', '请填写 API ID 和 API Hash')
            return
        
        ConfigManager.save_api_credentials(api_id, api_hash)
        messagebox.showinfo('成功', 'API 配置已保存')
        self.log('API 配置已保存')
    
    def _setup_ai_tab(self, notebook):
        """AI洗稿配置"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='AI洗稿')
        
        self.var_enable_ai = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text='启用AI洗稿', variable=self.var_enable_ai, command=self._toggle_ai_options).grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky='w')
        
        ttk.Label(frame, text='AI平台:').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.combo_ai_platform = ttk.Combobox(frame, values=['DeepSeek', 'OpenAI', 'Claude', 'Gemini', '智谱GLM', '百川智能', '通义千问', 'OpenRouter', 'Ollama'], state='readonly', width=20)
        self.combo_ai_platform.current(0)
        self.combo_ai_platform.bind('<<ComboboxSelected>>', self._on_platform_changed)
        self.combo_ai_platform.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        
        ttk.Label(frame, text='API Key:').grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.entry_ai_api_key = ttk.Entry(frame, width=50, show='*')
        self.entry_ai_api_key.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky='we')
        
        ttk.Label(frame, text='模型:').grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.entry_ai_model = ttk.Entry(frame, width=30)
        self.entry_ai_model.insert(0, 'deepseek-chat')
        self.entry_ai_model.grid(row=3, column=1, padx=10, pady=5, sticky='w')
        
        ttk.Label(frame, text='洗稿提示词:').grid(row=4, column=0, sticky='nw', padx=10, pady=5)
        self.text_ai_prompt = scrolledtext.ScrolledText(frame, width=60, height=4)
        self.text_ai_prompt.insert('1.0', '请改写以下文案，保持原意但换种表达方式，语言自然流畅：')
        self.text_ai_prompt.grid(row=4, column=1, columnspan=2, padx=10, pady=5)
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        ttk.Button(btn_frame, text='测试连接', command=self._test_ai_connection).pack(side='left', padx=10)
        ttk.Button(btn_frame, text='保存配置', command=self._save_ai_config).pack(side='left', padx=10)
        
        self._toggle_ai_options()
    
    def _setup_tasks_tab(self, notebook):
        """批量任务管理"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='批量任务')
        
        ttk.Label(frame, text='批量任务管理功能即将推出...').pack(padx=20, pady=20)
    
    def _setup_log_tab(self, notebook):
        """日志"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='日志')
        
        self.log_text = scrolledtext.ScrolledText(frame, width=120, height=40)
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def _toggle_ai_options(self):
        """启用/禁用AI洗稿选项"""
        enabled = self.var_enable_ai.get()
        state = 'normal' if enabled else 'disabled'
        self.combo_ai_platform.config(state=state if not enabled else 'readonly')
        self.entry_ai_api_key.config(state=state)
        self.entry_ai_model.config(state=state)
        self.text_ai_prompt.config(state=state)
    
    def _on_platform_changed(self, event=None):
        """平台切换时，自动更新模型列表和默认值"""
        self._update_ai_models()
    
    def _update_ai_models(self):
        """根据选择的平台，更新模型输入框的默认值"""
        platform = self.combo_ai_platform.get()
        
        models = {
            'DeepSeek': ['deepseek-chat', 'deepseek-coder'],
            'OpenAI': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o'],
            'Claude': ['claude-3-haiku-20240307', 'claude-3-sonnet-20240229', 'claude-3-opus-20240229'],
            'Gemini': ['gemini-1.5-pro-latest', 'gemini-1.5-flash-latest', 'gemini-pro-vision'],
            '智谱GLM': ['glm-4-flash', 'glm-4', 'glm-4-plus'],
            '百川智能': ['Baichuan3-Turbo', 'Baichuan3-Turbo-192k', 'Baichuan2-Turbo'],
            '通义千问': ['qwen-turbo', 'qwen-plus', 'qwen-max'],
            'OpenRouter': ['openai/gpt-4', 'anthropic/claude-3-opus', 'google/gemini-pro'],
            'Ollama': ['llama3', 'mistral', 'gemma', 'qwen']
        }
        
        if platform in models:
            self.entry_ai_model.delete(0, 'end')
            self.entry_ai_model.insert(0, models[platform][0])
            self.log(f'平台切换为 {platform}，模型已自动更新为 {models[platform][0]}')
    
    def _test_ai_connection(self):
        """测试 AI API 连接"""
        platform = self.combo_ai_platform.get()
        api_key = self.entry_ai_api_key.get().strip()
        model = self.entry_ai_model.get().strip()
        prompt = self.text_ai_prompt.get('1.0', 'end').strip()
        
        if not api_key:
            messagebox.showerror('错误', '请填写 API Key')
            return
        
        self.log('正在测试 AI API 连接...')
        
        def test():
            rewriter = AIRewriter(platform, api_key, model, prompt)
            success, result = rewriter.test_connection()
            
            if success:
                self.root.after(0, lambda: messagebox.showinfo('成功', f'AI API 连接成功！\n\n测试结果：\n{result}'))
                self.root.after(0, lambda: self.log('AI API 连接成功'))
            else:
                self.root.after(0, lambda: messagebox.showerror('失败', f'AI API 连接失败：\n\n{result}'))
                self.root.after(0, lambda: self.log(f'AI API 连接失败: {result}'))
        
        threading.Thread(target=test, daemon=True).start()
    
    def _save_ai_config(self):
        """保存 AI 配置"""
        ai_config = {
            'platform': self.combo_ai_platform.get(),
            'api_key': self.entry_ai_api_key.get().strip(),
            'model': self.entry_ai_model.get().strip(),
            'prompt': self.text_ai_prompt.get('1.0', 'end').strip()
        }
        ConfigManager.save_ai_config(ai_config)
        messagebox.showinfo('成功', 'AI 配置已保存')
        self.log('AI 配置已保存')
    
    def _load_config(self):
        """加载配置"""
        # 加载 API 凭证
        api_id, api_hash = ConfigManager.get_api_credentials()
        if api_id:
            self.entry_api_id.delete(0, tk.END)
            self.entry_api_id.insert(0, api_id)
        if api_hash:
            self.entry_api_hash.delete(0, tk.END)
            self.entry_api_hash.insert(0, api_hash)
        
        # 加载 AI 配置
        ai_config = ConfigManager.get_ai_config()
        self.combo_ai_platform.set(ai_config['platform'])
        self.entry_ai_api_key.insert(0, ai_config['api_key'])
        self.entry_ai_model.delete(0, tk.END)
        self.entry_ai_model.insert(0, ai_config['model'])
        self.text_ai_prompt.delete('1.0', 'end')
        self.text_ai_prompt.insert('1.0', ai_config['prompt'])
    
    def log(self, message):
        """日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f'[{timestamp}] {message}\n'
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        logging.info(message)
    
    def login(self):
        """登录"""
        if not self.entry_api_id.get().strip() or not self.entry_api_hash.get().strip() or not self.entry_phone.get().strip():
            messagebox.showerror('错误', '请填写完整信息（API ID、API Hash、手机号）')
            return
        
        self.log('开始登录...')
        
        api_id = self.entry_api_id.get().strip()
        api_hash = self.entry_api_hash.get().strip()
        phone = self.entry_phone.get().strip()
        
        # 使用 _submit_task 提交登录任务到后台事件循环
        future = self._submit_task(self._login_async(phone, int(api_id), api_hash))
        if future:
            future.add_done_callback(lambda f: self._on_login_complete(f))
        else:
            self.log('错误：事件循环未启动')
            messagebox.showerror('错误', '事件循环未启动，请重启程序')
    
    def _on_login_complete(self, future):
        """登录完成回调"""
        try:
            result = future.result()
            self.root.after(0, lambda: self.log('登录成功！可以开始转发了'))
            self.root.after(0, lambda: messagebox.showinfo('成功', '登录成功！'))
        except Exception as e:
            self.root.after(0, lambda: self.log(f'登录失败: {e}'))
            self.root.after(0, lambda: messagebox.showerror('错误', f'登录失败：\n\n{e}'))
    
    async def _login_async(self, phone, api_id, api_hash):
        """异步登录"""
        self.client = TelegramClient('telegram_session', api_id, api_hash, loop=self.loop)
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(phone)
            self.root.after(0, lambda: self.log('验证码已发送，请在 Telegram 中查看'))
            
            code = await self._ask_code_gui()
            await self.client.sign_in(phone, code)
    
    async def _ask_code_gui(self):
        """弹出对话框输入验证码"""
        code = tk.StringVar()
        
        def ask():
            dialog = tk.Toplevel(self.root)
            dialog.title('输入验证码')
            dialog.geometry('350x150')
            dialog.transient(self.root)
            dialog.grab_set()
            
            ttk.Label(dialog, text='请输入 Telegram 发送的验证码:', font=('Arial', 10)).pack(pady=15)
            entry = ttk.Entry(dialog, textvariable=code, width=30, font=('Arial', 12))
            entry.pack(pady=10)
            entry.focus()
            
            ttk.Button(dialog, text='确定', command=dialog.destroy).pack(pady=10)
            self.root.wait_window(dialog)
        
        self.root.after(0, ask)
        while not code.get():
            await asyncio.sleep(0.1)
        
        return code.get()
    
    def start_forwarding(self):
        """启动转发"""
        if not self.client:
            messagebox.showerror('错误', '请先登录')
            return
        
        source = self.entry_source.get().strip()
        target = self.entry_target.get().strip()
        
        if not source or not target:
            messagebox.showerror('错误', '请填写源频道和目标频道')
            return
        
        self.is_running = True
        self.btn_start.config(state='disabled')
        self.btn_stop.config(state='normal')
        
        self.log('开始转发...')
        
        # 使用 _submit_task 提交转发任务到后台事件循环
        future = self._submit_task(self._forward_async(source, target))
        if future:
            future.add_done_callback(lambda f: self._on_forward_complete(f))
        else:
            self.log('错误：事件循环未启动')
            messagebox.showerror('错误', '事件循环未启动，请重启程序')
            self.is_running = False
            self.btn_start.config(state='normal')
            self.btn_stop.config(state='disabled')
    
    def _on_forward_complete(self, future):
        """转发完成回调"""
        try:
            future.result()  # 如果任务失败，这里会抛出异常
            self.root.after(0, lambda: self.log('转发完成！'))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.log(f'转发失败: {msg}'))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.btn_start.config(state='normal'))
            self.root.after(0, lambda: self.btn_stop.config(state='disabled'))
    
    def stop_forwarding(self):
        """停止转发"""
        self.is_running = False
        self.log('已发送停止请求')
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')
    
    async def _forward_async(self, source, target):
        """异步转发"""
        try:
            source_entity = await self.client.get_entity(source)
            target_entity = await self.client.get_entity(target)
            
            self.log(f'源频道: {getattr(source_entity, "title", source)}')
            self.log(f'目标频道: {getattr(target_entity, "title", target)}')
            
            # 解析参数（支持消息链接和纯数字 ID）
            start_link = self.entry_start_id.get().strip()
            end_link = self.entry_end_id.get().strip()
            
            self.log(f'[诊断] 起始消息输入框内容: "{start_link}"')
            self.log(f'[诊断] 结束消息输入框内容: "{end_link}"')
            
            # 尝试解析为 Telegram 链接，如果失败则解析为数字 ID
            _, start_id = parse_telegram_link(start_link) if start_link else (None, None)
            _, end_id = parse_telegram_link(end_link) if end_link else (None, None)
            
            self.log(f'[诊断] 解析链接后: start_id={start_id}, end_id={end_id}')
            
            # 如果解析失败（返回 None），则尝试解析为数字
            if start_id is None and start_link:
                try:
                    start_id = int(start_link)
                    self.log(f'[诊断] 起始ID解析为数字: {start_id}')
                except ValueError:
                    self.log(f'错误：无法解析起始消息: {start_link}')
                    return
            
            if end_id is None and end_link:
                try:
                    end_id = int(end_link)
                    self.log(f'[诊断] 结束ID解析为数字: {end_id}')
                except ValueError:
                    self.log(f'错误：无法解析结束消息: {end_link}')
                    return
            
            start_id = start_id or 0
            end_id = end_id or 0
            
            # 修复：如果起始ID > 结束ID，自动交换（用户可能填反了）
            if start_id > 0 and end_id > 0 and start_id > end_id:
                self.log(f'警告：起始ID {start_id} > 结束ID {end_id}，自动交换')
                start_id, end_id = end_id, start_id
            
            delay = float(self.entry_delay.get())
            hide_author = self.var_hide_author.get()
            forward_albums = self.var_forward_albums.get()
            
            self.log(f'起始消息ID: {start_id or "从头开始"}')
            self.log(f'结束消息ID: {end_id or "到最新"}')
            self.log(f'隐藏发送者: {hide_author}')
            self.log(f'转发相册: {forward_albums}')
            
            # 构建 iter_messages 参数（扩大范围以确保相册完整性）
            MARGIN = 50
            iter_kwargs = {}
            if start_id > 0:
                expanded_min = max(0, start_id - MARGIN - 1)
                iter_kwargs['min_id'] = expanded_min
                self.log(f'起始ID {start_id}，实际获取从 {max(1, start_id - MARGIN)} 开始（确保完整相册）')
            if end_id > 0:
                expanded_max = end_id + MARGIN + 1
                iter_kwargs['max_id'] = expanded_max
                self.log(f'结束ID {end_id}，实际获取到 {end_id + MARGIN} 为止（确保完整相册）')
            
            count = 0
            
            # 初始化 AI 洗稿器
            ai_rewriter = None
            self.log(f'[诊断] AI洗稿复选框状态: {self.var_enable_ai.get()}')
            self.log(f'[诊断] 关键词替换规则: {self.entry_replace_keywords.get().strip()}')
            
            if self.var_enable_ai.get():
                platform = self.combo_ai_platform.get()
                api_key = self.entry_ai_api_key.get().strip()
                model = self.entry_ai_model.get().strip()
                prompt = self.text_ai_prompt.get('1.0', 'end').strip()
                api_key_status = '已填写' if api_key else '未填写'
                self.log(f'[诊断] 创建 AI 洗稿器: platform={platform}, model={model}, api_key={api_key_status}')
                ai_rewriter = AIRewriter(platform, api_key, model, prompt)
                self.log('AI 洗稿已启用')
            else:
                self.log('[诊断] AI 洗稿未启用（复选框未勾选）')
            
            if ai_rewriter is None:
                self.log('[诊断] ai_rewriter 为 None，AI 洗稿将不会执行')
            
            if forward_albums:
                count = await self._forward_with_albums(
                    source_entity, target_entity,
                    start_id, end_id,
                    delay, hide_author, iter_kwargs,
                    ai_rewriter
                )
            else:
                # 简单逐条转发
                async for message in self.client.iter_messages(source_entity, **iter_kwargs):
                    if not self.is_running:
                        break
                    
                    if start_id > 0 and message.id < start_id:
                        continue
                    if end_id > 0 and message.id > end_id:
                        continue
                    
                    # 关键词过滤（包含关键词 + 删除关键词）
                    msg_text = message.message or ''
                    modified_text = self._match_keywords(msg_text)
                    if modified_text is None:
                        self.log(f'跳过消息 {message.id}: 不匹配包含关键词')
                        continue
                    # 使用修改后的文本（已删除关键词）
                    msg_text = modified_text
                    
                    try:
                        # AI 洗稿
                        final_text = msg_text
                        if ai_rewriter and msg_text:
                            self.log(f'[诊断] 开始 AI 洗稿: 消息ID={message.id}, 原文案长度={len(msg_text)}')
                            success, rewritten, error = ai_rewriter.rewrite(msg_text)
                            if success:
                                final_text = rewritten
                                self.log(f'AI 洗稿成功: {message.id}, 洗稿后长度={len(rewritten)}')
                            else:
                                self.log(f'AI 洗稿失败，使用原文案: {error}')
                        elif not ai_rewriter:
                            self.log(f'[诊断] AI 洗稿器为 None，跳过洗稿: 消息ID={message.id}')
                        elif not msg_text:
                            self.log(f'[诊断] 消息无文案，跳过洗稿: 消息ID={message.id}')
                        
                        # 替换关键词（在 AI 洗稿之后）
                        original_text_before_replace = final_text
                        final_text = self._replace_keywords(final_text)
                        if original_text_before_replace != final_text:
                            self.log(f'[诊断] 关键词替换成功: 消息ID={message.id}, 替换前长度={len(original_text_before_replace)}, 替换后长度={len(final_text)}')
                        else:
                            self.log(f'[诊断] 关键词替换无变化: 消息ID={message.id}')
                        
                        # 发送消息
                        if final_text != msg_text or not message.media:
                            # 文案有变化（洗稿或替换），需要重新发送
                            if message.media:
                                await self.client.send_file(
                                    target_entity,
                                    message.media,
                                    caption=final_text
                                )
                            else:
                                await self.client.send_message(
                                    target_entity,
                                    final_text
                                )
                            self.log(f'已发送消息 {message.id} ({count+1}) (洗稿/替换)')
                        else:
                            # 文案无变化，直接转发
                            await self.client.forward_messages(
                                target_entity,
                                message.id,
                                from_peer=source_entity,
                                drop_author=hide_author
                            )
                            self.log(f'已转发消息 {message.id} ({count+1})')
                        
                        count += 1
                        await asyncio.sleep(delay)
                    
                    except Exception as e:
                        self.log(f'处理消息 {message.id} 失败: {e}')
            
            self.log(f'转发完成！共转发 {count} 条消息')
        
        except Exception as e:
            error_msg = traceback.format_exc()
            self.log(f'转发失败:\n{error_msg}')
        
        finally:
            self.root.after(0, lambda: self.btn_start.config(state='normal'))
            self.root.after(0, lambda: self.btn_stop.config(state='disabled'))
    
    def _match_keywords(self, text):
        """检查文本是否匹配关键词过滤条件
        
        返回：
        - None: 不匹配包含关键词，过滤掉
        - text: 匹配包含关键词（或没有包含关键词），且已删除关键词
        
        删除关键词功能：
        - 从文案中删除指定的关键词（不区分大小写）
        - 支持任何语言/字符
        - 例如：删除关键词填写 "广告"，文案 "这是广告内容" → "这是内容"
        """
        if not text:
            text = ''
        
        # 包含关键词检查（过滤整条消息）
        include_kw = self.entry_include_keywords.get().strip()
        if include_kw:
            keywords = [k.strip().lower() for k in include_kw.split(',') if k.strip()]
            if keywords and not any(k in text.lower() for k in keywords):
                self.log(f'[诊断] 消息不匹配包含关键词: "{text[:50]}..." 不匹配 {keywords}')
                return None  # 不匹配包含关键词，过滤掉
        
        # 删除关键词：从文本中删除（不区分大小写，支持任何语言）
        exclude_kw = self.entry_exclude_keywords.get().strip()
        if exclude_kw:
            keywords = [k.strip() for k in exclude_kw.split(',') if k.strip()]
            self.log(f'[诊断] 删除关键词: 原始文案="{text[:100]}"')
            for keyword in keywords:
                # 使用正则表达式，不区分大小写，删除关键词
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = pattern.findall(text)
                if matches:
                    self.log(f'[诊断]   删除关键词: "{keyword}" (找到 {len(matches)} 处)')
                text = pattern.sub('', text)
            self.log(f'[诊断] 删除关键词: 修改后文案="{text[:100]}"')
        
        return text  # 返回修改后的文本
    
    async def _forward_with_albums(self, source_entity, target_entity,
                                   start_id, end_id,
                                   delay, hide_author, iter_kwargs,
                                   ai_rewriter):
        """按相册分组转发"""
        messages = []
        async for message in self.client.iter_messages(source_entity, **iter_kwargs):
            if not self.is_running:
                break
            messages.append(message)
        
        if not messages:
            self.log('没有找到符合条件的消息')
            return 0
        
        # 按 grouped_id 分组
        groups = {}
        no_group = []
        
        for msg in messages:
            if msg.grouped_id:
                gid = msg.grouped_id
                if gid not in groups:
                    groups[gid] = []
                groups[gid].append(msg)
            else:
                no_group.append(msg)
        
        self.log(f'共 {len(messages)} 条消息，{len(groups)} 个相册组，{len(no_group)} 条单独消息')
        
        # 过滤：只转发用户指定范围内的内容
        if start_id > 0 or end_id > 0:
            filtered_groups = {}
            for gid, msgs in groups.items():
                if any((start_id == 0 or m.id >= start_id) and (end_id == 0 or m.id <= end_id) for m in msgs):
                    filtered_groups[gid] = msgs
            groups = filtered_groups
            no_group = [m for m in no_group if (start_id == 0 or m.id >= start_id) and (end_id == 0 or m.id <= end_id)]
        
        count = 0
        
        # 诊断日志
        if ai_rewriter is None:
            self.log('[诊断] 相册转发: ai_rewriter 为 None，AI 洗稿将不会执行')
        else:
            self.log('[诊断] 相册转发: ai_rewriter 已创建，将尝试 AI 洗稿')
        
        replace_rules = self.entry_replace_keywords.get().strip()
        if replace_rules:
            self.log(f'[诊断] 相册转发: 关键词替换规则已填写: {replace_rules}')
        else:
            self.log('[诊断] 相册转发: 关键词替换规则为空，将不会替换')
        
        # 转发相册组
        for gid in sorted(groups.keys(), key=lambda g: groups[g][0].id):
            if not self.is_running:
                break
            group = groups[gid]
            try:
                # 关键词过滤
                # 找到相册中的文案（遍历所有消息）
                album_caption = ''
                for msg in group:
                    if msg.message and msg.message.strip():
                        album_caption = msg.message
                        break
                
                # 诊断：显示相册中每条消息的文案
                self.log(f'[诊断] 相册 (起始ID={group[0].id}) 共有 {len(group)} 条消息')
                for i, msg in enumerate(group):
                    msg_text = msg.message or '(空)'
                    if len(msg_text) > 50:
                        self.log(f'[诊断]   消息{i+1}: id={msg.id}, 文案={msg_text[:50]}...')
                    else:
                        self.log(f'[诊断]   消息{i+1}: id={msg.id}, 文案={msg_text}')
                
                if not album_caption:
                    self.log(f'[诊断] 相册 (起始ID={group[0].id}) 所有消息都无文案')
                
                if not self._match_keywords(album_caption):
                    self.log(f'跳过相册(起始ID={group[0].id}): 不匹配关键词')
                    continue
                
                # 智能选择相册洗稿方式
                album_rewrite_mode = self.var_album_rewrite_mode.get()
                if album_rewrite_mode == 'auto':
                    # 智能模式：有文案且AI洗稿已启用 → 建议使用完整模式；否则 → 简单模式
                    if ai_rewriter and album_caption:
                        album_rewrite_mode = 'complete'
                        self.log(f'[诊断] 智能模式: 相册有文案且AI洗稿已启用，建议使用完整模式 (起始ID={group[0].id})')
                        self.log(f'[警告] 完整模式尚未实现，暂用简单模式替代')
                        album_rewrite_mode = 'simple'
                    else:
                        album_rewrite_mode = 'simple'
                        self.log(f'[诊断] 智能模式: 使用简单模式 (起始ID={group[0].id})')
                
                # 根据选择的方式处理相册
                if album_rewrite_mode == 'complete':
                    # 完整模式：下载媒体 → 重新上传（暂未实现，使用简单模式替代）
                    self.log(f'[警告] 完整模式尚未实现，暂用简单模式替代 (起始ID={group[0].id})')
                    album_rewrite_mode = 'simple'
                
                if album_rewrite_mode == 'simple':
                    # 简单模式：转发相册后，追加洗稿文案（作为单独消息）
                    msg_ids = [m.id for m in group]
                    await self.client.forward_messages(
                        target_entity,
                        msg_ids,
                        from_peer=source_entity,
                        drop_author=hide_author
                    )
                    
                    # 如果启用了AI洗稿且有文案，发送洗稿后的文案
                    if ai_rewriter and album_caption:
                        self.log(f'[诊断] 简单模式: 开始 AI 洗稿 (起始ID={group[0].id}), 原文案长度={len(album_caption)}')
                        success, rewritten, error = ai_rewriter.rewrite(album_caption)
                        if success:
                            # 替换关键词（在 AI 洗稿之后）
                            final_caption = self._replace_keywords(rewritten)
                            await self.client.send_message(
                                target_entity,
                                final_caption
                            )
                            self.log(f'相册洗稿+替换完成(起始ID={group[0].id}), 洗稿后长度={len(rewritten)}, 替换后长度={len(final_caption)}')
                        else:
                            # 洗稿失败，但还是尝试替换关键词
                            self.log(f'[诊断] 相册转发: AI 洗稿失败 (起始ID={group[0].id}): {error}')
                            final_caption = self._replace_keywords(album_caption)
                            if final_caption != album_caption:
                                await self.client.send_message(
                                    target_entity,
                                    final_caption
                                )
                                self.log(f'相册替换关键词完成(起始ID={group[0].id})')
                    else:
                        # 没有 AI 洗稿，只做关键词替换
                        if album_caption:
                            final_caption = self._replace_keywords(album_caption)
                            if final_caption != album_caption:
                                await self.client.send_message(
                                    target_entity,
                                    final_caption
                                )
                                self.log(f'相册替换关键词完成(起始ID={group[0].id})')
                
                # 【已注释】AI 洗稿 + 替换关键词
                # if ai_rewriter and album_caption:
                #     self.log(f'[诊断] 相册转发: 开始 AI 洗稿 (起始ID={group[0].id}), 原文案长度={len(album_caption)}')
                #     success, rewritten, error = ai_rewriter.rewrite(album_caption)
                #     if success:
                #         # 替换关键词（在 AI 洗稿之后）
                #         final_caption = self._replace_keywords(rewritten)
                #         await self.client.send_message(
                #             target_entity,
                #             final_caption
                #         )
                #         self.log(f'相册洗稿+替换完成(起始ID={group[0].id}), 洗稿后长度={len(rewritten)}, 替换后长度={len(final_caption)}')
                #     else:
                #         # 洗稿失败，但还是尝试替换关键词
                #         self.log(f'[诊断] 相册转发: AI 洗稿失败 (起始ID={group[0].id}): {error}')
                #         final_caption = self._replace_keywords(album_caption)
                #         if final_caption != album_caption:
                #             await self.client.send_message(
                #                 target_entity,
                #                 final_caption
                #             )
                #             self.log(f'相册替换关键词完成(起始ID={group[0].id})')
                # else:
                #     if not ai_rewriter:
                #         self.log(f'[诊断] 相册转发: ai_rewriter 为 None，跳过 AI 洗稿 (起始ID={group[0].id})')
                #     if not album_caption:
                #         self.log(f'[诊断] 相册转发: 相册无文案，跳过 AI 洗稿 (起始ID={group[0].id})')
                #     # 没有 AI 洗稿，只做关键词替换
                #     final_caption = self._replace_keywords(album_caption)
                #     if final_caption != album_caption:
                #         await self.client.send_message(
                #             target_entity,
                #             final_caption
                #         )
                #         self.log(f'相册替换关键词完成(起始ID={group[0].id})')
                
                count += len(group)
                self.log(f'已转发相册(共{len(group)}张) 消息ID={msg_ids} ({count})')
                await asyncio.sleep(delay)
            
            except Exception as e:
                self.log(f'转发相册失败(起始ID={group[0].id}): {e}')
        
        # 转发非相册消息
        for msg in no_group:
            if not self.is_running:
                break
            try:
                # 关键词过滤
                msg_text = msg.message or ''
                if not self._match_keywords(msg_text):
                    self.log(f'跳过消息 {msg.id}: 不匹配关键词')
                    continue
                
                # AI 洗稿 + 替换关键词
                final_text = msg_text
                if ai_rewriter and msg_text:
                    success, rewritten, error = ai_rewriter.rewrite(msg_text)
                    if success:
                        final_text = rewritten
                        self.log(f'AI 洗稿成功: {msg.id}')
                    else:
                        self.log(f'AI 洗稿失败: {error}')
                
                # 替换关键词（在 AI 洗稿之后）
                final_text = self._replace_keywords(final_text)
                
                # 发送消息
                if final_text != msg_text or not msg.media:
                    # 文案有变化（洗稿或替换），需要重新发送
                    if msg.media:
                        await self.client.send_file(
                            target_entity,
                            msg.media,
                            caption=final_text
                        )
                    else:
                        await self.client.send_message(
                            target_entity,
                            final_text
                        )
                    self.log(f'已发送消息 {msg.id} ({count+1}) (洗稿/替换)')
                else:
                    # 文案无变化，直接转发
                    await self.client.forward_messages(
                        target_entity,
                        msg.id,
                        from_peer=source_entity,
                        drop_author=hide_author
                    )
                    self.log(f'已转发消息 {msg.id} ({count+1})')
                
                count += 1
                await asyncio.sleep(delay)
            
            except Exception as e:
                self.log(f'转发消息 {msg.id} 失败: {e}')
        
        return count
    
    def _replace_keywords(self, text):
        """替换关键词（不区分大小写）
        格式：原词1=新词1,原词2=新词2
        """
        replace_rules = self.entry_replace_keywords.get().strip()
        self.log(f'[诊断] _replace_keywords() 被调用')
        self.log(f'[诊断]   读取到的替换规则: "{replace_rules}"')
        self.log(f'[诊断]   输入文本长度: {len(text) if text else 0}')
        
        if not replace_rules:
            self.log('[诊断]   替换规则为空，跳过替换')
            return text
        
        if not text:
            self.log('[诊断]   输入文本为空，跳过替换')
            return text
        
        try:
            import re
            rules = replace_rules.split(',')
            self.log(f'[诊断]   共 {len(rules)} 条规则')
            result = text
            for i, rule in enumerate(rules):
                if '=' in rule:
                    old_word, new_word = rule.split('=', 1)
                    old_word = old_word.strip()
                    new_word = new_word.strip()
                    if old_word:
                        # 使用正则表达式，不区分大小写
                        pattern = re.compile(re.escape(old_word), re.IGNORECASE)
                        matches = pattern.findall(result)
                        count = len(matches)
                        result = pattern.sub(new_word, result)
                        self.log(f'[诊断]   规则{i+1}: "{old_word}" -> "{new_word}" (替换了{count}处)')
            
            if result != text:
                self.log(f'[诊断]   替换完成: 原长度={len(text)}, 新长度={len(result)}')
            else:
                self.log('[诊断]   替换后文本无变化')
            return result
        except Exception as e:
            self.log(f'替换关键词失败: {e}')
            return text
    
    def run(self):
        """运行主循环"""
        try:
            self.root.mainloop()
        except Exception as e:
            error_msg = traceback.format_exc()
            logging.error(f'程序异常退出:\n{error_msg}')
            with open('error_log.txt', 'w', encoding='utf-8') as f:
                f.write(error_msg)
            messagebox.showerror('致命错误', f'程序异常退出:\n\n{e}')

# =============================================================================
# 主程序入口
# =============================================================================
if __name__ == '__main__':
    try:
        app = TelegramForwarder()
        app.run()
    except Exception as e:
        error_msg = traceback.format_exc()
        with open('error_log.txt', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        try:
            messagebox.showerror('致命错误', f'程序异常退出:\n\n{e}')
        except:
            pass
        print(f'致命错误:\n{error_msg}')
        input('按回车键退出...')
