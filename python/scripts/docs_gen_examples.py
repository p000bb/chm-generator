#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_gen_examples.py - Examples生成脚本
功能：在input_folder目录下递归查找所有readme.txt文件，提取IP Module、Name和Brief Description
生成JSON文件到output_folder的json/examples.json位置

主要功能：
1. 在input_folder目录下递归查找所有readme.txt文件
2. 提取IP Module、Name和Brief Description信息
3. 生成JSON文件到output_folder的json/examples.json位置

提取规则：
- 中文描述：从"1、功能说明"到"2、使用环境"之间的内容
- 英文描述：从"1. Function description"到"2. Development environment"之间的内容
- 提取逻辑：只要有中文描述或英文描述就会被包含在结果中（不要求两者都存在）
"""

import os
import re
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from common_utils import BaseGenerator, DirectoryScanner, FileUtils, JsonUtils, Logger, ArgumentParser, timing_decorator


class ExamplesGenerator(BaseGenerator):
    """
    Examples生成器类
    
    主要职责：
    - 在input_folder目录下递归查找所有readme.txt文件
    - 提取IP Module、Name和Brief Description信息
    - 生成JSON文件到output_folder的json/examples.json位置
    
    提取规则：
    - 中文描述：从"1、功能说明"到"2、使用环境"之间的内容
    - 英文描述：从"1. Function description"到"2. Development environment"之间的内容
    - 提取逻辑：只要有中文描述或英文描述就会被包含在结果中（不要求两者都存在）
    """
    
    def __init__(self, input_folder, output_folder, chip_config=None):
        """
        初始化Examples生成器
        
        参数：
        - input_folder: 输入目录路径
        - output_folder: 输出目录路径
        - chip_config: 芯片配置（可选，为了兼容BaseGenerator）
        """
        super().__init__(input_folder, output_folder, chip_config or {})
    
    def extract_brief_description(self, readme_path):
        """
        从readme.txt文件中提取Brief Description_CN和Brief Description_EN
        简化版本：只提取两种固定模式
        Brief Description_CN: 1、功能说明 到 2、使用环境之间的内容
        Brief Description_EN: 1. Function description 到 2. Development environment之间的内容
        """
        try:
            # 使用FileUtils智能读取文件
            content = FileUtils.read_file_with_encoding(readme_path)
            
            if not content:
                return {
                    "Brief Description_CN": "",
                    "Brief Description_EN": ""
                }
            
            # 提取中文描述：1、功能说明 到 2、使用环境之间的内容
            chinese_pattern = r'1、\s*功能说明\s*\n(.*?)(?=\n\s*2、\s*使用环境|\Z)'
            chinese_match = re.search(chinese_pattern, content, re.DOTALL)
            
            chinese_description = ""
            if chinese_match:
                chinese_description = chinese_match.group(1).strip()
                # 使用TextProcessor清理描述文本
                from common_utils import TextProcessor
                chinese_description = TextProcessor.clean_text(chinese_description)
            
            # 提取英文描述：1. Function description 到 2. Development environment之间的内容
            english_pattern = r'1\.\s*Function description\s*\n\s*(.*?)(?=\n\s*2\.\s*Development environment|\Z)'
            english_match = re.search(english_pattern, content, re.DOTALL | re.IGNORECASE)
            
            english_description = ""
            if english_match:
                english_description = english_match.group(1).strip()
                # 使用TextProcessor清理描述文本
                from common_utils import TextProcessor
                english_description = TextProcessor.clean_text(english_description)
            
            return {
                "Brief Description_CN": chinese_description,
                "Brief Description_EN": english_description
            }
            
        except Exception as e:
            return {
                "Brief Description_CN": "",
                "Brief Description_EN": ""
            }
    
    def has_code_files(self, directory):
        """
        检查目录是否包含.c或.h文件
        """
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(('.c', '.h')):
                        return True
            return False
        except (OSError, PermissionError):
            return False
    
    def generate_level_string(self, input_folder, readme_dir):
        """
        生成level字符串，格式为row_x_x_x_x_
        根据实际文件路径的层级结构生成，第二层级默认为0
        """
        # 获取从input_folder开始的相对路径
        input_rel_path = os.path.relpath(readme_dir, input_folder)
        path_parts = input_rel_path.split(os.sep)
        
        level_parts = []
        
        # 从input_folder的子目录开始计算索引
        current_path = input_folder
        for i, part in enumerate(path_parts):
            # 获取父目录
            parent_dir = current_path
            
            # 前两个层级默认为0
            if i < 2:
                level_parts.append("0")
            else:
                # 从第三个层级开始，计算当前目录在同级中的索引
                try:
                    # 获取所有同级目录
                    all_siblings = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
                    
                    # 使用Windows默认排序（按名称排序）
                    all_siblings.sort(key=str.lower)  # 不区分大小写的排序
                    
                    # 计算当前目录在同级目录中的索引
                    if part in all_siblings:
                        current_index = all_siblings.index(part)
                        level_parts.append(str(current_index))
                    else:
                        # 如果找不到，设为0
                        level_parts.append("0")
                        
                except (ValueError, OSError):
                    # 如果出错，设为0
                    level_parts.append("0")
            
            current_path = os.path.join(current_path, part)
        
        return "row_" + "_".join(level_parts) + "_"
    
    def find_examples_in_input_folder(self):
        """
        在input_folder目录下递归查找所有的readme.txt文件
        """
        examples_data = []
        
        if not self.input_folder.exists():
            return examples_data
        
        # 使用DirectoryScanner查找readme.txt文件
        readme_files = DirectoryScanner.find_files_by_name(self.input_folder, ['readme.txt'], recursive=True)
        
        for readme_path in readme_files:
            # 获取readme.txt文件所在目录的路径
            readme_dir = readme_path.parent
            
            # 确定IP Module和Name
            # 从input_folder目录开始计算相对路径
            input_rel_path = readme_dir.relative_to(self.input_folder)
            input_parts = input_rel_path.parts
            
            if len(input_parts) >= 2:
                # Name是最后一层
                name = input_parts[-1]
                # IP Module是Name的上一层（倒数第二层）
                ip_module = input_parts[-2] if len(input_parts) >= 2 else input_parts[0]
                
                # 生成level字符串
                level = self.generate_level_string(self.input_folder, str(readme_dir))
                
                # 提取Brief Description
                brief_description = self.extract_brief_description(readme_path)
                
                # 处理Path字段，只取input_folder后面的部分
                # 从完整路径中提取相对路径部分
                relative_path = readme_path.relative_to(self.input_folder)
                # 转换为正斜杠格式
                final_path = str(relative_path).replace('\\', '/')
                
                # 只要有中文描述或英文描述就添加到数据列表
                cn_desc = brief_description["Brief Description_CN"]
                en_desc = brief_description["Brief Description_EN"]
                
                if cn_desc or en_desc:  # 改为"或"的关系
                    examples_data.append({
                        "IP Module": ip_module,
                        "Name": name,
                        "Path": final_path,
                        "Level": level,
                        "Brief Description_CN": cn_desc,
                        "Brief Description_EN": en_desc
                    })
        
        return examples_data
    
    
    def save_json_file(self, examples_data):
        """
        将数据保存为output_folder的json/examples.json文件
        """
        # 在输出目录下创建json子目录
        json_dir = self.ensure_output_dir("json")
        
        # 保存为examples.json文件
        examples_file = json_dir / "examples.json"
        
        
        # 保存完整的汇总文件
        data_to_save = {
            "total_records": len(examples_data),
            "data": examples_data
        }
        
        if JsonUtils.save_json(data_to_save, examples_file, ensure_ascii=False, indent=2):
            return examples_file
        else:
            return None
    
    def run(self):
        """运行Examples生成"""
        # 在输入目录下查找examples
        examples_data = self.find_examples_in_input_folder()
        
        if not examples_data:
            return False
        
        # 保存到输出目录的json/examples.json文件
        examples_file = self.save_json_file(examples_data)
        
        return True


@timing_decorator
def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder = ArgumentParser.parse_standard_args(
            2, "python docs_gen_examples.py <input_folder> <output_folder>"
        )
        
        # 创建生成器并执行
        generator = ExamplesGenerator(input_folder, output_folder)
        
        if not generator.run():
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
