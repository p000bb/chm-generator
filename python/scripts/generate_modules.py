#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_modules.py - 自动生成doxygen模块的Markdown文件
功能：根据芯片系列名称过滤Excel数据，生成对应的MD文件
"""

import json
import pandas as pd
import sys
import shutil
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from common_utils import (
    ArgumentParser, timing_decorator, Logger
)

class DoxygenGenerator:
    """
    Doxygen模块生成器类
    
    主要职责：
    - 从项目根目录的config/path.xlsx读取Excel数据
    - 根据芯片系列名称过滤数据
    - 在输出目录下生成对应的MD文件
    """
    
    def __init__(self, output_folder, chip_config):
        """初始化Doxygen生成器"""
        self.output_folder = Path(output_folder)
        self.chip_config = chip_config
        
        # 从芯片配置中获取项目名
        self.project_name = chip_config.get('chipName', '')
        
        # 项目根目录（假设脚本在python/scripts目录下）
        self.work_dir = Path(__file__).parent.parent.parent
        
        # Excel文件路径
        self.excel_file = self.work_dir / "config" / "path.xlsx"
        
        # 基础配置文件路径
        self.base_config_file = self.work_dir / "config" / "base.json"
        
        # 基础配置
        self.excel_data = None
        self.base_config = None
        
    def load_excel(self):
        """加载Excel数据"""
        if not self.excel_file.exists():
            raise FileNotFoundError(f"Excel文件不存在: {self.excel_file}")
        
        self.excel_data = pd.read_excel(self.excel_file)
    
    def load_base_config(self):
        """加载基础配置文件"""
        if not self.base_config_file.exists():
            raise FileNotFoundError(f"基础配置文件不存在: {self.base_config_file}")
        
        with open(self.base_config_file, 'r', encoding='utf-8') as f:
            self.base_config = json.load(f)
    
    def filter_by_chip_series(self, chip_name):
        """根据芯片系列过滤数据"""
        if chip_name == "Common_Platform":
            result = self.excel_data[self.excel_data.iloc[:, 0] == "Common_Platform"]
            return result
        
        # 获取芯片版本信息
        chip_version = self.chip_config.get('chipVersion', '')
        version_pattern = f"{chip_name}_V{chip_version}" if chip_version else ""
        
        # 去除结尾所有的'x'来获取前缀
        prefix = chip_name.rstrip('x')
        
        final_filtered = []
        
        for _, row in self.excel_data.iterrows():
            series_name = str(row.iloc[0])
            
            # 条件1：A列包含Common_Platform，直接满足不需要往后走了
            if series_name == "Common_Platform":
                final_filtered.append(row)
                continue
            
            # 条件2：A列不包含Common_Platform，判断A列包含chip_name.rstrip('x')的内容
            if prefix in series_name:
                final_filtered.append(row)
                continue
            
            # 条件3：G列或者I列包含{chip_name}_V{chip_version}的内容
            if version_pattern:
                g_column_value = str(row.iloc[6]) if len(row) > 6 and pd.notna(row.iloc[6]) else ""
                i_column_value = str(row.iloc[8]) if len(row) > 8 and pd.notna(row.iloc[8]) else ""
                
                if (version_pattern in g_column_value or version_pattern in i_column_value):
                    final_filtered.append(row)
        
        result_df = pd.DataFrame(final_filtered) if final_filtered else pd.DataFrame()
        
        return result_df
    
    def filter_by_project_path(self, project_folder_name: str):
        """根据项目文件夹名称在G列或I列中匹配路径"""
        if not self.excel_data.empty:
            # 构建匹配条件：
            # 1. A列是Common_Platform（始终保留）
            # 2. G列包含项目文件夹名称路径
            # 3. 如果G列不存在或为空，则使用I列匹配
            mask = (
                (self.excel_data.iloc[:, 0] == "Common_Platform") |  # A列是Common_Platform
                (self.excel_data.iloc[:, 6].str.contains(f"/{project_folder_name}/", na=False)) |  # G列包含项目路径
                (
                    # 如果G列不存在或为空，检查I列
                    (self.excel_data.iloc[:, 6].isna() | (self.excel_data.iloc[:, 6] == "")) &
                    (self.excel_data.iloc[:, 8].str.contains(f"/{project_folder_name}/", na=False))  # I列包含项目路径
                )
            )
            return self.excel_data[mask]
        return pd.DataFrame()
    
    def filter_by_type_keywords(self, data, markdown_info):
        """根据type和keywords过滤数据"""
        if data.empty:
            return data
            
        # 根据type过滤B列
        target_type = markdown_info.get("type", "")
        if target_type:
            data = data[data.iloc[:, 1] == target_type]
            
        # 根据keywords过滤C列
        keywords = markdown_info.get("keywords", [])
        if keywords:
            mask = data.iloc[:, 2].isin(keywords)
            data = data[mask]
            
        return data
    
    def sort_data_by_keywords_and_platform(self, data, markdown_info):
        """根据keywords顺序和Common_Platform排序数据"""
        if data.empty:
            return data
            
        keywords = markdown_info.get("keywords", [])
        
        def get_sort_key(row):
            """获取排序键值"""
            # 获取列名列表
            columns = list(data.columns)
            series_name = str(row[columns[0]])  # 第一列：产品系列
            keyword_value = str(row[columns[2]])  # 第三列：name/keywords
            
            # Common_Platform放在最后
            if series_name == "Common_Platform":
                return (999, 999)
            
            # 按照keywords的顺序排序
            try:
                keyword_index = keywords.index(keyword_value)
                return (0, keyword_index)
            except ValueError:
                # 如果keyword不在keywords中，放在最后
                return (1, 999)
        
        # 转换为列表进行排序
        data_list = data.to_dict('records')
        data_list.sort(key=get_sort_key)
        
        # 转换回DataFrame
        return pd.DataFrame(data_list)
    
    def convert_filename_to_page_id(self, filename):
        """将文件名转换为page id格式"""
        parts = filename.split('-', 1)
        if len(parts) > 1:
            return parts[1].lower().replace('_', '_')
        return filename.lower()
    
    def get_file_type(self, file_url):
        """根据文件URL判断文件类型"""
        if not file_url:
            return "other"
        
        # 转换为小写并去除查询参数
        clean_url = file_url.lower().split('?')[0]
        
        # 检查是否为PDF文件
        if clean_url.endswith('.pdf'):
            return "pdf"
        
        # 检查是否为PACK文件
        elif clean_url.endswith('.pack'):
            return "pack"
        
        # 其他所有文件类型
        else:
            return "other"
    
    def get_file_icon(self, file_type):
        """根据文件类型获取图标信息"""
        icon_configs = {
            "pdf": {
                "src": "./pdf.png",
                "alt": "PDF",
                "class": "file-icon-pdf"
            },
            "pack": {
                "src": "./pack.png",
                "alt": "PACK",
                "class": "file-icon-pack"
            },
            "other": {
                "src": "./files.png",
                "alt": "File",
                "class": "file-icon-other"
            }
        }
        
        return icon_configs.get(file_type, icon_configs["other"])
    
    def copy_assets_to_output(self):
        """将template/assets下的图片复制到输出目录的assets目录"""
        template_assets_dir = self.work_dir / "template" / "assets"
        output_assets_dir = self.output_folder / "doxygen" / "main" / "assets"
        
        if not template_assets_dir.exists():
            return False
        
        # 确保输出assets目录存在
        output_assets_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制图片文件
        image_files = ["pdf.png", "pack.png", "files.png"]
        copied_count = 0
        
        for image_file in image_files:
            src_file = template_assets_dir / image_file
            dst_file = output_assets_dir / image_file
            
            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                copied_count += 1
        
        return copied_count > 0
    
    def copy_assets_to_project(self, project_path: Path):
        """将template/assets下的图片复制到项目的assets目录"""
        template_assets_dir = self.work_dir / "template" / "assets"
        project_assets_dir = project_path / "doxygen" / "main" / "assets"
        
        if not template_assets_dir.exists():
            return False
        
        # 确保项目assets目录存在
        project_assets_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制图片文件
        image_files = ["pdf.png", "pack.png", "files.png"]
        copied_count = 0
        
        for image_file in image_files:
            src_file = template_assets_dir / image_file
            dst_file = project_assets_dir / image_file
            
            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                copied_count += 1
        
        return copied_count > 0
    
    def generate_markdown_content(self, data, markdown_info, language, base_config):
        """生成Markdown内容"""
        lang_info = markdown_info.get(language, {})
        title = lang_info.get("title", "")
        overview = lang_info.get("overview", "")
        
        html_title = "Overview" if language == "en" else "概览"
        file_list_title = "File List" if language == "en" else "文件列表"
        
        # 获取下载URL前缀
        base_url = base_config.get("Md_DownloadUrl", "")
        
        content = f"""\\page {self.convert_filename_to_page_id(markdown_info['filename'])} {title}

