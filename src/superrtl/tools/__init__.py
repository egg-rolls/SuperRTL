"""
MCP Tools 实现
"""

from .compile import compile_verilog
from .lint import lint_verilog
from .simulate import simulate_verilog
from .synthesize import synthesize_verilog
from .testbench import generate_testbench
from .waveform import analyze_waveform

__all__ = [
    "compile_verilog",
    "simulate_verilog",
    "lint_verilog",
    "synthesize_verilog",
    "generate_testbench",
    "analyze_waveform",
]
