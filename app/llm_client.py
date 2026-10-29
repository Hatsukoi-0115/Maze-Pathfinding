"""大模型客户端模块。

负责读取项目根目录 .env 中的 API 配置，通过 OpenAI 兼容接口调用大模型，
为迷宫项目提供 AI 扩展功能：
- 解释寻路算法（BFS 与 A* 的原理及区别）。
- 对比分析 BFS / A* 在具体迷宫上的运行结果。

本模块与图形界面解耦，纯逻辑部分（配置读取、提示词构建、响应解析）
可独立进行单元测试。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

# 项目根目录（本文件位于 app/ 子目录下）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 系统提示词：约束大模型使用简洁中文、纯文本回答
SYSTEM_PROMPT = (
    "你是一位算法讲解助手，帮助用户理解迷宫寻路算法。"
    "请使用简洁清晰的中文，以纯文本回答，"
    "不要使用 Markdown 符号（如 #、*、`、- 列表等）。"
)


@dataclass
class LLMResult:
    """大模型调用结果。

    属性:
        ok: 调用是否成功。
        text: 成功时返回的助手回复文本。
        error: 失败时的错误信息。
    """

    ok: bool
    text: str = ""
    error: str = ""


def load_llm_config() -> Dict[str, str]:
    """从项目根目录 .env 文件读取大模型配置。

    返回包含 base_url、api_key、model 的字典，缺失的项为空字符串。
    """
    load_dotenv(PROJECT_ROOT / ".env")
    return {
        "base_url": os.getenv("LLM_BASE_URL", "").rstrip("/"),
        "api_key": os.getenv("LLM_API_KEY", ""),
        "model": os.getenv("LLM_MODEL", ""),
    }


def chat(messages: List[Dict[str, str]], timeout: float = 60.0) -> LLMResult:
    """调用大模型对话接口，返回助手回复文本。

    参数:
        messages: 消息列表，每项形如 {"role": "system"/"user", "content": "..."}。
        timeout: 请求超时时间（秒）。

    返回:
        LLMResult，包含调用是否成功、回复文本或错误信息。
    """
    config = load_llm_config()
    if not config["base_url"] or not config["api_key"] or not config["model"]:
        return LLMResult(False, error="缺少 .env 配置（LLM_BASE_URL / LLM_API_KEY / LLM_MODEL）")

    url = f"{config['base_url']}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": config["model"],
        "messages": messages,
        "temperature": 0.7,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        # 解析 OpenAI 兼容响应结构中的回复文本
        content = data["choices"][0]["message"]["content"]
        return LLMResult(ok=True, text=content.strip())
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:300]
        return LLMResult(False, error=f"HTTP 错误 {exc.response.status_code}：{detail}")
    except httpx.HTTPError as exc:
        return LLMResult(False, error=f"网络请求失败：{exc}")
    except (KeyError, IndexError, TypeError) as exc:
        return LLMResult(False, error=f"响应解析失败：{exc}")


def build_explain_messages() -> List[Dict[str, str]]:
    """构建「解释寻路算法」的提示词消息列表。"""
    user_content = (
        "请简要解释以下两种迷宫寻路算法的工作原理、优缺点以及它们之间的区别：\n"
        "1. 广度优先搜索（BFS）\n"
        "2. A* 算法（使用曼哈顿距离作为启发函数）\n"
        "请控制在 300 字以内，条理清晰。"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_compare_messages(
    rows: int,
    cols: int,
    bfs_found: bool,
    bfs_length: int,
    bfs_visited: int,
    bfs_ms: float,
    astar_found: bool,
    astar_length: int,
    astar_visited: int,
    astar_ms: float,
) -> List[Dict[str, str]]:
    """构建「对比分析 BFS 与 A* 结果」的提示词消息列表。"""
    def _status(found: bool) -> str:
        """将是否找到路径转换为中文描述。"""
        return "找到路径" if found else "未找到路径"

    user_content = (
        f"在一个 {rows} x {cols} 的迷宫中（左上角为起点、右下角为终点），"
        "两种寻路算法运行结果如下：\n"
        f"- BFS：{_status(bfs_found)}，路径长度 {bfs_length} 步，"
        f"访问 {bfs_visited} 个节点，耗时 {bfs_ms:.2f} ms\n"
        f"- A*：{_status(astar_found)}，路径长度 {astar_length} 步，"
        f"访问 {astar_visited} 个节点，耗时 {astar_ms:.2f} ms\n"
        "请分析这两种算法在该迷宫上的表现差异（路径长度是否一致、访问节点数、耗时），"
        "并解释为什么会出现这些差异。控制在 300 字以内。"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
