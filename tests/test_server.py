"""
MCP Server 测试
"""

import json
from unittest.mock import patch

import pytest

from superrtl.server import (
    call_tool,
    list_resources,
    list_tools,
    read_resource,
)


class TestListTools:
    """list_tools 测试"""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self):
        """测试返回所有工具"""
        tools = await list_tools()

        assert len(tools) == 6
        tool_names = [t.name for t in tools]
        assert "compile_verilog" in tool_names
        assert "simulate_verilog" in tool_names
        assert "lint_verilog" in tool_names
        assert "synthesize_verilog" in tool_names
        assert "generate_testbench" in tool_names
        assert "analyze_waveform" in tool_names

    @pytest.mark.asyncio
    async def test_tool_schemas(self):
        """测试工具 schema"""
        tools = await list_tools()

        for tool in tools:
            assert tool.name
            assert tool.description
            assert tool.inputSchema
            assert "type" in tool.inputSchema
            assert "properties" in tool.inputSchema


class TestCallTool:
    """call_tool 测试"""

    @pytest.mark.asyncio
    async def test_compile_verilog(self):
        """测试编译工具调用"""
        result = await call_tool("compile_verilog", {
            "code": "module test(input clk); endmodule"
        })

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "success" in data

    @pytest.mark.asyncio
    async def test_simulate_verilog(self):
        """测试仿真工具调用"""
        result = await call_tool("simulate_verilog", {
            "code": "module test(input clk); endmodule",
            "testbench": "module tb; initial $finish; endmodule"
        })

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "success" in data

    @pytest.mark.asyncio
    async def test_lint_verilog(self):
        """测试 lint 工具调用"""
        result = await call_tool("lint_verilog", {
            "code": "module test(input clk); endmodule"
        })

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "success" in data

    @pytest.mark.asyncio
    async def test_synthesize_verilog(self):
        """测试综合工具调用"""
        result = await call_tool("synthesize_verilog", {
            "code": "module test(input clk); endmodule"
        })

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "success" in data

    @pytest.mark.asyncio
    async def test_generate_testbench(self):
        """测试生成 testbench 工具调用"""
        result = await call_tool("generate_testbench", {
            "code": "module counter(input clk, output reg [3:0] count); endmodule"
        })

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "testbench" in data

    @pytest.mark.asyncio
    async def test_analyze_waveform(self):
        """测试波形分析工具调用"""
        vcd = "$timescale 1ns $end\n$enddefinitions $end\n#0\n0!\n"
        result = await call_tool("analyze_waveform", {
            "vcd_content": vcd
        })

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        """测试未知工具"""
        result = await call_tool("unknown_tool", {})

        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "未知工具" in data["error"]

    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """测试工具错误处理"""
        with patch("superrtl.server.compile_verilog", side_effect=Exception("test error")):
            result = await call_tool("compile_verilog", {"code": "test"})

            data = json.loads(result[0].text)
            assert data["success"] is False
            assert "test error" in data["error"]


class TestListResources:
    """list_resources 测试"""

    @pytest.mark.asyncio
    async def test_list_resources(self):
        """测试列出资源"""
        resources = await list_resources()

        assert isinstance(resources, list)
        # 应该有 skills 和 templates
        uris = [str(r.uri) for r in resources]
        assert any("skills://" in uri for uri in uris)
        assert any("templates://" in uri for uri in uris)

    @pytest.mark.asyncio
    async def test_resource_attributes(self):
        """测试资源属性"""
        resources = await list_resources()

        for resource in resources:
            assert resource.uri
            assert resource.name
            assert resource.description


class TestReadResource:
    """read_resource 测试"""

    @pytest.mark.asyncio
    async def test_read_skill(self):
        """测试读取 skill"""
        result = await read_resource("skills://fsm")

        # 应该返回内容
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_read_template(self):
        """测试读取 template"""
        result = await read_resource("templates://counter")

        # 应该返回内容
        assert isinstance(result, str)
        assert "module counter" in result

    @pytest.mark.asyncio
    async def test_read_unknown_resource(self):
        """测试读取未知资源"""
        result = await read_resource("unknown://test")

        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_read_nonexistent_skill(self):
        """测试读取不存在的 skill"""
        result = await read_resource("skills://nonexistent")

        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_read_nonexistent_template(self):
        """测试读取不存在的 template"""
        result = await read_resource("templates://nonexistent")

        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_read_resource_error_handling(self):
        """测试资源读取错误处理"""
        with patch("superrtl.server.get_skill", side_effect=Exception("read error")):
            result = await read_resource("skills://test")

            data = json.loads(result)
            assert "error" in data
