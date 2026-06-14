"""
Verilog 模块依赖解析

自动分析：
- `include 指令
- 模块实例化
- 构建依赖图
- 拓扑排序确定编译顺序
"""

import re
from pathlib import Path


def parse_includes(content: str) -> list[str]:
    """解析 `include 指令"""
    includes = []
    for match in re.finditer(r'`include\s+"([^"]+)"', content):
        includes.append(match.group(1))
    return includes


def parse_modules(content: str) -> list[dict]:
    """解析模块定义和实例化"""
    modules = []

    # 提取模块定义
    for match in re.finditer(r"module\s+(\w+)", content):
        modules.append({"type": "definition", "name": match.group(1)})

    # 提取模块实例化
    # 格式: module_name instance_name ( 或 module_name #(...) instance_name (
    for match in re.finditer(
        r"^\s*(\w+)\s+(?:#\([^)]*(?:\([^)]*\))*[^)]*\)\s+)?(\w+)\s*\(", content, re.MULTILINE
    ):
        mod_name = match.group(1)
        inst_name = match.group(2)
        # 排除关键字
        if mod_name not in (
            "module",
            "input",
            "output",
            "wire",
            "reg",
            "assign",
            "always",
            "initial",
            "begin",
            "end",
            "if",
            "else",
            "case",
            "default",
            "for",
            "while",
            "function",
            "task",
            "generate",
            "genvar",
            "parameter",
            "localparam",
        ):
            modules.append({"type": "instance", "module": mod_name, "instance": inst_name})

    return modules


def analyze_file(filepath: Path) -> dict:
    """分析单个文件"""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return {"file": str(filepath), "defines": [], "instances": [], "includes": []}

    includes = parse_includes(content)
    modules = parse_modules(content)

    defines = [m["name"] for m in modules if m["type"] == "definition"]
    instances = [m["module"] for m in modules if m["type"] == "instance"]

    return {
        "file": str(filepath),
        "defines": defines,
        "instances": instances,
        "includes": includes,
    }


def analyze_project(files: list[Path]) -> dict:
    """分析整个项目"""
    analysis = {}
    for f in files:
        analysis[str(f)] = analyze_file(f)
    return analysis


def build_dependency_graph(analysis: dict) -> dict:
    """构建依赖图

    Returns:
        {
            "module_to_file": {module_name: file_path},
            "dependencies": {module_name: [dep_module_name]},
            "files": {file_path: [module_names]},
        }
    """
    module_to_file = {}
    dependencies = {}
    files = {}

    # 第一遍：建立模块到文件的映射
    for filepath, info in analysis.items():
        files[filepath] = info["defines"]
        for mod in info["defines"]:
            module_to_file[mod] = filepath

    # 第二遍：建立依赖关系
    for filepath, info in analysis.items():
        for mod in info["defines"]:
            deps = []
            for inst in info["instances"]:
                if inst in module_to_file:
                    deps.append(inst)
                else:
                    # 可能是外部模块或未定义
                    deps.append(inst)
            dependencies[mod] = list(set(deps))

    return {
        "module_to_file": module_to_file,
        "dependencies": dependencies,
        "files": files,
    }


def topological_sort(graph: dict) -> list[str]:
    """拓扑排序，确定编译顺序

    Returns:
        模块名列表（从底层到顶层）

    Raises:
        ValueError: 存在循环依赖
    """
    deps = graph["dependencies"]
    visited = set()
    order = []
    visiting = set()  # 用于检测循环

    def visit(mod):
        if mod in visiting:
            raise ValueError(f"循环依赖: {mod}")
        if mod in visited:
            return

        visiting.add(mod)
        for dep in deps.get(mod, []):
            if dep in deps:  # 只处理项目内模块
                visit(dep)
        visiting.remove(mod)
        visited.add(mod)
        order.append(mod)

    for mod in deps:
        visit(mod)

    return order


def get_compilation_order(files: list[Path]) -> list[Path]:
    """获取文件编译顺序

    Returns:
        文件路径列表（按依赖顺序）
    """
    analysis = analyze_project(files)
    graph = build_dependency_graph(analysis)

    try:
        module_order = topological_sort(graph)
    except ValueError:
        # 循环依赖，返回原始顺序
        return files

    # 模块顺序转文件顺序
    file_order = []
    seen = set()
    for mod in module_order:
        filepath = graph["module_to_file"].get(mod)
        if filepath and filepath not in seen:
            seen.add(filepath)
            file_order.append(Path(filepath))

    # 添加没有依赖的文件
    for f in files:
        if str(f) not in seen:
            file_order.append(f)

    return file_order


def find_unused_modules(analysis: dict) -> list[str]:
    """查找未使用的模块"""
    graph = build_dependency_graph(analysis)
    all_modules = set(graph["module_to_file"].keys())
    used_modules = set()

    for deps in graph["dependencies"].values():
        used_modules.update(deps)

    return sorted(all_modules - used_modules)


def detect_cycles(graph: dict) -> list[list[str]]:
    """检测循环依赖"""
    deps = graph["dependencies"]
    cycles = []
    visited = set()
    path = []

    def dfs(mod):
        if mod in path:
            cycle_start = path.index(mod)
            cycles.append(path[cycle_start:] + [mod])
            return
        if mod in visited:
            return

        path.append(mod)
        for dep in deps.get(mod, []):
            if dep in deps:
                dfs(dep)
        path.pop()
        visited.add(mod)

    for mod in deps:
        dfs(mod)

    return cycles
