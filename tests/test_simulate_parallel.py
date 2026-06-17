"""
并行仿真测试
"""

import asyncio

import pytest
from conftest import requires_iverilog

from superrtl.tools.simulate_parallel import simulate_parallel


class TestSimulateParallel:
    """并行仿真功能测试"""

    def test_missing_design_files(self):
        """缺少设计文件应返回错误"""
        result = asyncio.run(
            simulate_parallel(
                design_file_paths=[],
                testbench_files=["tb.v"],
            )
        )
        assert result["success"] is False
        assert "设计文件" in result["error"]

    def test_missing_testbench_files(self):
        """缺少测试平台文件应返回错误"""
        result = asyncio.run(
            simulate_parallel(
                design_file_paths=["design.v"],
                testbench_files=[],
            )
        )
        assert result["success"] is False
        assert "测试平台" in result["error"]

    def test_invalid_design_files_type(self):
        """design_file_paths 非列表应返回错误"""
        result = asyncio.run(
            simulate_parallel(
                design_file_paths="design.v",
                testbench_files=["tb.v"],
            )
        )
        assert result["success"] is False
        assert "列表" in result["error"]

    def test_invalid_testbench_files_type(self):
        """testbench_files 非列表应返回错误"""
        result = asyncio.run(
            simulate_parallel(
                design_file_paths=["design.v"],
                testbench_files="tb.v",
            )
        )
        assert result["success"] is False
        assert "列表" in result["error"]


class TestSimulateParallelIntegration:
    """并行仿真集成测试"""

    @requires_iverilog
    @pytest.mark.asyncio
    async def test_parallel_simulation(self, tmp_path):
        """测试并行仿真多个 testbench"""
        # 设计文件
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

        # 多个 testbench
        tb1 = """
        `timescale 1ns/1ps
        module tb1;
            reg clk, rst_n;
            wire [3:0] count;
            counter uut (.clk(clk), .rst_n(rst_n), .count(count));
            initial begin clk = 0; forever #5 clk = ~clk; end
            initial begin
                rst_n = 0; #20; rst_n = 1; #50;
                $display("TB1 PASS");
                $finish;
            end
        endmodule
        """

        tb2 = """
        `timescale 1ns/1ps
        module tb2;
            reg clk, rst_n;
            wire [3:0] count;
            counter uut (.clk(clk), .rst_n(rst_n), .count(count));
            initial begin clk = 0; forever #5 clk = ~clk; end
            initial begin
                rst_n = 0; #20; rst_n = 1; #100;
                $display("TB2 PASS");
                $finish;
            end
        endmodule
        """

        tb1_file = tmp_path / "tb1.v"
        tb1_file.write_text(tb1, encoding="utf-8")
        tb2_file = tmp_path / "tb2.v"
        tb2_file.write_text(tb2, encoding="utf-8")

        result = await simulate_parallel(
            design_file_paths=[str(design_file)],
            testbench_files=[str(tb1_file), str(tb2_file)],
            timeout=30,
            max_concurrent=2,
        )

        assert result["success"] is True
        assert result["total"] == 2
        assert result["passed_count"] == 2
        assert result["failed_count"] == 0
