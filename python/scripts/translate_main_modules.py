#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
translate_main_modules.py - Markdown文件中文翻译脚本
根据base.json配置翻译指定项目下的中文内容为英文
"""

import os
import re
import sys
import shutil
from pathlib import Path
from common_utils import BaseGenerator, TextProcessor, FileUtils, Logger, ArgumentParser, ConfigManager

# 尝试导入翻译库，如果失败则提供友好的错误信息
try:
    from deep_translator import GoogleTranslator
except ImportError:
    Logger.error("缺少deep_translator模块，请安装: pip install deep_translator")
    sys.exit(1)


class MarkdownTranslator(BaseGenerator):
    """Markdown翻译器类"""
    
    def __init__(self, output_folder, chip_config):
        """初始化翻译器"""
        super().__init__("", output_folder, chip_config)  # input_folder 在此脚本中不使用
        self.translator = GoogleTranslator(source='zh-CN', target='en')
        
        # 专业术语中英文对照表
        self.technical_terms = {
            "概览": "Overview",
            "产品概览": "Product Overview",
            "系列型号": "Product Display",
            "典型应用": "Typical Applications",
            "主要特征": "Main Features",
            "技术资源": "Technical Resources",
            "产品简介": "Product Brief",
            "数据手册": "Datasheet",
            "用户手册": "User Manual",
            "勘误表": "Errata Sheet",
            "硬件评估板": "Hardware Evaluation Board",
            "软件开发包": "Software Development Kit",
            "应用笔记": "Application Notes",
            "用户指南": "User Guide",
            "详细的产品规格和特性介绍": "Detailed product specifications and feature introduction",
            "详细的技术规格和电气特性": "Detailed technical specifications and electrical characteristics",
            "开发指南和API参考": "Development guide and API reference",
            "已知问题和解决方案": "Known issues and solutions",
            "硬件参考设计": "Hardware reference design",
            "SDK、驱动库和示例代码": "SDK, driver library and example code",
            "典型应用实现方案": "Typical application implementation solutions",
            "资源下载": "Resource Download",
            "完整资源包下载": "Complete resource package download"
        }
        
        # 尝试从配置文件加载额外的专业术语
        self.load_technical_terms()
        
    def load_technical_terms(self):
        """从配置文件加载额外的专业术语对照表"""
        try:
            base_config = self.load_base_config()
            # 检查是否有专业术语配置
            if 'Technical_Terms' in base_config:
                additional_terms = base_config['Technical_Terms']
                self.technical_terms.update(additional_terms)
                        
        except Exception as e:
            pass  # 忽略配置加载失败
    
    def is_chinese_text(self, text):
        """判断文本是否包含中文"""
        return TextProcessor.is_chinese_text(text)
    
    def extract_chinese_content(self, content):
        """提取需要翻译的中文内容，保护HTML结构"""
        return TextProcessor.extract_chinese_content(content)
    
    def translate_text(self, text, retry_count=0):
        """翻译中文文本，优先使用专业术语对照表，支持重试机制"""
        max_retries = 3
        
        try:
            # 清理文本，去除多余空白
            cleaned_text = text.strip()
            if not cleaned_text:
                return text
            
            # 首先检查是否在专业术语对照表中
            if cleaned_text in self.technical_terms:
                return self.technical_terms[cleaned_text]
            
            # 如果不在对照表中，使用Google翻译
            translated = self.translator.translate(cleaned_text)
            return translated
            
        except Exception as e:
            if retry_count < max_retries:
                retry_count += 1
                import time
                time.sleep(1)
                return self.translate_text(text, retry_count)
            else:
                Logger.error(f"翻译失败: {text}")
                return text
    
    def translate_markdown_file(self, file_path):
        """翻译单个Markdown文件"""
        try:
            # 读取文件内容
            content = FileUtils.read_file_with_encoding(file_path)
            
            # 检查是否包含中文
            if not self.is_chinese_text(content):
                return True
            
            # 提取中文内容
            chinese_matches = self.extract_chinese_content(content)
            
            if not chinese_matches:
                return True
            
            # 创建翻译映射，避免重复翻译相同内容
            translation_map = {}
            
            for chinese_text in chinese_matches:
                if chinese_text not in translation_map:
                    translated_text = self.translate_text(chinese_text)
                    translation_map[chinese_text] = translated_text
            
            # 按长度降序排列，避免短文本被长文本包含的问题
            sorted_chinese = sorted(translation_map.keys(), key=len, reverse=True)
            
            # 应用翻译，保持原始内容结构
            translated_content = content
            for chinese_text in sorted_chinese:
                translated_text = translation_map[chinese_text]
                translated_content = translated_content.replace(chinese_text, translated_text)
            
            # 写回文件
            return FileUtils.write_file(file_path, translated_content)
            
        except Exception as e:
            Logger.error(f"翻译文件失败: {file_path}")
            return False
    
    def find_markdown_files(self):
        """查找需要翻译的Markdown文件"""
        # 查找中文目录下的Markdown文件
        cn_dir = self.output_folder / "doxygen" / "main" / "modules" / "cn"
        en_dir = self.output_folder / "doxygen" / "main" / "modules" / "en"
        
        md_files = []
        
        # 如果存在中文目录，翻译中文文件到英文目录
        if cn_dir.exists():
            for file in cn_dir.glob("*.md"):
                # 对应的英文文件路径
                en_file = en_dir / file.name
                # 确保英文目录存在
                en_dir.mkdir(parents=True, exist_ok=True)
                # 复制中文文件到英文目录
                shutil.copy2(file, en_file)
                md_files.append(en_file)
        
        # 如果英文目录存在，直接翻译英文目录下的文件
        elif en_dir.exists():
            for file in en_dir.glob("*.md"):
                md_files.append(file)
        
        return md_files
    
    def translate(self):
        """执行翻译"""
        try:
            # 查找Markdown文件
            md_files = self.find_markdown_files()
            
            if not md_files:
                Logger.info("未找到需要翻译的Markdown文件")
                return True
            
            success_count = 0
            failed_count = 0
            
            for md_file in md_files:
                if self.translate_markdown_file(md_file):
                    success_count += 1
                else:
                    failed_count += 1
            
            if failed_count > 0:
                Logger.error(f"{failed_count} 个文件翻译失败")
                return False
            
            return True
            
        except Exception as e:
            Logger.error(f"翻译过程失败: {e}")
            return False


def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python translate_main_modules.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        # 解析芯片配置JSON
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建翻译器并执行
        translator = MarkdownTranslator(output_folder, chip_config)
        translator.translate()
        
        Logger.success("Markdown文件翻译完成！")
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
