"""
模板资源管理
"""

import json
from pathlib import Path

# 模板目录 (相对于项目根目录)
# src/superrtl/resources/templates.py -> 4 levels up to project root
TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "shared" / "templates"


async def list_templates() -> str:
    """列出所有可用的模板"""
    templates = []

    if TEMPLATES_DIR.exists():
        for template_file in TEMPLATES_DIR.glob("*.v"):
            templates.append(template_file.stem)

    return json.dumps({
        "templates": templates,
        "count": len(templates)
    }, ensure_ascii=False)


async def get_template(template_name: str) -> str:
    """获取指定模板的内容"""
    possible_names = [
        f"{template_name}.v",
        f"{template_name}.sv",
    ]

    for name in possible_names:
        template_file = TEMPLATES_DIR / name
        if template_file.exists():
            return template_file.read_text(encoding="utf-8")

    # 如果找不到，返回错误
    available = []
    if TEMPLATES_DIR.exists():
        for f in TEMPLATES_DIR.glob("*.v"):
            available.append(f.stem)

    return json.dumps({
        "error": f"模板未找到: {template_name}",
        "available": available
    }, ensure_ascii=False)
