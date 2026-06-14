#!/usr/bin/env python3
"""
验证 Skills 文件格式

检查所有 shared/skills/*.md 文件是否包含有效的 YAML frontmatter。
"""

import re
import sys
from pathlib import Path


def validate_frontmatter(content: str, filename: str) -> list[str]:
    """验证 frontmatter 格式"""
    errors = []

    # 检查是否以 --- 开头
    if not content.startswith("---"):
        errors.append(f"{filename}: Missing YAML frontmatter (should start with ---)")
        return errors

    # 匹配 frontmatter 块
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        errors.append(f"{filename}: Invalid frontmatter format (missing closing ---)")
        return errors

    frontmatter = match.group(1)

    # 必需字段
    required_fields = ["name", "version", "description"]
    for field in required_fields:
        if not re.search(rf"^{field}:", frontmatter, re.MULTILINE):
            errors.append(f"{filename}: Missing required field '{field}'")

    # 验证 name 格式
    name_match = re.search(r'^name:\s*["\']?([^"\']+)', frontmatter, re.MULTILINE)
    if name_match:
        name = name_match.group(1).strip()
        if not re.match(r"^[a-z0-9-]+$", name):
            errors.append(f"{filename}: Invalid name '{name}' (use lowercase, digits, hyphens)")

    # 验证 version 格式
    version_match = re.search(r'^version:\s*["\']?([^"\']+)', frontmatter, re.MULTILINE)
    if version_match:
        version = version_match.group(1).strip()
        if not re.match(r"^\d+\.\d+\.\d+$", version):
            errors.append(f"{filename}: Invalid version '{version}' (use x.y.z format)")

    # 验证 tags 格式
    tags_match = re.search(r"^tags:\s*\[(.+)\]", frontmatter, re.MULTILINE)
    if tags_match:
        tags_str = tags_match.group(1)
        # 简单验证列表格式
        if not re.match(r'^"[^"]+"(\s*,\s*"[^"]+")*$', tags_str):
            errors.append(f'{filename}: Invalid tags format (use ["tag1", "tag2"])')

    return errors


def validate_skill_file(filepath: Path) -> list[str]:
    """验证单个 skill 文件"""
    errors = []

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"{filepath.name}: Read failed: {e}")
        return errors

    # 验证 frontmatter
    errors.extend(validate_frontmatter(content, filepath.name))

    # 验证内容不为空
    match = re.match(r"^---\s*\n.*?\n---\s*\n(.*)", content, re.DOTALL)
    if match:
        body = match.group(1).strip()
        if len(body) < 50:
            errors.append(f"{filepath.name}: Content too short ({len(body)} chars)")

    return errors


def main():
    """主函数"""
    # 找到 skills 目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    skills_dir = project_root / "shared" / "skills"

    if not skills_dir.exists():
        print(f"ERROR: skills directory not found: {skills_dir}")
        return 1

    # 验证所有 .md 文件
    all_errors = []
    skill_files = list(skills_dir.glob("*.md"))

    if not skill_files:
        print("WARNING: No skill files found")
        return 0

    print(f"Validating {len(skill_files)} skill files...")

    for filepath in sorted(skill_files):
        errors = validate_skill_file(filepath)
        all_errors.extend(errors)

    # 输出结果
    if all_errors:
        print("\nValidation failed:")
        for error in all_errors:
            print(f"  - {error}")
        return 1
    else:
        print("All skill files passed validation!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
