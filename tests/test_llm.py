"""大模型客户端模块的单元测试。

所有测试均通过 mock 隔离真实网络请求，不会实际调用 API，
也不会读取或泄露真实密钥。
"""

import httpx

from app import llm_client
from app.llm_client import (
    build_compare_messages,
    build_explain_messages,
    chat,
    load_llm_config,
)


def _disable_dotenv(monkeypatch):
    """将 load_dotenv 替换为空操作，避免测试依赖真实 .env 文件。"""
    monkeypatch.setattr(llm_client, "load_dotenv", lambda *args, **kwargs: None)


def _set_fake_env(monkeypatch):
    """设置一组假的环境变量，供需要完整配置的测试使用。"""
    monkeypatch.setenv("LLM_BASE_URL", "https://api.example.com/v1/")
    monkeypatch.setenv("LLM_API_KEY", "sk-test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")


class TestLoadConfig:
    """配置读取测试。"""

    def test_load_llm_config(self, monkeypatch):
        """应从环境变量读取配置，并去除 base_url 末尾斜杠。"""
        _disable_dotenv(monkeypatch)
        _set_fake_env(monkeypatch)
        config = load_llm_config()
        assert config["base_url"] == "https://api.example.com/v1"
        assert config["api_key"] == "sk-test-key"
        assert config["model"] == "test-model"

    def test_missing_config_defaults_empty(self, monkeypatch):
        """缺少环境变量时应返回空字符串。"""
        _disable_dotenv(monkeypatch)
        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)
        config = load_llm_config()
        assert config["base_url"] == ""
        assert config["api_key"] == ""
        assert config["model"] == ""


class TestPrompts:
    """提示词构建测试。"""

    def test_build_explain_messages(self):
        """解释算法的提示词应包含 system 与 user 消息，且提及两种算法。"""
        messages = build_explain_messages()
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "BFS" in messages[1]["content"]
        assert "A*" in messages[1]["content"]

    def test_build_compare_messages(self):
        """对比分析的提示词应包含迷宫规模与算法运行数据。"""
        messages = build_compare_messages(
            21, 21, True, 58, 76, 1.2, True, 58, 66, 0.8,
        )
        user = messages[1]["content"]
        assert "21 x 21" in user
        assert "找到路径" in user
        assert "58" in user
        assert "76" in user
        assert "66" in user


class TestChat:
    """大模型调用测试（全部 mock）。"""

    def test_chat_missing_config(self, monkeypatch):
        """缺少配置时应返回失败结果，而不是抛出异常。"""
        _disable_dotenv(monkeypatch)
        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)
        result = chat([{"role": "user", "content": "hi"}])
        assert not result.ok
        assert "缺少" in result.error

    def test_chat_success(self, monkeypatch):
        """成功响应应正确解析出助手回复文本。"""
        _disable_dotenv(monkeypatch)
        _set_fake_env(monkeypatch)

        class FakeResponse:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": [{"message": {"content": "  这是回复内容  "}}]}

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args, **kwargs):
                pass

            def post(self, *args, **kwargs):
                return FakeResponse()

        monkeypatch.setattr(llm_client.httpx, "Client", FakeClient)
        result = chat([{"role": "user", "content": "hi"}])
        assert result.ok
        assert result.text == "这是回复内容"

    def test_chat_network_error(self, monkeypatch):
        """网络异常时应返回失败结果，而不是抛出异常。"""
        _disable_dotenv(monkeypatch)
        _set_fake_env(monkeypatch)

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args, **kwargs):
                pass

            def post(self, *args, **kwargs):
                raise httpx.ConnectError("连接失败")

        monkeypatch.setattr(llm_client.httpx, "Client", FakeClient)
        result = chat([{"role": "user", "content": "hi"}])
        assert not result.ok
        assert "网络请求失败" in result.error
