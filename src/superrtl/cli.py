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
@click.option("--verbose", "-v", is_flag=True, help="显示详细日志")
def main(verbose: bool):
    """SuperRTL - Verilog EDA 工具的 MCP/CLI 客户端"""
    from .logging import setup_logging

    level = "debug" if verbose else "warning"
    setup_logging(level=level)


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


# ============ 项目命令 ============


@main.command()
@click.option("--name", "-n", default="my_project", help="项目名称")
@click.option("--top", "-t", default="", help="顶层模块名")
def init(name: str, top: str):
    """初始化项目配置 (.superrtl.yaml)"""
    from .project import init_project, save_config

    config = init_project(name, top)
    save_config(config)

    console.print("[OK] [green]项目已初始化[/green]")
    console.print("   配置文件: .superrtl.yaml")
    console.print(f"   项目名称: {config['project']['name']}")
    console.print(f"   源文件模式: {config['sources']}")


@main.command()
@click.option("--top", "-t", default="", help="顶层模块名 (覆盖配置)")
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def build(top: str, as_json: bool):
    """根据项目配置编译"""
    from .deps import get_compilation_order
    from .project import load_config, resolve_sources
    from .tools import compile_verilog

    config = load_config()
    top = top or config.get("project", {}).get("top", "")

    files = resolve_sources(config)
    if not files:
        console.print("[FAIL] [red]未找到源文件，请检查 .superrtl.yaml 配置[/red]")
        raise SystemExit(1)

    # 按依赖顺序编译
    ordered_files = get_compilation_order(files)

    with console.status(f"[bold blue]编译 {len(ordered_files)} 个文件..."):
        result = asyncio.run(compile_verilog(files=[str(f) for f in ordered_files], top_module=top))

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
@click.option("--tb", default="", help="测试平台文件 (覆盖配置)")
@click.option("--timeout", "-t", default=0, help="超时时间 (秒, 0=使用配置)")
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def test(tb: str, timeout: int, as_json: bool):
    """根据项目配置运行仿真"""
    from .deps import get_compilation_order
    from .project import load_config, resolve_sources, resolve_testbenches
    from .tools import simulate_verilog

    config = load_config()
    timeout = timeout or config.get("sim", {}).get("timeout", 30)

    # 获取测试平台
    if tb:
        tb_files = [Path(tb)]
    else:
        tb_files = resolve_testbenches(config)

    if not tb_files:
        console.print(
            "[FAIL] [red]未找到测试平台，请检查 .superrtl.yaml 配置或使用 --tb 指定[/red]"
        )
        raise SystemExit(1)

    # 获取设计文件（排除测试平台）
    design_files = resolve_sources(config)
    tb_file_set = {f.resolve() for f in tb_files}
    design_files = [f for f in design_files if f.resolve() not in tb_file_set]

    if not design_files:
        console.print("[FAIL] [red]未找到设计文件[/red]")
        raise SystemExit(1)

    ordered_files = get_compilation_order(design_files)

    # 运行每个测试平台
    all_passed = True
    for tb_file in tb_files:
        console.print(f"\n[INFO] [blue]运行测试: {tb_file.name}[/blue]")
        tb_code = tb_file.read_text(encoding="utf-8")

        with console.status("[bold blue]仿真中..."):
            result = asyncio.run(
                simulate_verilog(
                    testbench=tb_code,
                    timeout=timeout,
                    design_file_paths=[str(f) for f in ordered_files],
                )
            )

        if as_json:
            _output_result(result, True)
            continue

        if result.get("success") and result.get("passed"):
            console.print(f"[OK] [green]{tb_file.name} 通过[/green] ({result.get('duration')}s)")
        else:
            all_passed = False
            console.print(f"[FAIL] [red]{tb_file.name} 失败[/red]")
            if result.get("output"):
                console.print(f"   {result['output'][:200]}")

    if not as_json:
        if all_passed:
            console.print("\n[OK] [green]所有测试通过[/green]")
        else:
            console.print("\n[FAIL] [red]存在失败的测试[/red]")
            raise SystemExit(1)


