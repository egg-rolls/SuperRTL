"""
SuperRTL - Verilog EDA 工具的 MCP/CLI 客户端
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("superrtl")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

__author__ = "RTL-Agent Team"
