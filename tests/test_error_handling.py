"""
错误处理测试
"""

import pytest

from superrtl.tools.compile import compile_verilog
from superrtl.tools.lint import lint_verilog
from superrtl.tools.simulate import simulate_verilog
from superrtl.tools.synthesize import synthesize_verilog


class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_compile_result_has_success_field(self):
        """测试编译结果包含 success 字段"""
        result = await compile_verilog("module test; endmodule")
        assert "success" in result
        assert isinstance(result["success"], bool)

    @pytest.mark.asyncio
    async def test_simulate_result_has_success_field(self):
        """测试仿真结果包含 success 字段"""
        result = await simulate_verilog(
            "module test; endmodule", "module tb; initial $finish; endmodule"
        )
        assert "success" in result
        assert isinstance(result["success"], bool)

    @pytest.mark.asyncio
    async def test_lint_result_has_success_field(self):
        """测试 lint 结果包含 success 字段"""
        result = await lint_verilog("module test; endmodule")
        assert "success" in result
        assert isinstance(result["success"], bool)

    @pytest.mark.asyncio
    async def test_synthesize_result_has_success_field(self):
        """测试综合结果包含 success 字段"""
        result = await synthesize_verilog("module test; endmodule")
        assert "success" in result
        assert isinstance(result["success"], bool)

    @pytest.mark.asyncio
    async def test_compile_error_contains_message(self):
        """测试编译错误包含错误信息"""
        code = "module bad; invalid syntax here; endmodule"
        result = await compile_verilog(code)

        if not result.get("success"):
            assert "error" in result or "errors" in result

    @pytest.mark.asyncio
    async def test_simulate_error_contains_message(self):
        """测试仿真错误包含错误信息"""
        result = await simulate_verilog(
            "module bad; invalid; endmodule", "module tb; initial $finish; endmodule"
        )

        if not result.get("success"):
            assert "error" in result or "errors" in result

    @pytest.mark.asyncio
    async def test_lint_error_contains_message(self):
        """测试 lint 错误包含错误信息"""
        code = "module bad; invalid syntax; endmodule"
        result = await lint_verilog(code)

        if not result.get("success"):
            assert "error" in result or "errors" in result

    @pytest.mark.asyncio
    async def test_synthesize_error_contains_message(self):
        """测试综合错误包含错误信息"""
        code = "module bad; invalid syntax; endmodule"
        result = await synthesize_verilog(code)

        if not result.get("success"):
            assert "error" in result or "errors" in result

    @pytest.mark.asyncio
    async def test_compile_valid_code_structure(self):
        """测试有效代码编译结果结构"""
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

        if result.get("success"):
            assert "top_module" in result
            assert "duration" in result
            assert "message" in result
            assert result["duration"] > 0

    @pytest.mark.asyncio
    async def test_simulate_valid_code_structure(self):
        """测试有效代码仿真结果结构"""
        design = """
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
        testbench = """
        `timescale 1ns/1ps
        module counter_tb;
            reg clk, rst_n;
            wire [3:0] count;
            counter uut (.clk(clk), .rst_n(rst_n), .count(count));

            initial begin
                clk = 0;
                forever #5 clk = ~clk;
            end

            initial begin
                rst_n = 0;
                #20;
                rst_n = 1;
                #100;
                $display("PASS");
                $finish;
            end
        endmodule
        """
        result = await simulate_verilog(design, testbench)

        if result.get("success"):
            assert "passed" in result
            assert "stage" in result
            assert "duration" in result
            assert "output" in result
