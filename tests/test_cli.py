"""
CLI 命令测试
"""


import pytest
from click.testing import CliRunner

from superrtl.cli import main


@pytest.fixture
def runner():
    """CLI 测试运行器"""
    return CliRunner()


@pytest.fixture
def sample_verilog_file(tmp_path):
    """创建示例 Verilog 文件"""
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
    file_path = tmp_path / "counter.v"
    file_path.write_text(code)
    return file_path


@pytest.fixture
def sample_testbench_file(tmp_path):
    """创建示例 Testbench 文件"""
    code = """
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
    file_path = tmp_path / "counter_tb.v"
    file_path.write_text(code)
    return file_path


class TestMainCommand:
    """主命令测试"""

    def test_main_help(self, runner):
        """测试主命令帮助"""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "SuperRTL" in result.output

    def test_main_version(self, runner):
        """测试版本信息"""
        from superrtl import __version__
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestCompileCommand:
    """compile 命令测试"""

    def test_compile_help(self, runner):
        """测试 compile 帮助"""
        result = runner.invoke(main, ["compile", "--help"])
        assert result.exit_code == 0
        assert "编译" in result.output

    def test_compile_valid_file(self, runner, sample_verilog_file):
        """测试编译有效文件"""
        result = runner.invoke(main, ["compile", str(sample_verilog_file)])
        # 无论是否安装 iverilog，都不应该崩溃
        assert result.exit_code == 0

    def test_compile_with_top_module(self, runner, sample_verilog_file):
        """测试指定顶层模块"""
        result = runner.invoke(main, ["compile", str(sample_verilog_file), "--top", "counter"])
        assert result.exit_code == 0

    def test_compile_nonexistent_file(self, runner):
        """测试不存在的文件"""
        result = runner.invoke(main, ["compile", "nonexistent.v"])
        assert result.exit_code != 0


class TestSimulateCommand:
    """simulate 命令测试"""

    def test_simulate_help(self, runner):
        """测试 simulate 帮助"""
        result = runner.invoke(main, ["simulate", "--help"])
        assert result.exit_code == 0
        assert "仿真" in result.output

    def test_simulate_valid_files(self, runner, sample_verilog_file, sample_testbench_file):
        """测试仿真有效文件"""
        result = runner.invoke(main, [
            "simulate",
            str(sample_verilog_file),
            str(sample_testbench_file)
        ])
        assert result.exit_code == 0

    def test_simulate_with_timeout(self, runner, sample_verilog_file, sample_testbench_file):
        """测试带超时的仿真"""
        result = runner.invoke(main, [
            "simulate",
            str(sample_verilog_file),
            str(sample_testbench_file),
            "--timeout", "10"
        ])
        assert result.exit_code == 0

    def test_simulate_nonexistent_file(self, runner):
        """测试不存在的文件"""
        result = runner.invoke(main, ["simulate", "nonexistent.v", "tb.v"])
        assert result.exit_code != 0


class TestLintCommand:
    """lint 命令测试"""

    def test_lint_help(self, runner):
        """测试 lint 帮助"""
        result = runner.invoke(main, ["lint", "--help"])
        assert result.exit_code == 0
        assert "Lint" in result.output

    def test_lint_valid_file(self, runner, sample_verilog_file):
        """测试 lint 有效文件"""
        result = runner.invoke(main, ["lint", str(sample_verilog_file)])
        assert result.exit_code == 0

    def test_lint_with_style(self, runner, sample_verilog_file):
        """测试带风格的 lint"""
        result = runner.invoke(main, ["lint", str(sample_verilog_file), "--style", "strict"])
        assert result.exit_code == 0

    def test_lint_nonexistent_file(self, runner):
        """测试不存在的文件"""
        result = runner.invoke(main, ["lint", "nonexistent.v"])
        assert result.exit_code != 0


class TestSynthesizeCommand:
    """synthesize 命令测试"""

    def test_synthesize_help(self, runner):
        """测试 synthesize 帮助"""
        result = runner.invoke(main, ["synthesize", "--help"])
        assert result.exit_code == 0
        assert "综合" in result.output

    def test_synthesize_valid_file(self, runner, sample_verilog_file):
        """测试综合有效文件"""
        result = runner.invoke(main, ["synthesize", str(sample_verilog_file)])
        assert result.exit_code == 0

    def test_synthesize_with_target(self, runner, sample_verilog_file):
        """测试带目标的综合"""
        result = runner.invoke(main, [
            "synthesize",
            str(sample_verilog_file),
            "--target", "xilinx"
        ])
        assert result.exit_code == 0

    def test_synthesize_nonexistent_file(self, runner):
        """测试不存在的文件"""
        result = runner.invoke(main, ["synthesize", "nonexistent.v"])
        assert result.exit_code != 0


class TestTestbenchCommand:
    """testbench 命令测试"""

    def test_testbench_help(self, runner):
        """测试 testbench 帮助"""
        result = runner.invoke(main, ["testbench", "--help"])
        assert result.exit_code == 0
        assert "Testbench" in result.output

    def test_testbench_valid_file(self, runner, sample_verilog_file):
        """测试生成 testbench"""
        result = runner.invoke(main, ["testbench", str(sample_verilog_file)])
        assert result.exit_code == 0

    def test_testbench_with_output(self, runner, sample_verilog_file, tmp_path):
        """测试输出到文件"""
        output_file = tmp_path / "output_tb.v"
        result = runner.invoke(main, [
            "testbench",
            str(sample_verilog_file),
            "--output", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()

    def test_testbench_nonexistent_file(self, runner):
        """测试不存在的文件"""
        result = runner.invoke(main, ["testbench", "nonexistent.v"])
        assert result.exit_code != 0


class TestCheckToolsCommand:
    """check-tools 命令测试"""

    def test_check_tools(self, runner):
        """测试检查工具"""
        result = runner.invoke(main, ["check-tools"])
        assert result.exit_code == 0
        assert "EDA" in result.output


class TestMcpCommand:
    """mcp 命令测试"""

    def test_mcp_help(self, runner):
        """测试 mcp 帮助"""
        result = runner.invoke(main, ["mcp", "--help"])
        assert result.exit_code == 0
        assert "MCP" in result.output
