#!/usr/bin/env python3
"""
依赖检查脚本 - ASIN数据推送工具
检查所有必需的Python包是否正确安装

运行方式: python check_dependencies.py
"""

import sys
import subprocess
import pkg_resources
from typing import List, Tuple


def get_installed_version(package_name: str) -> str:
    """获取已安装包的版本"""
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return None


def check_package(package_name: str, min_version: str = None) -> Tuple[bool, str]:
    """检查单个包是否安装及版本"""
    installed_version = get_installed_version(package_name)
    
    if installed_version is None:
        return False, f"❌ {package_name} 未安装"
    
    if min_version:
        try:
            pkg_resources.require(f"{package_name}>={min_version}")
            return True, f"✅ {package_name} {installed_version} (>= {min_version})"
        except pkg_resources.VersionConflict:
            return False, f"⚠️  {package_name} {installed_version} < {min_version} (需要升级)"
    else:
        return True, f"✅ {package_name} {installed_version}"


def main():
    """主检查函数"""
    print("🔍 ASIN数据推送工具 - 依赖检查")
    print("=" * 50)
    
    # 核心依赖列表
    core_dependencies = [
        ("redis", "4.5.0"),
        ("PyMySQL", "1.0.0"),
        ("sshtunnel", "0.4.0"),
        ("oss2", "2.17.0"),
        ("cryptography", "40.0.0"),
    ]
    
    # 内置模块检查
    builtin_modules = [
        "configparser", "os", "time", "datetime", 
        "json", "argparse", "sys", "contextlib"
    ]
    
    print("📦 核心依赖检查:")
    all_core_ok = True
    
    for package, min_version in core_dependencies:
        is_ok, message = check_package(package, min_version)
        print(f"   {message}")
        if not is_ok:
            all_core_ok = False
    
    print(f"\n🐍 Python内置模块检查:")
    for module in builtin_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} 导入失败")
            all_core_ok = False
    
    print(f"\n📊 Python环境信息:")
    print(f"   Python版本: {sys.version}")
    print(f"   Python路径: {sys.executable}")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"   ✅ Python版本符合要求 (>= 3.8)")
    else:
        print(f"   ❌ Python版本过低 ({python_version.major}.{python_version.minor} < 3.8)")
        all_core_ok = False
    
    print(f"\n🎯 检查结果:")
    if all_core_ok:
        print("   ✅ 所有核心依赖检查通过!")
        print("   🚀 可以正常运行ASIN推送工具")
        return 0
    else:
        print("   ❌ 部分依赖缺失或版本不符合要求")
        print("\n💡 修复建议:")
        print("   1. 更新pip: python -m pip install --upgrade pip")
        print("   2. 安装依赖: pip install -r requirements.txt")
        print("   3. 使用国内镜像: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 