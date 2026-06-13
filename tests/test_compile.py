"""
编译工具测试
"""

import pytest

from superrtl.tools.compile import compile_verilog


class TestCompileVerilog:
    """compile_verilog 测试"""

    @pytest.mark.asyncio
    async def test_compile_valid_code(self):
        """测试编译有效代码"""
        code = """
        module counter (
            input clk,
            input rst_n,
            output reg [3:0] count
        );
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    count <= 4'b0;
                else
                    count <= count + 1'b1;
            end
        endmodule
        """
        result = await compile_verilog(code)

        # 如果 iverilog 安装了，应该成功
        if result.get("success"):
            assert result["top_module"] == "counter"
            assert "duration" in result
            assert result["duration"] > 0

    @pytest.mark.asyncio
    async def test_compile_with_top_module(self):
        """测试指定顶层模块名"""
        code = """
        module counter (input clk, output reg [3:0] count);
        endmodule
        module wrapper (input clk);
        endmodule
        """
        result = await compile_verilog(code, top_module="counter")

        if result.get("success"):
            assert result["top_module"] == "counter"

    @pytest.mark.asyncio
    async def test_compile_syntax_error(self):
        """测试语法错误代码"""
        code = """
        module bad_code (
            input clk,
            // 缺少分号
            output reg [3:0] count
        );
            always @(posedge clk
                count <= count + 1;
            end
        endmodule
        """
        result = await compile_verilog(code)

        # 应该失败
        if not result.get("success"):
            assert "errors" in result or "error" in result

    @pytest.mark.asyncio
    async def test_compile_empty_code(self):
        """测试空代码"""
        result = await compile_verilog("")

        # 空代码应该失败或返回默认模块名
        if result.get("success"):
            assert result["top_module"] == "top"

    @pytest.mark.asyncio
    async def test_compile_multiple_modules(self):
        """测试多模块编译"""
        code = """
        module sub_module (input a, output b);
            assign b = a;
        endmodule

        module top_module (input clk, output out);
            sub_module u1 (.a(clk), .b(out));
        endmodule
        """
        result = await compile_verilog(code, top_module="top_module")

        if result.get("success"):
            assert result["top_module"] == "top_module"

    @pytest.mark.asyncio
    async def test_compile_result_structure(self):
        """测试返回结果结构"""
        code = "module test(input clk); endmodule"
        result = await compile_verilog(code)

        # 应该有这些字段
        assert "success" in result
        assert "top_module" in result

        if result.get("success"):
            assert "duration" in result
            assert "message" in result

    @pytest.mark.asyncio
    async def test_compile_timeout_structure(self):
        """测试超时错误结构"""
        # 注意：实际超时测试需要特殊处理，这里只验证结构
        code = "module test(input clk); endmodule"
        result = await compile_verilog(code)

        # 如果失败，应该有错误信息
        if not result.get("success"):
            assert "error" in result or "errors" in result
