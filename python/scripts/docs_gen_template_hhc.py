#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_gen_template_hhc.py - HHC模板文件生成脚本

功能特性：
==========

HHC文件扫描：
- 递归扫描output_folder/output/sub目录
- 查找所有名为index.hhc的文件
- 前置条件检查：只处理目录下存在files.html文件的index.hhc
- 支持多种编码格式读取（utf-8, gbk, gb2312, gb18030, latin1）

内容提取与处理：
- 提取<UL>到</UL>之间的内容
- 替换Local参数中的路径，支持hash路径映射
- 应用值替换规则（如将&符号替换为下划线）
- 在UL内容中自动插入Examples_Overview

中文内容处理：
- 提供两种处理模式：
  * 清理模式：删除包含中文字符的整行（默认）
  * 翻译模式：将中文内容翻译为英文（仅限Hardware_Evaluation_Board目录）
- 支持标点符号和词汇翻译
- 未翻译的中文内容用方括号标记

特殊目录处理：
- 兼容Hardware_Evaluation_Board的两种拼写
- 统一生成正确拼写的模板文件
- 对Hardware_Evaluation_Board目录使用翻译而非删除中文内容

空目录处理：
- 检测项目docs目录下的第一层空目录
- 为空目录生成对应的模板文件和HTML文件
- 使用empty_directory.html.template作为基础模板

模板文件生成：
- 基于从sub开始的第三层目录名生成文件名
- 保存到项目特定的template目录
- 支持hash路径映射和文件名替换

质量检查：
- 检查所有模板文件中<UL>和</UL>标签的平衡性
- 统计平衡和不平衡的文件数量

技术特点：
- 支持多项目并行处理
- 智能路径映射和替换
- 中英文内容智能处理
- 自动质量检查和验证
- 详细的日志输出和错误处理
- 跨平台兼容性（Windows路径处理）

输出产物：
- 项目template目录下的.txt模板文件
- 空目录对应的HTML文件

