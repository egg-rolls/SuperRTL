#!/usr/bin/env python3
"""发布前检查脚本"""

import sys
from pathlib import Path


def check():
    print("=" * 50)
    print("SuperRTL v0.2.0 - 发布前检查")
    print("=" * 50)
    print()

    errors = []

    # 1. 版本检查
    try:
        import superrtl
        print(f"[OK] 版本号: {superrtl.__version__}")
    except Exception as e:
        errors.append(f"版本检查失败: {e}")
        print(f"[FAIL] 版本检查失败: {e}")

    # 2. 检查包是否可导入
    modules = [
        ("superrtl.cli", "main"),
        ("superrtl.server", "app"),
        ("superrtl.tools", "compile_verilog"),
        ("superrtl.resources", "get_skill"),
        ("superrtl.runtime", "tools_installed"),
        ("superrtl.setup", "install_tools"),
    ]

    for module_name, attr in modules:
        try:
            module = __import__(module_name, fromlist=[attr])
            getattr(module, attr)
            print(f"[OK] {module_name} 可导入")
        except Exception as e:
            errors.append(f"{module_name} 导入失败: {e}")
            print(f"[FAIL] {module_name} 导入失败: {e}")

    # 3. 检查共享资源
    try:
        package_dir = Path(superrtl.__file__).parent
        skills_dir = package_dir / "shared" / "skills"
        templates_dir = package_dir / "shared" / "templates"

        if skills_dir.exists():
            skills = list(skills_dir.glob("*.md"))
            print(f"[OK] Skills 资源: {len(skills)} 个")
        else:
            print("[WARN] Skills 目录不存在（开发模式正常）")

        if templates_dir.exists():
            templates = list(templates_dir.glob("*.v"))
            print(f"[OK] Templates 资源: {len(templates)} 个")
        else:
            print("[WARN] Templates 目录不存在（开发模式正常）")
    except Exception as e:
        print(f"[WARN] 资源检查: {e}")

    print()
    print("=" * 50)

    if errors:
        print(f"检查失败: {len(errors)} 个错误")
        for e in errors:
            print(f"  - {e}")
        return 1
    else:
        print("检查通过！可以发布。")
        return 0


if __name__ == "__main__":
    sys.exit(check())
