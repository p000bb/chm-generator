#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_decompression.py - 文档解压缩脚本
功能：遍历input_folder/level1/目录，智能解压所有zip文件，支持递归解压
使用7zip命令行工具进行解压，支持长路径处理

解压策略：
1. 如果zip包内只有一个文件夹：解压到当前位置（类似7-zip GUI的'解压到当前位置'）
2. 如果zip包内有多个文件/文件夹：解压到以zip文件名命名的子文件夹中
3. 递归解压：解压完成后，检查解压出来的文件夹中是否还有zip文件，如果有则再次解压（最多执行一次）
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
        
        try:
            # 检查输入文件夹是否存在
            if not self.input_folder.exists():
                Logger.error(f"输入文件夹不存在: {self.input_folder}")
                return zip_files
            
            # 扫描 input_folder 下面第一层级子目录中的zip文件
            for item in self.input_folder.iterdir():
                if item.is_dir():
                    # 扫描子目录中的zip文件
                    for zip_file in item.glob("*.zip"):
                        if zip_file.is_file():
                            zip_files.append(zip_file)
        except Exception as e:
            Logger.error(f"扫描zip文件时发生错误: {e}")
        
        return zip_files
    
    def find_zip_files_in_extracted_dirs(self, extracted_dirs):
        """在解压后的目录中查找zip文件"""
        zip_files = []
        
        for extracted_dir in extracted_dirs:
            if extracted_dir.exists() and extracted_dir.is_dir():
                # 递归查找zip文件
                for zip_file in extracted_dir.rglob("*.zip"):
                    if zip_file.is_file():
                        zip_files.append(zip_file)
        
        return zip_files
    
    def analyze_zip_structure(self, zip_path):
        """
        分析zip文件的结构，判断解压方式
        
        返回：
        - dict: {
            'extract_to_folder': bool,  # 是否需要解压到子文件夹
            'target_folder': str,       # 目标文件夹名称
            'root_items': list         # zip根目录下的项目列表
          }
        """
        try:
            import zipfile
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 获取zip文件根目录下的所有项目
                root_items = []
                for item in zip_ref.namelist():
                    # 只获取根目录下的项目（不包含子目录中的项目）
                    if '/' not in item or item.count('/') == 1 and item.endswith('/'):
                        root_items.append(item.rstrip('/'))
                
                # 过滤掉空字符串
                root_items = [item for item in root_items if item]
                
                # 判断解压方式
                if len(root_items) == 1 and root_items[0]:
                    # 只有一个根目录项目，解压到当前位置
                    return {
                        'extract_to_folder': False,
                        'target_folder': None,
                        'root_items': root_items
                    }
                else:
                    # 多个项目或单个文件，解压到以zip文件名命名的文件夹
                    zip_name = zip_path.stem  # 不包含扩展名的文件名
                    return {
                        'extract_to_folder': True,
                        'target_folder': zip_name,
                        'root_items': root_items
                    }
                    
        except Exception as e:
            Logger.error(f"分析zip文件结构失败 {zip_path.name}: {e}")
            # 出错时默认解压到子文件夹
            return {
                'extract_to_folder': True,
                'target_folder': zip_path.stem,
                'root_items': []
            }
    
    def is_already_extracted(self, zip_path, extract_info):
        """判断zip文件是否已经解压"""
        zip_dir = zip_path.parent
        zip_mtime = zip_path.stat().st_mtime
        
        if extract_info['extract_to_folder']:
            # 解压到子文件夹的情况
            target_folder = zip_dir / extract_info['target_folder']
            if target_folder.exists() and target_folder.is_dir():
                # 检查目标文件夹是否为空
                try:
                    if any(target_folder.iterdir()):
                        # 检查目标文件夹的修改时间是否晚于zip文件
                        if target_folder.stat().st_mtime > zip_mtime:
                            return True
                        # 或者检查目标文件夹内是否有比zip文件更新的文件
                        for item in target_folder.rglob('*'):
                            if item.is_file() and item.stat().st_mtime > zip_mtime:
                                return True
                except OSError:
                    pass
        else:
            # 解压到当前位置的情况
            # 检查是否有与zip根目录项目匹配的文件或文件夹
            expected_items = extract_info['root_items']
            if expected_items:
                # 检查第一个根项目是否存在且比zip文件新
                first_item = expected_items[0]
                first_item_path = zip_dir / first_item
                if first_item_path.exists():
                    if first_item_path.is_file() and first_item_path.stat().st_mtime > zip_mtime:
                        return True
                    elif first_item_path.is_dir():
                        # 检查目录的修改时间
                        if first_item_path.stat().st_mtime > zip_mtime:
                            return True
                        # 或者检查目录内是否有比zip文件更新的文件
                        try:
                            for item in first_item_path.rglob('*'):
                                if item.is_file() and item.stat().st_mtime > zip_mtime:
                                    return True
                        except OSError:
                            pass
            else:
                # 如果没有根项目信息，使用原来的时间检查方法
                for item in zip_dir.iterdir():
                    if item != zip_path and item.is_file():
                        if item.stat().st_mtime > zip_mtime:
                            return True
                    elif item != zip_path and item.is_dir():
                        try:
                            if item.stat().st_mtime > zip_mtime:
                                return True
                        except OSError:
                            pass
        
        return False
    
    def extract_zip_file(self, zip_path, extract_info):
        """根据zip文件结构解压到相应位置"""
        try:
            # 使用7zip命令行工具解压（更好的长路径支持）
            if not self.sevenzip_path:
                Logger.error("未找到7zip工具，无法解压文件")
                return False
            
            import subprocess
            import os
            
            if extract_info['extract_to_folder']:
                # 解压到以zip文件名命名的子文件夹
                extract_dir = zip_path.parent / extract_info['target_folder']
                extract_dir.mkdir(exist_ok=True)
                
                # 解压到子文件夹，保持目录结构
                cmd = [
                    self.sevenzip_path, 
                    'x',                    # 解压并保持目录结构
                    str(zip_path),          # 源文件
                    f'-o{extract_dir}',     # 输出到子文件夹
                    '-y',                   # 自动确认
                    '-r',                   # 递归处理
                    '-bb0'                  # 不显示进度条
                ]
            else:
                # 解压到当前位置
                extract_dir = zip_path.parent
                
                # 解压到当前位置，保持目录结构
                cmd = [
                    self.sevenzip_path, 
                    'x',                    # 解压并保持目录结构
                    str(zip_path),          # 源文件
                    f'-o{extract_dir}',     # 输出到zip文件所在目录
                    '-y',                   # 自动确认
                    '-r',                   # 递归处理
                    '-bb0'                  # 不显示进度条
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace')
            
            if result.returncode != 0:
                Logger.error(f"7zip解压失败: {result.stderr}")
                Logger.error(f"7zip输出: {result.stdout}")
                return False
            
            # 解压完成
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
    
    def process_zip_files(self, zip_files, is_recursive=False):
        """处理zip文件列表"""
        success_count = 0
        skip_count = 0
        extracted_dirs = []  # 记录解压后的目录，用于递归解压
        
        round_name = "递归解压" if is_recursive else "原始解压"
        
        for i, zip_file in enumerate(zip_files, 1):
            # 分析zip文件结构
            extract_info = self.analyze_zip_structure(zip_file)
            
            # 检查是否已经解压
            if self.is_already_extracted(zip_file, extract_info):
                skip_count += 1
                continue
            
            # 执行解压
            if self.extract_zip_file(zip_file, extract_info):
                success_count += 1
                # 记录解压后的目录，用于递归解压
                if extract_info['extract_to_folder']:
                    # 解压到子文件夹
                    extracted_dir = zip_file.parent / extract_info['target_folder']
                    extracted_dirs.append(extracted_dir)
                else:
                    # 解压到当前位置，记录解压后的根目录
                    if extract_info['root_items']:
                        first_item = extract_info['root_items'][0]
                        extracted_dir = zip_file.parent / first_item
                        extracted_dirs.append(extracted_dir)
            else:
                self.failed_files.append(zip_file)
                Logger.error(f"解压失败: {zip_file.name}")
        
        return success_count, skip_count, extracted_dirs
    
    def run(self):
        """执行解压任务"""
        # 检查输入文件夹是否存在
        if not self.input_folder.exists():
            Logger.error(f"输入文件夹不存在: {self.input_folder}")
            return False
        
        # 检查7zip工具是否可用
        if not self.check_sevenzip_availability():
            return False
        
        # 第一轮：解压原始zip文件
        zip_files = self.find_zip_files()
        if not zip_files:
            Logger.info("未找到任何zip文件")
            return True
        
        # 处理原始zip文件
        success_count, skip_count, extracted_dirs = self.process_zip_files(zip_files, is_recursive=False)
        
        # 第二轮：递归解压（最多执行一次）
        if extracted_dirs:
            recursive_zip_files = self.find_zip_files_in_extracted_dirs(extracted_dirs)
            
            if recursive_zip_files:
                rec_success, rec_skip, _ = self.process_zip_files(recursive_zip_files, is_recursive=True)
                
                # 合并统计信息
                success_count += rec_success
                skip_count += rec_skip
        # 输出最终统计信息
        
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
        if not decompressor.run():
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"脚本执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
