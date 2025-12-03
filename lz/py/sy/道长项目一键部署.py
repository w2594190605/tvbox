#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
import shutil
import json
from datetime import datetime
import signal

# 颜色定义
class Colors:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    NC = '\033[0m'  # No Color

# 日志函数
def log(message):
    print(f"{Colors.GREEN}[{datetime.now().strftime('%H:%M:%S')}] {message}{Colors.NC}")

def warn(message):
    print(f"{Colors.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] ⚠️ {message}{Colors.NC}")

def error(message):
    print(f"{Colors.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ {message}{Colors.NC}")

def info(message):
    print(f"{Colors.BLUE}[{datetime.now().strftime('%H:%M:%S')}] ℹ️ {message}{Colors.NC}")

# 检查 Termux 环境
def check_termux():
    if not os.path.exists("/data/data/com.termux/files/usr"):
        error("此脚本专为 Termux 环境设计")
        sys.exit(1)

# 显示主菜单
def show_main_menu():
    os.system('clear')
    print(f"{Colors.PURPLE}")
    print("╔══════════════════════════════════════════════╗")
    print("║           🚀 drpy-node 全能管理器            ║")
    print("╠══════════════════════════════════════════════╣")
    print("║  1. 一键部署 drpy-node                       ║")
    print("║  2. 服务管理                                 ║")
    print("║  3. 自启动配置                               ║")
    print("║  4. 彻底卸载                                 ║")
    print("║  5. 退出                                     ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"{Colors.NC}")

# 显示服务管理菜单
def show_service_menu():
    os.system('clear')
    print(f"{Colors.CYAN}")
    print("╔══════════════════════════════════════════════╗")
    print("║                🔧 服务管理                  ║")
    print("╠══════════════════════════════════════════════╣")
    print("║  1. 启动服务                                 ║")
    print("║  2. 停止服务                                 ║")
    print("║  3. 重启服务                                 ║")
    print("║  4. 查看状态                                 ║")
    print("║  5. 查看日志                                 ║")
    print("║  6. 返回主菜单                               ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"{Colors.NC}")

# 自动确认（10秒无操作自动继续）
def auto_confirm():
    info("🤖 智能部署脚本启动")
    info("将在 10 秒后自动开始部署...")
    print(f"{Colors.PURPLE}按 Ctrl+C 取消部署...{Colors.NC}", end="")
    
    try:
        for i in range(10, 0, -1):
            print(f"\r{Colors.PURPLE}{i}秒后开始自动部署...{Colors.NC} ", end="")
            sys.stdout.flush()
            time.sleep(1)
        print(f"\r{Colors.GREEN}开始自动部署...                      {Colors.NC}")
    except KeyboardInterrupt:
        print(f"\r{Colors.RED}部署已取消                            {Colors.NC}")
        sys.exit(1)

# 智能安装函数（自动重试）
def smart_install(pkg_name):
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        log(f"正在安装 {pkg_name} (尝试 {retry_count+1}/{max_retries})")
        try:
            result = subprocess.run(
                ["pkg", "install", "-y", pkg_name],
                capture_output=True,
                text=True,
                check=True
            )
            log(f"✓ {pkg_name} 安装成功")
            return True
        except subprocess.CalledProcessError:
            retry_count += 1
            warn(f"{pkg_name} 安装失败，正在重试...")
            time.sleep(2)
    
    error(f"{pkg_name} 安装失败，请检查网络连接")
    return False

# 一键环境准备
def setup_environment():
    info("🚀 开始智能环境准备")
    
    # 更新包管理器（静默模式）
    log("更新包管理器...")
    try:
        subprocess.run(["pkg", "update", "-y"], capture_output=True, check=True)
        subprocess.run(["pkg", "upgrade", "-y"], capture_output=True, check=True)
        log("✓ 系统更新完成")
    except subprocess.CalledProcessError:
        warn("系统更新失败，继续执行...")
    
    # 批量安装依赖
    dependencies = ["curl", "wget", "git", "python", "nodejs", "yarn"]
    for dep in dependencies:
        smart_install(dep)
    
    # 智能 Node.js 版本管理
    try:
        result = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True)
        node_version = result.stdout.strip().replace('v', '')
        major_version = int(node_version.split('.')[0])
        if major_version >= 20:
            log(f"✓ Node.js 版本符合要求 (v{node_version})")
        else:
            warn("Node.js 版本过低，升级中...")
            subprocess.run(["pkg", "install", "-y", "nodejs-lts"], capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        smart_install("nodejs-lts")
    
    # 安装 PM2
    try:
        subprocess.run(["pm2", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("安装 PM2 进程管理器...")
        subprocess.run(["npm", "install", "-g", "pm2"], capture_output=True)
        log("✓ PM2 安装完成")
    
    # 配置国内镜像
    log("配置国内镜像源...")
    subprocess.run(["npm", "config", "set", "registry", "https://registry.npmmirror.com"], capture_output=True)
    subprocess.run(["yarn", "config", "set", "registry", "https://registry.npmmirror.com"], capture_output=True)
    
    # 尝试配置 pip 镜像
    try:
        subprocess.run([
            "pip", "config", "set", "global.index-url", 
            "https://pypi.tuna.tsinghua.edu.cn/simple"
        ], capture_output=True)
    except:
        pass  # pip 配置可能失败，不影响主要流程
    
    log("✓ 镜像源配置完成")

# 智能依赖安装（增强版）
def install_dependencies():
    info("📚 安装项目依赖")
    
    # Node.js 依赖 - 智能多源安装
    log("安装 Node.js 依赖...")
    
    # 定义多个备选安装方案
    node_sources = [
        ["yarn", "install", "--production", "--silent", "--registry=https://registry.npmmirror.com"],
        ["yarn", "install", "--production", "--silent", "--registry=https://registry.npm.taobao.org"],
        ["yarn", "install", "--production", "--silent", "--registry=https://registry.npmjs.org"],
        ["npm", "install", "--production", "--silent", "--registry=https://registry.npmmirror.com"],
        ["npm", "install", "--production", "--silent", "--registry=https://registry.npm.taobao.org"],
        ["npm", "install", "--production", "--silent", "--registry=https://registry.npmjs.org"],
        ["npm", "install", "--silent", "--registry=https://registry.npmmirror.com"],
        ["npm", "install", "--silent", "--registry=https://registry.npm.taobao.org"],
    ]
    
    node_success = False
    for install_cmd in node_sources:
        log(f"尝试安装命令: {' '.join(install_cmd)}")
        try:
            subprocess.run(install_cmd, check=True, capture_output=True)
            log("✓ Node.js 依赖安装完成")
            node_success = True
            break
        except subprocess.CalledProcessError:
            warn("安装失败，尝试下一方案...")
            # 清理可能的缓存问题
            for item in ["node_modules", "package-lock.json", "yarn.lock"]:
                if os.path.exists(item):
                    if os.path.isdir(item):
                        shutil.rmtree(item)
                    else:
                        os.remove(item)
            time.sleep(2)
    
    if not node_success:
        error("所有 Node.js 依赖安装方案均失败")
        warn("尝试强制清理后重新安装...")
        for item in ["node_modules", "package-lock.json", "yarn.lock"]:
            if os.path.exists(item):
                if os.path.isdir(item):
                    shutil.rmtree(item)
                else:
                    os.remove(item)
        
        try:
            subprocess.run(["npm", "cache", "clean", "--force"], capture_output=True)
            subprocess.run(["npm", "install", "--silent"], capture_output=True, check=True)
            log("✓ Node.js 依赖最终安装成功")
        except subprocess.CalledProcessError:
            error("Node.js 依赖安装彻底失败，请检查网络")
            return False
    
    # Python 依赖 - 智能多源安装
    log("安装 Python 依赖...")
    if not os.path.exists(".venv"):
        subprocess.run(["python", "-m", "venv", ".venv"], capture_output=True)
    
    # 激活虚拟环境
    if os.path.exists(".venv/bin/activate"):
        activate_script = "source .venv/bin/activate"
    else:
        activate_script = ".venv\\Scripts\\activate"  # Windows
    
    # 智能选择 pip 源
    pip_sources = [
        "https://pypi.tuna.tsinghua.edu.cn/simple",
        "https://pypi.douban.com/simple",
        "https://mirrors.aliyun.com/pypi/simple",
        "https://pypi.mirrors.ustc.edu.cn/simple",
    ]
    
    pip_success = False
    requirements_file = "spider/py/base/requirements.txt"
    
    if os.path.exists(requirements_file):
        for source in pip_sources:
            log(f"尝试 pip 源: {source}")
            host = source.replace("https://", "").split("/")[0]
            try:
                cmd = [
                    "pip", "install", "-r", requirements_file, "-i", source,
                    "--trusted-host", host, "--quiet"
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                log("✓ Python 依赖安装完成")
                pip_success = True
                break
            except subprocess.CalledProcessError:
                warn(f"Pip 源 {source} 失败，尝试下一个...")
        
        if not pip_success:
            warn("所有 pip 源均失败，尝试不使用镜像源...")
            try:
                subprocess.run(["pip", "install", "-r", requirements_file, "--quiet"], 
                             check=True, capture_output=True)
                log("✓ Python 依赖安装完成（使用默认源）")
            except subprocess.CalledProcessError:
                error("Python 依赖安装失败")
                # 不退出，继续执行，因为 Python 依赖可能不是必须的
    else:
        warn(f"未找到 requirements.txt 文件: {requirements_file}")
    
    return True

# 智能配置文件设置
def setup_config_files():
    info("⚙️ 配置智能设置")
    
    # 创建配置目录
    os.makedirs("config", exist_ok=True)
    
    # 生成默认配置文件（如果不存在）
    if not os.path.exists("config/env.json"):
        log("创建 env.json 配置文件")
        env_config = {
            "ali_token": "",
            "ali_refresh_token": "",
            "quark_cookie": "",
            "uc_cookie": "",
            "bili_cookie": "",
            "thread": "10",
            "enable_dr2": "1",
            "enable_py": "2"
        }
        with open("config/env.json", "w", encoding="utf-8") as f:
            json.dump(env_config, f, indent=2, ensure_ascii=False)
    
    if not os.path.exists(".env"):
        log("创建 .env 配置文件（使用简洁密码）")
        env_content = """COOKIE_AUTH_CODE = drpy
API_AUTH_NAME = admin
API_AUTH_CODE = drpy
API_PWD = dzyyds
"""
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)

# 智能项目部署
def deploy_project():
    info("📦 开始项目部署")
    
    # 自动选择项目目录
    project_dir = os.path.expanduser("~/drpy-node")
    if os.path.exists(project_dir):
        warn(f"检测到已存在项目目录，使用现有目录: {project_dir}")
    else:
        log(f"创建项目目录: {project_dir}")
        os.makedirs(project_dir, exist_ok=True)
    
    os.chdir(project_dir)
    
    # 智能 Git 操作
    if os.path.exists(".git"):
        log("更新项目代码...")
        try:
            subprocess.run(["git", "fetch", "origin", "main"], capture_output=True, check=True)
            subprocess.run(["git", "pull", "origin", "main"], capture_output=True, check=True)
            log("✓ 项目更新完成")
        except subprocess.CalledProcessError:
            warn("代码更新冲突，执行强制更新...")
            subprocess.run(["git", "reset", "--hard", "origin/main"], capture_output=True)
    else:
        log("克隆项目代码...")
        # 自动选择最快的 GitHub 镜像
        mirrors = [
            "https://github.com/hjdhnx/drpy-node.git",
            "https://kgithub.com/hjdhnx/drpy-node.git",
            "https://gitclone.com/github.com/hjdhnx/drpy-node.git",
        ]
        
        success = False
        for mirror in mirrors:
            log(f"尝试镜像: {mirror}")
            try:
                # 清理目录
                for item in os.listdir(project_dir):
                    item_path = os.path.join(project_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                
                subprocess.run(["git", "clone", mirror, "."], 
                             timeout=30, capture_output=True, check=True)
                log("✓ 项目克隆成功")
                success = True
                break
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                warn("镜像连接失败，尝试下一个...")
        
        if not success:
            error("所有镜像连接失败，请检查网络")
            return False
    
    # 智能配置文件生成
    setup_config_files()
    
    # 安装项目依赖
    return install_dependencies()

# 智能服务管理
def setup_service():
    info("🚀 启动服务")
    
    # 检查服务是否存在
    try:
        result = subprocess.run(["pm2", "describe", "drpyS"], capture_output=True, text=True)
        if result.returncode == 0:
            log("重启现有服务...")
            subprocess.run(["pm2", "restart", "drpyS", "--silent"], capture_output=True)
        else:
            log("启动新服务...")
            subprocess.run(["pm2", "start", "index.js", "--name", "drpyS", "--silent"], capture_output=True)
    except subprocess.CalledProcessError:
        log("启动新服务...")
        subprocess.run(["pm2", "start", "index.js", "--name", "drpyS", "--silent"], capture_output=True)
    
    # 等待服务启动
    log("等待服务启动...")
    time.sleep(5)
    
    # 设置自启动
    subprocess.run(["pm2", "save", "--silent"], capture_output=True)
    log("✓ 服务启动完成")
    
    # 尝试设置开机自启
    try:
        result = subprocess.run(["pm2", "startup"], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        if lines:
            startup_cmd = lines[-1].strip()
            if startup_cmd:
                with open("pm2_startup.sh", "w") as f:
                    f.write(startup_cmd)
                os.chmod("pm2_startup.sh", 0o755)
                subprocess.run(["./pm2_startup.sh"], capture_output=True)
                os.remove("pm2_startup.sh")
    except:
        warn("PM2 开机自启配置失败，可手动配置")

# 智能网络检测
def show_network_info():
    info("🌐 检测网络信息")
    
    # 获取 IP 地址（简化版本）
    ip = "无法获取"
    try:
        # 尝试多种方法获取 IP
        result = subprocess.run(["ip", "route", "get", "1"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'src' in line:
                    parts = line.split()
                    if 'src' in parts:
                        idx = parts.index('src')
                        if idx + 1 < len(parts):
                            ip = parts[idx + 1]
                            break
    except:
        pass
    
    # 显示访问信息
    print(f"{Colors.CYAN}")
    print("╔══════════════════════════════════════════════╗")
    print("║                🎉 部署完成！                 ║")
    print("╠══════════════════════════════════════════════╣")
    print("║  🌍 访问地址:                                ║")
    print("║     • 本地: http://127.0.0.1:5757           ║")
    if ip != "无法获取":
        print(f"║     • 局域网: http://{ip}:5757              ║")
    print("║                                              ║")
    print("║  🔐 登录信息:                                ║")
    
    # 读取配置信息
    env_file = ".env"
    if os.path.exists(env_file):
        config = {}
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        api_name = config.get('API_AUTH_NAME', 'admin')
        api_code = config.get('API_AUTH_CODE', 'drpy')
        cookie_code = config.get('COOKIE_AUTH_CODE', 'drpy')
        api_pwd = config.get('API_PWD', 'dzyyds')
        
        print(f"║     • 用户名: {api_name:<28} ║")
        print(f"║     • 密码: {api_code:<30} ║")
        print(f"║     • 入库密码: {cookie_code:<25} ║")
        print(f"║     • 订阅PWD: {api_pwd:<26} ║")
    
    print("║                                              ║")
    print("║  📝 管理命令:                                ║")
    print("║     • pm2 logs drpyS    # 查看日志           ║")
    print("║     • pm2 restart drpyS # 重启服务           ║")
    print("║     • pm2 stop drpyS    # 停止服务           ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"{Colors.NC}")

# 健康检查
def health_check():
    info("🔍 执行健康检查")
    
    time.sleep(3)
    
    # 检查进程状态
    try:
        result = subprocess.run(["pm2", "describe", "drpyS"], capture_output=True, text=True, check=True)
        if "online" in result.stdout:
            log("✓ 服务运行正常")
            return True
    except subprocess.CalledProcessError:
        pass
    
    warn("服务启动异常，尝试修复...")
    subprocess.run(["pm2", "delete", "drpyS"], capture_output=True)
    time.sleep(2)
    subprocess.run(["pm2", "start", "index.js", "--name", "drpyS", "--silent"], capture_output=True)
    time.sleep(3)
    
    try:
        subprocess.run(["pm2", "describe", "drpyS"], capture_output=True, check=True)
        log("✓ 服务修复成功")
        return True
    except subprocess.CalledProcessError:
        error("服务启动失败，请查看日志: pm2 logs drpyS")
        return False

# 一键部署功能
def one_click_deploy():
    os.system('clear')
    print(f"{Colors.PURPLE}")
    print("╔══════════════════════════════════════════════╗")
    print("║           🤖 drpy-node 智能部署脚本          ║")
    print("║                 🚀 一键搞定                 ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"{Colors.NC}")
    
    # 执行部署流程
    check_termux()
    auto_confirm()
    setup_environment()
    if deploy_project():
        setup_service()
        health_check()
        show_network_info()
        log("🎊 所有操作已完成！打开浏览器访问上述地址即可使用。")
        warn("💡 提示：如需重新部署，再次运行此脚本即可")
    else:
        error("部署失败，请检查错误信息")

# 服务管理功能
def service_management():
    while True:
        show_service_menu()
        try:
            choice = input("请选择操作 (1-6): ").strip()
            
            if choice == "1":
                start_service()
            elif choice == "2":
                stop_service()
            elif choice == "3":
                restart_service()
            elif choice == "4":
                show_service_status()
            elif choice == "5":
                show_service_logs()
            elif choice == "6":
                return
            else:
                error("无效选择，请重新输入")
                time.sleep(2)
        except KeyboardInterrupt:
            return
        
        print()
        input("按回车键继续...")

# 启动服务
def start_service():
    info("启动 drpy-node 服务...")
    
    project_dir = os.path.expanduser("~/drpy-node")
    if not os.path.exists(project_dir):
        error("找不到 drpy-node 目录，请先部署项目")
        return False
    
    os.chdir(project_dir)
    
    # 激活虚拟环境
    if os.path.exists(".venv"):
        # 在 Python 中我们无法直接 source，依赖会在子进程中自动处理
        pass
    
    try:
        result = subprocess.run(["pm2", "describe", "drpyS"], capture_output=True, text=True)
        if result.returncode == 0:
            subprocess.run(["pm2", "restart", "drpyS", "--silent"], capture_output=True)
        else:
            subprocess.run(["pm2", "start", "index.js", "--name", "drpyS", "--silent"], capture_output=True)
        
        subprocess.run(["pm2", "save", "--silent"], capture_output=True)
        log("✓ 服务启动完成")
        show_service_status()
        return True
    except subprocess.CalledProcessError:
        error("PM2 操作失败")
        return False

# 停止服务
def stop_service():
    info("停止 drpy-node 服务...")
    
    try:
        result = subprocess.run(["pm2", "describe", "drpyS"], capture_output=True, text=True)
        if result.returncode == 0:
            subprocess.run(["pm2", "stop", "drpyS", "--silent"], capture_output=True)
            log("✓ 服务已停止")
        else:
            warn("服务未运行")
    except subprocess.CalledProcessError:
        error("未找到 PM2")

# 重启服务
def restart_service():
    info("重启 drpy-node 服务...")
    
    try:
        result = subprocess.run(["pm2", "describe", "drpyS"], capture_output=True, text=True)
        if result.returncode == 0:
            subprocess.run(["pm2", "restart", "drpyS", "--silent"], capture_output=True)
            log("✓ 服务重启完成")
            show_service_status()
        else:
            warn("服务未运行，尝试启动...")
            start_service()
    except subprocess.CalledProcessError:
        error("未找到 PM2")

# 显示服务状态
def show_service_status():
    info("服务状态检查...")
    
    try:
        print(f"{Colors.CYAN}")
        print("╔══════════════════════════════════════════════╗")
        print("║                📊 服务状态                  ║")
        print("╠══════════════════════════════════════════════╣")
        subprocess.run(["pm2", "list"])
        print("╚══════════════════════════════════════════════╝")
        print(f"{Colors.NC}")
    except subprocess.CalledProcessError:
        error("未安装 PM2")

# 显示服务日志
def show_service_logs():
    info("显示服务日志 (Ctrl+C 退出)...")
    print(f"{Colors.YELLOW}")
    print("════════════════ 开始日志 ═════════════════")
    print(f"{Colors.NC}")
    
    try:
        subprocess.run(["pm2", "logs", "drpyS", "--lines", "50", "--timestamp"])
    except subprocess.CalledProcessError:
        error("未安装 PM2")
    except KeyboardInterrupt:
        log("日志查看已退出")

# 自启动配置
def setup_autostart():
    info("开始配置自启动...")
    
    # 创建启动脚本
    startup_script = os.path.expanduser("~/.termux/boot/start_drpy.sh")
    
    # 创建 boot 目录
    os.makedirs(os.path.dirname(startup_script), exist_ok=True)
    
    # 创建启动脚本
    script_content = """#!/bin/bash
# Termux 开机自启动脚本

# 等待系统启动完成
sleep 10

# 设置环境变量
export HOME="/data/data/com.termux/files/home"
export PATH="/data/data/com.termux/files/usr/bin:$PATH"

# 等待 Termux 环境就绪
while [ ! -f "/data/data/com.termux/files/usr/bin/bash" ]; do
    sleep 5
done

# 等待网络连接
while ! ping -c 1 -W 1 8.8.8.8 >/dev/null 2>&1; do
    sleep 5
done

# 切换到项目目录
cd "$HOME/drpy-node" 2>/dev/null || {
    echo "错误: 找不到 drpy-node 目录"
    exit 1
}

# 激活 Python 虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 启动 PM2 服务
if command -v pm2 >/dev/null 2>&1; then
    # 等待 PM2 就绪
    sleep 3
    pm2 resurrect >/dev/null 2>&1 || {
        # 如果恢复失败，直接启动服务
        pm2 start index.js --name drpyS --silent
        pm2 save --silent
    }
    echo "drpy-node 服务已启动"
else
    echo "错误: 未找到 PM2"
fi
"""
    
    with open(startup_script, "w", encoding="utf-8") as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod(startup_script, 0o755)
    
    # 配置 PM2 自启动
    try:
        subprocess.run(["pm2", "save", "--silent"], capture_output=True)
        # 生成 PM2 启动脚本
        result = subprocess.run(["pm2", "startup"], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        if lines:
            startup_cmd = lines[-1].strip()
            if startup_cmd:
                pm2_script = os.path.expanduser("~/pm2_startup.sh")
                with open(pm2_script, "w") as f:
                    f.write(startup_cmd)
                os.chmod(pm2_script, 0o755)
                subprocess.run([pm2_script], capture_output=True)
                os.remove(pm2_script)
    except:
        warn("PM2 自启动配置失败")
    
    log("✓ 自启动配置完成")
    log(f"📝 启动脚本位置: {startup_script}")
    warn("⚠️ 需要 Termux:Boot 插件支持自启动功能")
    info("🔍 请从 F-Droid 安装 'Termux:Boot' 应用")
    print()
    info("📋 自启动配置说明：")
    info("  1. 安装 Termux:Boot 应用")
    info("  2. 重启设备测试自启动")
    info("  3. 查看日志: pm2 logs drpyS")

# 彻底卸载功能
def complete_uninstall():
    os.system('clear')
    print(f"{Colors.RED}")
    print("╔══════════════════════════════════════════════╗")
    print("║              🗑️ 彻底卸载                    ║")
    print("║                ❗️ 警告                       ║")
    print("╠══════════════════════════════════════════════╣")
    print("║ 此操作将永久删除 drpy-node 所有数据！        ║")
    print("║           包括：                             ║")
    print("║   • 所有项目文件                             ║")
    print("║   • 数据库和配置                             ║")
    print("║   • 服务设置                                 ║")
    print("║   • 自启动配置                               ║")
    print("║                                              ║")
    print("║           🚨 此操作不可恢复！               ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"{Colors.NC}")

    # 确认卸载
    confirm = input("确认要彻底卸载 drpy-node 吗？(输入 'DELETE' 确认): ").strip()

    if confirm != "DELETE":
        log("取消卸载操作")
        return

    # 开始卸载
    log("开始彻底卸载 drpy-node...")

    # 1. 停止服务
    log("停止运行的服务...")
    try:
        subprocess.run(["pm2", "delete", "drpyS", "--silent"], capture_output=True)
        subprocess.run(["pm2", "save", "--silent"], capture_output=True)
    except:
        pass

    # 2. 删除项目目录
    log("删除项目文件...")
    project_dir = os.path.expanduser("~/drpy-node")
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
        log("✓ 项目目录已删除")
    else:
        warn("项目目录不存在")

    # 3. 删除自启动脚本
    log("清理自启动配置...")
    boot_scripts = [
        os.path.expanduser("~/.termux/boot/start_drpy.sh"),
        os.path.expanduser("~/.termux/boot/drpy_autostart.sh"),
    ]

    for script in boot_scripts:
        if os.path.exists(script):
            os.remove(script)
            log(f"✓ 删除自启动脚本: {os.path.basename(script)}")

    # 4. 清理 PM2 配置
    log("清理 PM2 配置...")
    try:
        subprocess.run(["pm2", "delete", "drpyS", "--silent"], capture_output=True)
        subprocess.run(["pm2", "save", "--silent"], capture_output=True)
    except:
        pass

    # 5. 清理临时文件
    log("清理临时文件...")
    temp_dirs = [
        os.path.expanduser("~/.cache/drpy"),
        os.path.expanduser("~/.local/share/drpy"),
        os.path.expanduser("~/tmp/drpy"),
    ]

    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    # 6. 清理日志文件
    log("清理日志文件...")
    log_dir = os.path.expanduser("~/.pm2/logs")
    if os.path.exists(log_dir):
        for file in os.listdir(log_dir):
            if "drpyS" in file:
                os.remove(os.path.join(log_dir, file))

    # 完成卸载
    print()
    log("🎊 彻底卸载完成！")
    warn("💡 提示：所有 drpy-node 相关文件已删除")
    print()
    log("如果要重新安装，请运行本脚本的部署功能")

# 主函数
def main():
    check_termux()
    
    # 设置信号处理
    def signal_handler(sig, frame):
        error("脚本被用户中断")
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    while True:
        show_main_menu()
        try:
            choice = input("请选择操作 (1-5): ").strip()
            
            if choice == "1":
                one_click_deploy()
            elif choice == "2":
                service_management()
            elif choice == "3":
                setup_autostart()
            elif choice == "4":
                complete_uninstall()
            elif choice == "5":
                log("再见！")
                sys.exit(0)
            else:
                error("无效选择，请重新输入")
                time.sleep(2)
        except KeyboardInterrupt:
            log("再见！")
            sys.exit(0)
        except EOFError:
            log("再见！")
            sys.exit(0)
        
        print()
        input("按回车键返回主菜单...")

if __name__ == "__main__":
    main()