#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HHC文件生成脚本
扫描output_folder/output/sub目录下的HHC文件，生成index.hhc文件
支持模板文件加载、中文内容翻译、hash路径映射和层级限制处理

主要功能：
1. 加载template文件夹下的所有.txt模板文件
2. 扫描output_folder/output/sub目录结构
3. 生成HHC文件到output_folder/output/index.hhc位置
4. 对生成的HHC内容进行层级限制处理（最大6层）
5. 支持中文内容翻译为英文
6. 自动使用hash路径映射确保路径一致性
7. 应用value值替换规则确保CHM编译要求

技术特点：
- 支持多项目并行处理
- 智能中文内容翻译和专业术语替换
- 自动hash路径映射和长路径处理
- 流式处理大文件，避免内存溢出
- 精确的层级限制和内容裁剪
- 模板文件与默认结构的智能结合
- 详细的日志输出和错误处理

核心算法：
- 使用栈结构分析UL标签的嵌套层级
- 区间标记方式处理超层级内容
- 递归树结构裁剪和内容重建
- 重叠区间合并和内容重组

输出产物：
- output_folder/output/index.hhc文件
- 符合HTML Help Workshop标准的HHC格式
- 支持中文翻译的英文内容
- 限制在6层以内的层级结构

依赖库：
- deep_translator：用于中文到英文翻译
- pathlib：路径处理
- re：正则表达式处理
- json：配置文件读取
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from common_utils import (
    BaseGenerator,
    Logger,
    FileUtils,
    HashUtils,
    JsonUtils,
    ArgumentParser,
    timing_decorator,
    ConfigManager
)

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    Logger.warning("deep_translator未安装，将跳过中文翻译功能")


