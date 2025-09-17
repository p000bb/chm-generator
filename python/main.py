#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - CHM文档生成工具的主入口脚本
作为中间件，接收前端参数并打印调试信息
"""

import os
import sys
import json


def main():
    """主函数"""
    # 解析参数
    if len(sys.argv) < 4:
        print("错误: 缺少必要的参数")
        print("用法: python main.py <script_name> <input_folder> <output_folder> [chip_config_json]")
        sys.exit(1)
    
    script_name = sys.argv[1]
    input_folder = sys.argv[2]
    output_folder = sys.argv[3]
    chip_config_json = sys.argv[4] if len(sys.argv) > 4 else ""
    
    # 解析芯片配置数据
    chip_config = None
    if chip_config_json:
        try:
            chip_config = json.loads(chip_config_json)
        except json.JSONDecodeError as e:
            print(f"芯片配置JSON解析失败: {e}")
            sys.exit(1)

    # 构建目标脚本路径
    scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
    target_script = os.path.join(scripts_dir, f"{script_name}.py")
    
    # 检查目标脚本是否存在
    if not os.path.exists(target_script):
        print(f"错误: 脚本文件不存在: {target_script}")
        sys.exit(1)
    
    # 执行目标脚本（传递参数）
    try:
        import subprocess
        # 准备传递给目标脚本的参数
        target_args = [target_script, input_folder, output_folder]
        if chip_config_json:
            target_args.append(chip_config_json)
        
        # 调试信息
        result = subprocess.run([sys.executable] + target_args, 
                              capture_output=False, 
                              text=True, 
                              cwd=os.path.dirname(__file__))
        sys.exit(result.returncode)
    except Exception as e:
        print(f"执行脚本失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
