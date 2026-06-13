"""
Testbench 生成工具
"""

from ..utils import extract_ports, extract_top_module


async def generate_testbench(
    code: str,
    style: str = "basic",
    test_cases: int = 3
) -> dict:
    """
    自动生成 Testbench

    Args:
        code: Verilog 源代码
        style: 测试风格 (basic, comprehensive)
        test_cases: 测试用例数量

    Returns:
        生成的 Testbench 代码
    """
    top_module = extract_top_module(code)
    ports = extract_ports(code)

    # 分离时钟、复位和其他信号
    clk_name = None
    rst_name = None
    other_ports = []

    for port in ports:
        if port["name"] in ("clk", "clock"):
            clk_name = port["name"]
        elif port["name"] in ("rst_n", "rst", "reset"):
            rst_name = port["name"]
        else:
            other_ports.append(port)

    has_clk = clk_name is not None
    has_rst = rst_name is not None

    # 如果没有时钟，使用默认名（但不连接）
    if not has_clk:
        clk_name = "clk"

    # 生成 Testbench
    tb_code = f"""`timescale 1ns/1ps

module {top_module}_tb;
"""

    # 时钟和复位声明（如果需要）
    if has_clk:
        tb_code += f"""
    // 时钟和复位
    reg {clk_name};
"""
    if has_rst:
        tb_code += f"    reg {rst_name};\n"

    # 待测模块信号
    tb_code += """
    // 待测模块信号
"""

    # 声明信号
    for port in other_ports:
        width_str = f"[{port['width']-1}:0] " if port['width'] > 1 else ""
        if port["direction"] == "input":
            tb_code += f"    reg {width_str}{port['name']};\n"
        else:
            tb_code += f"    wire {width_str}{port['name']};\n"

    # 实例化待测模块
    tb_code += f"""
    // 实例化待测模块
    {top_module} uut (
"""

    # 连接端口
    port_connections = []
    if has_clk:
        port_connections.append(f"        .{clk_name}({clk_name})")
    if has_rst:
        port_connections.append(f"        .{rst_name}({rst_name})")
    for port in other_ports:
        port_connections.append(f"        .{port['name']}({port['name']})")
    tb_code += ",\n".join(port_connections) + "\n"
    tb_code += "    );\n"

    # 时钟生成（如果有时钟端口）
    if has_clk:
        tb_code += f"""
    // 时钟生成
    initial begin
        {clk_name} = 0;
        forever #5 {clk_name} = ~{clk_name};
    end
"""

    # 测试激励
    tb_code += """
    // 测试激励
    initial begin
"""

    # 复位逻辑（如果有复位端口）
    if has_rst:
        tb_code += f"""        // 复位
        {rst_name} = 0;
        #20;
        {rst_name} = 1;

"""

    # 添加测试激励
    for i in range(test_cases):
        tb_code += f"""
        // 测试用例 {i+1}
        #100;
"""

    # 结尾
    tb_code += f"""
        // 测试完成
        #100;
        $display("PASS");
        $finish;
    end

    // 波形输出
    initial begin
        $dumpfile("{top_module}_tb.vcd");
        $dumpvars(0, {top_module}_tb);
    end

    // 超时保护
    initial begin
        #100000;
        $display("TIMEOUT");
        $finish;
    end

endmodule
"""

    return {
        "success": True,
        "top_module": top_module,
        "testbench": tb_code,
        "style": style,
        "test_cases": test_cases,
        "ports": [p["name"] for p in other_ports],
        "has_clk": has_clk,
        "has_rst": has_rst,
    }
