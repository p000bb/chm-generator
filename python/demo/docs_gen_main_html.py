#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主文档HTML内容生成脚本
功能：为当前激活项目生成doxygen/main目录下的内容
1. 复制template/html目录下的所有内容到项目的doxygen/main目录
2. 修改Doxyfile_en和Doxyfile_zh中的占位符（如{PROJECT_NAME}、{PROJECT_NUMBER}）
3. 从项目名称中提取项目名和版本号
"""

import os
import shutil
import re
from pathlib import Path
from common_utils import get_work_dir, get_activated_project_paths


class MainHtmlGenerator:
    """主文档HTML内容生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.work_dir = get_work_dir()
        self.template_html_dir = Path(self.work_dir) / "template" / "html"
        self.activated_project_paths = get_activated_project_paths()
        self.overwrite_mode = self.get_user_choice()
        
        print("🚀 主文档HTML内容生成器初始化完成")
        print(f"📁 工作目录: {self.work_dir}")
        print(f"📁 模板目录: {self.template_html_dir}")
        print(f"🎯 激活项目数量: {len(self.activated_project_paths)}")
        print(f"🔄 覆盖模式: {'是' if self.overwrite_mode else '否'}")
    
    def get_user_choice(self):
        """
        获取用户选择：是否覆盖已存在的文件
        
        返回：
        - bool: True表示覆盖，False表示跳过
        """
        while True:
            print("\n请选择处理模式：")
            print("1. 跳过已存在的文件（推荐）")
            print("2. 覆盖已存在的文件")
            
            try:
                choice = input("请输入选择 (1 或 2，默认为 1): ").strip()
                
                if not choice:  # 默认选择1
                    choice = "1"
                
                if choice == "1":
                    print("✅ 已选择：跳过已存在的文件")
                    return False
                elif choice == "2":
                    print("⚠️  已选择：覆盖已存在的文件")
                    print("注意：这将覆盖所有已存在的文件！")
                    
                    # 二次确认
                    confirm = input("确认要覆盖吗？(y/N): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        return True
                    else:
                        print("已取消覆盖操作，将使用跳过模式")
                        return False
                else:
                    print("❌ 无效选择，请输入 1 或 2")
                    
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                return False
            except Exception as e:
                print(f"输入错误: {e}，将使用默认模式（跳过）")
                return False
    
    def parse_project_info(self, project_name):
        """
        解析项目名称，提取项目名和版本号
        
        参数：
        - project_name: 项目名称，如 "N32H48xxx_V1.1.0"
        
        返回：
        - tuple: (项目名, 版本号)
        """
        # 使用下划线分割，最后一部分是版本号
        if '_' in project_name:
            parts = project_name.split('_')
            if len(parts) >= 2:
                # 项目名是除了最后一部分的所有部分
                project_name_part = '_'.join(parts[:-1])
                version_part = parts[-1]
                return project_name_part, version_part
        
        # 如果没有下划线，整个名称作为项目名，版本号设为空
        return project_name, ""
    
    def replace_placeholders(self, content, project_name, version):
        """
        替换内容中的占位符
        
        参数：
        - content: 文件内容
        - project_name: 项目名
        - version: 版本号
        
        返回：
        - str: 替换后的内容
        """
        # 替换占位符
        content = content.replace("{PROJECT_NAME}", project_name)
        content = content.replace("{PROJECT_NUMBER}", version)
        
        return content
    
    def copy_and_process_file(self, src_file, dst_file, project_name, version):
        """
        复制并处理单个文件
        
        参数：
        - src_file: 源文件路径
        - dst_file: 目标文件路径
        - project_name: 项目名
        - version: 版本号
        """
        try:
            # 确保目标目录存在
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果是Doxyfile文件，需要处理占位符
            if src_file.name.startswith('Doxyfile'):
                print(f"  📝 处理Doxyfile: {src_file.name}")
                
                # 读取源文件内容
                with open(src_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换占位符
                processed_content = self.replace_placeholders(content, project_name, version)
                
                # 写入目标文件
                with open(dst_file, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
                
                print(f"    ✅ 已生成: {dst_file}")
                
            else:
                # 普通文件直接复制
                shutil.copy2(src_file, dst_file)
                print(f"  📋 已复制: {dst_file}")
                
        except Exception as e:
            print(f"  ❌ 处理文件失败 {src_file.name}: {e}")
    
    def copy_directory_recursively(self, src_dir, dst_dir, project_name, version):
        """
        递归复制目录并处理文件
        
        参数：
        - src_dir: 源目录
        - dst_dir: 目标目录
        - project_name: 项目名
        - version: 版本号
        """
        try:
            # 确保目标目录存在
            dst_dir.mkdir(parents=True, exist_ok=True)
            
            # 遍历源目录中的所有内容
            for item in src_dir.iterdir():
                src_path = src_dir / item.name
                dst_path = dst_dir / item.name
                
                if src_path.is_file():
                    # 复制并处理文件
                    self.copy_and_process_file(src_path, dst_path, project_name, version)
                elif src_path.is_dir():
                    # 递归处理子目录
                    self.copy_directory_recursively(src_path, dst_path, project_name, version)
                    
        except Exception as e:
            print(f"  ❌ 复制目录失败 {src_dir.name}: {e}")
    
    def generate_for_project(self, project_name, project_path):
        """
        为单个项目生成main目录内容
        
        参数：
        - project_name: 项目名称
        - project_path: 项目路径
        """
        print(f"\n[INFO] 处理项目: {project_name}")
        
        # 检查项目是否已有doxygen目录
        doxygen_dir = Path(project_path) / "doxygen"
        if doxygen_dir.exists():
            if self.overwrite_mode:
                print(f"  [INFO] 项目 {project_name} 已有doxygen目录，将覆盖现有内容")
                # 删除现有目录
                import shutil
                try:
                    shutil.rmtree(doxygen_dir)
                    print(f"    🗑️  已删除现有目录")
                except Exception as e:
                    print(f"    ❌ 删除现有目录失败: {e}")
                    return False
            else:
                print(f"  [INFO] 项目 {project_name} 已有doxygen目录，跳过处理")
                return False
        
        # 解析项目信息
        parsed_name, parsed_version = self.parse_project_info(project_name)
        print(f"  [INFO] 项目名: {parsed_name}")
        print(f"  [INFO] 版本号: {parsed_version}")
        
        # 构建目标目录路径
        target_main_dir = Path(project_path) / "doxygen" / "main"
        
        # 复制模板目录内容
        print(f"  [INFO] 开始复制模板内容到: {target_main_dir}")
        self.copy_directory_recursively(self.template_html_dir, target_main_dir, parsed_name, parsed_version)
        
        print(f"  [SUCCESS] 项目 {project_name} 处理完成")
        return True
    
    def generate_all(self):
        """为所有激活的项目生成main目录内容"""
        if not self.activated_project_paths:
            print("❌ 未找到任何激活的项目")
            return False
        
        print(f"🎯 开始为 {len(self.activated_project_paths)} 个激活项目生成main目录内容")
        
        success_count = 0
        skipped_count = 0
        for project_name, project_path in self.activated_project_paths.items():
            try:
                result = self.generate_for_project(project_name, project_path)
                if result:
                    success_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"❌ 项目 {project_name} 处理失败: {e}")
        
        print(f"\n📊 生成完成:")
        print(f"  ✅ 成功生成: {success_count} 个项目")
        print(f"  ⏭️  跳过处理: {skipped_count} 个项目")
        print(f"  📋 总计: {len(self.activated_project_paths)} 个项目")
        
        # 根据覆盖模式显示不同的提示
        if self.overwrite_mode:
            print(f"  🔄 覆盖模式：已覆盖 {success_count} 个项目的现有内容")
        else:
            print(f"  🔄 跳过模式：跳过了 {skipped_count} 个已有doxygen目录的项目")
        
        # 修改返回值逻辑：跳过的项目也应该算成功
        # 因为跳过的项目意味着已经完成，不需要重新生成
        total_processed = success_count + skipped_count
        if total_processed == len(self.activated_project_paths):
            print(f"  🎯 所有项目都已处理完成（生成或跳过）")
            return True
        else:
            print(f"  ⚠️  有 {len(self.activated_project_paths) - total_processed} 个项目处理失败")
            return False


def main():
    """主函数"""
    print("[INFO] 开始执行主文档HTML内容生成...")
    print("💡 提示：脚本会为每个激活项目生成doxygen/main目录下的HTML模板文件")
    
    # 检查模板目录是否存在
    template_dir = Path(get_work_dir()) / "template" / "html"
    if not template_dir.exists():
        print(f"[ERROR] 模板目录不存在: {template_dir}")
        print("请确保 template/html 目录存在")
        return False
    
    # 创建生成器并执行
    generator = MainHtmlGenerator()
    success = generator.generate_all()
    
    if success:
        print("[SUCCESS] 所有项目的主文档HTML内容生成完成！")
    else:
        print("[WARN] 部分项目的主文档HTML内容生成失败")
    
    return success


if __name__ == "__main__":
    main()
