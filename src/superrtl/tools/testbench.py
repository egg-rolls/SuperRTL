"""
Testbench 生成工具

生成包含实际激励和自检查逻辑的 Testbench。
"""

from ..utils import extract_ports, extract_top_module
from ..validation import ValidationError, validate_code


async def generate_testbench(code: str, style: str = "basic", test_cases: int = 3) -> dict:
    """
    自动生成 Testbench

    Args:
        code: Verilog 源代码
        style: 测试风格 (basic, comprehensive)
        test_cases: 测试用例数量

    Returns:
        生成的 Testbench 代码
    """
    try:
        validate_code(code, "code")
        top_module = extract_top_module(code)
        ports = extract_ports(code)
    except ValidationError as e:
        return {"success": False, "error": e.message, "suggestion": e.suggestion}
    except Exception as e:
        return {
            "success": False,
            "error": f"解析代码失败: {e}",
            "suggestion": "确保代码包含有效的 module 定义",
        }

    if not top_module:
        return {
            "success": False,
            "error": "未找到顶层模块定义",
            "suggestion": "确保代码包含 'module xxx (...)' 定义",
        }

    # 分离时钟、复位和其他信号
    clk_name = None
    rst_name = None
    rst_active_low = False
    input_ports = []
    output_ports = []

    for port in ports:
        pname = port["name"]
        if pname in ("clk", "clock"):
            clk_name = pname
        elif pname in ("rst_n", "reset_n"):
            rst_name = pname
            rst_active_low = True
        elif pname in ("rst", "reset"):
            rst_name = pname
            rst_active_low = False
        elif port["direction"] == "input":
            input_ports.append(port)
        else:
            output_ports.append(port)

    has_clk = clk_name is not None
    has_rst = rst_name is not None

    if not has_clk:
        clk_name = "clk"

    # 综合模式增加测试用例数
    if style == "comprehensive":
        test_cases = max(test_cases, 5)

    # 开始生成代码
    lines = []

    # 头部
    lines.append("`timescale 1ns/1ps")
    lines.append("")
    lines.append(f"module {top_module}_tb;")
    lines.append("")

    # 参数
    if has_clk:
        lines.append("    // 参数")
        lines.append("    parameter CLK_PERIOD = 10;")
        lines.append("")

    # 信号声明
    if has_clk:
        lines.append(f"    reg {clk_name};")
    if has_rst:
        lines.append(f"    reg {rst_name};")

    if input_ports or output_ports:
        lines.append("")
        lines.append("    // 待测模块信号")

    for port in input_ports:
        width = _width_str(port["width"])
        lines.append(f"    reg {width}{port['name']};")

    for port in output_ports:
        width = _width_str(port["width"])
        lines.append(f"    wire {width}{port['name']};")

    # 综合模式：添加检查变量
    if style == "comprehensive":
        lines.append("")
        lines.append("    // 测试控制")
        lines.append("    integer test_count = 0;")
        lines.append("    integer pass_count = 0;")
        lines.append("    integer error_count = 0;")

    # 实例化
    lines.append("")
    lines.append("    // 实例化待测模块")
    lines.append(f"    {top_module} uut (")

    connections = []
    if has_clk:
        connections.append(f"        .{clk_name}({clk_name})")
    if has_rst:
        connections.append(f"        .{rst_name}({rst_name})")
    for port in input_ports + output_ports:
        connections.append(f"        .{port['name']}({port['name']})")
    lines.append(",\n".join(connections))
    lines.append("    );")
    lines.append("")

    # 时钟生成
    if has_clk:
        lines.append("    // 时钟生成")
        lines.append("    initial begin")
        lines.append(f"        {clk_name} = 0;")
        lines.append(f"        forever #(CLK_PERIOD/2) {clk_name} = ~{clk_name};")
        lines.append("    end")
        lines.append("")

    # 测试任务（综合模式）
    if style == "comprehensive":
        lines.append("    // 检查任务")
        lines.append("    task check;")
        lines.append("        input [255:0] test_name;")
        lines.append("        input condition;")
        lines.append("        begin")
        lines.append("            test_count = test_count + 1;")
        lines.append("            if (condition) begin")
        lines.append('                $display("[PASS] %0s", test_name);')
        lines.append("                pass_count = pass_count + 1;")
        lines.append("            end else begin")
        lines.append('                $display("[FAIL] %0s", test_name);')
        lines.append("                error_count = error_count + 1;")
        lines.append("            end")
        lines.append("        end")
        lines.append("    endtask")
        lines.append("")

    # 测试激励
    lines.append("    // 测试激励")
    lines.append("    initial begin")

    # 复位
    if has_rst:
        rst_val = "0" if rst_active_low else "1"
        rst_release = "1" if rst_active_low else "0"
        lines.append("        // 复位")
        lines.append(f"        {rst_name} = {rst_val};")
        for port in input_ports:
            lines.append(f"        {port['name']} = 0;")
        lines.append("        #(CLK_PERIOD * 5);")
        lines.append(f"        {rst_name} = {rst_release};")
        lines.append(f"        @(posedge {clk_name});")
        lines.append("")
    else:
        for port in input_ports:
            lines.append(f"        {port['name']} = 0;")
        lines.append("")

    # 生成测试用例
    for i in range(test_cases):
        lines.append(f"        // 测试用例 {i + 1}: {_generate_test_comment(i, input_ports)}")

        for port in input_ports:
            value = _generate_test_value(port, i, test_cases)
            lines.append(f"        {port['name']} = {value};")

        wait_cycles = _get_wait_cycles(style)
        if has_clk:
            lines.append(f"        repeat({wait_cycles}) @(posedge {clk_name});")
        else:
            lines.append(f"        #{wait_cycles * 10};")

        # 综合模式：添加检查
        if style == "comprehensive" and output_ports:
            for port in output_ports:
                lines.append(
                    f'        check("Test {i + 1}: {port["name"]}", {port["name"]} !== 1\'bx);'
                )

        lines.append("")

    # 综合模式：随机测试
    if style == "comprehensive":
        lines.append("        // 随机测试")
        lines.append("        repeat(10) begin")
        for port in input_ports:
            lines.append(f"            {port['name']} = $random;")
        if has_clk:
            lines.append(f"            @(posedge {clk_name});")
        else:
            lines.append("            #10;")
        lines.append("        end")
        lines.append("")

    # 测试完成
    if style == "comprehensive":
        lines.append("        // 测试统计")
        lines.append('        $display("");')
        lines.append('        $display("=== Test Summary ===");')
        lines.append('        $display("Total: %0d", test_count);')
        lines.append('        $display("Pass:  %0d", pass_count);')
        lines.append('        $display("Fail:  %0d", error_count);')
        lines.append("        if (error_count == 0)")
        lines.append('            $display("PASS");')
        lines.append("        else")
        lines.append('            $display("FAIL");')
    else:
        lines.append("        // 测试完成")
        lines.append('        $display("PASS");')

    lines.append("        $finish;")
    lines.append("    end")
    lines.append("")

    # 波形输出
    lines.append("    // 波形输出")
    lines.append("    initial begin")
    lines.append(f'        $dumpfile("{top_module}_tb.vcd");')
    lines.append(f"        $dumpvars(0, {top_module}_tb);")
    lines.append("    end")
    lines.append("")

    # 超时保护
    timeout = 100000 if style == "basic" else 1000000
    lines.append("    // 超时保护")
    lines.append("    initial begin")
    lines.append(f"        #{timeout};")
    lines.append('        $display("TIMEOUT");')
    lines.append("        $finish;")
    lines.append("    end")
    lines.append("")
    lines.append("endmodule")

    tb_code = "\n".join(lines)

    return {
        "success": True,
        "top_module": top_module,
        "testbench": tb_code,
        "style": style,
        "test_cases": test_cases,
        "ports": [p["name"] for p in input_ports + output_ports],
        "has_clk": has_clk,
        "has_rst": has_rst,
    }


