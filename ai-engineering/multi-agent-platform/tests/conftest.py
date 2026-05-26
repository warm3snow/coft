from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _install_langchain_stubs() -> None:
    if "langchain_core" in sys.modules:
        return

    langchain_core = types.ModuleType("langchain_core")
    language_models = types.ModuleType("langchain_core.language_models")
    messages = types.ModuleType("langchain_core.messages")
    tools = types.ModuleType("langchain_core.tools")

    class BaseChatModel:
        def bind_tools(self, tools_list):
            return self

    class _BaseMessage:
        def __init__(self, content: str = "", tool_call_id: str | None = None):
            self.content = content
            self.tool_call_id = tool_call_id

    class HumanMessage(_BaseMessage):
        pass

    class SystemMessage(_BaseMessage):
        pass

    class AIMessage(_BaseMessage):
        pass

    class ToolMessage(_BaseMessage):
        pass

    class BaseTool:
        name = "base_tool"

        def invoke(self, arguments):
            if callable(self):
                return self(**arguments)
            raise NotImplementedError

    def tool(func):
        class FunctionTool(BaseTool):
            name = func.__name__

            def invoke(self, arguments):
                return func(**arguments)

        wrapped = FunctionTool()
        wrapped.__doc__ = func.__doc__
        wrapped.func = func
        return wrapped

    language_models.BaseChatModel = BaseChatModel
    messages.HumanMessage = HumanMessage
    messages.SystemMessage = SystemMessage
    messages.AIMessage = AIMessage
    messages.ToolMessage = ToolMessage
    tools.BaseTool = BaseTool
    tools.tool = tool

    sys.modules["langchain_core"] = langchain_core
    sys.modules["langchain_core.language_models"] = language_models
    sys.modules["langchain_core.messages"] = messages
    sys.modules["langchain_core.tools"] = tools


_install_langchain_stubs()


def _install_yaml_stub() -> None:
    if "yaml" in sys.modules:
        return

    yaml = types.ModuleType("yaml")

    def safe_load(text):
        raise NotImplementedError("PyYAML is required for YAML parsing in this environment")

    yaml.safe_load = safe_load
    sys.modules["yaml"] = yaml


_install_yaml_stub()


@pytest.fixture(autouse=True)
def reset_telemetry():
    from multi_agent_platform.observability import telemetry

    telemetry.reset()
    yield
    telemetry.reset()
