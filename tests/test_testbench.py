"""
Testbench 生成测试
"""

import pytest

from superrtl.tools.testbench import generate_testbench


class TestGenerateTestbench:
    """generate_testbench 测试"""

    @pytest.mark.asyncio
    async def test_basic_counter(self):
        """测试基本计数器 testbench 生成"""
        code = """
        module counter (
            input clk,
            input rst_n,
            output reg [3:0] count
        );
        endmodule
        """
        result = await generate_testbench(code)

        assert result["success"] is True
        assert result["top_module"] == "counter"
        assert "testbench" in result

        tb = result["testbench"]
        assert "module counter_tb" in tb
        assert "reg clk" in tb
        assert "reg rst_n" in tb
        assert "counter uut" in tb
        assert "$dumpfile" in tb
        assert "$display(\"PASS\")" in tb

    @pytest.mark.asyncio
    async def test_comprehensive_style(self):
        """测试 comprehensive 风格"""
        code = """
        module adder (
            input [7:0] a,
            input [7:0] b,
            output [8:0] sum
        );
        endmodule
        """
        result = await generate_testbench(code, style="comprehensive", test_cases=5)

        assert result["success"] is True
        assert result["style"] == "comprehensive"
        assert result["test_cases"] == 5

    @pytest.mark.asyncio
    async def test_custom_clock_reset(self):
        """测试自定义时钟复位信号名"""
        code = """
        module test (
            input clock,
            input reset,
            output reg [7:0] data
        );
        endmodule
        """
        result = await generate_testbench(code)

        assert result["success"] is True
        tb = result["testbench"]
        assert "reg clock" in tb
        assert "reg reset" in tb

    @pytest.mark.asyncio
    async def test_no_ports_module(self):
        """测试无端口模块"""
        code = "module empty; endmodule"
        result = await generate_testbench(code)

        assert result["success"] is True
        assert result["top_module"] == "empty"
        assert result["ports"] == []

    @pytest.mark.asyncio
    async def test_output_contains_timescale(self):
        """测试输出包含 timescale"""
        code = "module test(input clk); endmodule"
        result = await generate_testbench(code)
        assert "`timescale 1ns/1ps" in result["testbench"]

    @pytest.mark.asyncio
    async def test_output_contains_timeout(self):
        """测试输出包含超时保护"""
        code = "module test(input clk); endmodule"
        result = await generate_testbench(code)
        assert "TIMEOUT" in result["testbench"]
        assert "#100000" in result["testbench"]

    @pytest.mark.asyncio
    async def test_multiple_test_cases(self):
        """测试多个测试用例"""
        code = "module test(input clk, input [3:0] data); endmodule"
        result = await generate_testbench(code, test_cases=5)

        tb = result["testbench"]
        # 检查是否有 5 个测试用例编号 (1-5)
        for i in range(1, 6):
            assert f"// 测试用例 {i}" in tb

    @pytest.mark.asyncio
    async def test_sequential_ports(self):
        """测试顺序端口声明"""
        code = """
        module regs(
            input [7:0] d,
            output reg [7:0] q
        );
        endmodule
        """
        result = await generate_testbench(code)
        tb = result["testbench"]

        assert "reg [7:0] d" in tb
        assert "wire [7:0] q" in tb
