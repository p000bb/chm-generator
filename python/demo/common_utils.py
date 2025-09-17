#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
公共工具模块
提供其他脚本共用的功能：
1. 读取配置文件
2. 查找激活项目路径
3. 其他通用工具方法
"""

import os
import json
import datetime
import hashlib
from pathlib import Path

def get_work_dir():
    """
    获取工作目录（脚本所在目录的父目录）
    
    返回：
    - str: 工作目录的绝对路径
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)

def load_config(config_path="config/base.json"):
    """
    加载配置文件，获取激活的项目列表
    
    参数：
    - config_path: 配置文件路径，相对于工作目录
    
    返回：
    - list: 激活的项目名称列表
    """
    work_dir = get_work_dir()
    full_config_path = os.path.join(work_dir, config_path)
    
    try:
        with open(full_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            activated = config.get('Activate', [])
            print(f"[INFO] 从配置文件读取到 {len(activated)} 个激活项目")
            return activated
    except Exception as e:
        print(f"[ERROR] 加载配置文件失败: {e}")
        return []

def find_project_path(project_name):
    """
    根据项目名称查找对应的项目目录路径
    
    参数：
    - project_name: 项目名称（如 N32H48xxx_V1.1.0）
    
    返回：
    - str: 项目目录的绝对路径，如果找不到返回None
    """
    work_dir = get_work_dir()
    projects_dir = os.path.join(work_dir, "projects")
    
    if not os.path.exists(projects_dir):
        print(f"[ERROR] projects目录不存在: {projects_dir}")
        return None
    
    # 遍历projects下的所有子目录
    for company_dir in os.listdir(projects_dir):
        company_path = os.path.join(projects_dir, company_dir)
        if not os.path.isdir(company_path):
            continue
        
        # 在company目录下查找匹配的项目
        for project_dir in os.listdir(company_path):
            project_path = os.path.join(company_path, project_dir)
            if not os.path.isdir(project_path):
                continue
            
            # 检查项目名称是否匹配
            if project_name in project_dir or project_dir in project_name:
                print(f"[INFO] 找到项目 {project_name} 的目录: {project_path}")
                return project_path
    
    print(f"[ERROR] 未找到项目 {project_name} 对应的目录")
    return None

def generate_8char_hash(text: str) -> str:
    """
    生成8位hash值
    
    参数：
    - text: 输入文本
    
    返回：
    - str: 8位hash值
    """
    try:
        # 使用MD5生成hash，然后取前8位
        hash_object = hashlib.md5(text.encode('utf-8'))
        hash_hex = hash_object.hexdigest()
        return hash_hex[:8]
    except Exception as e:
        print(f"[WARN] 生成hash失败: {e}")
        # 降级方案：使用简单的字符串处理
        return str(abs(hash(text)) % 100000000).zfill(8)

def save_filename_mapping(project_path: str, hash_name: str, original_name: str, file_path: str):
    """
    保存文件名映射关系
    
    参数：
    - project_path: 项目路径
    - hash_name: hash文件名
    - original_name: 原始文件名
    - file_path: 文件路径
    """
    try:
        mapping_file = Path(project_path) / "output" / "pdf" / "filename_mapping.json"
        mapping_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 读取现有映射
        mappings = {}
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
            except Exception as e:
                print(f"[WARN] 读取映射文件失败: {e}")
        
        # 添加新映射
        mappings[hash_name] = {
            "original_name": original_name,
            "file_path": file_path,
            "hash_name": hash_name,
            "created_time": datetime.datetime.now().isoformat()
        }
        
        # 保存映射文件
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 保存文件名映射: {hash_name} -> {original_name}")
        
    except Exception as e:
        print(f"[ERROR] 保存文件名映射失败: {e}")

def get_hash_name_for_pdf(project_path: str, pdf_name: str) -> str:
    """
    根据PDF名称获取对应的hash文件名
    
    参数：
    - project_path: 项目路径
    - pdf_name: PDF文件名（不含扩展名）
    
    返回：
    - str: hash文件名，如果找不到返回None
    """
    try:
        mapping_file = Path(project_path) / "output" / "pdf" / "filename_mapping.json"
        if not mapping_file.exists():
            return None
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mappings = json.load(f)
        
        # 查找匹配的映射
        for hash_name, mapping in mappings.items():
            if mapping.get("original_name") == pdf_name:
                return hash_name
        
        return None
        
    except Exception as e:
        print(f"[ERROR] 获取hash文件名失败: {e}")
        return None

def get_original_name_for_hash(project_path: str, hash_name: str) -> str:
    """
    根据hash文件名获取原始文件名
    
    参数：
    - project_path: 项目路径
    - hash_name: hash文件名
    
    返回：
    - str: 原始文件名，如果找不到返回None
    """
    try:
        mapping_file = Path(project_path) / "output" / "pdf" / "filename_mapping.json"
        if not mapping_file.exists():
            return None
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mappings = json.load(f)
        
        if hash_name in mappings:
            return mappings[hash_name].get("original_name")
        
        return None
        
    except Exception as e:
        print(f"[ERROR] 获取原始文件名失败: {e}")
        return None

def get_activated_project_paths():
    """
    获取所有激活项目的路径
    
    如果Activate为空，则返回所有项目
    
    返回：
    - dict: {项目名称: 项目路径} 的字典
    """
    activated_projects = load_config()
    project_paths = {}
    
    # 如果Activate为空，扫描所有项目
    if not activated_projects:
        print("[INFO] Activate为空，扫描所有项目...")
        work_dir = get_work_dir()
        projects_dir = os.path.join(work_dir, "projects")
        
        if not os.path.exists(projects_dir):
            print(f"[ERROR] projects目录不存在: {projects_dir}")
            return project_paths
        
        # 遍历projects下的所有子目录
        for company_dir in os.listdir(projects_dir):
            company_path = os.path.join(projects_dir, company_dir)
            if not os.path.isdir(company_path):
                continue
            
            # 在company目录下查找项目
            for project_dir in os.listdir(company_path):
                project_path = os.path.join(company_path, project_dir)
                if not os.path.isdir(project_path):
                    continue
                
                project_paths[project_dir] = project_path
                print(f"[INFO] 找到项目: {company_dir}/{project_dir}")
    else:
        # 处理指定的激活项目
        for project_name in activated_projects:
            project_path = find_project_path(project_name)
            if project_path:
                project_paths[project_name] = project_path
    
    return project_paths

def has_source_files(directory):
    """
    检查目录是否包含源代码文件
    
    参数：
    - directory: 要检查的目录路径
    
    返回：
    - bool: 是否包含源代码文件
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.h', '.c', '.cpp', '.hpp')):
                return True
    return False

def extract_version_from_name(name):
    """
    从项目名称中提取版本号
    
    参数：
    - name: 项目名称
    
    返回：
    - str: 版本号
    """
    import re
    # 匹配版本号模式，如 .0.7.0, .1.1.0 等
    version_pattern = r'\.(\d+\.\d+\.\d+)$'
    match = re.search(version_pattern, name)
    if match:
        return match.group(1)
    
    # 如果没有找到版本号，返回默认版本
    return "1.0.0"

# ==================== 执行状态管理功能 ====================

def get_execution_marker_path(project_path):
    """
    获取项目执行状态标识文件路径
    
    参数：
    - project_path: 项目路径
    
    返回：
    - Path: 标识文件路径（放在json目录下）
    """
    return Path(project_path) / "json" / "execution_status.json"

def get_required_scripts():
    """
    获取需要参与执行状态统计的脚本列表
    
    返回：
    - list: 脚本名称列表（不含.py扩展名）
    """
    return [
        "docs_gen_config",
        "docs_gen_doxyfile", 
        "docs_gen_doxygen",
        "docs_gen_hhc",
        "docs_gen_hhp",
        "docs_gen_pdfhtml",
        "docs_gen_template_hhc",
        "docs_main_doxygen",
        "generate_modules"
    ]

def get_execution_order():
    """
    获取脚本执行顺序（依赖关系）
    
    返回：
    - dict: {脚本名称: [前置脚本列表]}
    """
    return {
        "docs_gen_main_html": [],  # 无依赖
        "docs_main_doxygen": ["docs_gen_main_html"],
        "generate_modules": ["docs_main_doxygen"],
        "docs_gen_doxyfile": ["generate_modules"],
        "docs_gen_doxygen": ["docs_gen_doxyfile"],
        "docs_gen_examples": ["docs_gen_doxygen"],
        "docs_gen_examples_overview": ["docs_gen_examples"],
        "docs_gen_examples_description": ["docs_gen_examples_overview"],
        "docs_gen_template_hhc": ["docs_gen_examples_description"],
        "docs_gen_hhc": ["docs_gen_template_hhc"],
        "docs_gen_hhp": ["docs_gen_hhc"],
        # 这两个脚本不依赖任何脚本，只需要最后判断是否执行
        "docs_gen_config": [],
        "docs_gen_pdfhtml": []
    }

def can_execute_script(script_name, project_path):
    """
    检查指定脚本是否可以执行（检查前置依赖）
    
    参数：
    - script_name: 脚本名称（不含.py扩展名）
    - project_path: 项目路径
    
    返回：
    - bool: 是否可以执行
    """
    try:
        execution_order = get_execution_order()
        
        if script_name not in execution_order:
            print(f"[WARN] 未知脚本: {script_name}")
            return False
        
        # 获取前置依赖
        dependencies = execution_order[script_name]
        
        # 如果没有依赖，直接返回True
        if not dependencies:
            return True
        
        # 检查前置依赖是否都已执行
        marker_path = get_execution_marker_path(project_path)
        
        if not marker_path.exists():
            print(f"[INFO] 项目 {Path(project_path).name} 未找到执行状态文件，无法检查依赖")
            return False
        
        with open(marker_path, 'r', encoding='utf-8') as f:
            try:
                status = json.load(f)
                executed_scripts = status.get("executed_scripts", [])
            except json.JSONDecodeError:
                print(f"[ERROR] 项目 {Path(project_path).name} 执行状态文件格式错误")
                return False
        
        # 检查所有依赖是否都已执行
        missing_dependencies = [dep for dep in dependencies if dep not in executed_scripts]
        
        if missing_dependencies:
            print(f"[INFO] 脚本 {script_name} 的前置依赖未完成: {', '.join(missing_dependencies)}")
            return False
        
        print(f"[INFO] 脚本 {script_name} 的前置依赖检查通过")
        return True
        
    except Exception as e:
        print(f"[ERROR] 检查脚本执行条件时出错: {e}")
        return False

def check_final_scripts_executed(project_path):
    """
    检查最终脚本（不依赖其他脚本的脚本）是否已执行
    
    参数：
    - project_path: 项目路径
    
    返回：
    - dict: 检查结果
    """
    try:
        execution_order = get_execution_order()
        final_scripts = [script for script, deps in execution_order.items() if not deps]
        
        marker_path = get_execution_marker_path(project_path)
        
        if not marker_path.exists():
            return {
                "final_scripts": final_scripts,
                "executed_final_scripts": [],
                "missing_final_scripts": final_scripts,
                "all_executed": False
            }
        
        with open(marker_path, 'r', encoding='utf-8') as f:
            try:
                status = json.load(f)
                executed_scripts = status.get("executed_scripts", [])
            except json.JSONDecodeError:
                return {
                    "final_scripts": final_scripts,
                    "executed_final_scripts": [],
                    "missing_final_scripts": final_scripts,
                    "all_executed": False
                }
        
        executed_final_scripts = [script for script in final_scripts if script in executed_scripts]
        missing_final_scripts = [script for script in final_scripts if script not in executed_scripts]
        
        return {
            "final_scripts": final_scripts,
            "executed_final_scripts": executed_final_scripts,
            "missing_final_scripts": missing_final_scripts,
            "all_executed": len(missing_final_scripts) == 0
        }
        
    except Exception as e:
        print(f"[ERROR] 检查最终脚本执行状态时出错: {e}")
        return {
            "final_scripts": [],
            "executed_final_scripts": [],
            "missing_final_scripts": [],
            "all_executed": False
        }

def mark_script_executed(script_name, project_path=None):
    """
    标记脚本已执行
    
    参数：
    - script_name: 脚本名称（不含.py扩展名）
    - project_path: 项目路径，如果为None则处理所有激活项目
    
    返回：
    - bool: 是否成功标记
    """
    try:
        if project_path:
            # 标记单个项目
            return _mark_single_project(script_name, project_path)
        else:
            # 标记所有激活项目
            activated_projects = get_activated_project_paths()
            success_count = 0
            
            for proj_name, proj_path in activated_projects.items():
                if _mark_single_project(script_name, proj_path):
                    success_count += 1
            
            print(f"[INFO] 成功标记 {success_count}/{len(activated_projects)} 个项目")
            return success_count > 0
            
    except Exception as e:
        print(f"[ERROR] 标记脚本执行状态失败: {e}")
        return False

def _mark_single_project(script_name, project_path):
    """为单个项目标记脚本执行状态"""
    try:
        marker_path = get_execution_marker_path(project_path)
        
        # 读取现有状态
        if marker_path.exists():
            with open(marker_path, 'r', encoding='utf-8') as f:
                try:
                    status = json.load(f)
                except json.JSONDecodeError:
                    status = {"executed_scripts": [], "last_updated": ""}
        else:
            status = {"executed_scripts": [], "last_updated": ""}
        
        # 添加脚本标记
        if script_name not in status["executed_scripts"]:
            status["executed_scripts"].append(script_name)
            status["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 计算统计信息
        required_scripts = get_required_scripts()
        status["total_required"] = len(required_scripts)
        status["executed_count"] = len(status["executed_scripts"])
        status["is_complete"] = status["executed_count"] >= status["total_required"]
        
        # 写入标识文件
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        with open(marker_path, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 项目 {Path(project_path).name} 标记脚本 {script_name} 已执行")
        return True
        
    except Exception as e:
        print(f"[ERROR] 标记项目 {Path(project_path).name} 失败: {e}")
        return False

def get_project_execution_status(project_path):
    """
    获取项目的执行状态
    
    参数：
    - project_path: 项目路径
    
    返回：
    - dict: 执行状态信息，如果文件不存在返回None
    """
    try:
        marker_path = get_execution_marker_path(project_path)
        
        if not marker_path.exists():
            return None
        
        with open(marker_path, 'r', encoding='utf-8') as f:
            status = json.load(f)
        
        return status
        
    except Exception as e:
        print(f"[ERROR] 读取项目 {Path(project_path).name} 执行状态失败: {e}")
        return None

def check_all_projects_status():
    """
    检查所有激活项目的执行状态
    
    返回：
    - dict: 状态汇总信息
    """
    activated_projects = get_activated_project_paths()
    status_summary = {
        "total_projects": len(activated_projects),
        "completed_projects": 0,
        "incomplete_projects": 0,
        "project_details": {},
        "overall_status": "unknown"
    }
    
    for proj_name, proj_path in activated_projects.items():
        status = get_project_execution_status(proj_path)
        if status:
            status_summary["project_details"][proj_name] = status
            if status.get("is_complete", False):
                status_summary["completed_projects"] += 1
            else:
                status_summary["incomplete_projects"] += 1
        else:
            status_summary["project_details"][proj_name] = {"status": "no_marker_file"}
            status_summary["incomplete_projects"] += 1
    
    # 判断整体状态
    if status_summary["completed_projects"] == status_summary["total_projects"]:
        status_summary["overall_status"] = "all_completed"
    elif status_summary["completed_projects"] > 0:
        status_summary["overall_status"] = "partially_completed"
    else:
        status_summary["overall_status"] = "none_completed"
    
    return status_summary

def can_execute_generate_chm():
    """
    检查是否可以执行generate_chm_fixed.py
    
    返回：
    - bool: 是否可以执行
    """
    status_summary = check_all_projects_status()
    return status_summary["overall_status"] == "all_completed"

#---------------------------------------------------------------------------
# 路径映射相关函数
#---------------------------------------------------------------------------

class HashPathMapping:
    """
    Hash路径映射管理器
    用于管理原始路径和8位hash路径的对应关系
    """
    
    def __init__(self, project_path):
        """
        初始化路径映射管理器
        
        参数：
        - project_path: 项目根目录路径
        """
        self.project_path = project_path
        self.json_dir = os.path.join(project_path, "json")
        self.mapping_file = os.path.join(self.json_dir, "path_mapping.json")
        self.ensure_json_dir()
        self.mappings = self.load_or_create_mappings()
    
    def ensure_json_dir(self):
        """确保json目录存在"""
        os.makedirs(self.json_dir, exist_ok=True)
    
    def load_or_create_mappings(self):
        """加载或创建映射表"""
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("mappings", [])
            except Exception as e:
                print(f"[WARN] 加载映射表失败: {e}")
                return self.create_empty_mappings()
        else:
            return self.create_empty_mappings()
    
    def create_empty_mappings(self):
        """创建空的映射表结构"""
        return []
    
    def generate_hash_name(self, original_name):
        """
        生成8位hash名称
        
        参数：
        - original_name: 原始名称
        
        返回：
        - str: 8位hash名称
        """
        import hashlib
        # 生成MD5 hash值
        hash_value = hashlib.md5(original_name.encode()).hexdigest()
        # 取前8位
        short_hash = hash_value[:8]
        return short_hash
    
    def get_or_create_hash_path(self, original_path):
        """
        获取或创建hash路径
        
        参数：
        - original_path: 原始路径
        
        返回：
        - str: hash路径
        """
        # 检查是否已有映射
        for mapping in self.mappings:
            if mapping["original_path"] == original_path:
                return mapping["hash_path"]
        
        # 创建新的hash路径
        original_name = os.path.basename(original_path)
        hash_name = self.generate_hash_name(original_name)
        
        # 构建hash路径
        parent_dir = os.path.dirname(original_path)
        hash_path = f"{parent_dir}/{hash_name}"
        
        # 添加到映射表
        self.add_mapping(original_path, hash_path)
        
        return hash_path
    
    def add_mapping(self, original_path, hash_path):
        """
        添加路径映射
        
        参数：
        - original_path: 原始路径
        - hash_path: hash路径
        """
        mapping = {
            "original_path": original_path,
            "hash_path": hash_path,
            "original_name": os.path.basename(original_path),
            "hash_name": os.path.basename(hash_path),
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # 检查是否已存在
        for i, existing_mapping in enumerate(self.mappings):
            if existing_mapping["original_path"] == original_path:
                self.mappings[i] = mapping
                break
        else:
            self.mappings.append(mapping)
        
        self.save_mappings()
    
    def save_mappings(self):
        """保存映射表到文件"""
        try:
            data = {
                "project_name": os.path.basename(self.project_path),
                "mappings": self.mappings,
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"[INFO] 路径映射表已保存: {self.mapping_file}")
            
        except Exception as e:
            print(f"[ERROR] 保存路径映射表失败: {e}")
    
    def get_original_path(self, hash_path):
        """
        通过hash路径获取原始路径
        
        参数：
        - hash_path: hash路径
        
        返回：
        - str: 原始路径，如果未找到返回None
        """
        for mapping in self.mappings:
            if mapping["hash_path"] == hash_path:
                return mapping["original_path"]
        return None
    
    def get_hash_path(self, original_path):
        """
        通过原始路径获取hash路径
        
        参数：
        - original_path: 原始路径
        
        返回：
        - str: hash路径，如果未找到返回原始路径
        """
        for mapping in self.mappings:
            if mapping["original_path"] == original_path:
                return mapping["hash_path"]
        return original_path

def get_hash_path_mapping(project_path):
    """
    获取项目的hash路径映射管理器
    
    参数：
    - project_path: 项目路径
    
    返回：
    - HashPathMapping: 路径映射管理器实例
    """
    return HashPathMapping(project_path)

def get_hash_path(project_path, original_path):
    """
    获取hash路径的便捷函数
    
    参数：
    - project_path: 项目路径
    - original_path: 原始路径
    
    返回：
    - str: hash路径
    """
    mapping = get_hash_path_mapping(project_path)
    return mapping.get_or_create_hash_path(original_path)

def get_original_path(project_path, hash_path):
    """
    获取原始路径的便捷函数
    
    参数：
    - project_path: 项目路径
    - hash_path: hash路径
    
    返回：
    - str: 原始路径，如果未找到返回None
    """
    mapping = get_hash_path_mapping(project_path)
    return mapping.get_original_path(hash_path)
