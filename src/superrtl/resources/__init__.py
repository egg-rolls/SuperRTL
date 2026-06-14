"""
MCP Resources 实现
"""

from .skills import get_skill, get_skill_raw, list_skills
from .templates import get_template, list_templates

__all__ = [
    "get_skill",
    "get_skill_raw",
    "list_skills",
    "get_template",
    "list_templates",
]
