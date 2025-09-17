#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_gen_config.py - 生成Config.html配置文件
为项目生成Config.html配置文件，用于CHM文档的基路径设置
"""

import os
import re
import sys
import json
from pathlib import Path


class ConfigGenerator:
    """Config.html生成器类"""
    
    def __init__(self, input_folder, output_folder, chip_config):
        """初始化Config生成器"""
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.chip_config = chip_config
        self.work_dir = Path(__file__).parent.parent.parent
        self.template_path = self.work_dir / "template" / "Config.html"
        
        # 从芯片配置中获取项目信息
        self.chip_name = chip_config.get('chipName', '')
        self.chip_version = chip_config.get('chipVersion', '')
        self.project_name = f"{self.chip_name}V{self.chip_version}"
    
    def load_template(self):
        """加载Config.html模板文件"""
        try:
            if not self.template_path.exists():
                print(f"[ERROR] 模板文件不存在: {self.template_path}")
                return ""
            
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"[ERROR] 读取模板文件失败: {e}")
            return ""
    
    def replace_project_name(self, template_content, project_name):
        """替换模板中的项目名称占位符"""
        try:
            pattern = r'(getProjectName:\s*function\s*\(\)\s*\{\s*[^}]*return\s*")[^"]*(".*?\})'
            
            def replace_func(match):
                before_return = match.group(1)
                after_return = match.group(2)
                return f'{before_return}{project_name}{after_return}'
            
            return re.sub(pattern, replace_func, template_content, flags=re.DOTALL)
        except Exception as e:
            print(f"[ERROR] 替换项目名称失败: {e}")
            return template_content
    
    def ensure_output_dir(self):
        """确保输出目录存在"""
        extra_dir = self.output_folder / "output" / "extra"
        extra_dir.mkdir(parents=True, exist_ok=True)
        return extra_dir
    
    def generate_config(self):
        """生成Config.html文件"""
        try:
            # 加载模板
            template_content = self.load_template()
            if not template_content:
                return False
            
            # 替换项目名称
            config_content = self.replace_project_name(template_content, self.project_name)
            
            # 确保输出目录存在
            extra_dir = self.ensure_output_dir()
            
            # 生成Config.html文件
            config_file = extra_dir / "Config.html"
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            print(f"[INFO] 成功生成Config.html: {config_file}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 生成Config.html失败: {e}")
            return False


def main():
    """主函数"""
    try:
        # 检查参数数量
        if len(sys.argv) < 4:
            print("错误: 参数不足，期望3个参数")
            print("用法: python docs_gen_config.py <input_folder> <output_folder> <chip_config_json>")
            sys.exit(1)
        
        # 获取参数
        input_folder = sys.argv[1]
        output_folder = sys.argv[2]
        chip_config_json = sys.argv[3]
        
        # 解析芯片配置JSON
        try:
            chip_config = json.loads(chip_config_json)
        except json.JSONDecodeError as e:
            print(f"芯片配置JSON解析失败: {e}")
            sys.exit(1)
        
        # 创建生成器并执行
        generator = ConfigGenerator(input_folder, output_folder, chip_config)
        
        if generator.generate_config():
            print("Config.html生成完成！")
        else:
            print("Config.html生成失败！")
            sys.exit(1)
        
    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()