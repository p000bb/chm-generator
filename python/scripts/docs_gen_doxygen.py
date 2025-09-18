#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doxygen文档生成脚本
在output_folder的doxygen/sub目录下查找包含Doxyfile的目录，并行执行doxygen命令生成文档

主要功能：
1. 在output_folder的doxygen/sub目录下查找包含Doxyfile的目录
2. 限制为最多2层结构：大目录/小目录
3. 为所有项目预创建输出目录
4. 使用进程池并行执行doxygen命令，最大并发数6个
5. 在执行doxygen前清除对应的输出目录
6. 支持超时控制（50分钟超时）
7. 验证doxygen是否真的生成了输出文件
8. 生成详细的执行报告和统计信息

技术特点：
- 多进程并行处理，最大并发数6个
- 动态任务调度，提高资源利用率
- 支持超时控制和进程管理
- 自动输出目录清理和预创建
- 详细的日志输出和进度显示
- 完整的错误处理和异常恢复
- 支持大文件和高并发处理
"""

import os
import sys
import subprocess
import time
import shutil
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from common_utils import (
    BaseGenerator,
    Logger,
    FileUtils,
    ArgumentParser
)

class DoxygenGenerator(BaseGenerator):
    """
    Doxygen文档生成器类
    
    主要职责：
    - 在output_folder的doxygen/sub目录下查找包含Doxyfile的目录
    - 限制为最多2层结构：大目录/小目录
    - 为所有项目预创建输出目录
    - 使用进程池并行执行doxygen命令
    - 在执行doxygen前清除对应的输出目录
    - 验证doxygen是否真的生成了输出文件
    - 生成详细的执行报告和统计信息
    """
    
    def __init__(self, input_folder: str, output_folder: str, chip_config: Dict[str, Any]):
        """初始化Doxygen生成器"""
        super().__init__(input_folder, output_folder, chip_config)
        
        # 设置最大并发数
        self.max_workers = 6
        
        # 构建doxygen/sub目录路径
        self.doxygen_sub_path = self.output_folder / "doxygen" / "sub"
        
        Logger.info("Doxygen文档生成器初始化完成")
        Logger.info(f"输出目录: {self.output_folder}")
        Logger.info(f"Doxygen子目录: {self.doxygen_sub_path}")
        Logger.info(f"最大并发数: {self.max_workers}")
    
    def find_doxyfile_directories(self) -> List[Dict[str, Any]]:
        """
        在output_folder的doxygen/sub目录下查找包含Doxyfile的目录
        限制为最多2层结构：大目录/小目录
        
        返回：
        - list: 包含目录信息的字典列表
        """
        doxyfile_dirs = []
        
        if not self.doxygen_sub_path.exists():
            Logger.warning(f"doxygen/sub目录不存在: {self.doxygen_sub_path}")
            return doxyfile_dirs
        
        # 只扫描第一层和第二层目录，不递归
        for first_level in self.doxygen_sub_path.iterdir():
            if not first_level.is_dir():
                continue
            
            # 扫描第二层目录
            for second_level in first_level.iterdir():
                if not second_level.is_dir():
                    continue
                
                # 检查第二层目录是否包含Doxyfile
                doxyfile_path = second_level / "Doxyfile"
                if doxyfile_path.exists():
                    # 构建相对路径：第一层/第二层
                    relative_path = f"{first_level.name}/{second_level.name}"
                    
                    doxyfile_dirs.append({
                        'name': relative_path,
                        'path': str(second_level),
                        'doxyfile_path': str(doxyfile_path),
                        'relative_path': relative_path
                    })
        
        Logger.success(f"扫描完成，共找到 {len(doxyfile_dirs)} 个Doxyfile")
        return doxyfile_dirs
    
    def create_output_directories(self, doxyfile_dirs: List[Dict[str, Any]]) -> bool:
        """
        为所有项目预创建输出目录
        
        参数：
        - doxyfile_dirs: Doxyfile目录信息列表
        
        返回：
        - bool: 创建是否成功
        """
        try:
            created_count = 0
            
            for directory_info in doxyfile_dirs:
                try:
                    # 读取Doxyfile获取输出目录路径
                    doxyfile_path = directory_info['doxyfile_path']
                    output_dir = self.parse_doxyfile_output_directory(doxyfile_path)
                    
                    if output_dir:
                        # 创建输出目录（包括所有父目录）
                        os.makedirs(output_dir, exist_ok=True)
                        
                        # 检查目录权限
                        if os.access(output_dir, os.W_OK):
                            created_count += 1
                        else:
                            Logger.error(f"输出目录无写入权限: {output_dir}")
                            return False
                    else:
                        Logger.warning(f"无法从Doxyfile获取输出目录路径: {doxyfile_path}")
                        
                except Exception as e:
                    Logger.error(f"创建输出目录失败 {directory_info['name']}: {e}")
                    return False
            
            Logger.success(f"输出目录创建完成，共创建 {created_count} 个目录")
            return True
                
        except Exception as e:
            Logger.error(f"预创建输出目录失败: {e}")
            return False
    
    def parse_doxyfile_output_directory(self, doxyfile_path: str) -> str:
        """
        解析Doxyfile中的OUTPUT_DIRECTORY配置
        
        参数：
        - doxyfile_path: Doxyfile路径
        
        返回：
        - str: 输出目录路径
        """
        try:
            with open(doxyfile_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('OUTPUT_DIRECTORY'):
                        output_dir = line.split('=')[1].strip()
                        
                        # 如果输出目录是相对路径，转换为绝对路径
                        if not os.path.isabs(output_dir):
                            # 相对于doxygen/sub目录
                            doxygen_sub_dir = os.path.dirname(os.path.dirname(doxyfile_path))
                            output_dir = os.path.join(doxygen_sub_dir, output_dir)
                        
                        return os.path.abspath(output_dir)
            
            return None
        except Exception as e:
            Logger.error(f"解析Doxyfile输出目录失败: {e}")
            return None
    
    def clean_output_directory(self, directory_info: Dict[str, Any]) -> bool:
        """
        清除Doxyfile对应的输出目录
        
        参数：
        - directory_info: 目录信息字典
        
        返回：
        - bool: 清除是否成功
        """
        try:
            dir_name = directory_info['name']
            doxyfile_path = directory_info['doxyfile_path']
            
            # 读取Doxyfile获取输出目录路径
            output_dir = self.parse_doxyfile_output_directory(doxyfile_path)
            
            if not output_dir:
                Logger.warning(f"无法从Doxyfile获取输出目录路径: {doxyfile_path}")
                return False
            
            # 检查输出目录是否存在
            if os.path.exists(output_dir):
                try:
                    # 删除目录中的所有内容，但保留目录本身
                    for item in os.listdir(output_dir):
                        item_path = os.path.join(output_dir, item)
                        try:
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                            else:
                                os.remove(item_path)
                        except Exception as item_e:
                            Logger.warning(f"删除 {item} 时出错: {item_e}")
                            # 继续处理其他项目，不中断整个清理过程
                    
                    return True
                    
                except Exception as clean_e:
                    Logger.error(f"清除输出目录内容失败: {clean_e}")
                    return False
            else:
                return True
                
        except Exception as e:
            Logger.error(f"清除输出目录时出错: {e}")
            return False
    
    def execute_doxygen_single(self, directory_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        在指定目录中执行doxygen命令（单进程版本，用于进程池）
        
        参数：
        - directory_info: 目录信息字典
        
        返回：
        - dict: 执行结果字典
        """
        try:
            dir_name = directory_info['name']
            
            # 获取Doxyfile的绝对路径
            doxyfile_path = os.path.abspath(directory_info['doxyfile_path'])
            
            # 在执行doxygen之前清除输出目录
            if not self.clean_output_directory(directory_info):
                Logger.warning(f"清除输出目录失败，继续执行: {dir_name}")
            
            # 执行doxygen命令，使用绝对路径，不切换工作目录
            start_time = time.time()
            
            # 使用subprocess.Popen来更好地控制进程
            process = subprocess.Popen(
                ["doxygen", doxyfile_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 等待进程完成，设置超时
            try:
                stdout, stderr = process.communicate(timeout=3000)  # 50分钟超时
                returncode = process.returncode
                end_time = time.time()
                
                # 创建result对象，保持兼容性
                result = type('Result', (), {
                    'returncode': returncode,
                    'stdout': stdout,
                    'stderr': stderr
                })()
                
            except subprocess.TimeoutExpired:
                # 超时，强制终止进程
                process.kill()
                process.communicate()
                Logger.warning(f"执行超时: {dir_name}")
                return {
                    'name': dir_name,
                    'path': directory_info['path'],
                    'success': False,
                    'error': '执行超时',
                    'duration': 3000
                }
            
            # 检查doxygen进程是否正常结束
            duration = end_time - start_time
            if result.returncode == 0:
                # 验证是否真的生成了输出文件
                if self.verify_doxygen_output(directory_info):
                    Logger.success(f"执行成功: {dir_name} (耗时: {duration:.2f}秒)")
                    return {
                        'name': dir_name,
                        'path': directory_info['path'],
                        'success': True,
                        'duration': duration
                    }
                else:
                    Logger.error(f"执行异常: {dir_name} - 输出文件不完整")
                    return {
                        'name': dir_name,
                        'path': directory_info['path'],
                        'success': False,
                        'error': '输出文件不完整',
                        'duration': duration
                    }
            else:
                # 执行失败
                Logger.error(f"执行失败: {dir_name}")
                if result.stderr.strip():
                    Logger.error(f"错误信息: {result.stderr.strip()}")
                return {
                    'name': dir_name,
                    'path': directory_info['path'],
                    'success': False,
                    'error': result.stderr,
                    'duration': duration
                }
                
        except Exception as e:
            Logger.error(f"执行异常: {dir_name} - {e}")
            return {
                'name': dir_name,
                'path': directory_info['path'],
                'success': False,
                'error': str(e),
                'duration': 0
            }
    
    def execute_doxygen_parallel(self, doxyfile_dirs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用进程池并行执行doxygen命令
        
        参数：
        - doxyfile_dirs: 所有Doxyfile目录信息列表
        
        返回：
        - list: 执行结果列表
        """
        Logger.info(f"开始并行执行doxygen命令（最大并发数: {self.max_workers}）")
        
        results = []
        completed_count = 0
        total_count = len(doxyfile_dirs)
        
        # 使用ProcessPoolExecutor进行并行处理
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_dir = {
                executor.submit(self.execute_doxygen_single, dir_info): dir_info 
                for dir_info in doxyfile_dirs
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_dir):
                dir_info = future_to_dir[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1
                    
                    # 显示进度
                    status = "成功" if result['success'] else "失败"
                    duration = result.get('duration', 0)
                    Logger.info(f"[{completed_count}/{total_count}] {result['name']}: {status} (耗时: {duration:.2f}秒)")
                    
                    if not result['success'] and 'error' in result:
                        Logger.error(f"错误: {result['error']}")
                    
                except Exception as e:
                    Logger.error(f"处理任务结果时出错: {e}")
                    # 添加错误结果
                    results.append({
                        'name': dir_info['name'],
                        'path': dir_info['path'],
                        'success': False,
                        'error': f'结果处理错误: {str(e)}',
                        'duration': 0
                    })
                    completed_count += 1
        
        Logger.success("所有任务执行完成！")
        return results
    
    def verify_doxygen_output(self, directory_info: Dict[str, Any]) -> bool:
        """
        验证doxygen是否真的生成了输出文件
        
        参数：
        - directory_info: 目录信息字典
        
        返回：
        - bool: 输出是否完整
        """
        try:
            # 读取Doxyfile获取输出目录
            doxyfile_path = directory_info['doxyfile_path']
            output_dir = self.parse_doxyfile_output_directory(doxyfile_path)
            
            if not output_dir:
                return False
            
            # 检查输出目录是否存在
            if not os.path.exists(output_dir):
                return False
            
            # 检查是否生成了关键的HTML文件
            html_dir = os.path.join(output_dir, "html")
            if not os.path.exists(html_dir):
                return False
            
            # 检查关键文件
            key_files = ["index.html", "files.html"]
            missing_files = []
            
            for key_file in key_files:
                file_path = os.path.join(html_dir, key_file)
                if not os.path.exists(file_path):
                    missing_files.append(key_file)
            
            if missing_files:
                return False
            
            return True
            
        except Exception as e:
            Logger.error(f"验证输出文件时出错: {e}")
            return False
    
    def generate_execution_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成执行报告"""
        summary = {
            'execution_time': datetime.now().isoformat(),
            'total_processed': len(results),
            'success_count': sum(1 for r in results if r['success']),
            'failed_count': sum(1 for r in results if not r['success']),
            'results': results
        }
        
        # 计算总耗时
        total_duration = sum(r.get('duration', 0) for r in results)
        
        # 打印汇总信息
        Logger.info("="*60)
        Logger.info("Doxygen文档生成汇总报告")
        Logger.info("="*60)
        Logger.info(f"执行时间: {summary['execution_time']}")
        Logger.info(f"总处理目录: {summary['total_processed']}")
        Logger.info(f"成功生成: {summary['success_count']}")
        Logger.info(f"生成失败: {summary['failed_count']}")
        Logger.info(f"总耗时: {total_duration:.2f}秒 ({total_duration/60:.2f}分钟)")
        
        return summary
    
    def run(self) -> bool:
        """运行Doxygen文档生成"""
        try:
            # 查找Doxyfile目录
            doxyfile_dirs = self.find_doxyfile_directories()
            
            if not doxyfile_dirs:
                Logger.warning("未找到任何包含Doxyfile的目录")
                return False
            
            # 预创建输出目录
            if not self.create_output_directories(doxyfile_dirs):
                Logger.error("输出目录创建失败")
                return False
            
            # 并行执行doxygen命令
            start_time = time.time()
            results = self.execute_doxygen_parallel(doxyfile_dirs)
            end_time = time.time()
            
            Logger.info(f"并行执行总耗时: {end_time - start_time:.2f}秒 ({(end_time - start_time)/60:.2f}分钟)")
            
            # 生成执行报告
            summary = self.generate_execution_report(results)
            
            Logger.success("Doxygen文档生成完成！")
            return summary['failed_count'] == 0
            
        except Exception as e:
            Logger.error(f"Doxygen文档生成失败: {e}")
            return False

def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            expected_count=3,
            usage_message="python docs_gen_doxygen.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        # 显示脚本信息
        Logger.info("="*60)
        Logger.info("Doxygen文档生成脚本")
        Logger.info("="*60)
        Logger.info("功能：在output_folder的doxygen/sub目录下查找包含Doxyfile的目录，并行执行doxygen命令生成文档")
        Logger.info("特点：多进程并行处理，最大并发数6个，支持超时控制和输出目录清理")
        Logger.info("="*60)
        
        # 解析芯片配置
        from common_utils import ConfigManager
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建生成器并运行
        generator = DoxygenGenerator(input_folder, output_folder, chip_config)
        success = generator.run()
        
        if success:
            Logger.success("脚本执行成功！")
            return 0
        else:
            Logger.error("脚本执行失败！")
            return 1
            
    except Exception as e:
        Logger.error(f"脚本执行异常: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
