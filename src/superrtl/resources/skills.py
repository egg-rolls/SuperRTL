"""
Skills 资源管理
"""

import json
import re
from pathlib import Path

# Skills 目录
# 优先使用包内的 shared 目录（安装后）
# 回退到项目根目录的 shared 目录（开发模式）
_PACKAGE_DIR = Path(__file__).parent.parent
SKILLS_DIR = _PACKAGE_DIR / "shared" / "skills"

# 如果包内没有，尝试项目根目录（开发模式）
if not SKILLS_DIR.exists():
    SKILLS_DIR = _PACKAGE_DIR.parent.parent / "shared" / "skills"


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 YAML frontmatter（不依赖 PyYAML）

    Returns:
        (metadata_dict, body_content)
    """
    metadata = {}
    body = content

    # 匹配 frontmatter 块
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if match:
        frontmatter_str = match.group(1)
        body = match.group(2)

        # 简单解析 YAML 键值对
        for line in frontmatter_str.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # 处理 key: "value" 或 key: value
            kv_match = re.match(r'^(\w+):\s*"([^"]*)"', line)
            if kv_match:
                metadata[kv_match.group(1)] = kv_match.group(2)
                continue

            # 处理 key: 'value'
            kv_match = re.match(r"^(\w+):\s*'([^']*)'", line)
            if kv_match:
                metadata[kv_match.group(1)] = kv_match.group(2)
                continue

            # 处理 key: value（无引号）
            kv_match = re.match(r"^(\w+):\s*(.+)$", line)
            if kv_match:
                value = kv_match.group(2).strip()
                # 处理列表 [item1, item2, ...]
                if value.startswith("[") and value.endswith("]"):
                    items = [
                        item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip()
                    ]
                    metadata[kv_match.group(1)] = items
                else:
                    metadata[kv_match.group(1)] = value

    return metadata, body


def _extract_skill_name(filename: str) -> str:
    """从文件名提取 skill 名称（去掉 verilog_ 前缀）"""
    name = filename.replace("verilog_", "")
    return name


async def list_skills() -> str:
    """列出所有可用的 Skills（包含元数据）"""
    skills = []

    if SKILLS_DIR.exists():
        for skill_file in sorted(SKILLS_DIR.glob("*.md")):
            content = skill_file.read_text(encoding="utf-8")
            metadata, _ = _parse_frontmatter(content)

            skill_name = _extract_skill_name(skill_file.stem)

            skill_info = {
                "name": metadata.get("name", skill_name),
                "file": skill_file.name,
                "display_name": skill_name,
                "description": metadata.get("description", ""),
                "version": metadata.get("version", "1.0.0"),
                "tags": metadata.get("tags", []),
            }
            skills.append(skill_info)

    return json.dumps({"skills": skills, "count": len(skills)}, ensure_ascii=False)


async def get_skill(skill_name: str) -> str:
    """获取指定 Skill 的内容（不含 frontmatter）"""
    # 尝试不同的文件名格式
    possible_names = [
        f"verilog_{skill_name}.md",
        f"{skill_name}.md",
    ]

    for name in possible_names:
        skill_file = SKILLS_DIR / name
        if skill_file.exists():
            content = skill_file.read_text(encoding="utf-8")
            metadata, body = _parse_frontmatter(content)

            # 返回结构化内容
            result = {
                "name": metadata.get("name", skill_name),
                "version": metadata.get("version", "1.0.0"),
                "description": metadata.get("description", ""),
                "tags": metadata.get("tags", []),
                "content": body.strip(),
            }
            return json.dumps(result, ensure_ascii=False)

    # 如果找不到，返回错误
    available = []
    if SKILLS_DIR.exists():
        for f in SKILLS_DIR.glob("*.md"):
            available.append(_extract_skill_name(f.stem))

    return json.dumps(
        {"error": f"Skill 未找到: {skill_name}", "available": available}, ensure_ascii=False
    )
