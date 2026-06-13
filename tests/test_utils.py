"""
Utils 工具函数测试
"""

from superrtl.utils import extract_ports, extract_top_module


class TestExtractTopModule:
    """extract_top_module 测试"""

    def test_simple_module(self):
        """测试简单模块名提取"""
        code = "module counter; endmodule"
        assert extract_top_module(code) == "counter"

    def test_module_with_ports(self):
        """测试带端口的模块"""
        code = """
        module counter (
            input clk,
            output reg [3:0] count
        );
        endmodule
        """
        assert extract_top_module(code) == "counter"

    def test_module_with_params(self):
        """测试带参数的模块"""
        code = """
        module fifo #(
            parameter WIDTH = 8
        )(input clk);
        endmodule
        """
        assert extract_top_module(code) == "fifo"

    def test_no_module(self):
        """测试无模块时返回默认值"""
        code = "wire a = b;"
        assert extract_top_module(code) == "top"

    def test_empty_string(self):
        """测试空字符串"""
        assert extract_top_module("") == "top"

    def test_multiple_modules(self):
        """测试多模块时返回第一个"""
        code = """
        module first; endmodule
        module second; endmodule
        """
        assert extract_top_module(code) == "first"

    def test_module_with_numbers(self):
        """测试模块名包含数字"""
        code = "module counter8bit; endmodule"
        assert extract_top_module(code) == "counter8bit"

    def test_module_with_underscore(self):
        """测试模块名包含下划线"""
        code = "module my_counter_top; endmodule"
        assert extract_top_module(code) == "my_counter_top"


class TestExtractPorts:
    """extract_ports 测试"""

    def test_simple_input(self):
        """测试简单输入端口"""
        code = "module test(input clk); endmodule"
        ports = extract_ports(code)
        assert len(ports) == 1
        assert ports[0]["name"] == "clk"
        assert ports[0]["direction"] == "input"
        assert ports[0]["width"] == 1

    def test_simple_output(self):
        """测试简单输出端口"""
        code = "module test(output out); endmodule"
        ports = extract_ports(code)
        assert len(ports) == 1
        assert ports[0]["name"] == "out"
        assert ports[0]["direction"] == "output"

    def test_output_reg(self):
        """测试 reg 输出端口"""
        code = "module test(output reg [3:0] count); endmodule"
        ports = extract_ports(code)
        assert len(ports) == 1
        assert ports[0]["name"] == "count"
        assert ports[0]["direction"] == "output"
        assert ports[0]["width"] == 4

    def test_multiple_ports(self):
        """测试多端口"""
        code = """
        module test(
            input clk,
            input rst_n,
            output reg [7:0] data,
            output valid
        );
        endmodule
        """
        ports = extract_ports(code)
        assert len(ports) == 4
        names = [p["name"] for p in ports]
        assert "clk" in names
        assert "rst_n" in names
        assert "data" in names
        assert "valid" in names

    def test_wide_bus(self):
        """测试宽总线"""
        code = "module test(input [31:0] data); endmodule"
        ports = extract_ports(code)
        assert ports[0]["width"] == 32

    def test_no_ports(self):
        """测试无端口"""
        code = "module test; endmodule"
        ports = extract_ports(code)
        assert len(ports) == 0

    def test_empty_string(self):
        """测试空字符串"""
        ports = extract_ports("")
        assert len(ports) == 0
