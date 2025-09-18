#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_gen_config.py - 生成Config.html配置文件
为项目生成Config.html配置文件，用于CHM文档的基路径设置
"""

import re
from pathlib import Path
import sys
from common_utils import BaseGenerator, TemplateProcessor, ArgumentParser, Logger


class ConfigGenerator(BaseGenerator):
    """Config.html生成器类"""
    
    def __init__(self, input_folder, output_folder, chip_config):
        """初始化Config生成器"""
        super().__init__(input_folder, output_folder, chip_config)
        self.template_path = self.get_template_path("Config.html")
        
        # 从芯片配置中获取项目信息
        self.project_name = f"{self.project_info['chip_name']}V{self.project_info['chip_version']}"
    
    def load_template(self):
        """加载Config.html模板文件"""
        try:
            if not self.template_path.exists():
                Logger.error(f"模板文件不存在: {self.template_path}")
                return ""
            
            from common_utils import FileUtils
            return FileUtils.read_file_with_encoding(self.template_path)
        except Exception as e:
            Logger.error(f"读取模板文件失败: {e}")
            return ""
    
    def replace_project_name(self, template_content, project_name):
        """替换模板中的项目名称占位符"""
        try:
            pattern = r'(getProjectName:\s*function\s*\(\)\s*\{\s*[^}]*return\s*")[^"]*(".*?\})'
            
            def replace_func(match):
                before_return = match.group(1)
                after_return = match.group(2)
                return f'{before_return}{project_name}{after_return}'
            
            return re.sub(pattern, replace_func, template_content, flags=re.DOTALL)
        except Exception as e:
            Logger.error(f"替换项目名称失败: {e}")
            return template_content
    
    def ensure_output_dir(self):
        """确保输出目录存在"""
        return self.ensure_output_dir("output", "extra")
    
    def generate_config(self):
        """生成Config.html文件"""
        try:
            # 加载模板
            template_content = self.load_template()
            if not template_content:
                return False
            
            # 替换项目名称
            config_content = self.replace_project_name(template_content, self.project_name)
            
            # 确保输出目录存在
            extra_dir = self.ensure_output_dir()
            
            # 生成Config.html文件
            config_file = extra_dir / "Config.html"
            from common_utils import FileUtils
            if FileUtils.write_file(config_file, config_content):
                Logger.info(f"成功生成Config.html: {config_file}")
                return True
            else:
                return False
            
        except Exception as e:
            Logger.error(f"生成Config.html失败: {e}")
            return False


def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python docs_gen_config.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        # 解析芯片配置JSON
        from common_utils import ConfigManager
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建生成器并执行
        generator = ConfigGenerator(input_folder, output_folder, chip_config)
        
        if generator.generate_config():
            Logger.success("Config.html生成完成！")
        else:
            Logger.error("Config.html生成失败！")
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()