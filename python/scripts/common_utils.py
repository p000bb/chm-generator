#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common_utils.py - 通用工具函数库
包含各个脚本共用的工具函数和类
"""

import os
import sys
import json
import time
from pathlib import Path

# 自动设置Python路径（仅在第一次导入时执行）
if not hasattr(sys, '_common_utils_path_set'):
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    sys._common_utils_path_set = True
import hashlib
import shutil
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from functools import wraps


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, project_root: Path = None):
        """初始化配置管理器"""
        if project_root is None:
            # 默认从当前脚本位置计算项目根目录
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = project_root
    
    def load_chip_config(self, chip_config_json: str) -> Dict[str, Any]:
        """解析芯片配置JSON"""
        try:
            return json.loads(chip_config_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"芯片配置JSON解析失败: {e}")
    
    def load_base_config(self) -> Dict[str, Any]:
        """加载基础配置文件"""
        try:
            config_path = self.project_root / "config" / "base.json"
            if not config_path.exists():
                raise FileNotFoundError(f"基础配置文件不存在: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"加载基础配置失败: {e}")
    
    def get_project_info(self, chip_config: Dict[str, Any]) -> Dict[str, str]:
        """从芯片配置中提取项目信息"""
        return {
            'chip_name': chip_config.get('chipName', ''),
            'chip_version': chip_config.get('chipVersion', ''),
            'project_name': chip_config.get('chipName', ''),
            'project_version': chip_config.get('chipVersion', ''),
            'cn_url': chip_config.get('Cn_WebUrl', ''),
            'en_url': chip_config.get('En_WebUrl', ''),
            'zip_url': chip_config.get('Zip_Url', '')
        }


class PathUtils:
    """路径工具类"""
    
    @staticmethod
    def get_project_root() -> Path:
        """获取项目根目录"""
        return Path(__file__).parent.parent.parent
    
    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> Path:
        """确保目录存在"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_relative_path(base_path: Union[str, Path], target_path: Union[str, Path]) -> str:
        """获取相对路径"""
        base_path = Path(base_path)
        target_path = Path(target_path)
        return str(target_path.relative_to(base_path))
    
    @staticmethod
    def normalize_path(path: Union[str, Path]) -> str:
        """标准化路径，统一使用正斜杠"""
        return str(Path(path)).replace('\\', '/')


class FileUtils:
    """文件工具类"""
    
    @staticmethod
    def read_file_with_encoding(file_path: Union[str, Path], 
                              encodings: List[str] = None) -> str:
        """智能读取文件，尝试多种编码"""
        if encodings is None:
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 
                        'latin1', 'iso-8859-1', 'cp1252']
        
        file_path = Path(file_path)
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
        
        raise Exception(f"无法读取文件 {file_path}，尝试了所有编码格式")
    
    @staticmethod
    def write_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """写入文件"""
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            Logger.error(f"写入文件失败 {file_path}: {e}")
            return False
    
    @staticmethod
    def copy_file_with_processing(src: Union[str, Path], dst: Union[str, Path], 
                                processor: callable = None) -> bool:
        """复制文件，可选择处理内容"""
        try:
            src = Path(src)
            dst = Path(dst)
            
            # 确保目标目录存在
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            if processor:
                # 读取源文件内容
                content = FileUtils.read_file_with_encoding(src)
                # 处理内容
                processed_content = processor(content)
                # 写入目标文件
                FileUtils.write_file(dst, processed_content)
            else:
                # 直接复制
                shutil.copy2(src, dst)
            
            return True
        except Exception as e:
            Logger.error(f"复制文件失败 {src} -> {dst}: {e}")
            return False