@main.command()
@click.option("--format", "-f", "fmt", default="text", type=click.Choice(["text", "dot", "json"]))
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def graph(fmt: str, as_json: bool):
    """显示模块依赖图"""
    from .deps import analyze_project, build_dependency_graph, detect_cycles, find_unused_modules
    from .project import load_config, resolve_sources

    config = load_config()
    files = resolve_sources(config)

    if not files:
        console.print("[FAIL] [red]未找到源文件[/red]")
        raise SystemExit(1)

    analysis = analyze_project(files)
    graph_data = build_dependency_graph(analysis)

    if as_json or fmt == "json":
        import json as json_mod

        output = {
            "modules": graph_data["module_to_file"],
            "dependencies": graph_data["dependencies"],
            "unused": find_unused_modules(analysis),
            "cycles": detect_cycles(graph_data),
        }
        console.print(json_mod.dumps(output, indent=2, ensure_ascii=False))
        return

    if fmt == "dot":
        # Graphviz DOT 格式
        console.print("digraph modules {")
        console.print("  rankdir=LR;")
        for mod, filepath in graph_data["module_to_file"].items():
            console.print(f'  {mod} [label="{mod}\\n{Path(filepath).name}"];')
        for mod, deps in graph_data["dependencies"].items():
            for dep in deps:
                if dep in graph_data["module_to_file"]:
                    console.print(f"  {mod} -> {dep};")
        console.print("}")
        return

    # 文本格式
    table = Table(title="Module Dependency Graph")
    table.add_column("Module", style="cyan")
    table.add_column("File", style="dim")
    table.add_column("Dependencies", style="green")
    table.add_column("Status", style="yellow")

    unused = find_unused_modules(analysis)
    cycles = detect_cycles(graph_data)

    for mod, filepath in graph_data["module_to_file"].items():
        deps = graph_data["dependencies"].get(mod, [])
        deps_str = ", ".join(deps) if deps else "-"
        status = ""
        if mod in unused:
            status = "[yellow]unused[/yellow]"
        if any(mod in c for c in cycles):
            status = "[red]cycle[/red]"
        table.add_row(mod, Path(filepath).name, deps_str, status)

    console.print(table)

    if unused:
        console.print(f"\n[WARN] [yellow]未使用的模块: {', '.join(unused)}[/yellow]")
    if cycles:
        console.print("\n[FAIL] [red]检测到循环依赖![/red]")
        for cycle in cycles:
            console.print(f"   {' -> '.join(cycle)}")


@main.command()
@click.option("--tb", default="", help="测试平台文件")
@click.option("--interval", "-i", default=2, help="检查间隔 (秒)")
def watch(tb: str, interval: int):
    """监视文件变化，自动编译/测试"""
    import time as time_mod

    from .project import load_config, resolve_sources

    config = load_config()
    files = resolve_sources(config)

    if not files:
        console.print("[FAIL] [red]未找到源文件[/red]")
        raise SystemExit(1)

    console.print(f"[INFO] [blue]监视 {len(files)} 个文件 (间隔 {interval}s)[/blue]")
    console.print("[INFO] 按 Ctrl+C 停止\n")

    # 记录文件修改时间
    file_mtimes = {}
    for f in files:
        try:
            file_mtimes[str(f)] = f.stat().st_mtime
        except Exception:
            pass

    def check_changes():
        changed = []
        for f in files:
            try:
                mtime = f.stat().st_mtime
                if str(f) in file_mtimes and mtime > file_mtimes[str(f)]:
                    changed.append(f)
                file_mtimes[str(f)] = mtime
            except Exception:
                pass
        return changed

    try:
        while True:
            time_mod.sleep(interval)
            changed = check_changes()

            if changed:
                console.print(f"\n[INFO] [blue]检测到 {len(changed)} 个文件变化[/blue]")
                for f in changed:
                    console.print(f"   {f.name}")

                # 自动编译
                console.print("[INFO] [blue]自动编译...[/blue]")
                from .tools import compile_verilog

                result = asyncio.run(compile_verilog(files=[str(f) for f in files]))
                if result.get("success"):
                    console.print(f"[OK] [green]编译成功[/green] ({result.get('duration')}s)")
                else:
                    console.print("[FAIL] [red]编译失败[/red]")
                    for error in result.get("errors", [])[:3]:
                        console.print(f"   {error}")

    except KeyboardInterrupt:
        console.print("\n[INFO] 停止监视")


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
@click.option(
    "--checks", "-c", multiple=True, help="检查类别 (synthesizability/latch/naming/reset/case)"
)
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def review(file: str, checks: tuple, as_json: bool):
    """代码审查 - 检查可综合性、常见陷阱和编码风格"""
    from .tools import review_verilog

    code = Path(file).read_text(encoding="utf-8")
    with console.status("[bold blue]代码审查中..."):
        result = asyncio.run(review_verilog(code, checks=list(checks) if checks else None))

    if as_json:
        _output_result(result, True)
        return

    if result.get("success"):
        summary = result.get("summary", {})
        total = sum(summary.values())

        if total == 0:
            console.print("[OK] [green]代码审查通过，未发现问题[/green]")
        else:
            console.print(f"[INFO] [blue]发现 {total} 个问题[/blue]")
            if summary.get("errors"):
                console.print(f"   [red]错误: {summary['errors']}[/red]")
            if summary.get("warnings"):
                console.print(f"   [yellow]警告: {summary['warnings']}[/yellow]")
            if summary.get("infos"):
                console.print(f"   [dim]提示: {summary['infos']}[/dim]")

            console.print("\n   问题列表:")
            for issue in result.get("issues", [])[:10]:
                severity_color = {"error": "red", "warning": "yellow", "info": "dim"}.get(
                    issue["severity"], "white"
                )
                console.print(
                    f"     [{severity_color}]{issue['severity'].upper()}[/{severity_color}] "
                    f"行 {issue.get('line', '?')}: {issue['message']}"
                )
                if issue.get("suggestion"):
                    console.print(f"       建议: {issue['suggestion']}")

        synthesizable = result.get("synthesizable", True)
        if synthesizable:
            console.print("\n[OK] [green]代码可综合[/green]")
        else:
            console.print("\n[WARN] [yellow]代码包含不可综合的结构[/yellow]")
    else:
        console.print(f"[FAIL] [red]{result.get('error')}[/red]")


