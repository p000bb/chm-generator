#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_gen_examples_overview.py - Examples概览生成脚本
功能：从{output_folder}/json/examples.json加载数据，生成HTML格式的examples overview表格

主要功能：
1. 从{output_folder}/json/examples.json加载examples数据
2. 生成HTML格式的examples overview表格
3. 表格包含5列：IP Module、Name、Brief Description_CN、Brief Description_EN、Path
4. 相同IP Module的行合并显示，使用斑马纹样式
5. 生成HTML文件，文件名为Path的第二部分
6. 支持CHM文件中的本地路径链接
"""

import os
import re
import sys
import winreg
from pathlib import Path
from typing import List, Dict

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
    HashUtils
)


class ExamplesOverviewGenerator(BaseGenerator):
    """
    Examples概览生成器类
    
    主要职责：
    - 从{output_folder}/json/examples.json加载数据
    - 生成HTML格式的examples overview表格
    - 相同IP Module的行合并显示
    - 生成对应的HTML文件
    """
    
    def __init__(self, output_folder, chip_config):
        """初始化Examples概览生成器"""
        super().__init__("", output_folder, chip_config)  # input_folder 在此脚本中不使用
        
        # 斑马纹颜色（参考截图样式）
        self.row_colors = ['#ffffff', '#f0f8ff']  # 白色和浅蓝色
        
    
    def get_filename_replace_rules(self):
        """获取文件名替换规则（用于HTML文件名）"""
        return {
            '&': '_',
            # 可以在这里添加更多替换规则
            # ' ': '_',
            # '-': '_',
        }
    
    def apply_filename_replace_rules(self, filename):
        """应用文件名替换规则"""
        replace_rules = self.get_filename_replace_rules()
        result = filename
        for old_char, new_char in replace_rules.items():
            result = result.replace(old_char, new_char)
        return result
    
    def load_examples_data(self) -> List[Dict[str, any]]:
        """
        从{output_folder}/json/examples.json加载examples数据
        
        返回：
        - List[Dict]: examples数据列表
        """
        try:
            examples_file = self.output_folder / "json" / "examples.json"
            
            if not examples_file.exists():
                Logger.warning(f"examples.json文件不存在: {examples_file}")
                return []
            
            data = JsonUtils.load_json(examples_file)
            examples_data = data.get("data", [])
            
            return examples_data
            
        except Exception as e:
            Logger.error(f"加载examples数据失败: {e}")
            return []
    
    def get_registry_pdf_base_path(self, project_name):
        """
        从注册表读取芯片文档基路径
        
        参数：
        - project_name: 项目名称
        
        返回：
        - str: 注册表中的基路径，如果不存在返回None
        """
        try:
            # 注册表路径：HKEY_CURRENT_USER\SOFTWARE\ChmConfig\
            reg_path = r"SOFTWARE\ChmConfig"
            key_name = f"pdfBasePath_{project_name}"
            
            # 打开注册表键
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ) as key:
                try:
                    # 读取值
                    value, _ = winreg.QueryValueEx(key, key_name)
                    return value
                except FileNotFoundError:
                    return None
                except Exception as e:
                    Logger.warning(f"读取注册表时出错: {e}")
                    return None
        except FileNotFoundError:
            return None
        except Exception as e:
            Logger.warning(f"访问注册表时出错: {e}")
            return None
    
    def get_ip_module_color(self, ip_module):
        """
        获取IP Module对应的颜色（基于模块名称生成不同颜色）
        
        参数：
        - ip_module: IP Module名称
        
        返回：
        - str: 颜色值
        """
        # 使用模块名称的哈希值生成不同的颜色
        hash_value = int(HashUtils.generate_8char_hash(ip_module), 16)
        
        # 生成柔和的颜色（避免太亮或太暗）
        r = (hash_value & 0xFF) % 128 + 128  # 128-255
        g = ((hash_value >> 8) & 0xFF) % 128 + 128  # 128-255
        b = ((hash_value >> 16) & 0xFF) % 128 + 128  # 128-255
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def extract_path_second_part(self, full_path):
        """
        从完整路径中提取第二部分作为文件名
        
        参数：
        - full_path: 完整路径，如 "6-Software_Development_Kit/Nations.N32H47x_48x_Library.1.1.0/..."
        
        返回：
        - str: 第二部分，如 "Nations.N32H47x_48x_Library.1.1.0"
        """
        # 统一路径分隔符，支持Windows和Unix路径
        normalized_path = full_path.replace('\\', '/')
        path_parts = normalized_path.split('/')
        if len(path_parts) >= 2:
            return path_parts[1]
        return "examples_overview"
    
    def clean_path_for_display(self, full_path):
        """
        清理路径用于显示（移除最后的/readme.txt）
        
        参数：
        - full_path: 完整路径
        
        返回：
        - str: 清理后的路径
        """
        # 统一路径分隔符，支持Windows和Unix路径
        normalized_path = full_path.replace('\\', '/')
        if normalized_path.endswith('/readme.txt'):
            cleaned_path = normalized_path[:-11]  # 移除最后的/readme.txt
            return cleaned_path
        return normalized_path
    
    
    def generate_html_table(self, examples_data, registry_base_path=None, project_name=None):
        """
        生成HTML表格
        
        参数：
        - examples_data: examples.json中的数据
        - registry_base_path: 注册表中的芯片文档基路径
        - project_name: 项目名称，用于注册表查询
        
        返回：
        - str: 生成的HTML内容
        """
        # 生成IP Module导航链接
        ip_module_links = self.generate_ip_module_links(examples_data)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Examples Overview</title>
    <style>
        body {{
            margin: 0;
        }}
        .container {{
            background-color: white;
            border: 2px solid #e2e8f0;
            overflow: hidden;
        }}
        .header {{
            background-color: #667eea;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }}
        .ip-module-nav {{
            padding: 20px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #e2e8f0;
        }}
        .ip-module-nav h3 {{
            margin: 0 0 15px 0;
            color: #2d3748;
            font-size: 18px;
        }}
        .ip-module-links {{
            display: block;
            margin: 0;
            padding: 0;
        }}
        .ip-module-link {{
            color: #3182ce;
            text-decoration: none;
            border-bottom: 1px dotted #3182ce;
            padding: 5px 10px;
            background-color: white;
            border: 1px solid #e2e8f0;
            font-size: 14px;
            display: inline-block;
            margin: 4px;
        }}
        .ip-module-link:hover {{
            color: #2c5aa0;
            border-bottom: 1px solid #2c5aa0;
            background-color: #f7fafc;
        }}
        .table-container {{
            overflow: hidden;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            border: 1px solid #e2e8f0;
        }}
        th {{
            background-color: #4a5568;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #2d3748;
        }}
        th:first-child {{
            border-left: 1px solid #2d3748;
        }}
        th:last-child {{
            border-right: 1px solid #2d3748;
        }}
        td {{
            padding: 10px 8px;
            border: 1px solid #e2e8f0;
            vertical-align: middle;
        }}
        tr:hover {{
            background-color: #f7fafc !important;
        }}
        .ip-module {{
            font-weight: bold;
            color: #2d3748;
            padding: 6px 12px;
            display: inline-block;
            min-width: 80px;
            text-align: center;
            border: 1px solid #e2e8f0;
            background-color: #f8f9fa;
        }}
        .ip-module-cell-link {{
            color: #3182ce;
            text-decoration: none;
            border-bottom: 1px dotted #3182ce;
            padding: 6px 12px;
            display: inline-block;
            min-width: 80px;
            text-align: center;
            border: 1px solid #e2e8f0;
            background-color: #f8f9fa;
            font-weight: bold;
            transition: all 0.2s ease;
        }}
        .ip-module-cell-link:hover {{
            color: #2c5aa0;
            border-bottom: 1px solid #2c5aa0;
            background-color: #f7fafc;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .example-name {{
            font-weight: bold;
            color: #2b6cb0;
        }}
        .example-name-link {{
            color: #2b6cb0;
            text-decoration: none;
            border-bottom: 1px dotted #2b6cb0;
        }}
        .example-name-link:hover {{
            color: #2c5aa0;
            border-bottom: 1px solid #2c5aa0;
        }}
        .description-cn {{
            color: #2d3748;
            margin-bottom: 8px;
            line-height: 1.4;
        }}
        .description-en {{
            color: #4a5568;
            margin-bottom: 8px;
            line-height: 1.4;
            font-style: italic;
        }}
        .path {{
            color: #718096;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            word-break: break-all;
        }}
        .path a {{
            color: #3182ce;
            text-decoration: none;
            border-bottom: 1px dotted #3182ce;
        }}
        .path a:hover {{
            color: #2c5aa0;
            border-bottom: 1px solid #2c5aa0;
        }}
        .path-link {{
            color: #28a745 !important;
            text-decoration: none;
            border-bottom: 1px dotted #28a745;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        .col-ip-module {{
            width: 12%;
        }}
        .col-name {{
            width: 15%;
        }}
        .col-description-cn {{
            width: 25%;
        }}
        .col-description-en {{
            width: 25%;
        }}
        .col-path {{
            width: 23%;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Examples Overview</h1>
        </div>
        
        <div class="ip-module-nav">
            <h3>The package contains the following examples:</h3>
            <div class="ip-module-links">
                {ip_module_links}
            </div>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="col-ip-module">IP Module</th>
                        <th class="col-name">Name</th>
                        <th class="col-description-cn">Brief Description (CN)</th>
                        <th class="col-description-en">Brief Description (EN)</th>
                        <th class="col-path">Path</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        # 按IP Module分组数据
        grouped_data = {}
        for item in examples_data:
            ip_module = item.get('IP Module', 'Unknown')
            if ip_module not in grouped_data:
                grouped_data[ip_module] = []
            grouped_data[ip_module].append(item)
        
        # 生成表格行（实现IP Module列的单元格合并效果）
        row_index = 0
        for ip_module, items in grouped_data.items():
            ip_module_color = self.get_ip_module_color(ip_module)
            
            # 斑马纹效果：不同IP Module之间交替颜色
            row_color = self.row_colors[row_index % len(self.row_colors)]
            
            for i, item in enumerate(items):
                name = item.get('Name', '')
                brief_cn = item.get('Brief Description_CN', '')
                brief_en = item.get('Brief Description_EN', '')
                path = item.get('Path', '')
                clean_path = self.clean_path_for_display(path)
                
                # 如果是同一IP Module的第一行，使用rowspan合并单元格
                if i == 0:
                    # 为IP Module生成可点击链接
                    ip_module_link = self.generate_ip_module_cell_link(ip_module, item)
                    ip_module_cell = f'<td rowspan="{len(items)}" style="background-color: {ip_module_color}; vertical-align: middle; text-align: center;">{ip_module_link}</td>'
                else:
                    ip_module_cell = ''  # 后续行不需要IP Module列
                
                # 为Name列生成跳转链接
                level = item.get('Level', '')
                name_link = name  # 默认显示名称
                
                if level and path:
                    # 1. 处理Path：分割获取第一部分和第二部分
                    path_parts = path.split('/')
                    if len(path_parts) >= 2:
                        path_part1 = path_parts[0]  # 6-Software_Development_Kit
                        path_part2 = path_parts[1]  # Nations.N32G4FR_Library.2.4.0
                        
                        # 2. 通过path_mapping.json获取hash值
                        hash_mapping = HashUtils.load_path_mapping(self.output_folder)
                        # 查找原始路径对应的hash路径
                        original_path = f"{path_part1}/{path_part2}"
                        hash_path = None
                        
                        # 遍历映射找到对应的hash路径
                        for mapping in hash_mapping:
                            if mapping.get("original_path") == original_path:
                                hash_path = mapping.get("hash_path")
                                break
                        
                        # 如果找到hash映射，使用hash值；否则使用原始值
                        if hash_path:
                            # hash_path 直接就是8位hash值，不需要分割
                            final_path2 = hash_path  # 直接使用hash值，如299332ec
                        else:
                            final_path2 = path_part2
                        
                        # 3. 生成链接：../sub/{path_part1}/{final_path2}/html/files.html#{level}
                        link_path = f"../sub/{path_part1}/{final_path2}/html/files.html#{level}"
                        
                        name_link = f'<a href="{link_path}" class="example-name-link">{name}</a>'
                
                # 为Path列生成链接
                path_link = f'<a href="#" onclick="showConfigTip(\'{clean_path}\'); return false;">{clean_path}</a>'
                
                html_content += f"""
                    <tr style="background-color: {row_color};">
                        {ip_module_cell}
                        <td class="example-name">{name_link}</td>
                        <td class="description-cn">{brief_cn}</td>
                        <td class="description-en">{brief_en}</td>
                        <td class="path">/{path_link}</td>
                    </tr>
