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


def _output_result(result: dict, as_json: bool):
    """统一输出结果"""
    if as_json:
        console.print(json.dumps(result, ensure_ascii=False, indent=2))


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


# ============ 工具命令 ============


def _resolve_files(patterns: tuple) -> list[str]:
    """解析文件模式，支持 glob 和目录"""
    import glob as glob_mod

    files = []
    for pattern in patterns:
        p = Path(pattern)
        if p.is_dir():
            # 目录：递归查找 .v 和 .sv 文件
            files.extend(sorted(str(f) for f in p.rglob("*.v")))
            files.extend(sorted(str(f) for f in p.rglob("*.sv")))
        elif "*" in pattern or "?" in pattern:
            # Glob 模式
            matched = sorted(glob_mod.glob(pattern))
            if not matched:
                console.print(f"[WARN] [yellow]未匹配到文件: {pattern}[/yellow]")
            files.extend(matched)
        elif p.exists():
            files.append(str(p))
        else:
            console.print(f"[WARN] [yellow]文件不存在: {pattern}[/yellow]")

    # 去重保持顺序
    seen = set()
    unique = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


@main.command()
@click.argument("files", nargs=-1, required=True)
@click.option("--top", "-t", default="", help="顶层模块名")
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def compile(files: tuple, top: str, as_json: bool):
    """编译 Verilog 代码

    支持多文件、glob 模式、目录：

    \b
    superrtl compile top.v
    superrtl compile src/*.v
    superrtl compile src/ top.v
    superrtl compile src/ --top my_module
    """
    from .tools import compile_verilog

    resolved = _resolve_files(files)
    if not resolved:
        console.print("[FAIL] [red]未找到任何文件[/red]")
        raise SystemExit(1)

    with console.status(f"[bold blue]编译 {len(resolved)} 个文件..."):
        result = asyncio.run(compile_verilog(files=resolved, top_module=top))

    if as_json:
        _output_result(result, True)
        return

    if result.get("success"):
        console.print(f"[OK] [green]编译成功[/green]: {result.get('top_module')}")
        console.print(f"   文件数: {result.get('source_files', 1)}")
        console.print(f"   耗时: {result.get('duration')}s")
    else:
        console.print("[FAIL] [red]编译失败[/red]")
        for error in result.get("errors", []):
            if isinstance(error, dict):
                console.print(
                    f"   {error.get('file', '')}:{error.get('line', '')} {error.get('message', '')}"
                )
            else:
                console.print(f"   {error}")


