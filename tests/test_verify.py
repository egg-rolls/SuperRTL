"""
综合验证测试
"""

import pytest
from conftest import requires_iverilog

from superrtl.tools.verify import verify_design


class TestVerifyDesign:
    """综合验证功能测试"""

    @pytest.mark.asyncio
    async def test_missing_design_files(self):
        """缺少设计文件应返回错误"""
        result = await verify_design(design_files=[])
        assert result["success"] is False
        assert "设计文件" in result["error"]

    @pytest.mark.asyncio
    async def test_nonexistent_design_file(self):
        """不存在的设计文件应返回错误"""
        result = await verify_design(design_files=["nonexistent.v"])
        assert result["success"] is False
        assert "不存在" in result["error"]

    @pytest.mark.asyncio
    async def test_nonexistent_testbench_file(self):
        """不存在的测试平台文件应返回错误"""
        # 创建一个临时设计文件
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".v", delete=False) as f:
            f.write("module test_module; endmodule")
            design_file = f.name

        result = await verify_design(
            design_files=[design_file],
            testbench_file="nonexistent_tb.v",
        )
        assert result["success"] is False
        assert "不存在" in result["error"]

        # 清理
        Path(design_file).unlink()

    @pytest.mark.asyncio
    async def test_skip_all_steps(self):
        """跳过所有步骤应返回成功"""
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode="w", suffix=".v", delete=False) as f:
            f.write("module test_module; endmodule")
            design_file = f.name

        result = await verify_design(
            design_files=[design_file],
            skip=["compile", "simulate", "lint", "review"],
        )
        assert result["success"] is True
        assert result["passed"] is True
        assert result["steps"] == {}

        # 清理
        Path(design_file).unlink()


class TestVerifyDesignIntegration:
    """综合验证集成测试"""

    @requires_iverilog
    @pytest.mark.asyncio
    async def test_full_verify(self, tmp_path):
        """测试完整验证流程"""
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
        design_file = tmp_path / "counter.v"
        design_file.write_text(design, encoding="utf-8")

        testbench = """
        `timescale 1ns/1ps
        module counter_tb;
            reg clk, rst_n;
            wire [3:0] count;
            counter uut (.clk(clk), .rst_n(rst_n), .count(count));
            initial begin clk = 0; forever #5 clk = ~clk; end
            initial begin
                rst_n = 0; #20; rst_n = 1; #100;
                $display("PASS");
                $finish;
            end
        endmodule
        """

        result = await verify_design(
            design_files=[str(design_file)],
            testbench=testbench,
            timeout=30,
        )

        assert result["success"] is True
        assert "compile" in result["steps"]
        assert "simulate" in result["steps"]
        assert "lint" in result["steps"]
        assert "review" in result["steps"]
        assert result["duration"] > 0

    @requires_iverilog
    @pytest.mark.asyncio
    async def test_verify_with_skip(self, tmp_path):
        """测试跳过某些步骤"""
        design = """
        module simple (
            input a,
            output b
        );
            assign b = a;
        endmodule
        """
        design_file = tmp_path / "simple.v"
        design_file.write_text(design, encoding="utf-8")

        result = await verify_design(
            design_files=[str(design_file)],
            skip=["simulate", "lint"],
        )

        assert result["success"] is True
        assert "compile" in result["steps"]
        assert "simulate" not in result["steps"]
        assert "lint" not in result["steps"]
        assert "review" in result["steps"]