## {html_title}

{overview}

## {file_list_title}
\\htmlonly
<div class="file-list">

"""
        
        # 统计链接获取情况
        g_column_count = 0
        i_column_count = 0
        
        # 生成文件列表
        if data.empty:
            # 没有数据时的提示信息
            if language == "cn":
                content += """<p style="text-align: center; color: #666; font-style: italic;">暂无中文文档</p>"""
            else:
                content += """<p style="text-align: center; color: #666; font-style: italic;">No English Document</p>"""
        else:
            # 有数据时生成表格
            content += """<table class="file-table">
"""
            valid_rows = 0  # 记录有效的行数
            
            for _, row in data.iterrows():
                file_title = str(row.iloc[3]) if len(row) > 3 else ""
                file_name = str(row.iloc[2]) if len(row) > 2 else ""  # C列：name值
                file_desc = str(row.iloc[4]) if len(row) > 4 else ""
                file_version = str(row.iloc[5]) if len(row) > 5 else ""
                
                # 获取文件链接 - 根据文件类型和语言调整获取逻辑
                file_href = ""
                
                # 获取G列和I列的值
                g_column_value = str(row.iloc[6]) if len(row) > 6 and pd.notna(row.iloc[6]) else ""
                i_column_value = str(row.iloc[8]) if len(row) > 8 and pd.notna(row.iloc[8]) else ""
                
                # 统一判断文件类型（优先使用G列，G列没有就用I列）
                if g_column_value and g_column_value != "nan":
                    # 优先从G列读取链接判断文件类型
                    if g_column_value.startswith('/'):
                        temp_full_href = base_url + g_column_value
                    else:
                        temp_full_href = g_column_value
                    file_type = self.get_file_type(temp_full_href)
                elif i_column_value and i_column_value != "nan":
                    # G列没有，从I列读取链接判断文件类型
                    if i_column_value.startswith('/'):
                        temp_full_href = base_url + i_column_value
                    else:
                        temp_full_href = i_column_value
                    file_type = self.get_file_type(temp_full_href)
                else:
                    # 如果G列和I列都没有链接，才根据文件名判断
                    if file_name.lower().endswith('.pdf'):
                        file_type = "pdf"
                    elif file_name.lower().endswith('.pack'):
                        file_type = "pack"
                    else:
                        file_type = "other"
                
                # 根据文件类型和语言获取链接
                if file_type == "pdf":
                    # PDF文件：严格按照语言取链接，如果为空则不生成可点击链接
                    if language == "cn":
                        # 中文PDF只能从G列取
                        if g_column_value and g_column_value != "nan":
                            file_href = g_column_value
                            g_column_count += 1
                        else:
                            # G列为空，不生成可点击链接
                            file_href = ""
                    else:  # en
                        # 英文PDF只能从I列取
                        if i_column_value and i_column_value != "nan":
                            file_href = i_column_value
                            i_column_count += 1
                        else:
                            # I列为空，不生成可点击链接
                            file_href = ""
                else:
                    # 非PDF文件：直接使用G列或I列的内容，不区分语言
                    if g_column_value and g_column_value != "nan":
                        file_href = g_column_value
                        g_column_count += 1
                    elif i_column_value and i_column_value != "nan":
                        file_href = i_column_value
                        i_column_count += 1
                    else:
                        file_href = ""
                
                # 构建完整链接（用于HTML生成）
                if file_href and file_href != "nan":
                    if file_href.startswith('/'):
                        full_href = base_url + file_href
                    else:
                        full_href = file_href
                else:
                    full_href = ""
                
                icon_info = self.get_file_icon(file_type)
                
                # 根据是否有链接决定生成链接还是纯文本
                if full_href and full_href != "nan":
                    # 有链接，生成可点击的链接
                    title_cell = f'<a href="{full_href}" target="_blank" class="file-link file-link-{file_type}">{file_title}</a>'
                else:
                    # 无链接，生成不可点击的纯文本
                    title_cell = f'<span class="file-title-no-link">{file_title}</span>'
                
                # 根据是否有链接决定行的CSS类
                row_class = f"file-row file-type-{file_type}"
                if not full_href or full_href == "nan":
                    row_class += " no-link"
                
                content += f"""  <tr class="{row_class}">
    <td class="file-icon-cell">
      <img src="{icon_info['src']}" alt="{icon_info['alt']}" class="file-icon {icon_info['class']}">
    </td>
    <td class="file-title-cell">
      {title_cell}
    </td>
    <td class="file-name-cell">{file_name}</td>
    <td class="file-desc-cell">{file_desc}</td>
    <td class="file-version-cell">{file_version}</td>
  </tr>