@main.command()
@click.argument("testbench", type=click.Path(exists=True))
@click.argument("designs", nargs=-1, required=True)
@click.option("--timeout", "-t", default=30, help="超时时间 (秒)")
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def simulate(testbench: str, designs: tuple, timeout: int, as_json: bool):
    """运行 Verilog 仿真

    测试平台在前，设计文件在后：

    \b
    superrtl simulate tb.v top.v
    superrtl simulate tb.v src/*.v
    superrtl simulate tb.v src/
    """
    from .tools import simulate_verilog

    design_paths = _resolve_files(designs)
    if not design_paths:
        console.print("[FAIL] [red]未找到设计文件[/red]")
        return

    tb_code = Path(testbench).read_text(encoding="utf-8")

    with console.status(f"[bold blue]仿真 {len(design_paths)} 个设计文件..."):
        result = asyncio.run(
            simulate_verilog(
                testbench=tb_code,
                timeout=timeout,
                design_file_paths=design_paths,
            )
        )

    if as_json:
        _output_result(result, True)
        return

    if result.get("success"):
        if result.get("passed"):
            console.print("[OK] [green]仿真通过[/green]")
        else:
            console.print("[FAIL] [red]仿真失败[/red]")
        console.print(f"   文件数: {result.get('source_files', 1)}")
        console.print(f"   耗时: {result.get('duration')}s")
        if result.get("output"):
            console.print(f"   输出:\n{result['output']}")
        if result.get("vcd_file"):
            console.print(f"   VCD 文件: {result['vcd_file']}")
    else:
        console.print(f"[FAIL] [red]仿真错误[/red]: {result.get('error')}")


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--style", "-s", default="default", type=click.Choice(["default", "strict", "relaxed"])
)
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def lint(file: str, style: str, as_json: bool):
    """Lint 检查"""
    from .tools import lint_verilog

    code = Path(file).read_text(encoding="utf-8")
    with console.status("[bold blue]Lint 检查中..."):
        result = asyncio.run(lint_verilog(code, style))

    if as_json:
        _output_result(result, True)
        return

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
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def synthesize(file: str, top: str, target: str, as_json: bool):
    """综合检查"""
    from .tools import synthesize_verilog

    code = Path(file).read_text(encoding="utf-8")
    with console.status("[bold blue]综合中..."):
        result = asyncio.run(synthesize_verilog(code, top, target))

    if as_json:
        _output_result(result, True)
        return

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
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def testbench(file: str, style: str, cases: int, output: str, as_json: bool):
    """生成 Testbench"""
    from .tools import generate_testbench

    code = Path(file).read_text(encoding="utf-8")
    with console.status("[bold blue]生成 Testbench..."):
        result = asyncio.run(generate_testbench(code, style, cases))

    if as_json:
        _output_result(result, True)
        return

    if result.get("success"):
        tb_code = result["testbench"]

        if output:
            Path(output).write_text(tb_code, encoding="utf-8")
            console.print(f"[OK] [green]Testbench 已保存[/green]: {output}")
        else:
            console.print(Syntax(tb_code, "verilog"))
    else:
        console.print(f"[FAIL] [red]生成失败[/red]: {result.get('error')}")


@main.group()
def waveform():
    """波形分析与查看"""
    pass


@waveform.command("analyze")
@click.argument("file", type=click.Path(exists=True))
@click.option("--signals", "-s", multiple=True, help="要分析的信号")
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def waveform_analyze(file: str, signals: tuple, as_json: bool):
    """分析 VCD 波形文件"""
    from .tools import analyze_waveform

    with console.status("[bold blue]分析波形..."):
        result = asyncio.run(
            analyze_waveform(vcd_file=file, signals=list(signals) if signals else None)
        )

    if as_json:
        _output_result(result, True)
        return

    if result.get("success"):
        console.print("[INFO] [blue]波形分析[/blue]")
        console.print(f"   信号数: {len(result.get('signals', {}))}")
        if result.get("ascii_waveform"):
            console.print("\n" + result["ascii_waveform"])
    else:
        console.print(f"[FAIL] [red]分析失败[/red]: {result.get('error')}")


@waveform.command("view")
@click.argument("file", type=click.Path(exists=True))
@click.option("--port", "-p", default=0, help="HTTP 端口 (0=自动选择)")
@click.option("--no-open", is_flag=True, help="不自动打开浏览器")
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def waveform_view(file: str, port: int, no_open: bool, as_json: bool):
    """启动交互式波形查看器"""
    from .tools.waveform_server import start_waveform_server

    with console.status("[bold blue]启动波形查看器..."):
        result = start_waveform_server(
            vcd_file=file,
            port=port,
            auto_open=not no_open,
        )

    if as_json:
        _output_result(result, True)
        return

    if result.get("success"):
        console.print("[OK] [green]波形查看器已启动[/green]")
        console.print(f"   URL: {result['url']}")
        console.print(f"   信号数: {result.get('signal_count', 0)}")
        time_range = result.get("time_range", {})
        console.print(f"   时间范围: {time_range.get('start', 0)} - {time_range.get('end', 0)}")
        console.print("\n   按 Ctrl+C 停止服务")

        try:
            # 保持主线程运行
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[INFO] 服务已停止")
    else:
        console.print(f"[FAIL] [red]启动失败[/red]: {result.get('error')}")


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
@click.option("--port", "-p", default=8080, help="SSE 端口")
def mcp(port: int):
    """启动 MCP Server (stdio 模式)"""
    from .server import main as server_main

    console.print("[START] [green]启动 SuperRTL MCP Server[/green]")
    server_main()


if __name__ == "__main__":
    main()
