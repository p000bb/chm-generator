#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_gen_doxyfile.py - Doxyfile生成脚本
功能：在input_folder目录下扫描源代码文件，生成对应的Doxyfile
"""

import os
import sys
import json
import shutil
import re
import hashlib
import datetime
from pathlib import Path


class HashPathMapping:
    """Hash路径映射管理器"""
    
    def __init__(self, project_path):
        """初始化路径映射管理器"""
        self.project_path = project_path
        self.json_dir = project_path / "json"
        self.mapping_file = self.json_dir / "path_mapping.json"
        self.ensure_json_dir()
        self.mappings = self.load_or_create_mappings()
    
    def ensure_json_dir(self):
        """确保json目录存在"""
        self.json_dir.mkdir(parents=True, exist_ok=True)
    
    def load_or_create_mappings(self):
        """加载或创建映射表"""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("mappings", [])
            except Exception as e:
                return self.create_empty_mappings()
        else:
            return self.create_empty_mappings()
    
    def create_empty_mappings(self):
        """创建空的映射表结构"""
        return []
    
    def generate_hash_name(self, original_name):
        """生成8位hash名称"""
        hash_value = hashlib.md5(original_name.encode()).hexdigest()
        return hash_value[:8]
    
    def get_or_create_hash_path(self, original_path):
        """获取或创建hash路径"""
        # 查找现有映射
        for mapping in self.mappings:
            if mapping["original_path"] == original_path:
                return mapping["hash_path"]
        
        # 创建新的hash路径
        hash_path = self.generate_hash_name(original_path)
        self.add_mapping(original_path, hash_path)
        return hash_path
    
    def add_mapping(self, original_path, hash_path):
        """添加路径映射"""
        mapping = {
            "original_path": original_path,
            "hash_path": hash_path,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # 检查是否已存在
        for i, existing in enumerate(self.mappings):
            if existing["original_path"] == original_path:
                self.mappings[i] = mapping
                break
        else:
            self.mappings.append(mapping)
        
        self.save_mappings()
    
    def save_mappings(self):
        """保存映射表到文件"""
        try:
            data = {
                "project_name": self.project_path.name,
                "mappings": self.mappings,
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            pass


class DoxyfileGenerator:
    """Doxyfile生成器类"""
    
    def __init__(self, input_folder, output_folder, chip_config):
        """初始化Doxyfile生成器"""
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.chip_config = chip_config
        self.work_dir = Path(__file__).parent.parent.parent
        self.template_path = self.work_dir / "template" / "Doxyfile.template"
        
        # 从芯片配置中获取项目信息
        self.project_name = chip_config.get('chipName', '')
        self.project_version = chip_config.get('chipVersion', '')
        
        # 初始化hash路径映射管理器
        self.hash_mapping = HashPathMapping(self.output_folder)
        
    def load_template(self):
        """加载Doxyfile模板"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"[ERROR] 加载模板失败: {e}")
            return None
    
    
    def find_sub_projects(self):
        """在input_folder目录下查找需要生成Doxyfile的子项目"""
        sub_projects = []
        
        if not self.input_folder.exists():
            print(f"[ERROR] 输入目录不存在: {self.input_folder}")
            return sub_projects
        
        # 只扫描第一层和第二层目录，不递归
        for first_level in os.listdir(self.input_folder):
            first_level_path = self.input_folder / first_level
            if not first_level_path.is_dir() or first_level == 'doxygen':
                continue
            
            # 扫描第二层目录
            for second_level in os.listdir(first_level_path):
                second_level_path = first_level_path / second_level
                if not second_level_path.is_dir():
                    continue
                
                # 检查第二层目录是否包含源代码文件或特定目录（深层遍历）
                has_source_files = False
                has_special_dir = False
                source_count = 0
                
                # 递归遍历第二层目录下的所有子目录，查找源代码文件
                def scan_for_source_files(directory):
                    nonlocal has_source_files, has_special_dir, source_count
                    
                    try:
                        if not directory.exists():
                            return
                        
                        for item in directory.iterdir():
                            if item.is_file():
                                # 检查源代码文件
                                if item.suffix.lower() in ['.c', '.cpp', '.h', '.hpp', '.cc', '.cxx', '.hh', '.hxx']:
                                    has_source_files = True
                                    source_count += 1
                            elif item.is_dir():
                                # 检查特定目录名
                                if item.name.lower() in ['firmware', 'middlewares', 'projects', 'src', 'code', 'source', 
                                                       'inc', 'include', 'lib', 'library', 'drivers', 'app', 
                                                       'application', 'components', 'modules', 'hal', 'll']:
                                    has_special_dir = True
                                # 递归遍历子目录
                                scan_for_source_files(item)
                    except (OSError, PermissionError, FileNotFoundError) as e:
                        return
                
                # 开始深层扫描
                scan_for_source_files(second_level_path)
                
                # 如果包含源代码或特定目录，则在此目录生成Doxyfile
                if has_source_files or has_special_dir:
                    # 构建相对路径：第一层/第二层
                    relative_path = f"{first_level}/{second_level}"
                    project_name = second_level
                    
                    # 查找.txt或.md文件作为主页面
                    mainpage_file = None
                    for file in second_level_path.iterdir():
                        if file.is_file() and file.suffix.lower() in ['.txt', '.md']:
                            mainpage_file = f"{relative_path}/{file.name}".replace(os.sep, '/')
                            break
                    
                    # 提取版本号
                    version = self.extract_version_from_name(project_name)
                    
                    sub_projects.append({
                        'name': project_name,
                        'path': str(second_level_path),
                        'relative_path': relative_path,
                        'version': version,
                        'mainpage_file': mainpage_file,
                        'source_files': []
                    })
        
        return sub_projects
    
    def extract_version_from_name(self, name):
        """从项目名称中提取版本号"""
        # 匹配版本号模式：V1.0.0, v1.0.0, 1.0.0, 1.0等
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
    
    def generate_doxyfile(self, template_content, project_info):
        """根据模板生成Doxyfile内容"""
        project_name = project_info['name']
        relative_path = project_info['relative_path']
        project_version = project_info['version']
        
        # 使用hash路径作为输出目录
        hash_path = self.hash_mapping.get_or_create_hash_path(relative_path)
        output_path = f"{self.output_folder}/output/sub/{hash_path}"
        
        # 计算INPUT路径：使用绝对路径
        input_path = str(self.input_folder / relative_path)
        
        # 如果路径包含空格，需要用引号包围
        if ' ' in input_path:
            input_path = f'"{input_path}"'
        
        # 计算到doxygen/main的绝对路径
        main_path = f"{self.output_folder}/doxygen/main"
        
        # 设置USE_MDFILE_AS_MAINPAGE
        use_mdfile = ""
        if project_info.get('mainpage_file'):
            use_mdfile = project_info['mainpage_file']
        
        # 替换模板中的变量
        doxyfile_content = template_content.replace("{Module_Name}", project_name)
        doxyfile_content = doxyfile_content.replace("{Module_Version}", project_version)
        doxyfile_content = doxyfile_content.replace("{OUTPUT_DIRECTORY}", output_path)
        doxyfile_content = doxyfile_content.replace("{INPUT}", input_path)
        doxyfile_content = doxyfile_content.replace("{Relative_Path}", main_path)
        doxyfile_content = doxyfile_content.replace("{USE_MDFILE_AS_MAINPAGE}", use_mdfile)
        doxyfile_content = doxyfile_content.replace("{CHM_FILE}", project_name)
        
        # 添加STRIP_FROM_PATH配置
        strip_from_path = str(self.input_folder) + '/'
        doxyfile_content = doxyfile_content.replace("STRIP_FROM_PATH        =", f"STRIP_FROM_PATH        = {strip_from_path}")
        
        # 修复HTML相关路径，使用绝对路径
        doxyfile_content = doxyfile_content.replace("HTML_HEADER            = {Relative_Path}/header.html", f"HTML_HEADER            = {main_path}/html/header_sub.html")
        doxyfile_content = doxyfile_content.replace("HTML_FOOTER            = {Relative_Path}/footer.html", f"HTML_FOOTER            = {main_path}/html/footer.html")
        doxyfile_content = doxyfile_content.replace("HTML_STYLESHEET        = {Relative_Path}/customdoxygen.css", f"HTML_STYLESHEET        = {main_path}/css/customdoxygen.css")
        doxyfile_content = doxyfile_content.replace("HTML_EXTRA_FILES       = {Relative_Path}/custom_scripts.js", f"HTML_EXTRA_FILES       = {main_path}/js/custom_scripts.js")
        
        # 修复markdown扩展映射问题
        doxyfile_content = doxyfile_content.replace("EXTENSION_MAPPING      = md=markdown", "EXTENSION_MAPPING      = ")
        
        return doxyfile_content
    
    def save_doxyfile(self, content, project_info):
        """保存Doxyfile到输出目录"""
        relative_path = project_info['relative_path']
        hash_path = self.hash_mapping.get_or_create_hash_path(relative_path)
        
        # 构建doxygen目录路径
        doxygen_dir = self.output_folder / "doxygen" / "sub" / hash_path
        
        # 创建目录
        try:
            doxygen_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"[ERROR] 创建目录失败: {e}")
            return False
        
        # 保存Doxyfile
        doxyfile_path = doxygen_dir / "Doxyfile"
        try:
            with open(doxyfile_path, 'w', encoding='utf-8') as f:
                f.write(content)
            # 保存路径映射信息
            mapping_file = doxygen_dir / "path_mapping.txt"
            with open(mapping_file, 'w', encoding='utf-8') as f:
                f.write(f"Original path: {relative_path}\n")
                f.write(f"Hash path: {hash_path}\n")
                f.write(f"Generated: {doxyfile_path}\n")
                f.write(f"Type: doxygen\n")
                f.write(f"Note: This directory uses hash path format\n")
            
            return True
        except Exception as e:
            print(f"[ERROR] 保存失败: {e}")
            return False
    
    def create_output_directories(self, project_info):
        """创建输出目录"""
        relative_path = project_info['relative_path']
        hash_path = self.hash_mapping.get_or_create_hash_path(relative_path)
        
        # 构建输出目录路径
        output_dir = self.output_folder / "doxygen" / "sub" / hash_path
        
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            return True
        except OSError as e:
            print(f"[ERROR] 创建输出目录失败: {e}")
            return False
    
    def generate(self):
        """生成Doxyfile"""
        try:
            # 加载模板
            template_content = self.load_template()
            if not template_content:
                return False
            
            # 查找子项目
            sub_projects = self.find_sub_projects()
            if not sub_projects:
                return True
            
            # 处理每个子项目
            for project_info in sub_projects:
                # 生成Doxyfile内容
                doxyfile_content = self.generate_doxyfile(template_content, project_info)
                
                # 保存Doxyfile
                if self.save_doxyfile(doxyfile_content, project_info):
                    # 创建输出目录
                    self.create_output_directories(project_info)
            
            return True
        except Exception as e:
            print(f"[ERROR] 生成Doxyfile失败: {e}")
            return False


def main():
    """主函数"""
    try:
        # 检查参数数量
        if len(sys.argv) < 4:
            print("错误: 参数不足，期望3个参数")
            print("用法: python docs_gen_doxyfile.py <input_folder> <output_folder> <chip_config_json>")
            sys.exit(1)
        
        # 获取参数
        input_folder = sys.argv[1]
        output_folder = sys.argv[2]
        chip_config_json = sys.argv[3]
        
        # 解析芯片配置JSON
        try:
            chip_config = json.loads(chip_config_json)
        except json.JSONDecodeError as e:
            print(f"芯片配置JSON解析失败: {e}")
            sys.exit(1)
        
        # 创建生成器并执行
        generator = DoxyfileGenerator(input_folder, output_folder, chip_config)
        
        if generator.generate():
            print("Doxyfile生成完成！")
        else:
            print("Doxyfile生成失败！")
            sys.exit(1)
        
    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