class HHCGenerator(BaseGenerator):
    """
    HHC文件生成器类
    
    主要职责：
    - 加载template文件夹下的所有.txt模板文件
    - 扫描output_folder/output/sub目录结构
    - 生成HHC文件到output_folder/output/index.hhc位置
    - 支持中文内容翻译为英文
    - 自动使用hash路径映射确保路径一致性
    - 对生成的HHC内容进行层级限制处理（最大6层）
    """
    
    def __init__(self, input_folder: str, output_folder: str, chip_config: Dict[str, Any]):
        """
        初始化HHC生成器
        
        参数：
        - input_folder: 输入文件夹路径
        - output_folder: 输出文件夹路径
        - chip_config: 芯片配置
        """
        super().__init__(input_folder, output_folder, chip_config)
        
        # 设置路径
        self.template_dir = Path(output_folder) / "template"
        self.sub_dir = Path(output_folder) / "output" / "sub"
        self.output_file = Path(output_folder) / "output" / "index.hhc"
        
        # 加载配置
        self.base_config = self.load_base_config()
        self.technical_terms = self.load_technical_terms()
        
        # 初始化翻译器
        if TRANSLATOR_AVAILABLE:
            self.translator = GoogleTranslator(source='zh-CN', target='en')
        else:
            self.translator = None
        
    
    def load_base_config(self) -> Dict:
        """加载base.json配置"""
        try:
            # 从项目根目录加载base.json
            config_path = self.project_root / "config" / "base.json"
            if not config_path.exists():
                Logger.warning(f"base.json文件不存在: {config_path}")
                return {}
            
            return JsonUtils.load_json(str(config_path))
        except Exception as e:
            Logger.error(f"加载base.json失败: {e}")
            return {}
    
    def load_technical_terms(self) -> Dict[str, str]:
        """加载base.json中的Technical_Terms"""
        try:
            technical_terms = self.base_config.get('Technical_Terms', {})
            return technical_terms
        except Exception as e:
            Logger.error(f"加载Technical_Terms失败: {e}")
            return {}
    
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
    
    def apply_value_replacements_to_dynamic_content(self, content):
        """
        对动态生成的HHC内容中的所有param标签的value属性应用替换规则
        
        参数：
        - content: 动态生成的HHC内容
        
        返回：
        - str: 应用替换规则后的内容
        """
        try:
            if not content:
                return content
            
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
            Logger.error(f"对动态内容应用value值替换规则时出错: {e}")
            return content
    
    def is_chinese_text(self, text: str) -> bool:
        """检查文本是否包含中文字符"""
        if not text:
            return False
        
        # 检查是否包含中文字符
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        return bool(chinese_pattern.search(text))
    
    def translate_chinese_content(self, text: str) -> str:
        """
        翻译中文内容为英文，并应用专业术语替换
        
        参数：
        - text: 包含中文的文本
        
        返回：
        - str: 翻译后的英文文本
        """
        try:
            if not text or not self.is_chinese_text(text) or not self.translator:
                return text
            
            # 使用deep_translator翻译
            translated = self.translator.translate(text)
            
            # 应用专业术语替换
            result = self.apply_technical_terms(translated)
            
            # 格式化：单词间用下划线分隔，首字母大写
            formatted = self.format_translated_text(result)
            
            return formatted
            
        except Exception as e:
            Logger.error(f"翻译失败: {e}")
            return text
    
    def apply_technical_terms(self, text: str) -> str:
        """
        应用专业术语替换
        
        参数：
        - text: 翻译后的英文文本
        
        返回：
        - str: 应用术语替换后的文本
        """
        try:
            result = text
            
            # 按术语长度降序排列，优先替换长术语
            sorted_terms = sorted(self.technical_terms.items(), 
                                key=lambda x: len(x[1]), reverse=True)
            
            for chinese_term, english_term in sorted_terms:
                if chinese_term in text:
                    result = result.replace(chinese_term, english_term)
            
            return result
            
        except Exception as e:
            Logger.error(f"应用专业术语失败: {e}")
            return text
    
    def format_translated_text(self, text: str) -> str:
        """
        格式化翻译后的文本：单词间用下划线分隔，首字母大写
        
        参数：
        - text: 翻译后的文本
        
        返回：
        - str: 格式化后的文本
        """
        try:
            if not text:
                return text
            
            # 分割文本为单词
            words = re.split(r'[\s\-_]+', text)
            
            # 过滤空字符串，首字母大写
            formatted_words = []
            for word in words:
                if word.strip():
                    # 首字母大写
                    capitalized = word.strip().capitalize()
                    formatted_words.append(capitalized)
            
            # 用下划线连接
            result = '_'.join(formatted_words)
            
            return result
            
        except Exception as e:
            Logger.error(f"格式化文本失败: {e}")
            return text
    
    def translate_hhc_name_value(self, name_value: str) -> str:
        """
        翻译HHC文件中的Name值
        
        参数：
        - name_value: Name参数的值
        
        返回：
        - str: 翻译后的值
        """
        try:
            if not name_value:
                return name_value
            
            # 如果是PDF文件名，提取文件名部分进行翻译
            if name_value.endswith('.pdf'):
                # 分离文件名和扩展名
                name_part = name_value[:-4]  # 去掉.pdf
                translated_name = self.translate_chinese_content(name_part)
                return f"{translated_name}.pdf"
            else:
                # 直接翻译
                return self.translate_chinese_content(name_value)
                
        except Exception as e:
            Logger.error(f"翻译HHC Name值失败: {e}")
            return name_value
    
    def load_template_files(self) -> Dict[str, str]:
        """加载template文件夹下的所有.txt文件内容，支持hash路径映射"""
        if not self.template_dir.exists():
            Logger.warning(f"template目录不存在: {self.template_dir}")
            return {}
        
        # 加载所有模板文件
        template_contents = {}
        for item in self.template_dir.iterdir():
            if item.is_file() and item.suffix.lower() == '.txt':
                try:
                    content = FileUtils.read_file_with_encoding(str(item))
                    # 使用不带.txt扩展名的文件名作为键
                    template_name = item.stem
                    template_contents[template_name] = content
                except Exception as e:
                    Logger.error(f"读取模板文件 {item.name} 时出错: {e}")
        
        # 创建原始目录名到模板内容的映射
        original_to_template = {}
        
        # 特殊处理：5-Hardware_Evaluation_Board.txt 直接映射到两个可能的目录名
        if '5-Hardware_Evaluation_Board' in template_contents:
            content = template_contents['5-Hardware_Evaluation_Board']
            original_to_template['5-Hardware_Evaluation_Board'] = content
            original_to_template['5-Hardware_Evaulation_Board'] = content
        
        # 获取hash路径映射数据
        hash_mapping = self.get_hash_path_mapping()
        
        # 遍历所有映射关系
        mappings = hash_mapping.get("mappings", [])
        
        for mapping in mappings:
            original_path = mapping.get("original_path")
            hash_path = mapping.get("hash_path")
            
            # 从原始路径中提取目录名（最后一部分）
            if original_path and hash_path:
                original_name = original_path.split('/')[-1] if '/' in original_path else original_path
                
                # 如果hash文件名在模板内容中，建立映射
                if hash_path in template_contents:
                    original_to_template[original_name] = template_contents[hash_path]
                else:
                    Logger.warning(f"未找到hash文件名 {hash_path} 对应的模板文件")
            else:
                Logger.warning(f"映射缺少必要字段")
        
        # 对于没有映射的模板文件，也添加到结果中（保持向后兼容）
        for template_name, content in template_contents.items():
            if template_name not in [m.get("hash_path") for m in hash_mapping.get("mappings", [])]:
                original_to_template[template_name] = content
        
        return original_to_template
    
    def scan_project_docs_structure(self) -> List[Dict]:
        """扫描input_folder目录结构，返回第一层级的目录信息"""
        if not self.input_folder.exists():
            Logger.warning(f"输入目录不存在: {self.input_folder}")
            return []
        
        structure = []
        
        # 遍历第一层级目录
        for item in self.input_folder.iterdir():
            if item.is_dir():
                dir_info = {
                    'name': item.name,
                    'path': item,
                    'items': []  # 存储所有项目（PDF文件和子目录）
                }
                
                # 扫描目录下的所有项目
                for file_item in item.iterdir():
                    if file_item.is_file() and file_item.suffix.lower() == '.pdf':
                        # PDF文件
                        dir_info['items'].append({
                            'type': 'pdf',
                            'name': file_item.stem,
                            'path': file_item
                        })
                    elif file_item.is_dir():
                        # 子目录
                        dir_info['items'].append({
                            'type': 'subdir',
                            'name': file_item.name,
                            'path': file_item
                        })
                
                structure.append(dir_info)
        
        return structure
    
    def generate_hhc_content(self, structure: List[Dict], template_contents: Dict[str, str]) -> str:
        """生成HHC文件内容，使用hash路径映射，支持中文翻译"""
        hhc_content = '''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<HTML>
<HEAD>
<meta name="GENERATOR" content="Microsoft&reg; HTML Help Workshop 4.1">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</HEAD>
<BODY>
<OBJECT type="text/site properties">
<param name="FrameName" value="right">
</OBJECT>
<UL>
<LI><OBJECT type="text/sitemap">
      <param name="Name" value="Overview">
    </OBJECT>
<UL>
<LI><OBJECT type="text/sitemap">
      <param name="Name" value="Overview_en">
      <param name="Local" value="main/en/html/index.html">
    </OBJECT></LI>
  <LI><OBJECT type="text/sitemap">
      <param name="Name" value="Overview_cn">
      <param name="Local" value="main/cn/html/index.html">
    </OBJECT></LI>
   <LI><OBJECT type="text/sitemap">
      <param name="Name" value="Config">
      <param name="Local" value="extra/Config.html">
    </OBJECT></LI>
</UL>
</LI>
'''
        
        # 生成其他模块，数量根据实际input_folder目录结构决定
        for dir_info in structure:
            dir_name = dir_info['name']
            
            # 检查第一层级目录是否有匹配的模板文件
            if dir_name in template_contents:
                # 找到匹配的模板文件，直接使用模板内容
                hhc_content += f'''  
  <LI><OBJECT type="text/sitemap">
      <param name="Name" value="{dir_name}">
    </OBJECT>
    {template_contents[dir_name]}
  </LI>
'''
            else:
                # 没有匹配的模板文件，使用原来的逻辑
                hhc_content += f'''  
  <LI><OBJECT type="text/sitemap">
      <param name="Name" value="{dir_name}">
    </OBJECT>
    <UL>
'''
                
                # 处理目录下的所有项目
                for item in dir_info['items']:
                    if item['type'] == 'pdf':
                        # PDF文件
                        pdf_name = item['name']
                        # 将文件名中的&替换为_
                        safe_pdf_name = pdf_name.replace('&', '_')
                        
                        # 翻译PDF文件名
                        translated_pdf_name = self.translate_hhc_name_value(safe_pdf_name)
                        
                        # 所有PDF都指向统一的HTML页面，使用锚点导航
                        hash_name = self.get_hash_name_for_pdf(pdf_name)
                        html_filename = f"index.html#{hash_name}"
                        
                        hhc_content += f'''      <LI><OBJECT type="text/sitemap">
          <param name="Name" value="{translated_pdf_name}.pdf">
          <param name="Local" value="pdf\\html\\{html_filename}">
        </OBJECT></LI>
'''
                    elif item['type'] == 'subdir':
                        # 子目录
                        subdir_name = item['name']
                        subdir_path = str(item['path'])
                        
                        # 翻译子目录名
                        translated_subdir_name = self.translate_hhc_name_value(subdir_name)
                        
                        # 获取相对路径（从input_folder开始）
                        relative_path = os.path.relpath(subdir_path, str(self.input_folder))
                        
                        # 通过映射表获取hash路径
                        hash_path = self.get_hash_path_for_relative_path(relative_path)
                        
                        # 检查是否有匹配的模板文件
                        if subdir_name in template_contents:
                            # 找到匹配的模板文件，直接使用内容
                            hhc_content += f'''      <LI><OBJECT type="text/sitemap">
          <param name="Name" value="{translated_subdir_name}">
        </OBJECT>{template_contents[subdir_name]}</LI>
'''
                        else:
                            # 没有匹配的模板文件，生成简单的条目
                            # 如果使用hash路径，生成对应的引用
                            if hash_path != relative_path:
                                # 尝试通过hash路径查找模板文件
                                hash_template_name = hash_path.split('/')[-1] if '/' in hash_path else hash_path
                                if hash_template_name in template_contents:
                                    hhc_content += f'''      <LI><OBJECT type="text/sitemap">
          <param name="Name" value="{translated_subdir_name}">
        </OBJECT>{template_contents[hash_template_name]}</LI>
'''
                                else:
                                    Logger.warning(f"通过hash路径也未找到模板文件: {hash_template_name}")
                                    hhc_content += f'''      <LI><OBJECT type="text/sitemap">
          <param name="Name" value="{translated_subdir_name}">
        </OBJECT></LI>
'''
                            else:
                                hhc_content += f'''      <LI><OBJECT type="text/sitemap">
          <param name="Name" value="{translated_subdir_name}">
        </OBJECT></LI>
'''
                
                hhc_content += '''    </UL>
  </LI>
'''
        
        hhc_content += '''</UL>
</BODY>
</HTML>'''
        
        # 对动态生成的HHC内容应用value值替换规则
        hhc_content = self.apply_value_replacements_to_dynamic_content(hhc_content)
        
        # 对生成的HHC内容进行层级限制处理（最大6层）
        limited_content = self.limit_hhc_levels(hhc_content, 6)
        
        return limited_content
    
    def get_hash_path_mapping(self):
        """获取hash路径映射数据"""
        try:
            # path_mapping.json文件在output_folder/json/目录下
            mapping_file = self.output_folder / "json" / "path_mapping.json"
            
            if not mapping_file.exists():
                Logger.warning(f"path_mapping.json文件不存在: {mapping_file}")
                return {"mappings": []}
            
            data = JsonUtils.load_json(mapping_file)
            return data
        except Exception as e:
            Logger.error(f"获取hash路径映射失败: {e}")
            return {"mappings": []}
    
    def get_hash_path_for_relative_path(self, relative_path: str) -> str:
        """根据相对路径获取hash路径"""
        hash_mapping = self.get_hash_path_mapping()
        mappings = hash_mapping.get("mappings", [])
        
        # 查找匹配的映射
        for mapping in mappings:
            if mapping.get("original_path") == relative_path:
                return mapping.get("hash_path", relative_path)
        
        return relative_path
    
    def get_hash_name_for_pdf(self, pdf_name: str) -> str:
        """获取PDF文件的hash名称"""
        try:
            # 从output_folder推断项目路径
            project_path = self.output_folder.parent
            mapping_file = project_path / "json" / "path_mapping.json"
            
            if not mapping_file.exists():
                return HashUtils.generate_8char_hash(pdf_name)
            
            data = JsonUtils.load_json(mapping_file)
            mappings = data.get("mappings", [])
            
            # 查找PDF文件的hash映射
            for mapping in mappings:
                original_path = mapping.get("original_path", "")
                hash_path = mapping.get("hash_path", "")
                
                # 检查是否是PDF文件路径
                if pdf_name in original_path and original_path.endswith('.pdf'):
                    return hash_path
            
            # 如果没找到映射，生成默认hash
            return HashUtils.generate_8char_hash(pdf_name)
        except Exception as e:
            Logger.error(f"获取PDF hash名称失败: {e}")
            return HashUtils.generate_8char_hash(pdf_name)
    
    def limit_hhc_levels(self, content: str, max_level: int) -> str:
        """
        限制HHC文件的层级深度
        
        参数：
        - content: 原始HHC内容
        - max_level: 最大允许的层级数
        
        返回：
        - str: 限制层级后的内容
        """
        try:
            # 使用流式处理，逐行分析，避免内存问题
            result_content = self.stream_process_levels(content, max_level)
            return result_content
            
        except Exception as e:
            Logger.error(f"层级限制处理失败: {e}")
            return content
    
    def stream_process_levels(self, content: str, max_level: int) -> str:
        """
        流式处理层级限制，使用区间标记方式
        
        参数：
        - content: 原始内容
        - max_level: 最大层级
        
        返回：
        - str: 限制层级后的内容
        """
        try:
            # 第一步：找到所有需要删除的UL区间
            skip_ranges = self.find_exceed_level_ranges(content, max_level)
            
            if not skip_ranges:
                return content
            
            # 第二步：基于区间重建内容
            result_content = self.rebuild_content_by_ranges(content, skip_ranges)
            
            return result_content
            
        except Exception as e:
            Logger.error(f"精确层级处理失败: {e}")
            return content
    
    def find_exceed_level_ranges(self, content: str, max_level: int) -> list:
        """
        找到所有超出最大层级的UL区间
        
        参数：
        - content: 原始内容
        - max_level: 最大层级
        
        返回：
        - list: 需要删除的区间列表 [(start, end), ...]
        """
        try:
            skip_ranges = []
            ul_stack = []  # 存储UL开始位置和层级
            current_level = 0
            
            # 使用正则表达式找到所有UL标签
            ul_open_pattern = r'<UL[^>]*>'
            ul_close_pattern = r'</UL>'
            
            # 找到所有UL开始和结束标签
            all_tags = []
            
            for match in re.finditer(ul_open_pattern, content):
                all_tags.append((match.start(), match.end(), 'open'))
            
            for match in re.finditer(ul_close_pattern, content):
                all_tags.append((match.start(), match.end(), 'close'))
            
            # 按位置排序
            all_tags.sort(key=lambda x: x[0])
            
            # 配对UL标签，找到超层级区间
            ul_stack = []
            current_level = 0
            
            for pos, end_pos, tag_type in all_tags:
                if tag_type == 'open':
                    current_level += 1
                    ul_stack.append((pos, current_level))
                    
                else:  # close
                    if ul_stack:
                        ul_start, ul_level = ul_stack.pop()
                        
                        # 如果这个UL区间超过最大层级，记录整个区间
                        if ul_level > max_level:
                            skip_ranges.append((ul_start, end_pos))
                    
                    current_level -= 1
            
            return skip_ranges
            
        except Exception as e:
            Logger.error(f"查找超层级区间失败: {e}")
            return []
    
    def rebuild_content_by_ranges(self, content: str, skip_ranges: list) -> str:
        """
        基于跳过区间重建内容
        
        参数：
        - content: 原始内容
        - skip_ranges: 需要跳过的区间列表
        
        返回：
        - str: 重建后的内容
        """
        try:
            if not skip_ranges:
                return content
            
            # 合并重叠区间
            merged_ranges = self.merge_overlapping_ranges(skip_ranges)
            
            # 按区间重建内容
            result_parts = []
            last_pos = 0
            
            for start, end in merged_ranges:
                # 添加区间前的内容
                if start > last_pos:
                    result_parts.append(content[last_pos:start])
                
                # 跳过这个区间
                last_pos = end
            
            # 添加最后的内容
            if last_pos < len(content):
                result_parts.append(content[last_pos:])
            
            return ''.join(result_parts)
            
        except Exception as e:
            Logger.error(f"基于区间重建内容失败: {e}")
            return content
    
    def merge_overlapping_ranges(self, ranges: list) -> list:
        """
        合并重叠的区间
        
        参数：
        - ranges: 区间列表
        
        返回：
        - list: 合并后的区间列表
        """
        if not ranges:
            return []
        
        # 按开始位置排序
        sorted_ranges = sorted(ranges, key=lambda x: x[0])
        merged = [sorted_ranges[0]]
        
        for current in sorted_ranges[1:]:
            last = merged[-1]
            
            # 如果当前区间与最后一个区间重叠，合并它们
            if current[0] <= last[1]:
                merged[-1] = (last[0], max(last[1], current[1]))
            else:
                merged.append(current)
        
        return merged
    
    def ensure_output_dir(self) -> Path:
        """确保输出目录存在"""
        output_dir = self.output_file.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def run(self) -> bool:
        """运行HHC生成"""
        try:
            # 加载模板文件
            template_contents = self.load_template_files()
            
            # 扫描项目docs目录结构
            structure = self.scan_project_docs_structure()
            
            if not structure:
                Logger.warning("sub目录下没有找到有效的目录结构")
                return False
            
            # 生成HHC内容
            hhc_content = self.generate_hhc_content(structure, template_contents)
            
            # 确保输出目录存在
            self.ensure_output_dir()
            
            # 写入HHC文件
            try:
                FileUtils.write_file(str(self.output_file), hhc_content)
                return True
                
            except Exception as e:
                Logger.error(f"生成HHC文件失败: {e}")
                return False
                
        except Exception as e:
            Logger.error(f"HHC生成过程出错: {e}")
            return False


@timing_decorator
def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python docs_gen_hhc.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建生成器并执行
        generator = HHCGenerator(input_folder, output_folder, chip_config)
        
        if not generator.run():
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