@main.command()
@click.argument("designs", nargs=-1, required=True)
@click.option("--tb", default="", help="测试平台文件路径")
@click.option("--top", "-t", default="", help="顶层模块名")
@click.option("--timeout", default=60, help="仿真超时 (秒)")
@click.option("--skip", multiple=True, help="跳过的步骤 (compile/simulate/lint/review)")
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def verify(designs: tuple, tb: str, top: str, timeout: int, skip: tuple, as_json: bool):
    """综合验证：compile + simulate + lint + review"""
    from .tools import verify_design

    resolved = _resolve_files(designs)
    if not resolved:
        console.print("[FAIL] [red]未找到设计文件[/red]")
        raise SystemExit(1)

    with console.status("[bold blue]综合验证中..."):
        result = asyncio.run(
            verify_design(
                design_files=resolved,
                testbench_file=tb if tb else None,
                top_module=top,
                timeout=timeout,
                skip=list(skip) if skip else None,
            )
        )

    if as_json:
        _output_result(result, True)
        return

    if result.get("success"):
        steps = result.get("steps", {})
        for step, status in steps.items():
            color = "green" if status == "PASS" else "red"
            icon = "OK" if status == "PASS" else "FAIL"
            console.print(f"  [{icon}] [{color}]{step}: {status}[/{color}]")

        if result.get("passed"):
            console.print(f"\n[OK] [green]全部通过[/green] ({result.get('duration')}s)")
        else:
            console.print(f"\n[FAIL] [red]存在失败项[/red] ({result.get('duration')}s)")
            raise SystemExit(1)
    else:
        console.print(f"[FAIL] [red]{result.get('error')}[/red]")


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


@main.command("formal")
@click.argument("file", type=click.Path(exists=True))
@click.option("--top", "-t", default="", help="顶层模块名")
@click.option("--depth", "-d", default=20, help="BMC 搜索深度")
@click.option("--timeout", default=300, help="超时时间 (秒)")
@click.option("--json", "-j", "as_json", is_flag=True, help="JSON 格式输出")
def formal(file: str, top: str, depth: int, timeout: int, as_json: bool):
    """形式验证 (SymbiYosys BMC)"""
    from .tools import formal_verify

    code = Path(file).read_text(encoding="utf-8")
    with console.status("[bold blue]形式验证中..."):
        result = asyncio.run(formal_verify(code, top_module=top, depth=depth, timeout=timeout))

    if as_json:
        _output_result(result, True)
        return

    if result.get("success"):
        if result.get("passed"):
            console.print("[OK] [green]形式验证通过[/green]")
        else:
            console.print("[FAIL] [red]形式验证失败[/red]")
        console.print(f"   顶层模块: {result.get('top_module')}")
        console.print(f"   BMC 深度: {result.get('depth')}")
        console.print(f"   耗时: {result.get('duration')}s")

        if result.get("properties"):
            console.print("   属性:")
            for prop in result["properties"]:
                status = "[green]PASS[/green]" if prop["status"] == "passed" else "[red]FAIL[/red]"
                console.print(f"     {status}: {prop.get('detail', '')}")
    else:
        console.print(f"[FAIL] [red]{result.get('error')}[/red]")
        if result.get("suggestion"):
            console.print(f"   建议: {result['suggestion']}")


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
def mcp():
    """启动 MCP Server (stdio 模式)"""
    import sys

    from .server import main as server_main

    # 检测 stdin 是否连接到终端（非 pipe 模式）
    if sys.stdin.isatty():
        print(
            "错误: MCP Server 需要通过 MCP 客户端调用，不能在终端直接运行。\n"
            "请在 MCP Host 中配置:\n"
            "  命令: superrtl\n"
            "  参数: mcp\n"
            "  类型: stdio",
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1)

    # MCP 协议使用 stdin/stdout 通信，状态信息只能输出到 stderr
    print("[START] 启动 SuperRTL MCP Server", file=sys.stderr, flush=True)
    server_main()


if __name__ == "__main__":
    main()
