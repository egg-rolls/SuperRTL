"""
SuperRTL CLI 命令行工具
"""

import asyncio
import json
from pathlib import Path

import click
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from . import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="superrtl")
def main():
    """SuperRTL - Verilog EDA 工具的 MCP/CLI 客户端"""
    pass


# ============ Skills 命令组 ============


@main.group()
def skills():
    """管理 Verilog 设计模式 Skills"""
    pass


@skills.command("list")
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def skills_list(as_json: bool):
    """列出所有可用的 Skills"""
    from .resources import list_skills

    result = asyncio.run(list_skills())
    data = json.loads(result)

    if as_json:
        console.print(result)
        return

    table = Table(title="Available Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description")
    table.add_column("Tags", style="dim")

    for skill in data.get("skills", []):
        tags = ", ".join(skill.get("tags", []))
        table.add_row(
            skill.get("display_name", skill.get("name", "")),
            skill.get("version", "1.0.0"),
            skill.get("description", ""),
            tags,
        )

    console.print(table)
    console.print(f"\nTotal: {data.get('count', 0)} skills")


@skills.command("show")
@click.argument("name")
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def skills_show(name: str, as_json: bool):
    """显示指定 Skill 的详细内容"""
    from .resources import get_skill

    result = asyncio.run(get_skill(name))
    data = json.loads(result)

    if "error" in data:
        console.print(f"[FAIL] [red]{data['error']}[/red]")
        if "available" in data:
            console.print(f"Available skills: {', '.join(data['available'])}")
        return

    if as_json:
        console.print(result)
        return

    console.print(f"[INFO] [blue]{data.get('name', name)}[/blue]")
    console.print(f"   Version: {data.get('version', '1.0.0')}")
    console.print(f"   Description: {data.get('description', '')}")
    console.print(f"   Tags: {', '.join(data.get('tags', []))}")
    console.print("\n" + "=" * 60 + "\n")
    console.print(data.get("content", ""))


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--top", "-t", default="", help="顶层模块名")
def compile(file: str, top: str):
    """编译 Verilog 代码"""
    from .tools import compile_verilog

    code = Path(file).read_text()
    result = asyncio.run(compile_verilog(code, top))

    if result.get("success"):
        console.print(f"[OK] [green]编译成功[/green]: {result.get('top_module')}")
        console.print(f"   耗时: {result.get('duration')}s")
    else:
        console.print("[FAIL] [red]编译失败[/red]")
        for error in result.get("errors", []):
            console.print(f"   {error}")


@main.command()
@click.argument("design", type=click.Path(exists=True))
@click.argument("testbench", type=click.Path(exists=True))
@click.option("--timeout", "-t", default=30, help="超时时间 (秒)")
def simulate(design: str, testbench: str, timeout: int):
    """运行 Verilog 仿真"""
    from .tools import simulate_verilog

    design_code = Path(design).read_text()
    tb_code = Path(testbench).read_text()
    result = asyncio.run(simulate_verilog(design_code, tb_code, timeout))

    if result.get("success"):
        if result.get("passed"):
            console.print("[OK] [green]仿真通过[/green]")
        else:
            console.print("[FAIL] [red]仿真失败[/red]")
        console.print(f"   耗时: {result.get('duration')}s")
        if result.get("output"):
            console.print(f"   输出: {result['output'][:200]}")
    else:
        console.print(f"[FAIL] [red]仿真错误[/red]: {result.get('error')}")


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--style", "-s", default="default", type=click.Choice(["default", "strict", "relaxed"])
)
def lint(file: str, style: str):
    """Lint 检查"""
    from .tools import lint_verilog

    code = Path(file).read_text()
    result = asyncio.run(lint_verilog(code, style))

    if result.get("success"):
        console.print("[OK] [green]Lint 通过[/green]")
    else:
        console.print("[FAIL] [red]Lint 失败[/red]")

    if result.get("warnings"):
        console.print(f"   警告: {len(result['warnings'])}")
        for w in result["warnings"][:5]:
            console.print(f"     - {w}")

    if result.get("errors"):
        console.print(f"   错误: {len(result['errors'])}")
        for e in result["errors"][:5]:
            console.print(f"     - {e}")


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--top", "-t", default="", help="顶层模块名")
@click.option("--target", default="generic", type=click.Choice(["generic", "xilinx", "ice40"]))
def synthesize(file: str, top: str, target: str):
    """综合检查"""
    from .tools import synthesize_verilog

    code = Path(file).read_text()
    result = asyncio.run(synthesize_verilog(code, top, target))

    if result.get("success"):
        console.print(f"[OK] [green]综合通过[/green]: {result.get('top_module')}")
        if result.get("resources"):
            console.print("   资源:")
            for k, v in result["resources"].items():
                console.print(f"     {k}: {v}")
    else:
        console.print("[FAIL] [red]综合失败[/red]")
        for error in result.get("errors", []):
            console.print(f"   {error}")


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--style", "-s", default="basic", type=click.Choice(["basic", "comprehensive"]))
@click.option("--cases", "-c", default=3, help="测试用例数量")
@click.option("--output", "-o", default="", help="输出文件路径")
def testbench(file: str, style: str, cases: int, output: str):
    """生成 Testbench"""
    from .tools import generate_testbench

    code = Path(file).read_text()
    result = asyncio.run(generate_testbench(code, style, cases))

    if result.get("success"):
        tb_code = result["testbench"]

        if output:
            Path(output).write_text(tb_code)
            console.print(f"[OK] [green]Testbench 已保存[/green]: {output}")
        else:
            console.print(Syntax(tb_code, "verilog"))
    else:
        console.print("[FAIL] [red]生成失败[/red]")


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--signals", "-s", multiple=True, help="要分析的信号")
def waveform(file: str, signals: tuple):
    """分析波形"""
    from .tools import analyze_waveform

    result = asyncio.run(
        analyze_waveform(vcd_file=file, signals=list(signals) if signals else None)
    )

    if result.get("success"):
        console.print("[INFO] [blue]波形分析[/blue]")
        console.print(f"   信号数: {len(result.get('signals', {}))}")
        if result.get("ascii_waveform"):
            console.print("\n" + result["ascii_waveform"])
    else:
        console.print(f"[FAIL] [red]分析失败[/red]: {result.get('error')}")


@main.command("check-tools")
def check_tools_cmd():
    """检查 EDA 工具安装状态"""
    from .setup import check_tools

    check_tools()


@main.command()
@click.option("--force", "-f", is_flag=True, help="强制重新安装")
def setup(force: bool):
    """安装 EDA 工具（首次运行时自动下载）"""
    from .setup import install_tools

    install_tools(force=force)


@main.command()
def uninstall():
    """卸载 EDA 工具"""
    from .setup import uninstall_tools

    if click.confirm("确定要卸载 EDA 工具吗？"):
        uninstall_tools()


@main.command()
@click.option("--transport", "-t", default="stdio", type=click.Choice(["stdio", "sse"]))
@click.option("--port", "-p", default=8080, help="SSE 端口")
def mcp(transport: str, port: int):
    """启动 MCP Server"""
    from .server import main as server_main

    if transport == "stdio":
        console.print("[START] [green]启动 SuperRTL MCP Server (stdio 模式)[/green]")
        server_main()
    else:
        console.print(f"[START] [green]启动 SuperRTL MCP Server (SSE 模式, 端口: {port})[/green]")
        console.print("[yellow]SSE 模式暂未实现，请使用 stdio 模式[/yellow]")


if __name__ == "__main__":
    main()
