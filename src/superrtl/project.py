"""
项目配置管理

支持 .superrtl.yaml 项目配置文件，定义：
- 项目元数据（名称、顶层模块）
- 源文件模式（glob 支持）
- 测试平台定义
- 构建目标
- lint/仿真选项
"""

from pathlib import Path
from typing import Any

import yaml

# 默认配置
DEFAULT_CONFIG = {
    "project": {
        "name": "my_project",
        "top": "",
    },
    "sources": ["*.v"],
    "testbenches": [],
    "sim": {
        "timeout": 30,
        "waveform": True,
    },
    "lint": {
        "style": "default",
    },
    "build": {
        "target": "generic",
    },
}

CONFIG_FILENAME = ".superrtl.yaml"


def find_config(start: Path = None) -> Path | None:
    """从当前目录向上查找配置文件"""
    if start is None:
        start = Path.cwd()

    current = start.resolve()
    while True:
        config_path = current / CONFIG_FILENAME
        if config_path.exists():
            return config_path
        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def load_config(config_path: Path = None) -> dict[str, Any]:
    """加载项目配置"""
    import logging

    logger = logging.getLogger("superrtl.project")

    if config_path is None:
        config_path = find_config()

    if config_path is None or not config_path.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(config_path, encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.warning("配置文件 YAML 语法错误 (%s): %s，使用默认配置", config_path, e)
        return DEFAULT_CONFIG.copy()
    except OSError as e:
        logger.warning("配置文件读取失败 (%s): %s，使用默认配置", config_path, e)
        return DEFAULT_CONFIG.copy()

    # 合并默认配置
    config = DEFAULT_CONFIG.copy()
    _deep_merge(config, user_config)
    return config


def _deep_merge(base: dict, override: dict):
    """深度合并字典"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def save_config(config: dict, path: Path = None):
    """保存项目配置"""
    if path is None:
        path = Path.cwd() / CONFIG_FILENAME

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def init_project(name: str = "my_project", top: str = "") -> dict:
    """初始化项目配置"""
    config = DEFAULT_CONFIG.copy()
    config["project"]["name"] = name
    config["project"]["top"] = top

    # 自动检测源文件
    v_files = list(Path.cwd().glob("*.v")) + list(Path.cwd().glob("**/*.v"))
    if v_files:
        # 按目录分组
        dirs = set()
        for f in v_files:
            rel = f.relative_to(Path.cwd())
            if len(rel.parts) > 1:
                dirs.add(rel.parts[0] + "/**/*.v")
            else:
                dirs.add("*.v")
        config["sources"] = sorted(dirs)

    return config


def resolve_sources(config: dict, base_dir: Path = None) -> list[Path]:
    """解析源文件模式，返回文件列表"""
    if base_dir is None:
        base_dir = Path.cwd()

    sources = config.get("sources", [])
    files = []

    for pattern in sources:
        if isinstance(pattern, str):
            # 处理 glob 模式
            if "**" in pattern:
                matched = sorted(base_dir.glob(pattern))
            else:
                matched = sorted(base_dir.glob(pattern))
            files.extend(matched)
        elif isinstance(pattern, dict):
            # 处理带 include/exclude 的配置
            include = pattern.get("include", [])
            exclude = pattern.get("exclude", [])
            for inc in include:
                matched = base_dir.glob(inc)
                for m in matched:
                    if not any(m.match(ex) for ex in exclude):
                        files.append(m)

    # 去重保持顺序
    seen = set()
    unique = []
    for f in files:
        resolved = f.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(f)

    return unique


def resolve_testbenches(config: dict, base_dir: Path = None) -> list[Path]:
    """解析测试平台文件"""
    if base_dir is None:
        base_dir = Path.cwd()

    testbenches = config.get("testbenches", [])
    files = []

    for pattern in testbenches:
        if isinstance(pattern, str):
            matched = sorted(base_dir.glob(pattern))
            files.extend(matched)

    return files


def get_project_info(config: dict) -> dict:
    """获取项目摘要信息"""
    project = config.get("project", {})
    sources = config.get("sources", [])
    testbenches = config.get("testbenches", [])

    return {
        "name": project.get("name", "unknown"),
        "top": project.get("top", ""),
        "source_patterns": sources,
        "testbench_patterns": testbenches,
        "sim_timeout": config.get("sim", {}).get("timeout", 30),
        "lint_style": config.get("lint", {}).get("style", "default"),
        "build_target": config.get("build", {}).get("target", "generic"),
    }
