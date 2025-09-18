#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_main_doxygen.py - 主文档Doxygen生成脚本
在指定目录下执行doxygen Doxyfile_en 和 doxygen Doxyfile_zh
"""

import os
import subprocess
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from common_utils import BaseGenerator, ArgumentParser, Logger, ConfigManager


class DoxygenGenerator(BaseGenerator):
    """Doxygen生成器类"""
    
    def __init__(self, output_folder, chip_config):
        """初始化Doxygen生成器"""
        super().__init__("", output_folder, chip_config)  # input_folder 在此脚本中不使用
        self.doxygen_dir = self.output_folder / "doxygen" / "main"
        
    def run_doxygen_command(self, doxyfile_name):
        """执行doxygen命令"""
        try:
            # 切换到doxygen目录
            os.chdir(self.doxygen_dir)
            
            # 执行doxygen命令
            result = subprocess.run(
                ['doxygen', doxyfile_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            return True
            
        except subprocess.CalledProcessError as e:
            Logger.error(f"执行失败: doxygen {doxyfile_name}")
            if e.stderr:
                Logger.error(f"错误信息: {e.stderr}")
            return False
            
        except FileNotFoundError:
            Logger.error("未找到 doxygen 命令，请确保已安装 Doxygen 并添加到系统 PATH 中")
            return False
            
        except Exception as e:
            Logger.error(f"执行 doxygen {doxyfile_name} 时发生未知错误: {e}")
            return False
    
    def check_doxyfile_exists(self, doxyfile_name):
        """检查Doxyfile文件是否存在"""
        doxyfile_path = self.doxygen_dir / doxyfile_name
        return doxyfile_path.exists()
    
    def ensure_output_directories(self):
        """确保输出目录存在"""
        try:
            # 创建输出目录
            self.ensure_output_dir("output", "main", "en")
            self.ensure_output_dir("output", "main", "cn")
            return True
            
        except Exception as e:
            Logger.error(f"创建输出目录失败: {e}")
            return False

    def generate(self):
        """生成Doxygen文档"""
        try:
            # 检查doxygen目录是否存在
            if not self.doxygen_dir.exists():
                Logger.error(f"Doxygen目录不存在: {self.doxygen_dir}")
                return False
            
            # 确保输出目录存在
            if not self.ensure_output_directories():
                return False
            
            # 检查Doxyfile文件
            doxyfile_en_exists = self.check_doxyfile_exists("Doxyfile_en")
            doxyfile_zh_exists = self.check_doxyfile_exists("Doxyfile_zh")
            
            if not doxyfile_en_exists and not doxyfile_zh_exists:
                Logger.error("未找到任何Doxyfile文件")
                return False
            
            success_count = 0
            total_count = 0
            
            # 执行英文版
            if doxyfile_en_exists:
                total_count += 1
                if self.run_doxygen_command("Doxyfile_en"):
                    success_count += 1
                else:
                    Logger.error("英文版Doxygen生成失败")
            
            # 执行中文版
            if doxyfile_zh_exists:
                total_count += 1
                if self.run_doxygen_command("Doxyfile_zh"):
                    success_count += 1
                else:
                    Logger.error("中文版Doxygen生成失败")
            
            # 检查结果
            if success_count == total_count and total_count > 0:
                return True
            else:
                Logger.error(f"Doxygen生成失败: 成功 {success_count}/{total_count}")
                return False
                
        except Exception as e:
            Logger.error(f"Doxygen生成过程失败: {e}")
            return False


def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python docs_main_doxygen.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        # 解析芯片配置JSON
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建生成器并执行
        generator = DoxygenGenerator(output_folder, chip_config)
        
        if generator.generate():
            Logger.success("Doxygen文档生成完成！")
        else:
            Logger.error("Doxygen文档生成失败！")
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