class HashUtils:
    """哈希工具类"""
    
    @staticmethod
    def generate_md5_hash(text: str, length: int = 8) -> str:
        """生成MD5哈希值"""
        hash_obj = hashlib.md5(text.encode('utf-8'))
        return hash_obj.hexdigest()[:length]
    
    @staticmethod
    def generate_8char_hash(text: str) -> str:
        """生成8位哈希值（兼容性方法）"""
        return HashUtils.generate_md5_hash(text, 8)
    
    @staticmethod
    def reverse_hash_lookup(hash_value: str, mapping_data: List[Dict[str, Any]]) -> Optional[str]:
        """
        根据hash值反向查找原始路径
        
        参数：
        - hash_value: 要查找的hash值
        - mapping_data: 映射数据列表
        
        返回：
        - str: 原始路径，如果未找到则返回None
        """
        for mapping in mapping_data:
            if mapping.get("hash_path") == hash_value:
                return mapping.get("original_path")
        return None
    
    @staticmethod
    def load_path_mapping(project_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        加载路径映射文件
        
        参数：
        - project_path: 项目路径
        
        返回：
        - List[Dict]: 映射数据列表
        """
        try:
            project_path = Path(project_path)
            mapping_file = project_path / "json" / "path_mapping.json"
            
            if not mapping_file.exists():
                return []
            
            data = JsonUtils.load_json(mapping_file)
            return data.get("mappings", [])
        except Exception as e:
            Logger.error(f"加载路径映射失败: {e}")
            return []
    
    @staticmethod
    def find_original_path_by_hash(hash_value: str, project_path: Union[str, Path]) -> Optional[str]:
        """
        根据hash值查找原始路径（便捷方法）
        
        参数：
        - hash_value: 要查找的hash值
        - project_path: 项目路径
        
        返回：
        - str: 原始路径，如果未找到则返回None
        """
        mapping_data = HashUtils.load_path_mapping(project_path)
        return HashUtils.reverse_hash_lookup(hash_value, mapping_data)


class TemplateProcessor:
    """模板处理器"""
    
    def __init__(self, replacements: Dict[str, str] = None):
        """初始化模板处理器"""
        self.replacements = replacements or {}
    
    def add_replacement(self, placeholder: str, value: str):
        """添加替换规则"""
        self.replacements[placeholder] = value
    
    def process_template(self, content: str) -> str:
        """处理模板内容，替换占位符"""
        result = content
        for placeholder, value in self.replacements.items():
            result = result.replace(placeholder, value)
        return result
    
    def process_file(self, src_file: Union[str, Path], dst_file: Union[str, Path]) -> bool:
        """处理模板文件"""
        try:
            content = FileUtils.read_file_with_encoding(src_file)
            processed_content = self.process_template(content)
            return FileUtils.write_file(dst_file, processed_content)
        except Exception as e:
            Logger.error(f"处理模板文件失败 {src_file}: {e}")
            return False


class ArgumentParser:
    """命令行参数解析器"""
    
    @staticmethod
    def parse_standard_args(expected_count: int = 3, 
                          usage_message: str = None) -> tuple:
        """解析标准参数格式"""
        if len(sys.argv) < expected_count + 1:
            if usage_message:
                Logger.error(f"参数不足，期望{expected_count}个参数")
                Logger.error(f"用法: {usage_message}")
            else:
                Logger.error(f"参数不足，期望{expected_count}个参数")
            sys.exit(1)
        
        return tuple(sys.argv[1:expected_count + 1])


class Logger:
    """日志工具类"""
    
    @staticmethod
    def info(message: str):
        """信息日志"""
        print(f"[INFO] {message}")
    
    @staticmethod
    def error(message: str):
        """错误日志"""
        print(f"[ERROR] {message}")
    
    @staticmethod
    def success(message: str):
        """成功日志"""
        print(f"[SUCCESS] {message}")
    
    @staticmethod
    def warning(message: str):
        """警告日志"""
        print(f"[WARNING] {message}")


class DirectoryScanner:
    """目录扫描器"""
    
    @staticmethod
    def find_files_by_extension(directory: Union[str, Path], 
                               extensions: List[str], 
                               recursive: bool = True) -> List[Path]:
        """根据扩展名查找文件"""
        directory = Path(directory)
        files = []
        
        if not directory.exists():
            return files
        
        if recursive:
            for ext in extensions:
                files.extend(directory.rglob(f"*.{ext}"))
        else:
            for ext in extensions:
                files.extend(directory.glob(f"*.{ext}"))
        
        return files
    
    @staticmethod
    def find_files_by_name(directory: Union[str, Path], 
                          filenames: List[str], 
                          recursive: bool = True) -> List[Path]:
        """根据文件名查找文件"""
        directory = Path(directory)
        files = []
        
        if not directory.exists():
            return files
        
        if recursive:
            for filename in filenames:
                files.extend(directory.rglob(filename))
        else:
            for filename in filenames:
                files.extend(directory.glob(filename))
        
        return files


class TextProcessor:
    """文本处理器"""
    
    @staticmethod
    def is_chinese_text(text: str) -> bool:
        """判断文本是否包含中文"""
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        return bool(chinese_pattern.search(text))
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本，去除多余空白"""
        # 清理空行
        text = re.sub(r'\n\s*\n', '\n', text)
        # 清理行首行尾空格
        text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)
        return text
    
    @staticmethod
    def extract_chinese_content(content: str) -> List[str]:
        """提取中文内容"""
        chinese_matches = []
        lines = content.split('\n')
        
        for line in lines:
            if '<' in line and '>' in line:
                # HTML行，检查标签外的中文文本
                html_parts = re.split(r'(<[^>]+>)', line)
                for part in html_parts:
                    if not (part.startswith('<') and part.endswith('>')) and TextProcessor.is_chinese_text(part):
                        chinese_matches.append(part.strip())
            else:
                # 纯文本行
                if TextProcessor.is_chinese_text(line):
                    chinese_matches.append(line.strip())
        
        return [match for match in chinese_matches if match.strip()]


