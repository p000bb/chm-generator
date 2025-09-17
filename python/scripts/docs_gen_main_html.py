#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_gen_main_html.py - 生成 Doxygen HTML 模板脚本
功能：复制template/html目录到output_folder/doxygen/main，并替换占位符
"""

import os
import shutil
import json
import sys
from pathlib import Path


class MainHtmlGenerator:
    """主文档HTML内容生成器"""
    
    def __init__(self, output_folder, chip_config):
        """初始化生成器"""
        self.output_folder = Path(output_folder)
        self.chip_config = chip_config
        self.work_dir = Path(__file__).parent.parent.parent  # 项目根目录
        self.template_html_dir = self.work_dir / "template" / "html"
        
        # 从芯片配置中获取项目名和版本号
        self.project_name = chip_config.get('chipName', '')
        self.chip_version = chip_config.get('chipVersion', '')
        self.project_number = f"V{self.chip_version}" if self.chip_version else "V1.0.0"
    
    def replace_placeholders(self, content):
        """
        替换内容中的占位符
        
        参数：
        - content: 文件内容
        
        返回：
        - str: 替换后的内容
        """
        # 替换占位符
        content = content.replace("{PROJECT_NAME}", self.project_name)
        content = content.replace("{PROJECT_NUMBER}", self.project_number)
        
        return content
    
    def copy_and_process_file(self, src_file, dst_file):
        """
        复制并处理单个文件
        
        参数：
        - src_file: 源文件路径
        - dst_file: 目标文件路径
        """
        try:
            # 确保目标目录存在
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果是Doxyfile文件，需要处理占位符
            if src_file.name.startswith('Doxyfile'):
                # 读取源文件内容
                with open(src_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换占位符
                processed_content = self.replace_placeholders(content)
                
                # 写入目标文件
                with open(dst_file, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
                
            else:
                # 普通文件直接复制
                shutil.copy2(src_file, dst_file)
                
        except Exception as e:
            raise Exception(f"处理文件失败 {src_file.name}: {e}")
    
    def copy_directory_recursively(self, src_dir, dst_dir):
        """
        递归复制目录并处理文件
        
        参数：
        - src_dir: 源目录
        - dst_dir: 目标目录
        """
        try:
            # 确保目标目录存在
            dst_dir.mkdir(parents=True, exist_ok=True)
            
            # 遍历源目录中的所有内容
            for item in src_dir.iterdir():
                src_path = src_dir / item.name
                dst_path = dst_dir / item.name
                
                if src_path.is_file():
                    # 复制并处理文件
                    self.copy_and_process_file(src_path, dst_path)
                elif src_path.is_dir():
                    # 递归处理子目录
                    self.copy_directory_recursively(src_path, dst_path)
                    
        except Exception as e:
            raise Exception(f"复制目录失败 {src_dir.name}: {e}")
    
    def generate(self):
        """生成main目录内容"""
        try:
            # 检查模板目录是否存在
            if not self.template_html_dir.exists():
                raise Exception(f"模板目录不存在: {self.template_html_dir}")
            
            # 构建目标目录路径
            target_main_dir = self.output_folder / "doxygen" / "main"
            
            # 如果目标目录已存在，先删除
            if target_main_dir.exists():
                shutil.rmtree(target_main_dir)
            
            # 复制模板目录内容
            self.copy_directory_recursively(self.template_html_dir, target_main_dir)
            
            return True
            
        except Exception as e:
            raise Exception(f"生成失败: {e}")


def main():
    """主函数"""
    try:
        # 检查参数数量
        if len(sys.argv) < 4:
            print("错误: 参数不足，期望3个参数")
            print("用法: python docs_gen_main_html.py <input_folder> <output_folder> <chip_config_json>")
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
        generator = MainHtmlGenerator(output_folder, chip_config)
        generator.generate()
        
        print("HTML模板生成完成！")
        
    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()