#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_gen_examples_description.py - Examples描述信息添加脚本
遍历output目录下的files.html文件，根据json/examples.json添加描述信息

主要功能：
1. 在output目录下查找所有files.html文件
2. 根据json/examples.json添加描述信息
3. 支持多项目处理
4. 根据files.html的路径过滤examples.json数据
"""

import os
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup

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
    JsonUtils,
    HashUtils,
    timing_decorator
)


class ExamplesDescriptionAdder(BaseGenerator):
    """
    Examples描述信息添加器类
    
    主要职责：
    - 在output目录下查找所有files.html文件
    - 根据json/examples.json添加描述信息
    - 支持多项目处理
    - 根据files.html的路径过滤examples.json数据
    """
    
    def __init__(self, output_folder, chip_config):
        """初始化Examples描述信息添加器"""
        super().__init__("", output_folder, chip_config)  # input_folder 在此脚本中不使用
        
    
    def load_examples_data(self) -> list:
        """加载examples.json数据"""
        try:
            examples_file = self.output_folder / "json" / "examples.json"
            
            if not examples_file.exists():
                Logger.warning(f"examples.json文件不存在: {examples_file}")
                return []
            
            data = JsonUtils.load_json(examples_file)
            examples_data = data.get('data', [])
            
            return examples_data
            
        except Exception as e:
            Logger.error(f"加载examples数据失败: {e}")
            return []
    
    def extract_path_from_files_html(self, files_html_path):
        """
        从files.html的路径中提取关键路径信息
        
        参数：
        - files_html_path: files.html的完整路径
        
        返回：
        - str: 提取的关键路径，用于过滤examples.json
        """
        try:
            # 将files.html路径转换为相对路径
            # 例如：output/sub/7-Application_Note/AN_N32G43x_N32L43x_N32L40x_USB_Xtal_Less_Application_Note_V1.1/html/files.html
            # 提取：7-Application_Note/AN_N32G43x_N32L43x_N32L40x_USB_Xtal_Less_Application_Note_V1.1
            
            # 移除output根路径部分
            relative_path = os.path.relpath(files_html_path, self.output_folder)
            
            # 查找 sub/ 后面到 /html 前面的路径
            # 格式：sub/[关键路径]/html/files.html
            # 注意：这里可能是hash路径，需要通过映射表反向查找原始路径
            # 支持Windows和Unix路径分隔符
            match = re.search(r'sub[\\/](.+?)[\\/]html[\\/]files\.html$', relative_path)
            if match:
                key_path = match.group(1)
                
                # 检查是否是hash路径，如果是则反向查找原始路径
                hash_mapping = HashUtils.load_path_mapping(self.output_folder)
                
                # 统一路径分隔符为正斜杠，因为映射表使用正斜杠
                normalized_key_path = key_path.replace('\\', '/')
                
                # 提取hash部分（路径的最后一部分）
                path_parts = normalized_key_path.split('/')
                hash_part = path_parts[-1] if path_parts else normalized_key_path
                
                # 查找原始路径
                original_path = None
                for mapping in hash_mapping:
                    if mapping.get("hash_path") == hash_part:
                        original_path = mapping.get("original_path")
                        break
                # 验证路径的有效性
                if self.validate_extracted_path(key_path):
                    return key_path
                else:
                    Logger.warning(f"提取的路径无效: {key_path}")
                    return None
            else:
                Logger.warning(f"无法从路径中提取关键信息: {relative_path}")
                return None
                
        except Exception as e:
            Logger.error(f"提取路径信息失败: {e}")
            return None
    
    def validate_extracted_path(self, path):
        """
        验证提取的路径是否有效
        
        参数：
        - path: 提取的路径
        
        返回：
        - bool: 路径是否有效
        """
        if not path:
            return False
        
        # 检查路径是否包含必要的组件
        path_parts = path.replace('\\', '/').split('/')
        
        # 路径应该至少包含两个部分（如：7-Application_Note/AN_N32G43x_N32L43x_N32L40x_USB_Xtal_Less_Application_Note_V1.1）
        if len(path_parts) < 2:
            return False
        
        # 检查路径是否包含常见的有效模式
        valid_patterns = [
            'Software_Development_Kit',
            'Application_Note', 
            'Hardware_Evaulation_Board', # 兼容
            'Hardware_Evaluation_Board', # 兼容
            'User_Manual',
            'User_Guide',
            'Datasheet',
            'Product_Brief',
            'Errata_Sheet'
        ]
        
        # 检查第一个路径段是否匹配有效模式
        first_segment = path_parts[0]
        has_valid_pattern = any(pattern in first_segment for pattern in valid_patterns)
        if not has_valid_pattern:
            return False
        
        return True
    
    def filter_examples_by_path(self, examples_data, target_path):
        """
        根据目标路径过滤examples.json数据
        
        参数：
        - examples_data: examples.json中的所有数据
        - target_path: 目标路径（用于过滤）
        
        返回：
        - list: 过滤后的数据
        """
        if not target_path:
            return examples_data
        
        filtered_data = []
        
        for item in examples_data:
            item_path = item.get('Path', '')
            
            # 统一路径分隔符，将反斜杠转换为正斜杠
            normalized_target_path = target_path.replace('\\', '/')
            normalized_item_path = item_path.replace('\\', '/')
            
            # 使用精确的路径前缀匹配
            if normalized_item_path.startswith(normalized_target_path + '/'):
                filtered_data.append(item)
            elif normalized_item_path == normalized_target_path:
                # 完全匹配的情况
                filtered_data.append(item)
        
        return filtered_data
    
    def find_files_html_files(self):
        """在output目录下查找所有files.html文件"""
        files_html_list = []
        
        if not self.output_folder.exists():
            Logger.warning(f"输出目录不存在: {self.output_folder}")
            return files_html_list
        
        
        for root, dirs, files in os.walk(self.output_folder):
            for file in files:
                if file == 'files.html':
                    full_path = os.path.join(root, file)
                    files_html_list.append(full_path)
        
        return files_html_list
    
    def process_html_file(self, html_file_path, examples_data):
        """处理单个HTML文件，添加描述信息"""
        
        # 提取关键路径信息
        key_path = self.extract_path_from_files_html(html_file_path)
        
        # 如果路径提取失败，直接返回，不处理任何数据
        if key_path is None:
            Logger.error("无法提取关键路径，跳过此文件")
            return False
        
        # 读取HTML文件
        try:
            html_content = FileUtils.read_file_with_encoding(html_file_path)
        except Exception as e:
            Logger.error(f"无法读取HTML文件: {e}")
            return False
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 清空所有td.desc元素的内容
        desc_elements = soup.find_all('td', class_='desc')
        cleared_count = 0
        
        for desc_elem in desc_elements:
            desc_elem.clear()
            cleared_count += 1
        
        
        # 根据路径过滤examples数据
        filtered_examples = self.filter_examples_by_path(examples_data, key_path)
        
        if not filtered_examples:
            # 即使没有匹配数据，也要保存清空后的文件
            try:
                FileUtils.write_file(html_file_path, str(soup))
                return True
            except Exception as e:
                Logger.error(f"保存清空后的文件失败: {e}")
                return False
        
        modified_count = 0
        
        # 遍历过滤后的examples数据
        for item in filtered_examples:
            level = item.get('Level', '')
            if not level:
                continue
                
            # 在HTML中查找对应的元素 - 精确匹配id
            target_element = soup.find(id=level)
            
            if not target_element:
                continue
            
            # 找到该元素的.desc子元素
            desc_element = target_element.find(class_='desc')
            if not desc_element:
                continue
            
            # 获取中文和英文描述
            cn_desc = item.get('Brief Description_CN', '')
            en_desc = item.get('Brief Description_EN', '')
            
            # 将换行符转换为HTML内容项
            def text_to_content_items(text):
                if not text:
                    return ""
                # 将\n转换为多个content-item div
                paragraphs = text.split('\n')
                html_items = []
                for p in paragraphs:
                    p = p.strip()
                    if p:  # 只添加非空段落
                        html_items.append('<div class="content-item"><span class="item-text">{}</span></div>'.format(p))
                return "".join(html_items)
            
            # 生成HTML格式的描述
            html_desc = '<div class="content-wrapper">'
            
            # 中文部分
            if cn_desc:
                html_desc += '<div class="chinese-section">'
                html_desc += '<div class="section-title chinese-title"><strong>中文说明</strong></div>'
                html_desc += '<div class="content-area chinese-content">'
                html_desc += text_to_content_items(cn_desc)
                html_desc += '</div>'
                html_desc += '</div>'
            
            # 分隔符（只有当中文和英文都存在时才添加）
            if cn_desc and en_desc:
                html_desc += '<div class="separator"></div>'
            
            # 英文部分
            if en_desc:
                html_desc += '<div class="english-section">'
                html_desc += '<div class="section-title english-title"><strong>English Description</strong></div>'
                html_desc += '<div class="content-area english-content">'
                html_desc += text_to_content_items(en_desc)
                html_desc += '</div>'
                html_desc += '</div>'
            
            html_desc += '</div>'
            
            # 更新描述内容为HTML格式
            desc_element.string = ""
            desc_element.append(BeautifulSoup(html_desc, 'html.parser'))
            modified_count += 1
        
        
        # 直接在原文件中保存修改
        try:
            FileUtils.write_file(html_file_path, str(soup))
            return True
        except Exception as e:
            Logger.error(f"更新files.html失败: {e}")
            return False
    
    def generate(self) -> bool:
        """
        生成Examples描述信息
        
        返回：
        - bool: 是否成功
        """
        try:
            
            # 检查output目录是否存在
            if not self.output_folder.exists():
                Logger.error(f"输出目录不存在: {self.output_folder}")
                return False
            
            # 加载examples数据
            examples_data = self.load_examples_data()
            if not examples_data:
                Logger.warning("没有找到examples数据")
                return False
            
            # 查找output目录下的所有files.html文件
            files_html_list = self.find_files_html_files()
            
            if not files_html_list:
                Logger.warning("output目录下没有找到files.html文件")
                return False
            
            # 处理每个HTML文件
            success_count = 0
            for html_file in files_html_list:
                if self.process_html_file(html_file, examples_data):
                    success_count += 1
            
            return True
            
        except Exception as e:
            Logger.error(f"添加Examples描述信息时出错: {e}")
            return False


@timing_decorator
def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python docs_gen_examples_description.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        # 解析芯片配置JSON
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建生成器并执行
        adder = ExamplesDescriptionAdder(output_folder, chip_config)
        
        if not adder.generate():
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
