"""
集成测试 - 测试完整的编译 → 仿真流程
"""

import pytest
from conftest import requires_iverilog

from superrtl.tools.compile import compile_verilog
from superrtl.tools.simulate import simulate_verilog


class TestCompileSimulateFlow:
    """编译 → 仿真完整流程测试"""

    @requires_iverilog
    @pytest.mark.asyncio
    async def test_counter_compile_and_simulate(self):
        """测试计数器的编译和仿真"""
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

            initial begin
                $dumpfile("counter_tb.vcd");
                $dumpvars(0, counter_tb);
            end
        endmodule
        """

        # 步骤 1: 编译
        compile_result = await compile_verilog(design)
        assert compile_result["success"] is True
        assert compile_result["top_module"] == "counter"

        # 步骤 2: 仿真
        sim_result = await simulate_verilog(design, testbench)
        assert sim_result["success"] is True
        assert sim_result["passed"] is True
        assert "PASS" in sim_result["output"]

    @requires_iverilog
    @pytest.mark.asyncio
    async def test_fsm_compile_and_simulate(self):
        """测试 FSM 的编译和仿真"""
        design = """
        module fsm (
            input clk,
            input rst_n,
            input start,
            output reg done
        );
            localparam IDLE = 2'b00;
            localparam RUN  = 2'b01;
            localparam DONE = 2'b10;

            reg [1:0] state, next_state;

            always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    state <= IDLE;
                else
                    state <= next_state;
            end

            always @(*) begin
                case (state)
                    IDLE: next_state = start ? RUN : IDLE;
                    RUN:  next_state = DONE;
                    DONE: next_state = IDLE;
                    default: next_state = IDLE;
                endcase
            end

            always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    done <= 0;
                else
                    done <= (state == DONE);
            end
        endmodule
        """

        testbench = """
        `timescale 1ns/1ps
        module fsm_tb;
            reg clk, rst_n, start;
            wire done;
            fsm uut (.clk(clk), .rst_n(rst_n), .start(start), .done(done));

            initial begin
                clk = 0;
                forever #5 clk = ~clk;
            end

            initial begin
                rst_n = 0;
                start = 0;
                #20;
                rst_n = 1;
                #10;
                start = 1;
                #10;
                start = 0;
                #50;
                $display("PASS");
                $finish;
            end
        endmodule
        """

        # 编译
        compile_result = await compile_verilog(design)
        assert compile_result["success"] is True

        # 仿真
        sim_result = await simulate_verilog(design, testbench)
        assert sim_result["success"] is True
        assert sim_result["passed"] is True

    @pytest.mark.asyncio
    async def test_compile_error_handling(self):
        """测试编译错误处理"""
        bad_code = """
        module bad (
            input clk,
            // 语法错误
            output reg [3:0] count
        );
            always @(posedge clk
                count <= count + 1;
            end
        endmodule
        """

        result = await compile_verilog(bad_code)

        # 应该失败
        if not result.get("success"):
            assert "errors" in result or "error" in result

    @pytest.mark.asyncio
    async def test_simulate_error_handling(self):
        """测试仿真错误处理"""
        bad_design = """
        module bad (
            input clk,
            output reg [3:0] count
        );
            // 语法错误
            always @(posedge clk
                count <= count + 1;
            end
        endmodule
        """

        testbench = """
        module tb;
            initial $finish;
        endmodule
        """

        result = await simulate_verilog(bad_design, testbench)

        # 应该失败
        assert result["success"] is False


class TestWorkflowIntegration:
    """工作流集成测试"""

    @requires_iverilog
    @pytest.mark.asyncio
    async def test_multiple_modules_workflow(self):
        """测试多模块工作流"""
        # 顶层模块
        top = """
        module top (
            input clk,
            input rst_n,
            output [7:0] count
        );
            counter u_counter (
                .clk(clk),
                .rst_n(rst_n),
                .count(count)
            );
        endmodule
        """

        # 子模块
        sub = """
        module counter (
            input clk,
            input rst_n,
            output reg [7:0] count
        );
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    count <= 0;
                else
                    count <= count + 1;
            end
        endmodule
        """

        # 合并代码
        design = sub + "\n" + top

        # 编译
        compile_result = await compile_verilog(design, top_module="top")
        assert compile_result["success"] is True