def _width_str(width: int) -> str:
    """生成位宽字符串"""
    if width > 1:
        return f"[{width - 1}:0] "
    return ""


def _generate_test_comment(index: int, input_ports: list) -> str:
    """生成测试用例注释"""
    if index == 0:
        return "零值测试"
    elif index == 1:
        return "全1测试"
    elif index == 2:
        return "递增测试"
    elif index == 3:
        return "交替测试"
    else:
        return f"随机测试 {index - 3}"


def _generate_test_value(port: dict, index: int, total: int) -> str:
    """生成测试值"""
    width = port["width"]

    if index == 0:
        # 零值
        return f"{width}'d0" if width > 1 else "0"
    elif index == 1:
        # 全1
        if width > 1:
            return f"{width}'h{'f' * ((width + 3) // 4)}"
        return "1"
    elif index == 2:
        # 递增
        if width > 1:
            return f"{width}'d1"
        return "1"
    elif index == 3:
        # 交替
        if width > 1:
            return f"{width}'h{'a' * ((width + 3) // 4)}"
        return "1"
    else:
        # 随机
        if width > 1:
            return "$random"
        return "$random % 2"


def _get_wait_cycles(style: str) -> int:
    """获取等待周期数"""
    if style == "comprehensive":
        return 5
    return 10
