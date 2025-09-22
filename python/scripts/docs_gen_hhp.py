#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_gen_hhp.py - HHP文件生成脚本
功能：在output_folder/output目录下扫描所有文件，生成index.hhp文件

主要功能：
1. 在output_folder/output目录下查找main、pdf、sub、extra子目录
2. 收集所有HTML、JS、CSS、PNG、SVG等文件
3. 生成完整的HHP文件内容，包括[OPTIONS]和[FILES]部分
4. 支持CHM文件中的本地路径链接

参数：
- input_folder: 输入目录（未使用，但保持接口一致性）
- output_folder: 输出目录路径
- chip_config_json: 芯片配置JSON（未使用，但保持接口一致性）
"""

import os
import sys
from pathlib import Path
from typing import Set

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from common_utils import (
    FileUtils, 
    Logger,
    ArgumentParser,
    timing_decorator,
    ConfigManager
)

class HHPGenerator:
    """
    HHP文件生成器类
    
    主要职责：
    - 在output_folder/output目录下查找文件结构
    - 收集所有需要包含在CHM中的文件
    - 生成完整的HHP文件内容
    """
    
    def __init__(self, input_folder: str, output_folder: str, chip_config: dict = None):
        """
        初始化HHP生成器
        
        参数：
        - input_folder: 输入目录路径（未使用，但保持接口一致性）
        - output_folder: 输出目录路径
        - chip_config: 芯片配置
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.output_dir = self.output_folder / "output"
        self.chip_config = chip_config or {}
        
        # 定义需要包含的文件扩展名
        self.include_extensions = {
            '.html', '.htm', '.js', '.css', '.png', '.jpg', '.jpeg', 
            '.gif', '.svg', '.ico', '.bmp', '.tiff', '.webp'
        }
    
    def get_chip_series_name(self):
        """
        获取芯片系列名称，格式为 chipName + "_V" + chipVersion
        
        返回：
        - str: 芯片系列名称
        """
        # 从芯片配置中获取芯片名称和版本
        chip_name = self.chip_config.get('chipName', 'Unknown')
        chip_version = self.chip_config.get('chipVersion', '1.0.0')
        
        # 组合为 chipName + "V" + chipVersion 格式
        chip_series = f"{chip_name}_V{chip_version}"
        return chip_series
    
    def scan_directory(self, directory_path: Path) -> Set[str]:
        """
        扫描指定目录下的所有文件
        
        参数：
        - directory_path: 要扫描的目录路径
        
        返回：
        - Set[str]: 文件路径集合（相对于output目录）
        """
        files = set()
        
        if not directory_path.exists():
            return files
        
        # 递归扫描所有文件
        for root, dirs, filenames in os.walk(directory_path):
            root_path = Path(root)
            
            for filename in filenames:
                file_path = root_path / filename
                
                # 检查文件扩展名
                if file_path.suffix.lower() in self.include_extensions:
                    # 计算相对于output目录的路径
                    try:
                        relative_path = file_path.relative_to(self.output_dir)
                        # 转换为Windows路径格式（使用反斜杠）
                        relative_path_str = str(relative_path).replace('/', '\\')
                        files.add(relative_path_str)
                    except ValueError:
                        # 如果无法计算相对路径，跳过
                        continue
        
        return files
    
    def generate_hhp_content(self, all_files: Set[str], chip_series: str) -> str:
        """
        生成HHP文件内容
        
        参数：
        - all_files: 所有文件路径集合
        - chip_series: 芯片系列名称
        
        返回：
        - str: 完整的HHP文件内容
        """
        # 生成[OPTIONS]部分
        options_section = f"""[OPTIONS]
Compiled file=../{chip_series}.chm
Default topic=main/en/html/index.html
Contents file=index.hhc
Index file=index.hhk
Title={chip_series} Documentation
Display compile progress=Yes
Language=0x409 English (United States)
Default Window=main
Full-text search=No

[WINDOWS]
main="{chip_series} Documentation","index.hhc","index.hhk","main/en/html/index.html","main/en/html/index.html",,,,,0x23520,,0x10387e,,,,,,,,0

"""
        
        # 生成[FILES]部分
        files_section = "[FILES]\n"
        
        # 按目录分组排序文件
        sorted_files = sorted(all_files)
        
        for file_path in sorted_files:
            files_section += f"{file_path}\n"
        
        # 组合完整内容
        hhp_content = options_section + files_section
        
        return hhp_content
    
    def generate_hhk_content(self) -> str:
        """
        生成HHK文件内容
        
        返回：
        - str: 完整的HHK文件内容
        """
        hhk_content = """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<HTML>
<HEAD>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</HEAD>
<BODY>
<UL>
</UL>
</BODY>
</HTML>"""
        
        return hhk_content
    
    def generate_hhp_files(self) -> bool:
        """
        生成HHP文件
        
        返回：
        - bool: 是否成功
        """
        # 获取芯片系列名称
        chip_series = self.get_chip_series_name()
        try:
            if not self.output_dir.exists():
                Logger.error(f"输出目录不存在: {self.output_dir}")
                return False
            
            # 扫描各个子目录
            all_files = set()
            
            # 扫描main目录
            main_dir = self.output_dir / "main"
            if main_dir.exists():
                main_files = self.scan_directory(main_dir)
                all_files.update(main_files)
            
            # 扫描pdf目录
            pdf_dir = self.output_dir / "pdf"
            if pdf_dir.exists():
                pdf_files = self.scan_directory(pdf_dir)
                all_files.update(pdf_files)
            
            # 扫描sub目录
            sub_dir = self.output_dir / "sub"
            if sub_dir.exists():
                sub_files = self.scan_directory(sub_dir)
                all_files.update(sub_files)
            
            # 扫描extra目录
            extra_dir = self.output_dir / "extra"
            if extra_dir.exists():
                extra_files = self.scan_directory(extra_dir)
                all_files.update(extra_files)
            
            # 扫描output根目录下的其他文件
            for item in self.output_dir.iterdir():
                if item.is_file() and item.suffix.lower() in self.include_extensions:
                    relative_path = item.relative_to(self.output_dir)
                    relative_path_str = str(relative_path).replace('/', '\\')
                    all_files.add(relative_path_str)
            
            # 生成HHP内容
            hhp_content = self.generate_hhp_content(all_files, chip_series)
            
            # 写入HHP文件
            hhp_file = self.output_dir / "index.hhp"
            if not FileUtils.write_file(hhp_file, hhp_content):
                Logger.error(f"写入HHP文件失败: {hhp_file}")
                return False
            
            # 生成并写入HHK文件
            hhk_content = self.generate_hhk_content()
            hhk_file = self.output_dir / "index.hhk"
            if not FileUtils.write_file(hhk_file, hhk_content):
                Logger.error(f"写入HHK文件失败: {hhk_file}")
                return False
            
            return True
            
        except Exception as e:
            Logger.error(f"生成HHP文件时出错: {e}")
            return False
    
    def run(self) -> bool:
        """
        运行HHP生成器
        
        返回：
        - bool: 是否成功
        """
        # 生成HHP文件
        return self.generate_hhp_files()


@timing_decorator
def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python docs_gen_hhp.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建生成器并执行
        generator = HHPGenerator(input_folder, output_folder, chip_config)
        
        if not generator.run():
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()