"""
                valid_rows += 1
            
            # 如果没有有效的行，显示暂无文档提示
            if valid_rows == 0:
                content += """</table>
<p style="text-align: center; color: #666; font-style: italic;">"""
                if language == "cn":
                    content += "暂无中文文档"
                else:
                    content += "No English Document"
                content += """</p>"""
            else:
                content += """</table>
"""
        
        content += """

</div>

<style>
.file-type-pdf .file-icon-pdf {
    filter: hue-rotate(0deg);
}

.file-type-pack .file-icon-pack {
    filter: hue-rotate(240deg);
}

.file-type-other .file-icon-other {
    filter: hue-rotate(180deg);
}

.file-link-pdf {
    color: #d32f2f !important;
    font-weight: bold;
}

.file-link-pack {
    color: #388e3c !important;
    font-weight: bold;
}

.file-link-other {
    color: #7b1fa2 !important;
    font-weight: bold;
}

.file-type-pdf {
    background-color: rgba(211, 47, 47, 0.05);
}

.file-type-pack {
    background-color: rgba(56, 142, 60, 0.05);
}

.file-type-other {
    background-color: rgba(123, 31, 162, 0.05);
}

.file-row:hover {
    background-color: rgba(0, 0, 0, 0.05) !important;
    transform: translateX(2px);
    transition: all 0.2s ease;
}

