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

# 设置默认编码
if sys.platform.startswith('win'):
    import locale
    try:
        # 尝试设置控制台编码为UTF-8
        os.system('chcp 65001 > nul 2>&1')
    except:
        pass

def safe_str(s):
    """安全地处理字符串，避免编码问题"""
    if isinstance(s, str):
        return s
    elif isinstance(s, bytes):
        try:
            return s.decode('utf-8', errors='replace')
        except:
            return str(s)
    else:
        return str(s)

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from common_utils import (
    BaseGenerator,
    Logger,
    ArgumentParser,
    timing_decorator
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
    
    def get_doxygen_executable_path(self) -> str:
        """
        获取项目中的doxygen.exe路径
        
        返回：
        - str: doxygen.exe的绝对路径，如果未找到则返回None
        """
        try:
            # 获取当前脚本所在目录
            current_dir = Path(__file__).parent
            
            # 构建doxygen.exe路径：当前脚本目录 -> .. -> .. -> tools -> doxygen -> doxygen.exe
            doxygen_exe = current_dir / ".." / ".." / "tools" / "doxygen" / "doxygen.exe"
            doxygen_exe = doxygen_exe.resolve()
            
            # 检查文件是否存在
            if doxygen_exe.exists():
                return str(doxygen_exe)
            else:
                Logger.error(f"doxygen.exe不存在: {doxygen_exe}")
                return None
                
        except Exception as e:
            Logger.error(f"获取doxygen.exe路径时出错: {e}")
            return None
        
    
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
            
            # 获取项目中的doxygen.exe路径
            doxygen_exe = self.get_doxygen_executable_path()
            if not doxygen_exe:
                Logger.error(f"未找到doxygen.exe")
                return {
                    'name': dir_name,
                    'path': directory_info['path'],
                    'success': False,
                    'error': '未找到doxygen.exe',
                    'duration': 0
                }
            
            # 执行doxygen命令，使用项目中的doxygen.exe
            start_time = time.time()
            
            # 使用subprocess.Popen来更好地控制进程
            process = subprocess.Popen(
                [doxygen_exe, doxyfile_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
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
                Logger.error(f"[{dir_name}] Doxygen执行超时（50分钟），已强制终止进程")
                return {
                    'name': dir_name,
                    'path': directory_info['path'],
                    'success': False,
                    'error': '执行超时（50分钟）',
                    'duration': 3000
                }
            
            # 检查doxygen进程是否正常结束
            duration = end_time - start_time
            if result.returncode == 0:
                # 验证是否真的生成了输出文件
                if self.verify_doxygen_output(directory_info):
                    return {
                        'name': dir_name,
                        'path': directory_info['path'],
                        'success': True,
                        'duration': duration
                    }
                else:
                    Logger.error(f"[{dir_name}] Doxygen执行完成但输出文件不完整，耗时: {duration:.2f}秒")
                    return {
                        'name': dir_name,
                        'path': directory_info['path'],
                        'success': False,
                        'error': '输出文件不完整',
                        'duration': duration
                    }
            else:
                # 执行失败
                Logger.error(f"[{dir_name}] Doxygen执行失败，返回码: {result.returncode}，耗时: {duration:.2f}秒")
                if result.stderr.strip():
                    error_msg = safe_str(result.stderr.strip())
                    Logger.error(f"[{dir_name}] 错误信息: {error_msg}")
                return {
                    'name': dir_name,
                    'path': directory_info['path'],
                    'success': False,
                    'error': safe_str(result.stderr),
                    'duration': duration
                }
                
        except Exception as e:
            error_msg = safe_str(str(e))
            Logger.error(f"[{dir_name}] Doxygen执行异常: {error_msg}")
            return {
                'name': dir_name,
                'path': directory_info['path'],
                'success': False,
                'error': error_msg,
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
                    
                    
                    if not result['success'] and 'error' in result:
                        Logger.error(f"[{result['name']}] 执行失败: {result['error']}")
                    
                except Exception as e:
                    Logger.error(f"[{dir_info['name']}] 处理任务结果时出错: {e}")
                    # 添加错误结果
                    results.append({
                        'name': dir_info['name'],
                        'path': dir_info['path'],
                        'success': False,
                        'error': f'结果处理错误: {str(e)}',
                        'duration': 0
                    })
                    completed_count += 1
        
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
            dir_name = directory_info['name']
            doxyfile_path = directory_info['doxyfile_path']
            
            # 读取Doxyfile获取输出目录
            output_dir = self.parse_doxyfile_output_directory(doxyfile_path)
            
            if not output_dir:
                Logger.error(f"[{dir_name}] 无法从Doxyfile获取输出目录路径: {doxyfile_path}")
                return False
            
            # 检查输出目录是否存在
            if not os.path.exists(output_dir):
                Logger.error(f"[{dir_name}] 输出目录不存在: {output_dir}")
                return False
            
            # 检查是否生成了关键的HTML文件
            html_dir = os.path.join(output_dir, "html")
            if not os.path.exists(html_dir):
                Logger.error(f"[{dir_name}] HTML目录不存在: {html_dir}")
                return False
            
            # 检查关键文件
            key_files = ["index.html", "files.html"]
            missing_files = []
            
            for key_file in key_files:
                file_path = os.path.join(html_dir, key_file)
                if not os.path.exists(file_path):
                    missing_files.append(key_file)
            
            if missing_files:
                missing_files_str = ', '.join(missing_files)
                Logger.error(f"[{dir_name}] 缺少关键文件: {missing_files_str} (在目录: {html_dir})")
                return False
            
            return True
            
        except Exception as e:
            Logger.error(f"[{directory_info.get('name', 'unknown')}] 验证输出文件时出错: {e}")
            return False
    
    def check_hhc_ul_balance(self, hhc_file_path: str) -> bool:
        """
        检查HHC文件中<UL>和</UL>标签是否平衡
        
        参数：
        - hhc_file_path: HHC文件路径
        
        返回：
        - bool: 标签是否平衡
        """
        try:
            if not os.path.exists(hhc_file_path):
                Logger.warning(f"HHC文件不存在: {hhc_file_path}")
                return False
            
            with open(hhc_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 统计<UL>和</UL>标签数量
            ul_open_count = content.count('<UL>')
            ul_close_count = content.count('</UL>')
            
            return ul_open_count == ul_close_count
            
        except Exception as e:
            Logger.error(f"检查HHC文件标签平衡时出错: {e}")
            return False
    
    def find_hhc_files(self, doxyfile_dirs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        查找所有输出目录中的HHC文件
        
        参数：
        - doxyfile_dirs: Doxyfile目录信息列表
        
        返回：
        - list: 包含HHC文件信息的字典列表
        """
        hhc_files = []
        
        for directory_info in doxyfile_dirs:
            try:
                # 读取Doxyfile获取输出目录
                doxyfile_path = directory_info['doxyfile_path']
                output_dir = self.parse_doxyfile_output_directory(doxyfile_path)
                
                if not output_dir or not os.path.exists(output_dir):
                    continue
                
                # 查找index.hhc文件（在html子目录下）
                hhc_file_path = os.path.join(output_dir, "html", "index.hhc")
                if os.path.exists(hhc_file_path):
                    hhc_files.append({
                        'name': directory_info['name'],
                        'path': directory_info['path'],
                        'doxyfile_path': doxyfile_path,
                        'hhc_file_path': hhc_file_path,
                        'output_dir': output_dir
                    })
                else:
                    Logger.warning(f"未找到HHC文件: {directory_info['name']} -> {hhc_file_path}")
                    
            except Exception as e:
                Logger.error(f"查找HHC文件时出错 {directory_info['name']}: {e}")
                continue
        
        return hhc_files
    
    def validate_all_hhc_files(self, hhc_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证所有HHC文件的标签平衡
        
        参数：
        - hhc_files: HHC文件信息列表
        
        返回：
        - list: 验证失败的HHC文件列表
        """
        failed_files = []
        
        for hhc_info in hhc_files:
            hhc_file_path = hhc_info['hhc_file_path']
            dir_name = hhc_info['name']
            
            if self.check_hhc_ul_balance(hhc_file_path):
                pass  # 标签平衡，无需记录
            else:
                Logger.warning(f"❌ HHC文件标签不平衡: {dir_name}")
                failed_files.append(hhc_info)
        
        return failed_files
    
    def retry_failed_directories(self, failed_dirs: List[Dict[str, Any]], max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        重试失败的目录，最多重试指定次数
        
        参数：
        - failed_dirs: 失败的目录信息列表
        - max_retries: 最大重试次数
        
        返回：
        - list: 重试结果列表
        """
        if not failed_dirs:
            return []
        
        retry_results = []
        current_failed = failed_dirs.copy()
        
        for retry_round in range(1, max_retries + 1):
            if not current_failed:
                break
                
            Logger.warning(f"开始第 {retry_round} 轮重试，处理 {len(current_failed)} 个失败目录")
            
            # 重新执行doxygen命令
            round_results = self.execute_doxygen_parallel(current_failed)
            
            # 重新验证HHC文件
            round_hhc_files = self.find_hhc_files(current_failed)
            still_failed = self.validate_all_hhc_files(round_hhc_files)
            
            # 记录重试结果
            for result in round_results:
                result['retry_round'] = retry_round
                result['hhc_balanced'] = result['name'] not in [f['name'] for f in still_failed]
                retry_results.append(result)
            
            # 更新当前失败的目录列表
            current_failed = still_failed
            
            if not current_failed:
                Logger.warning(f"第 {retry_round} 轮重试完成，所有目录处理成功")
                break
            else:
                Logger.warning(f"第 {retry_round} 轮重试后仍有 {len(current_failed)} 个目录失败")
        
        if current_failed:
            Logger.error(f"经过 {max_retries} 轮重试后，仍有 {len(current_failed)} 个目录失败")
        
        return retry_results
    
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
        
        # 统计重试信息
        retry_count = sum(1 for r in results if r.get('retry_round', 0) > 0)
        hhc_balanced_count = sum(1 for r in results if r.get('hhc_balanced', True))
        
        # 按重试轮次分组统计
        retry_stats = {}
        for result in results:
            retry_round = result.get('retry_round', 0)
            if retry_round not in retry_stats:
                retry_stats[retry_round] = {'total': 0, 'success': 0, 'failed': 0}
            retry_stats[retry_round]['total'] += 1
            if result['success']:
                retry_stats[retry_round]['success'] += 1
            else:
                retry_stats[retry_round]['failed'] += 1
        
        # 添加重试统计信息
        summary['retry_count'] = retry_count
        summary['hhc_balanced_count'] = hhc_balanced_count
        summary['hhc_validation_passed'] = hhc_balanced_count == len(results)
        summary['retry_stats'] = retry_stats
        summary['total_duration'] = total_duration
        
        # 只记录错误和警告，不记录info日志
        
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
            
            # 第一步：并行执行doxygen命令
            start_time = time.time()
            results = self.execute_doxygen_parallel(doxyfile_dirs)
            end_time = time.time()
            
            # 第二步：验证HHC文件标签平衡
            
            # 查找所有HHC文件
            hhc_files = self.find_hhc_files(doxyfile_dirs)
            
            if not hhc_files:
                Logger.warning("未找到任何HHC文件，跳过标签平衡验证")
                # 生成执行报告
                summary = self.generate_execution_report(results)
                return summary['failed_count'] == 0
            
            # 验证HHC文件标签平衡
            failed_hhc_files = self.validate_all_hhc_files(hhc_files)
            
            # 第三步：重试失败的目录
            retry_results = []
            if failed_hhc_files:
                retry_results = self.retry_failed_directories(failed_hhc_files, max_retries=3)
                
                # 合并原始结果和重试结果
                all_results = results + retry_results
            else:
                all_results = results
            
            # 生成最终执行报告
            summary = self.generate_execution_report(all_results)
            
            # 添加重试统计信息
            summary['retry_count'] = len(retry_results)
            summary['hhc_validation_passed'] = len(failed_hhc_files) == 0
            
            return summary['failed_count'] == 0 and summary['hhc_validation_passed']
            
        except Exception as e:
            Logger.error(f"Doxygen文档生成失败: {e}")
            return False

@timing_decorator
def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python docs_gen_doxygen.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        # 解析芯片配置JSON
        from common_utils import ConfigManager
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建生成器并执行
        generator = DoxygenGenerator(input_folder, output_folder, chip_config)
        
        if not generator.run():
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