使用场景：
这个脚本是CHM文档生成流程中的关键步骤，用于将Doxygen生成的HTML帮助文档转换为CHM编译所需的模板文件，确保生成的文件质量和格式正确，为后续的CHM文档生成做准备。
"""

import os
import re
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from common_utils import (
    BaseGenerator,
    Logger,
    ArgumentParser,
    FileUtils,
    HashUtils,
    PathUtils,
    TextProcessor,
    timing_decorator
)


class HHCContentExtractor(BaseGenerator):
    """
    HHC内容提取器类
    
    主要职责：
    - 在output_folder/output/sub目录下查找所有index.hhc文件
    - 前置条件检查：只处理目录下存在files.html文件的index.hhc
    - 提取HHC内容并生成模板文件到output_folder/template目录
    - 支持多项目处理
    - 检测input_folder目录下的空目录（第一层）
    - 为空目录生成对应的模板文件和HTML文件
    - 智能处理Hardware_Evaluation_Board目录（兼容两种拼写，统一生成正确拼写的模板文件，中文内容翻译为英文）
    - 自动清理包含中文的行，确保模板文件质量
    """
    
    def __init__(self, input_folder, output_folder, chip_config=None):
        """初始化HHC内容提取器"""
        super().__init__(input_folder, output_folder, chip_config or {})
        
        # 加载base.json配置
        self.base_config = self.load_base_config()
    
    def get_template_path(self, template_filename: str) -> Path:
        """获取模板文件路径"""
        try:
            # 首先在项目根目录的template目录中查找
            template_dir = Path(__file__).parent.parent.parent / "template"
            template_path = template_dir / template_filename
            
            if template_path.exists():
                return template_path
            
            # 如果没找到，尝试在output_folder的template目录中查找
            output_template_dir = self.output_folder / "template"
            output_template_path = output_template_dir / template_filename
            
            if output_template_path.exists():
                return output_template_path
            
            Logger.warning(f"未找到模板文件: {template_filename}")
            return template_path  # 返回第一个路径，即使不存在
            
        except Exception as e:
            Logger.error(f"获取模板文件路径时出错: {e}")
            return Path(template_filename)
    
    def ensure_output_dir(self, *path_parts) -> Path:
        """确保输出目录存在"""
        try:
            # 构建目录路径
            if len(path_parts) == 1:
                # 如果只有一个参数，直接使用
                target_dir = self.output_folder / path_parts[0]
            else:
                # 如果有多个参数，依次拼接
                target_dir = self.output_folder
                for part in path_parts:
                    target_dir = target_dir / part
            
            # 创建目录（如果不存在）
            target_dir.mkdir(parents=True, exist_ok=True)
            
            return target_dir
            
        except Exception as e:
            Logger.error(f"确保输出目录时出错: {e}")
            import traceback
            Logger.error(f"详细错误信息: {traceback.format_exc()}")
            return self.output_folder
        
    
    def get_value_replace_rules(self):
        """获取value值替换规则（用于param标签的value属性）"""
        return {
            # 当前不需要任何替换规则，保持原始内容
        }
    
    def apply_value_replace_rules(self, value):
        """应用value值替换规则"""
        replace_rules = self.get_value_replace_rules()
        result = value
        for old_char, new_char in replace_rules.items():
            result = result.replace(old_char, new_char)
        return result
    
    def apply_value_replacements_to_content(self, content):
        """对内容中的所有param标签的value属性应用替换规则"""
        try:
            # 匹配param标签的value属性的正则表达式
            pattern = r'(<param\s+name="[^"]*"\s+value=")([^"]*)(")'
            
            def replace_func(match):
                prefix = match.group(1)  # <param name="xxx" value="
                original_value = match.group(2)  # 原始value值
                suffix = match.group(3)  # ">
                
                # 应用替换规则
                new_value = self.apply_value_replace_rules(original_value)
                
                return prefix + new_value + suffix
            
            # 执行替换
            replaced_content = re.sub(pattern, replace_func, content)
            return replaced_content
            
        except Exception as e:
            Logger.error(f"应用value值替换规则时出错: {e}")
            return content
    
    def is_directory_empty(self, dir_path: Path) -> bool:
        """检查目录是否为空（只检查第一层）"""
        try:
            if not dir_path.exists() or not dir_path.is_dir():
                return True
            
            # 只检查第一层，不递归
            items = list(dir_path.iterdir())
            return len(items) == 0
        except Exception as e:
            Logger.warning(f"检查目录 {dir_path} 时出错: {e}")
            return True
    
    def find_empty_docs_directories(self) -> list:
        """查找input_folder目录下的空目录（第一层）"""
        empty_dirs = []
        docs_dir = self.input_folder  # input_folder 本身就是 docs 目录
        
        if not docs_dir.exists():
            return empty_dirs
        
        # 检查第一层子目录
        for item in docs_dir.iterdir():
            if item.is_dir():
                dir_name = item.name
                if self.is_directory_empty(item):
                    empty_dirs.append(dir_name)
        
        return empty_dirs
    
    def generate_empty_directory_template(self, dir_name: str) -> str:
        """为空目录生成模板文件内容"""
        template_content = f"""<UL>
    <LI><OBJECT type="text/sitemap">
        <param name="Name" value="readme">
        <param name="Local" value="extra/{dir_name}.html">
    </OBJECT></LI>
