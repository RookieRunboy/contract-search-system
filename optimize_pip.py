#!/usr/bin/env python3
"""
Python包下载速度优化脚本
优化pip配置，提升国内用户下载速度
"""

import subprocess
import sys
import os

def optimize_pip_config():
    """优化pip配置"""
    
    # 国内常用镜像源配置
    mirrors = {
        "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "aliyun": "https://mirrors.aliyun.com/pypi/simple",
        "douban": "https://pypi.douban.com/simple",
        "ustc": "https://pypi.mirrors.ustc.edu.cn/simple"
    }
    
    print("=== Python包下载速度优化工具 ===\n")
    print("当前pip配置:")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "config", "list"], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            print(result.stdout)
        else:
            print("无自定义配置")
    except Exception as e:
        print(f"读取配置失败: {e}")
    
    print("\n推荐的国内镜像源:")
    for name, url in mirrors.items():
        print(f"- {name}: {url}")
    
    # 设置清华镜像源（推荐）
    print(f"\n正在配置清华镜像源...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "config", "set", 
            "global.index-url", mirrors["tsinghua"]
        ], check=True)
        print("✅ 成功设置清华镜像源")
        
        # 设置超时时间
        subprocess.run([
            sys.executable, "-m", "pip", "config", "set", 
            "global.timeout", "60"
        ], check=True)
        print("✅ 成功设置超时时间")
        
        # 设置重试次数
        subprocess.run([
            sys.executable, "-m", "pip", "config", "set", 
            "global.retries", "3"
        ], check=True)
        print("✅ 成功设置重试次数")
        
        # 启用信任主机
        subprocess.run([
            sys.executable, "-m", "pip", "config", "set", 
            "global.trusted-host", "pypi.tuna.tsinghua.edu.cn"
        ], check=True)
        print("✅ 成功配置信任主机")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 配置失败: {e}")
        return False
    
    # 升级pip到最新版本
    print(f"\n升级pip到最新版本...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True, timeout=120)
        print("✅ pip升级成功")
    except Exception as e:
        print(f"⚠️ pip升级失败（可以忽略）: {e}")
    
    print("\n=== 优化完成！ ===")
    print("现在你的pip下载速度应该会显著提升！")
    
    # 验证配置
    print("\n优化后的pip配置:")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "config", "list"], 
                              capture_output=True, text=True, encoding='utf-8')
        print(result.stdout)
    except Exception as e:
        print(f"验证失败: {e}")
    
    return True

def test_speed():
    """测试下载速度"""
    print("\n=== 下载速度测试 ===")
    
    test_packages = ["requests", "numpy", "pandas"]
    
    for package in test_packages:
        print(f"测试下载 {package}...")
        try:
            # 先卸载（如果存在）
            subprocess.run([
                sys.executable, "-m", "pip", "uninstall", "-y", package
            ], capture_output=True)
            
            # 测试下载时间
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package, "--timeout", "30"
            ], capture_output=True, text=True, timeout=90)
            
            if result.returncode == 0:
                print(f"✅ {package} 下载成功")
            else:
                print(f"⚠️ {package} 下载失败")
                
        except Exception as e:
            print(f"❌ {package} 测试失败: {e}")

if __name__ == "__main__":
    print("开始优化pip配置...")
    
    if optimize_pip_config():
        print("\n配置优化完成！")
        
        # 询问是否进行速度测试
        try:
            choice = input("\n是否进行下载速度测试？(y/n): ").strip().lower()
            if choice in ['y', 'yes', '是']:
                test_speed()
        except KeyboardInterrupt:
            print("\n用户取消测试")
    else:
        print("配置优化失败！")
        sys.exit(1)
    
    print("\n优化脚本执行完成！")