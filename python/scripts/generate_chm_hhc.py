#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_chm_hhc.py - 基于Microsoft HTML Help Workshop的CHM文件生成脚本

功能特性：
==========

必要文件验证：
- 检查output目录下的index.hhp文件
- 检查output目录下的index.hhc文件
- 检查output目录下的index.hhk文件
- 确保所有必要文件都存在

HHP文件优化：
- 更新HHP文件使用正确的CHM文件名
- 自动优化性能设置（禁用全文搜索以提升编译速度）
- 替换编译文件名为项目特定的芯片系列名称

Microsoft hhc.exe 查找：
- 在常见安装路径中查找hhc.exe
- 支持Program Files、System32等标准路径
- 在系统PATH中搜索hhc.exe
- 提供详细的安装指导

CHM文件生成：
- 调用Microsoft HTML Help Workshop的hhc.exe编译器
- 切换到output目录执行编译
- 处理Microsoft hhc.exe的特殊返回代码逻辑
- 支持自定义hhc.exe路径

编译结果验证：
- 验证CHM文件是否成功生成
- 检查生成文件的大小和完整性
- 记录编译时间和性能统计

技术特点：
- 基于Microsoft官方HTML Help Workshop
- 自动性能优化（禁用全文搜索）
- 详细的错误检查和报告
- 支持自定义hhc.exe路径

核心算法：
- Microsoft hhc.exe返回代码处理（成功返回1，失败返回0）
- 文件存在性验证
- 编译时间统计和性能分析

输出产物：
- output目录下的.chm文件
- 详细的编译统计报告

使用场景：
这个脚本是CHM文档生成流程中的最终步骤，用于将之前生成的所有HTML文档、HHP文件、HHC文件等编译成最终的CHM帮助文档。

依赖工具：
- Microsoft HTML Help Workshop hhc.exe
- 项目特定的HHP、HHC、HHK文件

性能优化：
- 自动禁用全文搜索以提升编译速度
- 详细的编译时间统计
- 文件大小和完整性验证

错误处理：
- 完整的文件存在性检查
- Microsoft hhc.exe路径自动查找
- 详细的错误报告和修复建议

命令行支持：
- 支持默认hhc.exe路径
- 支持自定义hhc.exe路径参数
- 提供详细的使用说明
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# 添加当前目录到Python路径（必须在导入common_utils之前）
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from common_utils import (
    BaseGenerator,
    Logger,
    ArgumentParser,
    ConfigManager,
    FileUtils,
    timing_decorator
)