</UL>"""
        return template_content
    
    def generate_empty_directory_html(self, dir_name: str) -> str:
        """为空目录生成HTML文件内容"""
        try:
            # 读取HTML模板
            template_path = self.get_template_path("empty_directory.html.template")
            
            if not template_path.exists():
                Logger.warning(f"HTML模板文件不存在: {template_path}")
                return ""
            
            content = FileUtils.read_file_with_encoding(template_path)
            
            # 获取项目名称（不包含版本号）
            project_short_name = self.project_info.get('project_name', 'Project').split('_')[0]
            
            # 从base.json获取标题信息
            cn_title = dir_name
            en_title = dir_name
            
            if dir_name in self.base_config.get("MarkDown_Info", {}):
                markdown_info = self.base_config["MarkDown_Info"][dir_name]
                cn_title = markdown_info.get("cn", {}).get("title", dir_name)
                en_title = markdown_info.get("en", {}).get("title", dir_name)
            
            # 替换占位符
            html_content = content.replace("{Empty_directory_title}", dir_name)
            html_content = html_content.replace("{Project_Name}", project_short_name)
            html_content = html_content.replace("{CN_title}", cn_title)
            html_content = html_content.replace("{EN_title}", en_title)
            
            return html_content
            
        except Exception as e:
            Logger.error(f"生成HTML文件内容时出错: {e}")
            import traceback
            Logger.error(f"详细错误信息: {traceback.format_exc()}")
            return ""
    
    def save_empty_directory_files(self, empty_dirs: list):
        """为空目录生成模板文件和HTML文件"""
        for dir_name in empty_dirs:
            # 1. 生成模板文件
            template_content = self.generate_empty_directory_template(dir_name)
            template_filename = f"{dir_name}.txt"
            self.save_template_file(template_filename, template_content)
            
            # 2. 生成HTML文件
            html_content = self.generate_empty_directory_html(dir_name)
            if html_content:
                self.save_empty_directory_html(dir_name, html_content)
            else:
                Logger.warning(f"HTML内容生成失败，跳过保存: {dir_name}")
    
    def save_empty_directory_html(self, dir_name: str, html_content: str):
        """保存空目录的HTML文件到output/extra目录"""
        try:
            extra_dir = self.ensure_output_dir("output", "extra")
            html_file = extra_dir / f"{dir_name}.html"
            FileUtils.write_file(html_file, html_content)
            
        except Exception as e:
            Logger.error(f"保存HTML文件 {dir_name}.html 时出错: {e}")
            import traceback
            Logger.error(f"详细错误信息: {traceback.format_exc()}")
    
    def generate_hardware_evaluation_board_template(self, subdirs: list, dir_name: str = "5-Hardware_Evaluation_Board") -> str:
        """为Hardware_Evaluation_Board目录生成模板文件内容（非空目录）"""
        if not subdirs:
            Logger.warning("子目录列表为空，返回空字符串")
            return ""
        
        # 使用统一的HTML文件名
        html_file = "hardware_evaluation_board.html"
        
        li_items = []
        for subdir in subdirs:
            li_item = f"""      <LI><OBJECT type="text/sitemap">
          <param name="Name" value="{subdir}">
          <param name="Local" value="main/en/html/{html_file}">
        </OBJECT></LI>"""
            li_items.append(li_item)
        
        template_content = f"""<UL>
{chr(10).join(li_items)}
    </UL>"""
        return template_content
    
    def process_hardware_evaluation_board_directory(self, dir_name: str):
        """通用的Hardware_Evaluation_Board目录处理方法"""
        docs_dir = self.input_folder / dir_name  # input_folder 本身就是 docs 目录
        
        if not docs_dir.exists():
            return
        
        # 统一使用正确拼写的模板文件名，无论原始目录名是什么拼写
        normalized_template_filename = "5-Hardware_Evaluation_Board.txt"
        
        # 检查目录是否为空
        is_empty = self.is_directory_empty(docs_dir)
        
        if is_empty:
            # 使用空目录生成逻辑，但使用统一的模板文件名
            template_content = self.generate_empty_directory_template("5-Hardware_Evaluation_Board")
            # 对于Hardware_Evaluation_Board目录，使用翻译而不是删除中文
            is_hardware_eval = "Hardware_Evaluation_Board" in dir_name or "Hardware_Evaulation_Board" in dir_name
            self.save_template_file(normalized_template_filename, template_content, is_hardware_eval)
            
            # 生成HTML文件（使用原始目录名作为参数）
            html_content = self.generate_empty_directory_html(dir_name)
            if html_content:
                self.save_empty_directory_html(dir_name, html_content)
        else:
            # 获取子目录列表
            subdirs = []
            for item in docs_dir.iterdir():
                if item.is_dir():
                    subdirs.append(item.name)
            
            if subdirs:
                # 使用非空目录生成逻辑，但使用统一的模板文件名
                template_content = self.generate_hardware_evaluation_board_template(subdirs, "5-Hardware_Evaluation_Board")
                # 对于Hardware_Evaluation_Board目录，使用翻译而不是删除中文
                is_hardware_eval = "Hardware_Evaluation_Board" in dir_name or "Hardware_Evaulation_Board" in dir_name
                self.save_template_file(normalized_template_filename, template_content, is_hardware_eval)
            else:
                Logger.warning("未找到任何子目录")
    
    def process_hardware_evaluation_board(self):
        """处理5-Hardware_Evaluation_Board目录（兼容两种拼写）"""
        # 先处理错误拼写版本（向后兼容）
        dir_name_old = "5-Hardware_Evaulation_Board"
        self.process_hardware_evaluation_board_directory(dir_name_old)
        
        # 再处理正确拼写版本
        dir_name_correct = "5-Hardware_Evaluation_Board"
        self.process_hardware_evaluation_board_directory(dir_name_correct)
    
    def find_hhc_files(self) -> list:
        """在output_folder/output/sub目录下递归查找所有index.hhc文件"""
        hhc_files = []
        
        # output/sub目录
        sub_dir = self.output_folder / "output" / "sub"
        
        if not sub_dir.exists():
            Logger.warning(f"目录不存在: {sub_dir}")
            return hhc_files
        
        # 使用os.walk递归扫描所有子目录
        for root, dirs, files in os.walk(sub_dir):
            for file in files:
                if file == 'index.hhc':
                    full_path = Path(root) / file
                    hhc_files.append(full_path)
        return hhc_files
    
    def process_hhc_files_parallel(self, hhc_files: list, max_workers: int = 4):
        """并行处理HHC文件（可选功能，当前版本使用串行处理）"""
        
        # 当前版本使用串行处理，确保稳定性和错误处理
        # 未来可以添加多线程/多进程支持
        processed_count = 0
        failed_count = 0
        skipped_count = 0  # 因为缺少files.html而跳过的文件数量
        
        for i, hhc_file in enumerate(hhc_files, 1):
            try:
                # 检查前置条件：是否存在files.html文件
                if not self.check_files_html_exists(hhc_file):
                    skipped_count += 1
                    continue
                
                self.process_hhc_file(hhc_file)
                processed_count += 1
            except Exception as e:
                Logger.error(f"处理文件 {hhc_file} 时出错: {e}")
                failed_count += 1
        
        return processed_count, failed_count, skipped_count
    
    def read_hhc_file(self, hhc_path: Path) -> str:
        """读取index.hhc文件内容，支持多种编码格式"""
        try:
            # 定义支持的编码格式，按优先级排序
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'latin1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(hhc_path, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                    return content
                except (UnicodeDecodeError, LookupError):
                    continue
            
            # 如果所有编码都失败，使用FileUtils的智能读取
            Logger.warning(f"所有编码格式都失败，尝试智能读取: {hhc_path}")
            return FileUtils.read_file_with_encoding(hhc_path)
            
        except Exception as e:
            Logger.error(f"读取 {hhc_path} 时出错: {e}")
            return ""
    
    def extract_ul_content(self, hhc_content: str) -> str:
        """提取<UL>到</UL>之间的内容"""
        # 查找第一个<UL>和最后一个</UL>
        start_pattern = r'<UL>'
        end_pattern = r'</UL>'
        
        start_match = re.search(start_pattern, hhc_content)
        if not start_match:
            Logger.warning("未找到<UL>标签")
            return ""
        
        # 从后往前查找最后一个</UL>
        content_before_end = hhc_content[start_match.start():]
        end_match = None
        
        # 找到最后一个</UL>的位置
        for match in re.finditer(end_pattern, content_before_end):
            end_match = match
        
        if not end_match:
            Logger.warning("未找到</UL>标签")
            return ""
        
        # 提取内容（包含<UL>和</UL>）
        extracted_content = content_before_end[:end_match.end()]
        return extracted_content
    
    def replace_local_paths(self, content: str, hhc_path: Path) -> str:
        """替换Local参数中的路径，支持hash路径映射和跨平台路径处理"""
        try:
            # 找到hhc文件所在的目录
            hhc_dir = hhc_path.parent
            
            # 获取从sub开始的相对路径
            relative_path = None
            for part in hhc_dir.parts:
                if part == 'sub':
                    sub_index = hhc_dir.parts.index('sub')
                    relative_path = Path(*hhc_dir.parts[sub_index:])
                    break
            
            if not relative_path:
                Logger.warning(f"无法确定 {hhc_path} 的相对路径")
                return content
            
            # 获取hash路径映射数据
            hash_mapping_data = HashUtils.load_path_mapping(self.output_folder)
            
            # 检查这个路径是否是hash路径，如果是，需要反向查找原始路径
            original_path = HashUtils.reverse_hash_lookup(str(relative_path), hash_mapping_data)
            if original_path:
                # 使用原始路径进行替换
                relative_path_str = self._normalize_path_for_platform(str(original_path))
            else:
                # 使用当前路径
                relative_path_str = self._normalize_path_for_platform(str(relative_path))
            
            # 替换所有Local参数的值
            pattern = r'<param name="Local" value="([^"]*)"'
            
            def replace_func(match):
                original_value = match.group(1)
                # 标准化原始值中的路径分隔符
                normalized_original = self._normalize_path_for_platform(original_value)
                
                # 如果原始值不是以相对路径开头的，则替换
                if not normalized_original.startswith(relative_path_str):
                    return f'<param name="Local" value="{relative_path_str}\\{normalized_original}"'
                return match.group(0)
            
            replaced_content = re.sub(pattern, replace_func, content)
            return replaced_content
            
        except Exception as e:
            Logger.error(f"替换路径时出错: {e}")
            return content
    
    def _normalize_path_for_platform(self, path_str: str) -> str:
        """标准化路径分隔符，确保跨平台兼容性"""
        # 统一使用反斜杠，因为这是Windows CHM文件的标准
        return path_str.replace('/', '\\')
    
    def get_template_filename(self, hhc_path: Path) -> str:
        """获取模板文件名（从sub开始的第三层目录名）"""
        try:
            # 获取从sub开始的相对路径
            relative_path = None
            for part in hhc_path.parent.parts:
                if part == 'sub':
                    sub_index = hhc_path.parent.parts.index('sub')
                    relative_path = hhc_path.parent.parts[sub_index:]
                    break
            
            if not relative_path or len(relative_path) < 3:
                Logger.warning(f"无法确定 {hhc_path} 的第三层目录名")
                return "unknown"
            
            # 第三层目录名（从sub开始数，sub是第0层）
            third_level = relative_path[2]
            return f"{third_level}.txt"
            
        except Exception as e:
            Logger.error(f"获取模板文件名时出错: {e}")
            return "unknown.txt"
    
    def ensure_template_dir(self) -> Path:
        """确保template目录存在"""
        template_dir = self.output_folder / "template"
        return PathUtils.ensure_dir(template_dir)
    
    def insert_examples_overview(self, ul_content: str, template_filename: str) -> str:
        """在UL内容中插入Examples_Overview，支持hash路径映射和文件名替换规则"""
        try:
            # 获取不带扩展名的文件名
            base_filename = template_filename.replace('.txt', '')
            
            # 获取hash路径映射数据
            hash_mapping_data = HashUtils.load_path_mapping(self.output_folder)
            
            # 通过hash文件名查找对应的原始名称
            original_name = None
            for mapping in hash_mapping_data:
                if mapping.get("hash_path") == base_filename:
                    original_name = mapping.get("original_path")
                    break
            
            if not original_name:
                Logger.warning(f"未找到hash文件名 {base_filename} 对应的原始名称")
                return ul_content
            
            # 应用文件名替换规则，生成替换后的文件名
            replaced_original_name = self.apply_value_replace_rules(original_name)
            
            # 检查多个可能的HTML文件位置
            html_file_paths = self._find_examples_html_file(original_name, replaced_original_name)
            
            if not html_file_paths:
                return ul_content
            
            # 使用找到的第一个HTML文件
            final_filename = html_file_paths[0]
            
            # 检查UL内容中是否已经包含Examples_Overview
            if "Examples_OverView" in ul_content:
                return ul_content
            
            # 构建要插入的内容
            examples_overview_content = f"""<LI><OBJECT type="text/sitemap">
