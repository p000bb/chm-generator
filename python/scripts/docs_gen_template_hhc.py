#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_gen_template_hhc.py - HHC模板文件生成脚本
功能：
1. 扫描output_folder/output/sub下所有包含index.hhc文件的目录
2. 直接读取index.hhc文件内容
3. 截取<UL>到</UL>之间的内容
4. 替换Local参数值
5. 在output_folder/template目录下创建对应的文本文件
6. 检测output_folder/docs目录下的空目录（第一层）
7. 为空目录生成对应的模板文件和HTML文件
8. 特殊处理Hardware_Evaluation_Board目录（兼容两种拼写，统一生成正确拼写的模板文件，对中文内容进行翻译而非删除）
9. 自动清理包含中文的行（删除包含中文字符的整行）

主要功能：
1. 在output_folder/output/sub目录下查找所有index.hhc文件
2. 提取HHC内容并生成模板文件到output_folder/template目录
3. 支持多项目处理
4. 自动检测空目录并生成相应的模板和HTML文件
5. 智能处理Hardware_Evaluation_Board目录（兼容两种拼写，统一生成正确拼写的模板文件，中文内容翻译为英文）
6. 智能清理中文内容，确保生成的模板文件不包含中文OBJECT块
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
    JsonUtils,
    HashUtils,
    PathUtils,
    TextProcessor
)


