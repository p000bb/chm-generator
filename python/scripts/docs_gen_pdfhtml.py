#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_gen_pdfhtml.py - PDF HTML生成脚本
功能：在input_folder目录下扫描PDF文件，生成统一的HTML页面
"""

import sys
import json
import re
import hashlib
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from common_utils import (
    ArgumentParser, timing_decorator, ConfigManager, Logger
)


class PDFHTMLGenerator:
    """PDF HTML生成器类"""
    
    def __init__(self, input_folder, output_folder, chip_config):
        """初始化PDF HTML生成器"""
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.chip_config = chip_config
        self.work_dir = Path(__file__).parent.parent.parent
        self.template_path = self.work_dir / "template" / "pdf.html.template"
        
        # 从芯片配置中获取项目信息
        chip_name = chip_config.get('chipName', '')
        chip_version = chip_config.get('chipVersion', '')
        self.project_name = f"{chip_name}_V{chip_version}"
        self.project_version = chip_version
        
    def load_base_config(self):
        """加载基础配置文件"""
        try:
            config_path = self.work_dir / "config" / "base.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            Logger.error(f"加载基础配置失败: {e}")
            return None
    
    def extract_project_name_from_config(self, config_html_path):
        """从Config.html文件中提取项目名称"""
        try:
            with open(config_html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找getProjectName函数中的return语句
            pattern = r'return\s*["\']([^"\']+)["\']\s*;'
            matches = re.findall(pattern, content)
            
            if matches:
                return matches[0]
            else:
                return "default"
                
        except Exception as e:
            return "default"
    
    def get_filename_replace_rules(self):
        """获取文件名替换规则"""
        return {
            '&': '_',
        }
    
    def get_content_replace_rules(self):
        """获取内容替换规则"""
        return {
            '3-UserManual': '3-UserManual',
        }
    
    def generate_8char_hash(self, text):
        """生成8位hash"""
        hash_obj = hashlib.md5(text.encode('utf-8'))
        return hash_obj.hexdigest()[:8]
    
    def find_pdf_files(self):
        """在input_folder目录下扫描PDF文件"""
        pdf_files = []
        
        if not self.input_folder.exists():
            Logger.error(f"输入目录不存在: {self.input_folder}")
            return pdf_files
        
        # 只扫描第一层目录
        for first_level_dir in self.input_folder.iterdir():
            if first_level_dir.is_dir():
                for pdf_file in first_level_dir.glob("*.pdf"):
                    # 确保文件是PDF
                    if pdf_file.suffix.lower() == ".pdf":
                        pdf_files.append(pdf_file)
        
        return pdf_files
    
    def get_directory_mapping_rules(self):
        """获取目录名称映射规则"""
        return {
            '3-UserManual': '3-User_Manual',
        }
    
    def generate_script_content(self, pdf_files, base_config, registry_project_name):
        """生成JavaScript代码"""
        pdf_mappings = {}
        for pdf_file in pdf_files:
            hash_name = self.generate_8char_hash(pdf_file.stem)
            dir_name = pdf_file.parent.name
            file_name = pdf_file.name
            
            # 应用目录名称映射规则
            directory_mapping_rules = self.get_directory_mapping_rules()
            mapped_dir_name = directory_mapping_rules.get(dir_name, dir_name)
            
            # 构建在线PDF路径
            online_path = f"{base_config['Base_DownloadUrl']}/{self.project_name}/{mapped_dir_name}/{file_name}"
            
            pdf_mappings[hash_name] = {
                'fileName': file_name,
                'dirName': dir_name,
                'mappedDirName': mapped_dir_name,
                'onlinePath': online_path
            }
        
        # 将映射数据转换为JavaScript对象
        mappings_json = json.dumps(pdf_mappings, ensure_ascii=False, indent=2)
        
        # 生成JavaScript代码
        script_content = f"""
    <script>
    // PDF映射数据
    var pdfMappings = {mappings_json};
    
    // 智能PDF加载策略
    function loadPDF() {{
        var pdfViewer = document.getElementById('pdfViewer');
        var loadingDiv = document.getElementById('loading');
        
        // 检测网络连接
        function checkNetworkAndLoad() {{
            var img = new Image();
            img.onload = function() {{
                loadingDiv.style.display = "none";
                pdfViewer.style.display = "block";
            }};
            img.onerror = function() {{
                loadingDiv.innerHTML = "网络连接失败，正在加载本地pdf。";
                loadingDiv.style.color = "#e74c3c";
            }};
            img.src = "https://www.nationstech.com/favicon.ico?" + new Date().getTime();
        }}
        
        if (document.readyState === 'loading') {{
            if (document.addEventListener) {{
                document.addEventListener('DOMContentLoaded', checkNetworkAndLoad, false);
            }} else if (document.attachEvent) {{
                document.attachEvent('onreadystatechange', function() {{
                    if (document.readyState === 'complete') {{
                        checkNetworkAndLoad();
                    }}
                }});
            }}
        }} else {{
            checkNetworkAndLoad();
        }}
    }}
    
    // 智能PDF加载函数
    function loadPDFByHash(hashName) {{
        var mapping = pdfMappings[hashName];
        if (!mapping) {{
            alert('未找到对应的PDF文件');
            return;
        }}
        
        var pdfViewer = document.getElementById('pdfViewer');
        var loading = document.getElementById('loading');
        
        loading.style.display = 'block';
        loading.innerHTML = '正在检测网络连接...';
        pdfViewer.style.display = 'none';
        
        checkNetworkAndLoadPDF(mapping, pdfViewer, loading);
        
        var currentHash = window.location.hash.substring(1);
        if (currentHash !== hashName) {{
            window.location.hash = hashName;
        }}
    }}
    
    // 检测网络并加载PDF
    function checkNetworkAndLoadPDF(mapping, pdfViewer, loading) {{
        var img = new Image();
        img.onload = function() {{
            loading.innerHTML = '网络连接正常，正在加载在线PDF...';
            loadOnlinePDF(mapping, pdfViewer, loading);
        }};
        img.onerror = function() {{
            loading.innerHTML = '网络连接失败，正在尝试加载本地PDF...';
            loadLocalPDF(mapping, pdfViewer, loading);
        }};
        img.src = "https://www.nationstech.com/favicon.ico?" + new Date().getTime();
    }}
    
    // 加载在线PDF
    function loadOnlinePDF(mapping, pdfViewer, loading) {{
        try {{
            pdfViewer.src = mapping.onlinePath;
            loading.style.display = 'none';
            pdfViewer.style.display = 'block';
        }} catch (e) {{
            loadLocalPDF(mapping, pdfViewer, loading);
        }}
    }}
    
    // 加载本地PDF
    function loadLocalPDF(mapping, pdfViewer, loading) {{
        var localPath = getLocalPdfPath(mapping);
        if (localPath) {{
            testLocalPDF(localPath, function(success) {{
                if (success) {{
                    pdfViewer.src = localPath;
                    loading.style.display = 'none';
                    pdfViewer.style.display = 'block';
                }} else {{
                    loading.innerHTML = '网络连接失败，且本地PDF不可访问。<br>请检查网络连接或本地PDF文件。';
                    loading.style.color = '#e74c3c';
                }}
            }});
        }} else {{
            loading.innerHTML = '网络连接失败，且未配置本地PDF路径。<br>请检查网络连接或配置本地PDF路径。';
            loading.style.color = '#e74c3c';
        }}
    }}
    
    // 获取本地PDF路径
    function getLocalPdfPath(mapping) {{
        try {{
            var shell = new ActiveXObject("WScript.Shell");
            var basePath = shell.RegRead("HKEY_CURRENT_USER\\\\SOFTWARE\\\\ChmConfig\\\\pdfBasePath_{registry_project_name}");
            if (basePath && basePath !== "") {{
                var localPath = basePath + "\\\\" + mapping.dirName + "\\\\" + mapping.fileName;
                return "file:///" + localPath.replace(/\\\\/g, "/");
            }}
        }} catch (e) {{
        }}
        return null;
    }}
    
    // 测试本地PDF是否可访问
    function testLocalPDF(localPath, callback) {{
        try {{
            var xhr = new ActiveXObject("Microsoft.XMLHTTP");
            xhr.open("HEAD", localPath, false);
            xhr.send();
            var success = (xhr.status === 200 || xhr.status === 0);
            callback(success);
        }} catch (e) {{
            try {{
                var xhr = new ActiveXObject("Microsoft.XMLHTTP");
                xhr.open("GET", localPath, false);
                xhr.send();
                var success = (xhr.status === 200 || xhr.status === 0);
                callback(success);
            }} catch (e2) {{
                callback(false);
            }}
        }}
    }}
    
    // 页面加载完成后检查URL锚点
    function checkHashOnLoad() {{
        var hash = window.location.hash.substring(1);
        if (hash && pdfMappings[hash]) {{
            setTimeout(function() {{ loadPDFByHash(hash); }}, 100);
        }}
    }}
    
    // 监听锚点变化
    function checkHashChange() {{
        var hash = window.location.hash.substring(1);
        if (hash && pdfMappings[hash]) {{
            loadPDFByHash(hash);
        }}
    }}
    
    // 页面加载完成后执行
    if (window.addEventListener) {{
        window.addEventListener('load', checkHashOnLoad, false);
        window.addEventListener('hashchange', checkHashChange, false);
    }} else if (window.attachEvent) {{
        window.attachEvent('onload', checkHashOnLoad);
        var lastHash = window.location.hash;
        setInterval(function() {{
            var currentHash = window.location.hash;
            if (currentHash !== lastHash) {{
                lastHash = currentHash;
                if (currentHash && currentHash.length > 1) {{
                    checkHashChange();
                }}
            }}
        }}, 500);
    }}
    
    if (window.addEventListener) {{
        window.addEventListener('load', loadPDF, false);
    }} else if (window.attachEvent) {{
        window.attachEvent('onload', loadPDF);
    }}
    </script>
    """
        
        return script_content
    
    def generate_html_content(self, pdf_files, base_config, registry_project_name):
        """生成HTML内容"""
        script_content = self.generate_script_content(pdf_files, base_config, registry_project_name)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PDF文档查看器 - {self.project_name}</title>
    <style>
      html,
      body {{
        margin: 0;
        padding: 0;
        height: 100%;
        overflow: hidden;
      }}
      .container {{
        width: 100%;
        height: 100%;
        border: none;
        position: relative;
      }}
      .header {{
        background: #2c3e50;
        color: white;
        padding: 20px;
        text-align: center;
      }}
      .pdf-viewer {{
        width: 100%;
        height: 100%;
        border: none;
        position: absolute;
        top: 0;
        left: 0;
      }}
      .fallback {{
        padding: 20px;
        text-align: center;
        color: #666;
      }}
      .loading {{
        position: absolute;
        top: 50%;
        left: 50%;
        margin-top: -8px;
        margin-left: -150px;
        color: #3498db;
        font-size: 16px;
        text-align: center;
        width: 300px;
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <div id="loading" class="loading">正在检测网络环境并加载PDF...</div>
      <iframe
        id="pdfViewer"
        src=""
        class="pdf-viewer"
        title="PDF查看器"
        style="display: none;"
        frameborder="0"
      ></iframe>
    </div>
  
    {script_content}
  </body>
</html>"""
        
        return html_content
    
    def ensure_output_dirs(self):
        """确保输出目录存在并清空现有文件"""
        html_dir = self.output_folder / "output" / "pdf" / "html"
        
        # 清空现有文件
        if html_dir.exists():
            html_file_count = 0
            for file in html_dir.glob("*.html"):
                try:
                    file.unlink()
                    html_file_count += 1
                except Exception as e:
                    pass
            
            # 清空映射文件
            mapping_file = html_dir.parent / "filename_mapping.json"
            if mapping_file.exists():
                try:
                    mapping_file.unlink()
                except Exception as e:
                    pass
        
        try:
            html_dir.mkdir(parents=True, exist_ok=True)
            return html_dir
        except OSError as e:
            Logger.error(f"创建输出目录失败: {e}")
            return None
    
    def save_filename_mapping(self, pdf_files):
        """保存文件名映射"""
        try:
            mapping_file = self.output_folder / "output" / "pdf" / "filename_mapping.json"
            mappings = {}
            
            for pdf_file in pdf_files:
                hash_name = self.generate_8char_hash(pdf_file.stem)
                mappings[hash_name] = {
                    'original_name': pdf_file.stem,
                    'dir_name': pdf_file.parent.name,
                    'file_name': pdf_file.name
                }
            
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mappings, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            Logger.error(f"保存文件名映射失败: {e}")
            return False
    
    def apply_filename_replace_rules(self, filename):
        """应用文件名替换规则"""
        rules = self.get_filename_replace_rules()
        for old, new in rules.items():
            filename = filename.replace(old, new)
        return filename
    
    def apply_content_replace_rules(self, content):
        """应用内容替换规则"""
        rules = self.get_content_replace_rules()
        for old, new in rules.items():
            content = content.replace(old, new)
        return content
    
    def generate_unified_html_for_project(self, pdf_files, html_dir, base_config, registry_project_name):
        """为指定项目生成统一的HTML页面"""
        try:
            # 生成统一的HTML内容
            html_content = self.generate_html_content(pdf_files, base_config, registry_project_name)
            
            # 生成HTML文件
            html_filename = "index.html"
            html_path = html_dir / html_filename
            
            # 写入HTML文件
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 保存文件名映射（用于HHC生成）
            for pdf_file in pdf_files:
                hash_name = self.generate_8char_hash(pdf_file.stem)
                # 这里可以添加更多映射保存逻辑
            
            return True
            
        except Exception as e:
            Logger.error(f"生成统一HTML页面失败: {e}")
            return False
    
    def generate(self):
        """生成PDF HTML"""
        try:
            # 加载基础配置
            base_config = self.load_base_config()
            if not base_config:
                return False
            
            # 查找PDF文件
            pdf_files = self.find_pdf_files()
            if not pdf_files:
                return True
            
            # 确保输出目录存在并清空现有文件
            html_dir = self.ensure_output_dirs()
            if not html_dir:
                return False
            
            # 尝试从Config.html文件获取注册表项目名称
            config_html_path = self.output_folder / "output" / "extra" / "Config.html"
            if config_html_path.exists():
                registry_project_name = self.extract_project_name_from_config(config_html_path)
            else:
                registry_project_name = self.project_name
            
            # 生成统一的HTML页面
            success = self.generate_unified_html_for_project(pdf_files, html_dir, base_config, registry_project_name)
            
            if success:
                # 保存文件名映射
                self.save_filename_mapping(pdf_files)
                return True
            else:
                return False
                
        except Exception as e:
            Logger.error(f"生成PDF HTML失败: {e}")
            return False


@timing_decorator
def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python docs_gen_pdfhtml.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建生成器并执行
        generator = PDFHTMLGenerator(input_folder, output_folder, chip_config)
        
        if not generator.generate():
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