<param name="Name" value="Examples_OverView">
<param name="Local" value="extra/{final_filename}.html">
</OBJECT></LI>"""
            
            # 在第一个<UL>标签后插入内容
            # 查找第一个<UL>标签的位置
            ul_pattern = r'(<UL>)'
            match = re.search(ul_pattern, ul_content)
            
            if match:
                # 在<UL>标签后插入内容
                insert_pos = match.end()
                enhanced_content = (
                    ul_content[:insert_pos] + 
                    "\n" + 
                    examples_overview_content + 
                    ul_content[insert_pos:]
                )
                return enhanced_content
            else:
                Logger.warning("未找到<UL>标签，无法插入Examples_Overview")
                return ul_content
                
        except Exception as e:
            Logger.error(f"插入Examples_Overview时出错: {e}")
            return ul_content
    
    def _find_examples_html_file(self, original_name: str, replaced_original_name: str) -> list:
        """查找Examples HTML文件，支持多个位置和文件名变体"""
        possible_paths = []
        
        # 可能的目录位置
        search_dirs = [
            self.output_folder / "output" / "extra",
            self.output_folder / "extra",
            self.output_folder / "output",
        ]
        
        # 可能的文件名变体
        name_variants = [
            original_name,
            replaced_original_name,
            original_name.split('/')[-1],  # 只取最后一部分
            replaced_original_name.split('/')[-1],  # 只取最后一部分
        ]
        
        # 去重
        name_variants = list(set(name_variants))
        
        # 搜索所有可能的组合
        for search_dir in search_dirs:
            if search_dir.exists():
                for name_variant in name_variants:
                    # 尝试不同的文件名格式
                    html_files = [
                        search_dir / f"{name_variant}.html",
                        search_dir / f"{name_variant.replace(' ', '_')}.html",
                        search_dir / f"{name_variant.replace(' ', '%20')}.html",
                    ]
                    
                    for html_file in html_files:
                        if html_file.exists():
                            possible_paths.append(html_file.stem)  # 只返回文件名（不含扩展名）
        
        return possible_paths
    
    def contains_chinese(self, text: str) -> bool:
        """检查文本是否包含中文字符"""
        return TextProcessor.is_chinese_text(text)
    
    def translate_chinese_content(self, content: str) -> str:
        """翻译中文内容为英文（针对Hardware_Evaluation_Board目录）"""
        try:
            # 中文标点符号到英文的映射
            punctuation_map = {
                '（': '(',
                '）': ')',
                '，': ',',
                '。': '.',
                '：': ':',
                '；': ';',
                '！': '!',
                '？': '?',
                '"': '"',
                '"': '"',
                ''': "'",
                ''': "'",
                '【': '[',
                '】': ']',
                '《': '<',
                '》': '>',
                '、': ',',
                '～': '~',
                '—': '-',
                '－': '-',
                '·': '·',
            }
            
            # 常见中文词汇到英文的映射
            translation_map = {
                '硬件评估板': 'Hardware Evaluation Board',
                '评估板': 'Evaluation Board',
                '开发板': 'Development Board',
                '开发套件': 'Development Kit',
                '用户手册': 'User Manual',
                '使用指南': 'User Guide',
                '快速入门': 'Quick Start',
                '入门指南': 'Getting Started',
                '参考设计': 'Reference Design',
                '应用笔记': 'Application Note',
                '技术文档': 'Technical Documentation',
                '数据手册': 'Datasheet',
                '产品简介': 'Product Introduction',
                '勘误手册': 'Errata Sheet',
                '软件开发包': 'Software Development Kit',
                '固件': 'Firmware',
                '软件': 'Software',
                '硬件': 'Hardware',
                '接口': 'Interface',
                '连接器': 'Connector',
                '引脚': 'Pin',
                '电源': 'Power Supply',
                '时钟': 'Clock',
                '复位': 'Reset',
                '调试': 'info',
                '编程': 'Programming',
                '下载': 'Download',
                '烧录': 'Programming',
                '配置': 'Configuration',
                '设置': 'Settings',
                '参数': 'Parameters',
                '功能': 'Function',
                '特性': 'Features',
                '规格': 'Specifications',
                '说明': 'Description',
                '介绍': 'Introduction',
                '概述': 'Overview',
                '详细': 'Detailed',
                '基本': 'Basic',
                '高级': 'Advanced',
                '示例': 'Example',
                '演示': 'Demo',
                '测试': 'Test',
                '验证': 'Verification',
                '支持': 'Support',
                '兼容': 'Compatible',
                '版本': 'Version',
                '更新': 'Update',
                '升级': 'Upgrade',
                '安装': 'Installation',
                '卸载': 'Uninstallation',
                '启动': 'Start',
                '停止': 'Stop',
                '运行': 'Run',
                '执行': 'Execute',
                '操作': 'Operation',
                '步骤': 'Steps',
                '流程': 'Process',
                '方法': 'Method',
                '方式': 'Way',
                '工具': 'Tool',
                '设备': 'Device',
                '系统': 'System',
                '平台': 'Platform',
                '环境': 'Environment',
                '项目': 'Project',
                '工程': 'Project',
                '文件': 'File',
                '目录': 'Directory',
                '文件夹': 'Folder',
                '路径': 'Path',
                '地址': 'Address',
                '位置': 'Location',
                '名称': 'Name',
                '标题': 'Title',
                '内容': 'Content',
                '信息': 'Information',
                '数据': 'Data',
                '结果': 'Result',
                '输出': 'Output',
                '输入': 'Input',
                '错误': 'Error',
                '警告': 'Warning',
                '提示': 'Tip',
                '注意': 'Note',
                '重要': 'Important',
                '关键': 'Key',
                '主要': 'Main',
                '次要': 'Secondary',
                '可选': 'Optional',
                '必需': 'Required',
                '必要': 'Necessary',
                '推荐': 'Recommended',
                '建议': 'Suggested',
                '默认': 'Default',
                '标准': 'Standard',
                '通用': 'General',
                '特殊': 'Special',
                '专用': 'Dedicated',
                '专业': 'Professional',
                '商业': 'Commercial',
                '工业': 'Industrial',
                '消费': 'Consumer',
                '家用': 'Home',
                '办公': 'Office',
                '企业': 'Enterprise',
                '个人': 'Personal',
                '公共': 'Public',
                '私有': 'Private',
                '开放': 'Open',
                '封闭': 'Closed',
                '免费': 'Free',
                '付费': 'Paid',
                '试用': 'Trial',
                '正式': 'Official',
                '测试版': 'Beta',
                '稳定版': 'Stable',
                '最新版': 'Latest',
                '旧版本': 'Old Version',
                '新版本': 'New Version',
            }
            
            # 先替换标点符号
            translated_content = content
            for chinese_punct, english_punct in punctuation_map.items():
                if chinese_punct in translated_content:
                    translated_content = translated_content.replace(chinese_punct, english_punct)
            
            # 再替换中文词汇
            for chinese_word, english_word in translation_map.items():
                if chinese_word in translated_content:
                    translated_content = translated_content.replace(chinese_word, english_word)
            
            # 检查是否还有未翻译的中文字符
            remaining_chinese = re.findall(r'[\u4e00-\u9fff]+', translated_content)
            if remaining_chinese:
                # 对于未翻译的中文，可以尝试简单的音译或保留原文
                for chinese_text in remaining_chinese:
                    # 简单的音译处理（可以根据需要扩展）
                    pinyin_approximation = f"[{chinese_text}]"  # 用方括号标记未翻译内容
                    translated_content = translated_content.replace(chinese_text, pinyin_approximation)
            
            return translated_content
            
        except Exception as e:
            Logger.error(f"翻译中文内容时出错: {e}")
            return content
    
    def clean_chinese_content(self, content: str) -> str:
        """清理包含中文的行"""
        try:
            # 按行处理内容
            lines = content.split('\n')
            cleaned_lines = []
            removed_count = 0
            
            for line_num, line in enumerate(lines, 1):
                # 检查整行是否包含中文字符
                if self.contains_chinese(line):
                    removed_count += 1
                    continue  # 跳过这一行，不添加到cleaned_lines
                
                # 保留这一行
                cleaned_lines.append(line)
            
            if removed_count == 0:
                return content
            
            
            # 重新组合内容
            cleaned_content = '\n'.join(cleaned_lines)
            return cleaned_content
            
        except Exception as e:
            Logger.error(f"清理中文内容时出错: {e}")
            return content
    
    def save_template_file(self, filename: str, content: str, is_hardware_evaluation_board: bool = False):
        """保存模板文件到template目录"""
        template_dir = self.ensure_template_dir()
        template_file = template_dir / filename
        
        try:
            if is_hardware_evaluation_board:
                # Hardware_Evaluation_Board目录：翻译中文内容而不是删除
                translated_content = self.translate_chinese_content(content)
                
                # 保存翻译后的内容
                FileUtils.write_file(template_file, translated_content)
            else:
                # 其他目录：清理包含中文的行
                cleaned_content = self.clean_chinese_content(content)
                
                # 保存清理后的内容
                FileUtils.write_file(template_file, cleaned_content)
                
                # 再次检查保存的文件是否还包含中文
                if self.contains_chinese(cleaned_content):
                    Logger.warning("保存后的文件仍然包含中文内容！")
            
            # 验证文件是否成功保存
            if not template_file.exists():
                Logger.error(f"文件保存失败，文件不存在: {template_file}")
                
        except Exception as e:
            Logger.error(f"保存文件 {template_file} 时出错: {e}")
            import traceback
            Logger.error(f"详细错误信息: {traceback.format_exc()}")
    
    def check_files_html_exists(self, hhc_path: Path) -> bool:
        """检查index.hhc文件所在目录下是否存在files.html文件"""
        try:
            hhc_dir = hhc_path.parent
            files_html_path = hhc_dir / "files.html"
            return files_html_path.exists()
        except Exception as e:
            Logger.error(f"检查files.html文件时出错: {e}")
            return False
    
    def process_hhc_file(self, hhc_path: Path):
        """处理单个HHC文件"""
        # 0. 前置条件检查：检查目录下是否存在files.html文件
        if not self.check_files_html_exists(hhc_path):
            return
        
        # 1. 读取HHC内容
        hhc_content = self.read_hhc_file(hhc_path)
        if not hhc_content:
            Logger.warning(f"无法读取HHC文件内容: {hhc_path}")
            return
        
        # 2. 提取UL内容
        ul_content = self.extract_ul_content(hhc_content)
        if not ul_content:
            Logger.warning(f"无法从HHC文件中提取UL内容: {hhc_path}")
            return
        
        # 3. 应用value值替换规则（在路径替换之前进行）
        value_replaced_content = self.apply_value_replacements_to_content(ul_content)
        
        # 4. 替换路径
        replaced_content = self.replace_local_paths(value_replaced_content, hhc_path)
        
        # 5. 获取模板文件名
        template_filename = self.get_template_filename(hhc_path)
        
        # 6. 在UL内容中插入Examples_Overview
        enhanced_content = self.insert_examples_overview(replaced_content, template_filename)
        
        # 7. 保存模板文件到template目录
        self.save_template_file(template_filename, enhanced_content)
    
    def check_ul_balance_in_template_files(self):
        """检查template目录下所有.txt文件中<UL>和</UL>标签的平衡性"""
        template_dir = self.output_folder / "template"
        if not template_dir.exists():
            return {"balanced": [], "unbalanced": []}
        
        # 查找所有.txt文件
        txt_files = list(template_dir.glob("*.txt"))
        if not txt_files:
            return {"balanced": [], "unbalanced": []}
        
        balanced_files = []
        unbalanced_files = []
        
        for txt_file in txt_files:
            try:
                # 读取文件内容
                content = FileUtils.read_file_with_encoding(txt_file)
                
                # 统计<UL>和</UL>标签数量
                ul_open_count = content.count('<UL>')
                ul_close_count = content.count('</UL>')
                
                # 检查是否平衡
                is_balanced = ul_open_count == ul_close_count
                
                if is_balanced:
                    balanced_files.append({
                        'filename': txt_file.name,
                        'ul_open': ul_open_count,
                        'ul_close': ul_close_count
                    })
                else:
                    unbalanced_files.append({
                        'filename': txt_file.name,
                        'ul_open': ul_open_count,
                        'ul_close': ul_close_count,
                        'difference': abs(ul_open_count - ul_close_count)
                    })
                
                # 显示检查结果
                status_icon = "✅" if is_balanced else "❌"
                
            except Exception as e:
                Logger.error(f"检查文件 {txt_file.name} 时出错: {e}")
                unbalanced_files.append({
                    'filename': txt_file.name,
                    'ul_open': 0,
                    'ul_close': 0,
                    'error': str(e)
                })
        
        # 显示检查总结
        
        # 如果有不平衡的文件，详细列出
        if unbalanced_files:
            Logger.warning(f"发现 {len(unbalanced_files)} 个UL标签不平衡的文件:")
            for file_info in unbalanced_files:
                if 'error' in file_info:
                    Logger.warning(f"{file_info['filename']}: 检查出错 - {file_info['error']}")
                else:
                    Logger.warning(f"{file_info['filename']}: <UL>={file_info['ul_open']}, </UL>={file_info['ul_close']} (差异: {file_info['difference']})")
        
        return {
            "balanced": balanced_files,
            "unbalanced": unbalanced_files,
            "total_files": len(txt_files)
        }
    
    def show_generated_template_files(self):
        """显示生成的模板文件列表"""
        try:
            template_dir = self.output_folder / "template"
            if not template_dir.exists():
                Logger.warning("template目录不存在")
                return
            
            # 查找所有.txt文件
            txt_files = list(template_dir.glob("*.txt"))
            if not txt_files:
                Logger.warning("template目录下没有找到任何.txt文件")
                return
            
            for txt_file in sorted(txt_files):
                file_size = txt_file.stat().st_size
                    
        except Exception as e:
            Logger.error(f"显示生成的模板文件时出错: {e}")
    
    def run(self):
        """运行HHC内容提取"""
        try:
            # 1. 查找output/sub目录下的所有index.hhc文件
            hhc_files = self.find_hhc_files()
                
            if not hhc_files:
                Logger.warning("未找到任何HHC文件，跳过HHC文件处理")
            else:
                # 2. 处理HHC文件
                processed_count, failed_count, skipped_count = self.process_hhc_files_parallel(hhc_files)
            
            # 3. 查找并处理空目录
            empty_dirs = self.find_empty_docs_directories()
            
            if empty_dirs:
                self.save_empty_directory_files(empty_dirs)
            
            # 4. 特殊处理Hardware_Evaluation_Board目录（兼容两种拼写）
            self.process_hardware_evaluation_board()
            
            # 5. 检查UL标签平衡性
            balance_result = self.check_ul_balance_in_template_files()
            
            # 6. 显示生成的模板文件
            self.show_generated_template_files()
            return True
            
        except Exception as e:
            Logger.error(f"HHC内容提取过程中发生错误: {e}")
            import traceback
            Logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False


@timing_decorator
def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder = ArgumentParser.parse_standard_args(
            2, "python docs_gen_template_hhc.py <input_folder> <output_folder>"
        )
        
        # 验证目录存在性
        if not Path(input_folder).exists():
            Logger.error(f"输入目录不存在: {input_folder}")
            sys.exit(1)
        
        if not Path(output_folder).exists():
            Logger.error(f"输出目录不存在: {output_folder}")
            sys.exit(1)
        
        # 创建提取器并执行
        extractor = HHCContentExtractor(input_folder, output_folder)
        
        if not extractor.run():
            Logger.error("HHC内容提取失败")
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        import traceback
        Logger.error(f"详细错误信息: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