class HHCContentExtractor(BaseGenerator):
    """
    HHC内容提取器类
    
    主要职责：
    - 在output_folder/output/sub目录下查找所有index.hhc文件
    - 提取HHC内容并生成模板文件到output_folder/template目录
    - 支持多项目处理
    - 检测output_folder/docs目录下的空目录（第一层）
    - 为空目录生成对应的模板文件和HTML文件
    - 智能处理Hardware_Evaluation_Board目录（兼容两种拼写，统一生成正确拼写的模板文件，中文内容翻译为英文）
    - 自动清理包含中文的行，确保模板文件质量
    """
    
    def __init__(self, input_folder, output_folder, chip_config=None):
        """初始化HHC内容提取器"""
        super().__init__(input_folder, output_folder, chip_config or {})
        
        # 加载base.json配置
        self.base_config = self.load_base_config()
        
        Logger.info("HHC内容提取器初始化完成")
    
    def get_value_replace_rules(self):
        """获取value值替换规则（用于param标签的value属性）"""
        return {
            '&': '_',
            # 可以在这里添加更多替换规则
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
            Logger.info("开始对内容应用value值替换规则...")
            
            # 匹配param标签的value属性的正则表达式
            pattern = r'(<param\s+name="[^"]*"\s+value=")([^"]*)(")'
            
            def replace_func(match):
                prefix = match.group(1)  # <param name="xxx" value="
                original_value = match.group(2)  # 原始value值
                suffix = match.group(3)  # ">
                
                # 应用替换规则
                new_value = self.apply_value_replace_rules(original_value)
                
                # 如果值发生了变化，输出日志
                if new_value != original_value:
                    Logger.info(f"替换value值: '{original_value}' -> '{new_value}'")
                
                return prefix + new_value + suffix
            
            # 执行替换
            replaced_content = re.sub(pattern, replace_func, content)
            
            Logger.info("value值替换规则应用完成")
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
        """查找docs目录下的空目录（第一层）"""
        empty_dirs = []
        docs_dir = self.output_folder / "docs"
        
        if not docs_dir.exists():
            Logger.info(f"docs目录不存在: {docs_dir}")
            return empty_dirs
        
        Logger.info(f"检查docs目录下的空目录: {docs_dir}")
        
        # 检查第一层子目录
        for item in docs_dir.iterdir():
            if item.is_dir():
                dir_name = item.name
                if self.is_directory_empty(item):
                    empty_dirs.append(dir_name)
                    Logger.info(f"发现空目录: {dir_name}")
        
        Logger.info(f"共发现 {len(empty_dirs)} 个空目录")
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
            return ""
    
    def save_empty_directory_files(self, empty_dirs: list):
        """为空目录生成模板文件和HTML文件"""
        for dir_name in empty_dirs:
            Logger.info(f"为空目录 {dir_name} 生成文件...")
            
            # 1. 生成模板文件
            template_content = self.generate_empty_directory_template(dir_name)
            template_filename = f"{dir_name}.txt"
            self.save_template_file(template_filename, template_content)
            
            # 2. 生成HTML文件
            html_content = self.generate_empty_directory_html(dir_name)
            if html_content:
                self.save_empty_directory_html(dir_name, html_content)
    
    def save_empty_directory_html(self, dir_name: str, html_content: str):
        """保存空目录的HTML文件到output/extra目录"""
        try:
            extra_dir = self.ensure_output_dir("output", "extra")
            
            html_file = extra_dir / f"{dir_name}.html"
            FileUtils.write_file(html_file, html_content)
            
            Logger.info(f"已保存HTML文件: {html_file}")
            
        except Exception as e:
            Logger.error(f"保存HTML文件 {dir_name}.html 时出错: {e}")
    
    def generate_hardware_evaluation_board_template(self, subdirs: list, dir_name: str = "5-Hardware_Evaluation_Board") -> str:
        """为Hardware_Evaluation_Board目录生成模板文件内容（非空目录）"""
        if not subdirs:
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
        docs_dir = self.output_folder / "docs" / dir_name
        
        if not docs_dir.exists():
            Logger.info(f"目录不存在: {docs_dir}")
            return
        
        Logger.info(f"检查目录: {docs_dir}")
        
        # 统一使用正确拼写的模板文件名，无论原始目录名是什么拼写
        normalized_template_filename = "5-Hardware_Evaluation_Board.txt"
        
        # 检查目录是否为空
        if self.is_directory_empty(docs_dir):
            Logger.info(f"目录 {dir_name} 为空，使用空目录生成逻辑")
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
            Logger.info(f"目录 {dir_name} 非空，使用非空目录生成逻辑")
            # 获取子目录列表
            subdirs = []
            for item in docs_dir.iterdir():
                if item.is_dir():
                    subdirs.append(item.name)
            
            if subdirs:
                Logger.info(f"发现 {len(subdirs)} 个子目录: {', '.join(subdirs)}")
                # 使用非空目录生成逻辑，但使用统一的模板文件名
                template_content = self.generate_hardware_evaluation_board_template(subdirs, "5-Hardware_Evaluation_Board")
                # 对于Hardware_Evaluation_Board目录，使用翻译而不是删除中文
                is_hardware_eval = "Hardware_Evaluation_Board" in dir_name or "Hardware_Evaulation_Board" in dir_name
                self.save_template_file(normalized_template_filename, template_content, is_hardware_eval)
            else:
                Logger.info(f"目录 {dir_name} 中没有子目录")
    
    def process_hardware_evaluation_board(self):
        """处理5-Hardware_Evaluation_Board目录（兼容两种拼写）"""
        # 先处理错误拼写版本（向后兼容）
        dir_name_old = "5-Hardware_Evaulation_Board"
        self.process_hardware_evaluation_board_directory(dir_name_old)
        
        # 再处理正确拼写版本
        dir_name_correct = "5-Hardware_Evaluation_Board"
        self.process_hardware_evaluation_board_directory(dir_name_correct)
    
    def find_hhc_files(self) -> list:
        """在output_folder/output/sub目录下查找所有index.hhc文件"""
        hhc_files = []
        
        # output/sub目录
        sub_dir = self.output_folder / "output" / "sub"
        
        if not sub_dir.exists():
            Logger.info(f"output/sub目录不存在: {sub_dir}")
            return hhc_files
        
        Logger.info(f"在output/sub目录下查找index.hhc文件: {sub_dir}")
        
        for root, dirs, files in os.walk(sub_dir):
            for file in files:
                if file == 'index.hhc':
                    full_path = Path(root) / file
                    hhc_files.append(full_path)
                    Logger.info(f"找到index.hhc: {full_path}")
        
        Logger.info(f"共找到 {len(hhc_files)} 个index.hhc文件")
        return hhc_files
    
    def read_hhc_file(self, hhc_path: Path) -> str:
        """直接读取index.hhc文件内容"""
        try:
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
        """替换Local参数中的路径，支持hash路径映射"""
        # 获取相对路径（从sub开始）
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
                Logger.info(f"检测到hash路径: {relative_path} -> {original_path}")
                # 使用原始路径进行替换
                relative_path_str = str(original_path).replace('/', '\\')
            else:
                # 使用当前路径
                relative_path_str = str(relative_path).replace('/', '\\')
            
            Logger.info(f"使用相对路径: {relative_path_str}")
            
            # 替换所有Local参数的值
            pattern = r'<param name="Local" value="([^"]*)"'
            
            def replace_func(match):
                original_value = match.group(1)
                # 如果原始值不是以相对路径开头的，则替换
                if not original_value.startswith(relative_path_str):
                    return f'<param name="Local" value="{relative_path_str}\\{original_value}"'
                return match.group(0)
            
            replaced_content = re.sub(pattern, replace_func, content)
            return replaced_content
            
        except Exception as e:
            Logger.error(f"替换路径时出错: {e}")
            return content
    
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
            
            Logger.info(f"找到hash文件名 {base_filename} 对应的原始名称: {original_name}")
            
            # 应用文件名替换规则，生成替换后的文件名
            replaced_original_name = self.apply_value_replace_rules(original_name)
            Logger.info(f"原始名称应用替换规则后: {original_name} -> {replaced_original_name}")
            
            # 检查output/extra目录下是否存在对应的.html文件
            extra_dir = self.output_folder / "output" / "extra"
            
            # 优先尝试替换后的文件名
            html_file = extra_dir / f"{replaced_original_name}.html"
            if html_file.exists():
                Logger.info(f"找到替换后文件名的HTML文件: {html_file}")
                final_filename = replaced_original_name
            else:
                # 如果替换后的文件名不存在，尝试原始文件名
                html_file = extra_dir / f"{original_name}.html"
                if html_file.exists():
                    Logger.info(f"找到原始文件名的HTML文件: {html_file}")
                    final_filename = original_name
                else:
                    Logger.info(f"未找到对应的HTML文件，尝试原始文件名: {original_name}")
                    Logger.info(f"也未找到替换后文件名: {replaced_original_name}")
                    return ul_content
            
            Logger.info(f"最终使用的HTML文件名: {final_filename}")
            
            # 检查UL内容中是否已经包含Examples_Overview
            if "Examples_OverView" in ul_content:
                Logger.info("UL内容中已包含Examples_Overview，跳过插入")
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
                Logger.info("成功在UL内容中插入Examples_Overview")
                return enhanced_content
            else:
                Logger.warning("未找到<UL>标签，无法插入Examples_Overview")
                return ul_content
                
        except Exception as e:
            Logger.error(f"插入Examples_Overview时出错: {e}")
            return ul_content
    
    def contains_chinese(self, text: str) -> bool:
        """检查文本是否包含中文字符"""
        return TextProcessor.is_chinese_text(text)
    
    def translate_chinese_content(self, content: str) -> str:
        """翻译中文内容为英文（针对Hardware_Evaluation_Board目录）"""
        try:
            Logger.info("开始翻译中文内容...")
            
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
                '调试': 'Debug',
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
                    Logger.info(f"替换标点符号: '{chinese_punct}' -> '{english_punct}'")
            
            # 再替换中文词汇
            for chinese_word, english_word in translation_map.items():
                if chinese_word in translated_content:
                    translated_content = translated_content.replace(chinese_word, english_word)
                    Logger.info(f"翻译词汇: '{chinese_word}' -> '{english_word}'")
            
            # 检查是否还有未翻译的中文字符
            remaining_chinese = re.findall(r'[\u4e00-\u9fff]+', translated_content)
            if remaining_chinese:
                Logger.warning(f"仍有未翻译的中文字符: {remaining_chinese}")
                # 对于未翻译的中文，可以尝试简单的音译或保留原文
                for chinese_text in remaining_chinese:
                    # 简单的音译处理（可以根据需要扩展）
                    pinyin_approximation = f"[{chinese_text}]"  # 用方括号标记未翻译内容
                    translated_content = translated_content.replace(chinese_text, pinyin_approximation)
                    Logger.info(f"标记未翻译内容: '{chinese_text}' -> '{pinyin_approximation}'")
            
            Logger.info("中文内容翻译完成")
            return translated_content
            
        except Exception as e:
            Logger.error(f"翻译中文内容时出错: {e}")
            return content
    
    def clean_chinese_content(self, content: str) -> str:
        """清理包含中文的行"""
        try:
            Logger.info("开始清理包含中文的行...")
            
            # 按行处理内容
            lines = content.split('\n')
            cleaned_lines = []
            removed_count = 0
            
            for line_num, line in enumerate(lines, 1):
                # 检查整行是否包含中文字符
                if self.contains_chinese(line):
                    Logger.info(f"第{line_num}行包含中文内容，将删除这一行: '{line.strip()}'")
                    removed_count += 1
                    continue  # 跳过这一行，不添加到cleaned_lines
                
                # 保留这一行
                cleaned_lines.append(line)
            
            if removed_count == 0:
                Logger.info("未发现包含中文的行")
                return content
            
            Logger.info(f"清理完成，共删除 {removed_count} 行包含中文的行")
            
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
                Logger.info(f"保存Hardware_Evaluation_Board模板文件，进行中文翻译: {filename}")
                
                translated_content = self.translate_chinese_content(content)
                
                # 保存翻译后的内容
                FileUtils.write_file(template_file, translated_content)
                Logger.info(f"已保存翻译后的模板文件: {template_file}")
                
                # 检查翻译效果
                remaining_chinese = re.findall(r'[\u4e00-\u9fff]+', translated_content)
                if remaining_chinese:
                    Logger.info(f"翻译后仍有中文字符: {remaining_chinese}")
                else:
                    Logger.info("翻译完成，已无中文字符")
            else:
                # 其他目录：清理包含中文的行
                Logger.info(f"保存模板文件前进行中文内容清理: {filename}")
                
                cleaned_content = self.clean_chinese_content(content)
                
                # 保存清理后的内容
                FileUtils.write_file(template_file, cleaned_content)
                Logger.info(f"已保存清理后的模板文件: {template_file}")
                
                # 再次检查保存的文件是否还包含中文
                if self.contains_chinese(cleaned_content):
                    Logger.warning("保存后的文件仍然包含中文内容！")
                else:
                    Logger.info("保存后的文件已成功清理所有中文内容")
        except Exception as e:
            Logger.error(f"保存文件 {template_file} 时出错: {e}")
    
    def process_hhc_file(self, hhc_path: Path):
        """处理单个HHC文件"""
        Logger.info(f"处理HHC文件: {hhc_path}")
        
        # 1. 读取HHC内容
        hhc_content = self.read_hhc_file(hhc_path)
        if not hhc_content:
            return
        
        # 2. 提取UL内容
        ul_content = self.extract_ul_content(hhc_content)
        if not ul_content:
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
            Logger.info("template目录不存在")
            return {"balanced": [], "unbalanced": []}
        
        Logger.info("检查template文件UL标签平衡性...")
        
        # 查找所有.txt文件
        txt_files = list(template_dir.glob("*.txt"))
        if not txt_files:
            Logger.info("template目录下没有找到.txt文件")
            return {"balanced": [], "unbalanced": []}
        
        Logger.info(f"找到 {len(txt_files)} 个.txt文件，开始检查UL标签平衡性...")
        
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
                Logger.info(f"{status_icon} {txt_file.name}: <UL>={ul_open_count}, </UL>={ul_close_count}")
                
            except Exception as e:
                Logger.error(f"检查文件 {txt_file.name} 时出错: {e}")
                unbalanced_files.append({
                    'filename': txt_file.name,
                    'ul_open': 0,
                    'ul_close': 0,
                    'error': str(e)
                })
        
        # 显示检查总结
        Logger.info(f"UL标签平衡性检查完成:")
        Logger.info(f"总文件数: {len(txt_files)}")
        Logger.info(f"平衡文件: {len(balanced_files)}")
        Logger.info(f"不平衡文件: {len(unbalanced_files)}")
        
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
    
    def run(self):
        """运行HHC内容提取"""
        Logger.info("开始处理HHC内容提取")
        
        # 1. 查找output/sub目录下的所有index.hhc文件
        hhc_files = self.find_hhc_files()
        
        if not hhc_files:
            Logger.info("output/sub目录下没有找到index.hhc文件")
        else:
            Logger.info(f"找到 {len(hhc_files)} 个index.hhc文件")
            # 处理每个HHC文件
            for hhc_file in hhc_files:
                self.process_hhc_file(hhc_file)
        
        # 2. 查找并处理docs目录下的空目录
        empty_dirs = self.find_empty_docs_directories()
        if empty_dirs:
            Logger.info(f"发现 {len(empty_dirs)} 个空目录，开始生成模板文件...")
            self.save_empty_directory_files(empty_dirs)
        else:
            Logger.info("docs目录下没有发现空目录")
        
        # 3. 特殊处理Hardware_Evaluation_Board目录（兼容两种拼写）
        Logger.info("开始处理Hardware_Evaluation_Board目录...")
        self.process_hardware_evaluation_board()
        
        # 4. 检查UL标签平衡性
        Logger.info("开始检查UL标签平衡性...")
        self.check_ul_balance_in_template_files()
        
        Logger.success("HHC内容提取完成！")


def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder = ArgumentParser.parse_standard_args(
            2, "python docs_gen_template_hhc.py <input_folder> <output_folder>"
        )
        
        # 创建提取器并执行
        extractor = HHCContentExtractor(input_folder, output_folder)
        
        if extractor.run():
            Logger.success("HHC模板文件生成完成！")
        else:
            Logger.error("HHC模板文件生成失败！")
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
