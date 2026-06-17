"""
日志系统模块

提供统一的日志配置和格式化。
"""

import logging
import sys
from pathlib import Path

# 日志格式
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志级别映射
LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def setup_logging(
    level: str = "info",
    log_file: str = None,
    log_dir: str = None,
) -> logging.Logger:
    """配置日志系统

    Args:
        level: 日志级别 (debug, info, warning, error, critical)
        log_file: 日志文件路径（可选）
        log_dir: 日志目录（可选，与 log_file 二选一）

    Returns:
        配置好的 logger
    """
    # 获取 root logger
    logger = logging.getLogger("superrtl")
    logger.setLevel(LEVEL_MAP.get(level.lower(), logging.INFO))

    # 清除现有处理器
    logger.handlers.clear()

    # 控制台处理器 — 级别与 logger 一致
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(LEVEL_MAP.get(level.lower(), logging.INFO))
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定了路径）
    if log_file or log_dir:
        if log_dir:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            log_file = str(log_path / "superrtl.log")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """获取子 logger

    Args:
        name: logger 名称（通常是模块名）

    Returns:
        子 logger
    """
    return logging.getLogger(f"superrtl.{name}")
