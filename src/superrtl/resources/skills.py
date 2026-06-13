"""
Skills 资源管理
"""

import json
from pathlib import Path

# Skills 目录
# 优先使用包内的 shared 目录（安装后）
# 回退到项目根目录的 shared 目录（开发模式）
_PACKAGE_DIR = Path(__file__).parent.parent
SKILLS_DIR = _PACKAGE_DIR / "shared" / "skills"

# 如果包内没有，尝试项目根目录（开发模式）
if not SKILLS_DIR.exists():
    SKILLS_DIR = _PACKAGE_DIR.parent.parent / "shared" / "skills"


async def list_skills() -> str:
    """列出所有可用的 Skills"""
    skills = []

    if SKILLS_DIR.exists():
        for skill_file in SKILLS_DIR.glob("*.md"):
            skill_name = skill_file.stem.replace("verilog_", "")
            skills.append(skill_name)

    return json.dumps({
        "skills": skills,
        "count": len(skills)
    }, ensure_ascii=False)


async def get_skill(skill_name: str) -> str:
    """获取指定 Skill 的内容"""
    # 尝试不同的文件名格式
    possible_names = [
        f"verilog_{skill_name}.md",
        f"{skill_name}.md",
    ]

    for name in possible_names:
        skill_file = SKILLS_DIR / name
        if skill_file.exists():
            return skill_file.read_text(encoding="utf-8")

    # 如果找不到，返回错误
    available = []
    if SKILLS_DIR.exists():
        for f in SKILLS_DIR.glob("*.md"):
            available.append(f.stem.replace("verilog_", ""))

    return json.dumps({
        "error": f"Skill 未找到: {skill_name}",
        "available": available
    }, ensure_ascii=False)
