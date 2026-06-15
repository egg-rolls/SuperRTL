"""
共享测试配置和 fixtures
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

# ============ EDA 工具可用性检查 ============


def iverilog_works() -> bool:
    """检查 iverilog 是否可用"""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.v"
            test_file.write_text("module test; endmodule", encoding="utf-8")
            output_file = Path(tmpdir) / "test.vvp"
            result = subprocess.run(
                ["iverilog", "-o", str(output_file), str(test_file)],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
    except Exception:
        return False


def sby_works() -> bool:
    """检查 SymbiYosys (sby) 是否可用"""
    try:
        result = subprocess.run(
            ["sby", "--help"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


# ============ Pytest Skip Markers ============

requires_iverilog = pytest.mark.skipif(not iverilog_works(), reason="iverilog 不能正常工作")
requires_sby = pytest.mark.skipif(not sby_works(), reason="SymbiYosys (sby) 不能正常工作")


# ============ 共享 Verilog 代码 Fixtures ============


COUNTER_CODE = """\
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

COUNTER_TESTBENCH = """\
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

SIMPLE_MODULE_CODE = """\
module simple (
    input a,
    input b,
    output y
);
    assign y = a & b;
endmodule
"""


@pytest.fixture
def counter_code():
    """返回一个简单的 counter 模块代码"""
    return COUNTER_CODE


@pytest.fixture
def counter_testbench():
    """返回 counter 模块的 testbench"""
    return COUNTER_TESTBENCH


@pytest.fixture
def simple_module_code():
    """返回一个简单的组合逻辑模块代码"""
    return SIMPLE_MODULE_CODE