class VersionUtils:
    """版本工具类"""
    
    @staticmethod
    def extract_version_from_name(name: str) -> str:
        """从项目名称中提取版本号"""
        version_patterns = [
            r'[Vv]?(\d+\.\d+\.\d+)',  # V1.0.0, v1.0.0, 1.0.0
            r'[Vv]?(\d+\.\d+)',       # V1.0, v1.0, 1.0
            r'[Vv]?(\d+)',            # V1, v1, 1
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, name)
            if match:
                return match.group(1)
        
        return "1.0.0"  # 默认版本


class JsonUtils:
    """JSON工具类"""
    
    @staticmethod
    def save_json(data: Any, file_path: Union[str, Path], 
                  ensure_ascii: bool = False, indent: int = 2) -> bool:
        """保存JSON文件"""
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
            return True
        except Exception as e:
            Logger.error(f"保存JSON文件失败 {file_path}: {e}")
            return False
    
    @staticmethod
    def load_json(file_path: Union[str, Path]) -> Any:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"加载JSON文件失败 {file_path}: {e}")


class BaseGenerator:
    """基础生成器类"""
    
    def __init__(self, input_folder: str, output_folder: str, chip_config: Dict[str, Any]):
        """初始化基础生成器"""
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.chip_config = chip_config
        self.project_root = PathUtils.get_project_root()
        
        # 初始化配置管理器
        self.config_manager = ConfigManager(self.project_root)
        
        # 获取项目信息
        self.project_info = self.config_manager.get_project_info(chip_config)
    
    def ensure_output_dir(self, *path_parts) -> Path:
        """确保输出目录存在"""
        output_dir = self.output_folder
        for part in path_parts:
            output_dir = output_dir / part
        return PathUtils.ensure_dir(output_dir)
    
    def get_template_path(self, template_name: str) -> Path:
        """获取模板文件路径"""
        return self.project_root / "template" / template_name
    
    def load_base_config(self) -> Dict[str, Any]:
        """加载基础配置"""
        return self.config_manager.load_base_config()


# 便捷函数
def create_base_generator(input_folder: str, output_folder: str, chip_config_json: str) -> BaseGenerator:
    """创建基础生成器实例"""
    config_manager = ConfigManager()
    chip_config = config_manager.load_chip_config(chip_config_json)
    return BaseGenerator(input_folder, output_folder, chip_config)


def parse_standard_arguments(expected_count: int = 3, usage_message: str = None) -> tuple:
    """解析标准命令行参数"""
    return ArgumentParser.parse_standard_args(expected_count, usage_message)


def log_info(message: str):
    """记录信息日志"""
    Logger.info(message)


def log_error(message: str):
    """记录错误日志"""
    Logger.error(message)


def log_success(message: str):
    """记录成功日志"""
    Logger.success(message)


def log_warning(message: str):
    """记录警告日志"""
    Logger.warning(message)


def timing_decorator(func):
    """时间统计装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 获取脚本名称
        script_name = Path(func.__code__.co_filename).stem
        Logger.info(f"{script_name}开始执行")
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            Logger.success(f"{script_name}执行完成")
            Logger.info(f"脚本执行完成，总耗时: {elapsed_time:.2f} 秒")
            return result
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            Logger.error(f"脚本执行失败，耗时: {elapsed_time:.2f} 秒，错误: {e}")
            raise
    return wrapper


def format_duration(seconds: float) -> str:
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds:.2f} 秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes} 分 {remaining_seconds:.2f} 秒"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours} 小时 {remaining_minutes} 分 {remaining_seconds:.2f} 秒"
