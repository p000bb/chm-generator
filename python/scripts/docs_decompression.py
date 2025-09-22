#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_decompression.py - 文档解压缩脚本
功能：遍历input_folder/level1/目录，解压所有zip文件到同名文件夹
使用7zip命令行工具进行解压，支持长路径处理
"""

import os
import sys
import shutil
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from common_utils import (
    Logger, PathUtils, FileUtils, 
    timing_decorator, ArgumentParser
)

# 使用7zip命令行工具进行解压


class DocsDecompressor:
    """文档解压缩器"""
    
    def __init__(self, input_folder, output_folder):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.project_root = Path(__file__).parent.parent.parent
        self.failed_files = []  # 记录失败的文件
        self.sevenzip_path = self._find_sevenzip_executable()
    
    def _find_sevenzip_executable(self):
        """查找7zip可执行文件"""
        # 优先使用7z.exe（完整版本）
        sevenzip_path = self.project_root / "tools" / "7z" / "7z.exe"
        
        if sevenzip_path.exists() and sevenzip_path.is_file():
            return str(sevenzip_path)
        
        # 备用：尝试7za.exe
        sevenza_path = self.project_root / "tools" / "7z" / "7za.exe"
        if sevenza_path.exists() and sevenza_path.is_file():
            return str(sevenza_path)
        
        # 如果项目中没有，尝试系统PATH中的7zip
        system_path = shutil.which("7z.exe")
        if system_path:
            return system_path
        
        Logger.warning("未找到7zip工具，请确保7z.exe已放置在tools/7z/目录下")
        return None
    
    def check_sevenzip_availability(self):
        """检查7zip工具是否可用"""
        if not self.sevenzip_path:
            Logger.error("7zip工具不可用，无法执行解压操作")
            return False
        
        # 测试7zip工具是否正常工作
        try:
            import subprocess
            result = subprocess.run([self.sevenzip_path, '--help'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True
            else:
                Logger.error(f"7zip工具测试失败: {result.stderr}")
                return False
        except Exception as e:
            Logger.error(f"7zip工具测试异常: {e}")
            return False
    
    def find_zip_files(self):
        """查找input_folder下面第一层级子目录中的zip文件"""
        zip_files = []
        
        # 扫描 input_folder 下面第一层级子目录中的zip文件
        for item in self.input_folder.iterdir():
            if item.is_dir():
                # 扫描子目录中的zip文件
                for zip_file in item.glob("*.zip"):
                    if zip_file.is_file():
                        zip_files.append(zip_file)
        
        return zip_files
    
    def is_already_extracted(self, zip_path):
        """判断zip文件是否已经解压（检查同名文件夹）"""
        extract_dir = zip_path.with_suffix('')
        return extract_dir.exists() and extract_dir.is_dir()
    
    def extract_zip_file(self, zip_path):
        """解压单个zip文件"""
        try:
            extract_dir = zip_path.with_suffix('')
            
            # 检查目标目录是否已存在
            if extract_dir.exists():
                Logger.error(f"解压失败: 目标目录已存在 {extract_dir}")
                return False
            
            # 创建解压目录
            PathUtils.ensure_dir(extract_dir)
            
            # 使用7zip命令行工具解压（更好的长路径支持）
            if not self.sevenzip_path:
                Logger.error("未找到7zip工具，无法解压文件")
                return False
            
            import subprocess
            import os
            
            # 直接解压到目标目录
            cmd = [
                self.sevenzip_path, 
                'x',                    # 解压并保持目录结构
                str(zip_path),          # 源文件
                f'-o{extract_dir}',     # 输出目录
                '-y',                   # 自动确认
                '-r',                   # 递归处理
                '-bb0'                  # 不显示进度条
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                Logger.error(f"7zip解压失败: {result.stderr}")
                Logger.error(f"7zip输出: {result.stdout}")
                return False
            
            # 解压完成，保持原结构
            
            return True
                
        except subprocess.TimeoutExpired:
            Logger.error(f"解压超时: {zip_path.name}")
            return False
        except FileNotFoundError:
            Logger.error(f"7zip工具未找到: {self.sevenzip_path}")
            Logger.error(f"请确保7z.exe已放置在tools/7z/目录下")
            return False
        except Exception as e:
            Logger.error(f"解压失败 {zip_path.name}: {e}")
            return False
    
    def run(self):
        """执行解压任务"""
        # 检查7zip工具是否可用
        if not self.check_sevenzip_availability():
            return False
        
        zip_files = self.find_zip_files()
        if not zip_files:
            return True
        
        # 单线程解压
        success_count = 0
        skip_count = 0
        
        for zip_file in zip_files:
            if self.is_already_extracted(zip_file):
                skip_count += 1
                continue
            
            if self.extract_zip_file(zip_file):
                success_count += 1
            else:
                self.failed_files.append(zip_file)
        
        if self.failed_files:
            Logger.error(f"解压失败的文件 ({len(self.failed_files)} 个):")
            for failed_file in self.failed_files:
                Logger.error(f"  - {failed_file.name}")
            return False
        
        return True


@timing_decorator
def main():
    """主函数"""
    try:
        # 解析参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            expected_count=3,
            usage_message="python docs_decompression.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        # 创建解压器（解压缩脚本不需要chip_config）
        decompressor = DocsDecompressor(input_folder, output_folder)
        
        # 执行解压
        success = decompressor.run()
        
        if success:
            return 0
        else:
            return 1
        
    except Exception as e:
        Logger.error(f"脚本执行失败: {e}")
        return 1


if __name__ == "__main__":
    main()