.file-title-no-link {
    color: #999 !important;
    font-style: italic;
    cursor: not-allowed;
}

.file-row.no-link:hover {
    transform: none;
}
</style>

\\endhtmlonly
"""
        return content, g_column_count, i_column_count
    
    def ensure_output_dir(self, module_key: str, language: str) -> Path:
        """确保输出目录存在"""
        output_dir = self.output_folder / "doxygen" / "main" / "modules" / language
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def ensure_project_output_dir(self, project_path: Path, module_key: str, language: str) -> Path:
        """确保项目输出目录存在"""
        output_dir = project_path / "doxygen" / "main" / "modules" / language
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def generate_modules(self):
        """生成模块文件"""
        try:
            # 根据芯片系列过滤数据
            filtered_data = self.filter_by_chip_series(self.project_name)
            
            # 复制资源文件到输出目录
            self.copy_assets_to_output()
            
            # 从基础配置中获取Markdown信息
            markdown_info = self.base_config.get("MarkDown_Info", {})
            
            # 为每个模块生成文件
            for module_key, module_info in markdown_info.items():
                # 添加filename字段用于page id生成
                module_info['filename'] = module_key
                
                # 进一步过滤数据
                module_data = self.filter_by_type_keywords(filtered_data, module_info)
                
                # 对数据进行排序
                module_data = self.sort_data_by_keywords_and_platform(module_data, module_info)
                
                # 生成英文和中文版本
                for lang in ['en', 'cn']:
                    # 确保输出目录存在
                    output_dir = self.ensure_output_dir(module_key, lang)
                    output_file = output_dir / f"{module_key}.md"
                    
                    # 生成内容
                    content, g_count, i_count = self.generate_markdown_content(module_data, module_info, lang, self.base_config)
                    
                    # 写入文件
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            return True
            
        except Exception as e:
            Logger.error(f"生成模块文件时出错: {e}")
            return False
    
    def generate_project_modules(self, project_name: str, project_path: Path):
        """为指定项目生成模块文件"""
        try:
            # 从项目路径提取项目文件夹名称
            project_folder_name = project_path.name
            
            # 复制资源文件到项目目录
            self.copy_assets_to_project(project_path)
            
            # 使用路径匹配逻辑，在G列中查找项目路径
            filtered_data = self.filter_by_project_path(project_folder_name)
            
            markdown_info = self.base_config.get("MarkDown_Info", {})
            
            # 为每个模块生成文件
            for module_key, module_info in markdown_info.items():
                # 添加filename字段用于page id生成
                module_info['filename'] = module_key
                
                # 进一步过滤数据
                module_data = self.filter_by_type_keywords(filtered_data, module_info)
                
                # 对数据进行排序
                module_data = self.sort_data_by_keywords_and_platform(module_data, module_info)
                
                # 统计链接获取情况
                total_g_column_count = 0
                total_i_column_count = 0
                
                # 生成英文和中文版本
                for lang in ['en', 'cn']:
                    # 确保项目特定的输出目录存在
                    output_dir = self.ensure_project_output_dir(project_path, module_key, lang)
                    output_file = output_dir / f"{module_key}.md"
                    
                    # 生成内容
                    content, g_count, i_count = self.generate_markdown_content(module_data, module_info, lang, self.base_config)
                    
                    # 累计统计
                    total_g_column_count += g_count
                    total_i_column_count += i_count
                    
                    # 写入文件
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            return True
            
        except Exception as e:
            Logger.error(f"为项目 {project_name} 生成模块文件时出错: {e}")
            return False
    
    def run(self):
        """运行生成器"""
        try:
            # 加载Excel数据
            self.load_excel()
            
            # 加载基础配置
            self.load_base_config()
            
            # 生成模块文件
            self.generate_modules()
            
            return True
            
        except Exception as e:
            Logger.error(f"运行生成器时出错: {e}")
            return False


@timing_decorator
def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python generate_modules.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        # 解析芯片配置JSON
        from common_utils import ConfigManager
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建生成器并执行
        generator = DoxygenGenerator(output_folder, chip_config)
        
        if not generator.run():
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
