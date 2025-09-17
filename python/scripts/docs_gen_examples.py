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
import sys
import json
import re
from pathlib import Path


class ExamplesGenerator:
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
    
    def __init__(self, input_folder, output_folder):
        """
        初始化Examples生成器
        
        参数：
        - input_folder: 输入目录路径
        - output_folder: 输出目录路径
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
    
    def extract_brief_description(self, readme_path):
        """
        从readme.txt文件中提取Brief Description_CN和Brief Description_EN
        简化版本：只提取两种固定模式
        Brief Description_CN: 1、功能说明 到 2、使用环境之间的内容
        Brief Description_EN: 1. Function description 到 2. Development environment之间的内容
        """
        try:
            # 智能判断编码格式并读取文件
            content = ""
            
            # 尝试多种编码读取文件
            encodings_to_try = [
                'utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 
                'latin1', 'iso-8859-1', 'cp1252'
            ]
            
            for encoding in encodings_to_try:
                try:
                    with open(readme_path, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                except LookupError:
                    # 编码名称不存在，跳过
                    continue
            
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
                # 清理描述文本，保留换行符但清理多余空格
                chinese_description = re.sub(r'\n\s*\n', '\n', chinese_description)  # 清理空行
                chinese_description = re.sub(r'^\s+|\s+$', '', chinese_description, flags=re.MULTILINE)  # 清理行首行尾空格
            
            # 提取英文描述：1. Function description 到 2. Development environment之间的内容
            english_pattern = r'1\.\s*Function description\s*\n\s*(.*?)(?=\n\s*2\.\s*Development environment|\Z)'
            english_match = re.search(english_pattern, content, re.DOTALL | re.IGNORECASE)
            
            english_description = ""
            if english_match:
                english_description = english_match.group(1).strip()
                # 清理描述文本，保留换行符但清理多余空格
                english_description = re.sub(r'\n\s*\n', '\n', english_description)  # 清理空行
                english_description = re.sub(r'^\s+|\s+$', '', english_description, flags=re.MULTILINE)  # 清理行首行尾空格
            
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
        从input_folder开始计算，每个目录在同级中的索引位置
        只考虑包含.c或.h文件的目录（包括子目录）
        """
        # 获取从input_folder开始的相对路径
        input_rel_path = os.path.relpath(readme_dir, input_folder)
        path_parts = input_rel_path.split(os.sep)
        
        level_parts = ["0"]  # input_folder本身算作第0个
        
        # 从input_folder的子目录开始计算索引
        current_path = input_folder
        for i, part in enumerate(path_parts):
            # 获取父目录
            parent_dir = current_path
            # 获取当前目录在同级中的索引（只考虑包含代码文件的目录）
            try:
                # 获取所有同级目录
                all_siblings = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
                
                # 只保留包含代码文件的目录（包括子目录）
                valid_siblings = []
                for sibling in all_siblings:
                    sibling_path = os.path.join(parent_dir, sibling)
                    if self.has_code_files(sibling_path):
                        valid_siblings.append(sibling)
                
                # 使用Windows默认排序（按名称排序）
                valid_siblings.sort(key=str.lower)  # 不区分大小写的排序
                
                # 计算当前目录在有效目录中的索引
                if part in valid_siblings:
                    current_index = valid_siblings.index(part)
                    level_parts.append(str(current_index))
                else:
                    # 如果当前目录不包含代码文件，设为0
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
        
        # 遍历input_folder文件夹
        for root, dirs, files in os.walk(self.input_folder):
            for file in files:
                if file == 'readme.txt':
                    readme_path = os.path.join(root, file)
                    
                    # 获取readme.txt文件所在目录的路径
                    readme_dir = os.path.dirname(readme_path)
                    
                    # 提取路径信息
                    path_parts = readme_dir.split(os.sep)
                    
                    # 确定IP Module和Name
                    # 从input_folder目录开始计算相对路径
                    input_rel_path = os.path.relpath(readme_dir, self.input_folder)
                    input_parts = input_rel_path.split(os.sep)
                    
                    if len(input_parts) >= 2:
                        # Name是最后一层
                        name = input_parts[-1]
                        # IP Module是Name的上一层（倒数第二层）
                        ip_module = input_parts[-2] if len(input_parts) >= 2 else input_parts[0]
                        
                        # 生成level字符串
                        level = self.generate_level_string(self.input_folder, readme_dir)
                        
                        # 提取Brief Description
                        brief_description = self.extract_brief_description(readme_path)
                        
                        # 处理Path字段，只取input_folder后面的部分
                        # 从完整路径中提取相对路径部分
                        path_parts = readme_path.split(str(self.input_folder))
                        if len(path_parts) > 1:
                            relative_path = path_parts[1]  # 获取input_folder后面的部分
                            # 转换为正斜杠格式
                            final_path = relative_path.strip('\\/').replace('\\', '/')
                        else:
                            final_path = readme_path.replace('\\', '/')
                        
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
    
    def modify_level_field(self, data):
        """
        临时功能：将Level字段的前9个字符替换为row_0_0_0
        注意：这是暂时功能，后续应该会去除
        """
        for item in data:
            if "Level" in item:
                original_level = item["Level"]
                # 替换前9个字符为row_0_0_0
                if len(original_level) >= 9:
                    new_level = "row_0_0_0" + original_level[9:]
                    item["Level"] = new_level
        
        return data
    
    def save_json_file(self, examples_data):
        """
        将数据保存为output_folder的json/examples.json文件
        """
        # 在输出目录下创建json子目录
        json_dir = self.output_folder / "json"
        json_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存为examples.json文件
        examples_file = json_dir / "examples.json"
        
        # 临时功能：修改Level字段
        examples_data = self.modify_level_field(examples_data)
        
        # 保存完整的汇总文件
        with open(examples_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_records": len(examples_data),
                "data": examples_data
            }, f, ensure_ascii=False, indent=2)
        
        return examples_file
    
    def run(self):
        """运行Examples生成"""
        # 在输入目录下查找examples
        examples_data = self.find_examples_in_input_folder()
        
        if not examples_data:
            return False
        
        # 保存到输出目录的json/examples.json文件
        examples_file = self.save_json_file(examples_data)
        
        return True


def main():
    """
    主函数
    """
    try:
        # 检查参数数量
        if len(sys.argv) < 3:
            print("错误: 参数不足，期望2个参数")
            print("用法: python docs_gen_examples.py <input_folder> <output_folder>")
            sys.exit(1)
        
        # 获取参数
        input_folder = sys.argv[1]
        output_folder = sys.argv[2]
        
        # 创建生成器并执行
        generator = ExamplesGenerator(input_folder, output_folder)
        
        if generator.run():
            print("Examples生成完成！")
        else:
            print("Examples生成失败！")
            sys.exit(1)
        
    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
