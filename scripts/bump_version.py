#!/usr/bin/env python3
"""
版本号管理脚本

用法:
    python scripts/bump_version.py patch  # 0.2.0 -> 0.2.1
    python scripts/bump_version.py minor  # 0.2.0 -> 0.3.0
    python scripts/bump_version.py major  # 0.2.0 -> 1.0.0
"""

import re
import sys
from pathlib import Path


def get_current_version() -> str:
    """获取当前版本号"""
    init_file = Path("src/superrtl/__init__.py")
    content = init_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Cannot find version in __init__.py")
    return match.group(1)


def bump_version(version: str, part: str) -> str:
    """递增版本号"""
    major, minor, patch = map(int, version.split("."))

    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Unknown part: {part}")


def update_version_in_file(filepath: Path, old_version: str, new_version: str) -> None:
    """更新文件中的版本号"""
    content = filepath.read_text()
    new_content = content.replace(old_version, new_version)
    if new_content != content:
        filepath.write_text(new_content)
        print(f"  Updated: {filepath}")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("major", "minor", "patch"):
        print(__doc__)
        sys.exit(1)

    part = sys.argv[1]
    old_version = get_current_version()
    new_version = bump_version(old_version, part)

    print(f"Version: {old_version} -> {new_version}")
    print()

    # 更新文件
    files_to_update = [
        Path("src/superrtl/__init__.py"),
        Path("pyproject.toml"),
    ]

    for filepath in files_to_update:
        if filepath.exists():
            update_version_in_file(filepath, old_version, new_version)

    print()
    print(f"Done! New version: {new_version}")
    print()
    print("Next steps:")
    print(f"  1. Update CHANGELOG.md")
    print(f"  2. git add -A && git commit -m 'Bump version to {new_version}'")
    print(f"  3. git tag v{new_version}")
    print(f"  4. git push && git push --tags")


if __name__ == "__main__":
    main()