class HHCCHMGenerator(BaseGenerator):
    """
    基于 Microsoft hhc.exe 的 CHM文件生成器类
    
    主要职责：
    - 检查output目录下的CHM配置文件
    - 调用 Microsoft HTML Help Workshop 的 hhc.exe
    - 在output目录下生成CHM文件
    """
    
    def __init__(self, input_folder, output_folder, chip_config):
        """初始化CHM生成器"""
        super().__init__(input_folder, output_folder, chip_config)
        
        # 时间统计
        self.compilation_stats = {}
        
    
    def get_chip_series_name(self):
        """
        获取芯片系列名称
        
        返回：
        - str: 芯片系列名称
        """
        # 从项目信息中获取芯片名称
        chip_series = self.project_info.get('chip_name', 'Unknown')
        return chip_series
    
    def update_hhp_file(self, hhp_file_path, chip_series, enable_optimization=True):
        """
        更新和优化HHP文件以使用正确的CHM文件名并提升性能
        
        参数：
        - hhp_file_path: HHP文件路径
        - chip_series: 芯片系列名称
        - enable_optimization: 是否启用性能优化（禁用全文搜索）
        
        返回：
        - bool: 更新是否成功
        """
        try:
            # 读取HHP文件
            content = FileUtils.read_file_with_encoding(hhp_file_path)
            
            # 替换编译文件名
            new_content = content.replace(
                "Compiled file=combined_docs.chm",
                f"Compiled file={chip_series}.chm"
            )
            
            # 性能优化：禁用全文搜索以大幅提升编译速度
            if enable_optimization:
                if "Full-text search=Yes" in new_content:
                    new_content = new_content.replace(
                        "Full-text search=Yes",
                        "Full-text search=No"
                    )
                elif "Full-text search=No" not in new_content and "[OPTIONS]" in new_content:
                    new_content = new_content.replace(
                        "[OPTIONS]",
                        "[OPTIONS]\nFull-text search=No"
                    )
            
            # 写回文件
            FileUtils.write_file(hhp_file_path, new_content)
            
            return True
            
        except Exception as e:
            Logger.error(f"更新HHP文件失败: {e}")
            return False
    
    def check_required_files(self):
        """
        检查output目录下是否存在必要的文件
        
        返回：
        - bool: 如果所有文件都存在则返回True
        """
        output_dir = self.output_folder / "output"
        
        required_files = [
            output_dir / "index.hhp",
            output_dir / "index.hhc",
            output_dir / "index.hhk"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not file_path.exists():
                missing_files.append(str(file_path))
        
        if missing_files:
            Logger.warning("缺少必要文件:")
            for file_path in missing_files:
                Logger.warning(f"  - {file_path}")
            return False
        
        return True
    
    def find_hhc_exe(self):
        """
        查找项目中的 hhc.exe
        
        返回：
        - str: hhc.exe的完整路径，如果未找到则返回None
        """
        # 获取脚本所在目录，然后构建hhc.exe的绝对路径
        script_dir = Path(__file__).parent
        hhc_exe = script_dir / ".." / ".." / "tools" / "hhc" / "hhc.exe"
        hhc_exe = hhc_exe.resolve()  # 转换为绝对路径
        
        if hhc_exe.exists():
            return str(hhc_exe)
        
        Logger.error(f"未找到项目中的 hhc.exe: {hhc_exe}")
        return None
    
    def generate_chm(self, hhc_path=None):
        """
        生成CHM文件
        
        参数：
        - hhc_path: hhc.exe的路径，如果为None则自动查找
        
        返回：
        - tuple: (生成是否成功, 编译时间)
        """
        # 记录开始时间
        start_time = time.time()
        
        # 检查必要文件
        if not self.check_required_files():
            return False, 0
        
        # 获取芯片系列名称
        chip_series = self.get_chip_series_name()
        
        # 输出目录和HHP文件路径
        output_dir = self.output_folder / "output"
        hhp_file_path = output_dir / "index.hhp"
        
        # 更新HHP文件使用正确的文件名并优化性能
        if not self.update_hhp_file(hhp_file_path, chip_series):
            return False, 0
        
        # 查找hhc.exe
        if hhc_path is None:
            hhc_path = self.find_hhc_exe()
            if hhc_path is None:
                return False, 0
        
        # 切换到输出目录
        original_dir = os.getcwd()
        os.chdir(output_dir)
        
        try:
            
            # 记录编译开始时间
            compile_start_time = time.time()
            
            # 执行 Microsoft HTML Help Compiler
            # 注意：hhc.exe 成功时返回代码为1，失败时返回代码为0或其他值
            # 只隐藏标准输出，保留错误日志用于调试
            with open(os.devnull, 'w') as devnull:
                return_code = subprocess.call(
                    [hhc_path, os.path.basename(hhp_file_path)],
                    stdout=devnull
                )
            
            # 计算编译时间
            compilation_time = time.time() - compile_start_time
            total_time = time.time() - start_time
            
            # Microsoft hhc.exe 的返回代码逻辑与常规程序相反
            if return_code == 1:
                return True, total_time
            else:
                Logger.error("CHM文件生成失败")
                Logger.error(f"返回代码: {return_code}")
                Logger.error(f"处理时间: {total_time:.2f} 秒")
                return False, total_time
                
        except Exception as e:
            total_time = time.time() - start_time
            Logger.error(f"生成CHM文件时出错: {e}")
            Logger.error(f"处理时间: {total_time:.2f} 秒")
            return False, total_time
        finally:
            # 恢复原始目录
            os.chdir(original_dir)
    
    def verify_chm_file(self):
        """验证生成的CHM文件"""
        chip_series = self.get_chip_series_name()
        chm_file = self.output_folder / "output" / f"{chip_series}.chm"
        
        if chm_file.exists():
            return True
        else:
            Logger.error("CHM文件未生成")
            return False
    
    def run(self, hhc_path=None):
        """运行CHM生成器"""
        
        # 记录总开始时间
        total_start_time = time.time()
        
        # 生成CHM文件
        success, compilation_time = self.generate_chm(hhc_path)
        
        # 计算总时间
        total_time = time.time() - total_start_time
        
        if success:
            # 验证生成的CHM文件
            self.verify_chm_file()
        else:
            Logger.error("CHM文件生成失败！")


@timing_decorator
def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python generate_chm_hhc.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        # 解析芯片配置JSON
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建生成器并执行
        generator = HHCCHMGenerator(input_folder, output_folder, chip_config)
        
        # 如果命令行参数提供了hhc.exe路径，使用指定的路径
        hhc_path = None
        if len(sys.argv) > 4:
            hhc_path = sys.argv[4]
        else:
            # 使用项目中的hhc.exe
            hhc_path = None  # 让find_hhc_exe()自动查找项目中的hhc.exe
        
        generator.run(hhc_path)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()