"""
            
            # 每处理完一个IP Module，增加行索引
            row_index += 1
        
        html_content += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content
    
    def generate_ip_module_cell_link(self, ip_module, item):
        """
        为表格中的IP Module单元格生成可点击链接
        
        参数：
        - ip_module: IP Module名称
        - item: 当前数据项（包含Level和Path信息）
        
        返回：
        - str: 生成的HTML链接内容
        """
        level = item.get('Level', '')
        path = item.get('Path', '')
        
        if level and path:
            # 1. 处理Level：去除最后2项
            level_parts = level.split('_')
            if len(level_parts) >= 2:
                anchor_level = '_'.join(level_parts[:-2]) + '_'
            else:
                anchor_level = level
            
            # 2. 处理Path：分割获取第一部分和第二部分
            path_parts = path.split('/')
            if len(path_parts) >= 2:
                path_part1 = path_parts[0]  # 6-Software_Development_Kit
                path_part2 = path_parts[1]  # Nations.N32G4FR_Library.2.4.0
                
                # 3. 通过path_mapping.json获取hash值
                hash_mapping = HashUtils.load_path_mapping(self.output_folder)
                # 查找原始路径对应的hash路径
                original_path = f"{path_part1}/{path_part2}"
                hash_path = None
                
                # 遍历映射找到对应的hash路径
                for mapping in hash_mapping:
                    if mapping.get("original_path") == original_path:
                        hash_path = mapping.get("hash_path")
                        break
                
                # 如果找到hash映射，使用hash值；否则使用原始值
                if hash_path:
                    # hash_path 直接就是8位hash值，不需要分割
                    final_path2 = hash_path  # 直接使用hash值，如299332ec
                else:
                    final_path2 = path_part2
                
                # 4. 生成链接：../sub/{path_part1}/{final_path2}/html/files.html#{anchor_level}
                link_path = f"../sub/{path_part1}/{final_path2}/html/files.html#{anchor_level}"
                
                return f'<a href="{link_path}" class="ip-module-cell-link">{ip_module}</a>'
        
        # 如果无法生成链接，返回普通的span标签
        return f'<span class="ip-module">{ip_module}</span>'

    def generate_ip_module_links(self, examples_data):
        """
        生成IP Module导航链接
        
        参数：
        - examples_data: examples.json中的数据
        
        返回：
        - str: 生成的HTML链接内容
        """
        # 收集所有唯一的IP Module
        unique_ip_modules = set()
        ip_module_items = {}
        
        for item in examples_data:
            ip_module = item.get('IP Module', '')
            if ip_module:
                unique_ip_modules.add(ip_module)
                ip_module_items[ip_module] = item  # 保存第一个找到的item作为代表
        
        # 生成链接HTML
        links_html = ""
        for ip_module in sorted(unique_ip_modules):
            item = ip_module_items.get(ip_module, {})
            level = item.get('Level', '')
            path = item.get('Path', '')
            
            if level and path:
                # 1. 处理Level：去除最后2项
                level_parts = level.split('_')
                if len(level_parts) >= 2:
                    anchor_level = '_'.join(level_parts[:-2]) + '_'
                else:
                    anchor_level = level
                
                # 2. 处理Path：分割获取第一部分和第二部分
                path_parts = path.split('/')
                if len(path_parts) >= 2:
                    path_part1 = path_parts[0]  # 6-Software_Development_Kit
                    path_part2 = path_parts[1]  # Nations.N32G4FR_Library.2.4.0
                    
                    # 3. 通过path_mapping.json获取hash值
                    hash_mapping = HashUtils.load_path_mapping(self.output_folder)
                    # 查找原始路径对应的hash路径
                    original_path = f"{path_part1}/{path_part2}"
                    hash_path = None
                    
                    # 遍历映射找到对应的hash路径
                    for mapping in hash_mapping:
                        if mapping.get("original_path") == original_path:
                            hash_path = mapping.get("hash_path")
                            break
                    
                    # 如果找到hash映射，使用hash值；否则使用原始值
                    if hash_path:
                        # hash_path 直接就是8位hash值，不需要分割
                        final_path2 = hash_path  # 直接使用hash值，如299332ec
                    else:
                        final_path2 = path_part2
                    
                    # 4. 生成链接：../sub/{path_part1}/{final_path2}/html/files.html#{anchor_level}
                    link_path = f"../sub/{path_part1}/{final_path2}/html/files.html#{anchor_level}"
                    
                    links_html += f'<a href="{link_path}" class="ip-module-link">{ip_module}</a>'
                else:
                    links_html += f'<span class="ip-module-link">{ip_module}</span>'
            else:
                links_html += f'<span class="ip-module-link">{ip_module}</span>'
        
        return links_html
    
    def generate(self) -> bool:
        """
        生成Examples概览HTML文件
        
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
            
            # 获取项目名称
            project_name = self.project_info['chip_name']
            
            # 获取注册表中的芯片文档基路径
            registry_base_path = self.get_registry_pdf_base_path(project_name)
            # 按Path的第二部分分组数据
            path_groups = {}
            for item in examples_data:
                path = item.get('Path', '')
                path_second = self.extract_path_second_part(path)
                if path_second not in path_groups:
                    path_groups[path_second] = []
                path_groups[path_second].append(item)
            
            
            # 为每个分组生成HTML文件
            for group_name, group_data in path_groups.items():
                
                # 生成HTML内容
                html_content = self.generate_html_table(group_data, registry_base_path, project_name)
                
                # 确保文件名合法
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', group_name)
                
                # 应用文件名替换规则（将&替换为_等）
                safe_filename = self.apply_filename_replace_rules(safe_filename)
                
                # 创建输出目录
                output_dir = self.ensure_output_dir("output/extra")
                
                # 生成HTML文件
                output_file = output_dir / f"{safe_filename}.html"
                
                if FileUtils.write_file(output_file, html_content):
                    Logger.success(f"生成HTML文件: {output_file.name}")
                else:
                    Logger.error(f"写入HTML文件失败: {output_file}")
                    return False
            
            return True
            
        except Exception as e:
            Logger.error(f"生成Examples概览HTML文件时出错: {e}")
            return False


def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python docs_gen_examples_overview.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        # 解析芯片配置JSON
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建生成器并执行
        generator = ExamplesOverviewGenerator(output_folder, chip_config)
        
        if generator.generate():
            Logger.success("Examples概览HTML文件生成完成！")
        else:
            Logger.error("Examples概览HTML文件生成失败！")
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
