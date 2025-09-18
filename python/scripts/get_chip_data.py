#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_chip_data.py - 芯片数据获取脚本
功能：从芯片配置的URL获取信息，下载图片并生成overview.md文件
"""

import os
import json
import requests
import re
import sys
import shutil
import copy
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from common_utils import (
    ArgumentParser
)

class ChipDataGenerator:
    """芯片数据生成器类"""
    
    def __init__(self, output_folder, chip_config):
        """初始化芯片数据生成器"""
        self.output_folder = Path(output_folder)
        self.chip_config = chip_config
        
        # 从芯片配置中获取URL信息
        self.cn_url = chip_config.get('Cn_WebUrl', '')
        self.en_url = chip_config.get('En_WebUrl', '')
        self.zip_url = chip_config.get('Zip_Url', '')
        self.chip_name = chip_config.get('chipName', '')
        
        print(f"[INFO] 芯片数据生成器初始化完成")
    
    def get_web_content(self, url, timeout=30):
        """获取网页内容"""
        try:
            # 尝试从base.json加载PHPSESSID
            phpsessid = None
            try:
                # 假设base.json在项目根目录的config文件夹中
                base_config_path = self.output_folder.parent.parent / "config" / "base.json"
                if base_config_path.exists():
                    with open(base_config_path, "r", encoding="utf-8") as f:
                        base_config = json.load(f)
                        phpsessid = base_config.get("PHPSESSID")
            except Exception as e:
                pass  # 忽略PHPSESSID加载失败
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.nationstech.com/",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            
            # 添加Cookie
            cookies = {}
            if phpsessid:
                cookies["PHPSESSID"] = phpsessid
            
            response = requests.get(url, headers=headers, cookies=cookies, timeout=timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            return response.text
        except Exception as e:
            print(f"[ERROR] 获取网页内容失败: {e}")
            return None
    
    def extract_content(self, html_content, selectors, fallback_selectors=None):
        """从HTML内容中提取指定选择器的内容"""
        if not html_content:
            return {}
        
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            extracted_content = {}
            
            # 调试：显示页面中所有可能的类名
            all_classes = set()
            for tag in soup.find_all(class_=True):
                all_classes.update(tag.get("class", []))
            
            for selector in selectors:
                # 移除选择器开头的点号来匹配类名
                class_name = selector[1:] if selector.startswith(".") else selector
                
                # 尝试主要选择器
                elements = soup.select(selector)
                
                # 如果主要选择器失败，尝试备用选择器
                if not elements and fallback_selectors and selector in fallback_selectors:
                    for fallback_selector in fallback_selectors[selector]:
                        elements = soup.select(fallback_selector)
                        if elements:
                            break
                
                # 如果还是失败，尝试通过class属性查找
                if not elements:
                    elements = soup.find_all(class_=class_name)
                
                if elements:
                    if selector == ".productsDetail p":
                        # 对于.productsDetail p，改为查找.productsDetail下的所有p标签
                        products_detail_p = soup.select(".productsDetail p")
                        if products_detail_p:
                            content = products_detail_p[0].get_text(strip=True)
                            extracted_content[selector] = content
                        else:
                            extracted_content[selector] = ""
                    elif selector == ".productsFeaturesMain":
                        # 对于.productsFeaturesMain，保持原有HTML格式
                        content = str(elements[0])
                        extracted_content[selector] = content if content.strip() else ""
                    elif selector == ".typicalApplicationsMain":
                        # 对于.typicalApplicationsMain，尝试多种方式提取内容
                        content = ""
                        
                        # 方法1: 尝试查找.MsoListParagraph元素
                        mso_list_elements = elements[0].select(".MsoListParagraph")
                        if mso_list_elements:
                            text_contents = []
                            for mso_elem in mso_list_elements:
                                text = mso_elem.get_text(strip=True)
                                if text and len(text) > 5:
                                    text_contents.append(text)
                            
                            if text_contents:
                                content = "\n".join([f"• {text}" for text in text_contents])
                        
                        # 方法2: 如果没有.MsoListParagraph，尝试查找所有p标签
                        if not content:
                            p_elements = elements[0].find_all("p")
                            if p_elements:
                                text_contents = []
                                for p_elem in p_elements:
                                    text = p_elem.get_text(strip=True)
                                    if text and len(text) > 5:
                                        text_contents.append(text)
                                
                                if text_contents:
                                    content = "\n".join([f"• {text}" for text in text_contents])
                        
                        # 方法3: 如果还是没有内容，尝试查找所有li标签
                        if not content:
                            li_elements = elements[0].find_all("li")
                            if li_elements:
                                text_contents = []
                                for li_elem in li_elements:
                                    text = li_elem.get_text(strip=True)
                                    if text and len(text) > 5:
                                        text_contents.append(text)
                                
                                if text_contents:
                                    content = "\n".join([f"• {text}" for text in text_contents])
                        
                        # 方法4: 最后尝试，直接获取整个元素的文本内容
                        if not content:
                            full_text = elements[0].get_text(strip=True)
                            if full_text and len(full_text) > 20:
                                lines = [
                                    line.strip()
                                    for line in full_text.split("\n")
                                    if line.strip() and len(line.strip()) > 5
                                ]
                                if lines:
                                    content = "\n".join([f"• {line}" for line in lines])
                        
                        extracted_content[selector] = content
                    elif selector == ".productsDisplayArea":
                        # 特殊处理.productsDisplayArea：如果包含table则只保留table，否则保持原样
                        element = elements[0]
                        
                        # 检查是否包含table
                        table_element = element.find("table")
                        if table_element:
                            # 如果包含table，只保留table内容
                            import copy
                            table_copy = copy.copy(table_element)
                            
                            # 处理table内的所有img标签，只保留src中最后一个斜杠后面的内容
                            for img_tag in table_copy.find_all("img"):
                                src = img_tag.get("src")
                                if src:
                                    last_slash_index = src.rfind("/")
                                    if last_slash_index != -1:
                                        new_src = "." + src[last_slash_index:]
                                        img_tag["src"] = new_src
                                    else:
                                        new_src = "./" + src
                                        img_tag["src"] = new_src
                            
                            # 去除所有a标签，保留文本内容
                            for a_tag in table_copy.find_all("a"):
                                a_tag.replace_with(a_tag.get_text())
                            
                            # 清理所有标签的style属性
                            for tag in table_copy.find_all(True):
                                if tag.has_attr("style"):
                                    del tag["style"]
                                if tag.has_attr("height"):
                                    del tag["height"]
                                if tag.has_attr("width"):
                                    del tag["width"]
                                if tag.has_attr("valign"):
                                    del tag["valign"]
                            
                            # 清理table标签的所有属性
                            for attr in list(table_copy.attrs.keys()):
                                del table_copy[attr]
                            
                            # 简化CSS样式
                            css_styles = """<style>
.productsDisplayArea {
    width: 100%;
    overflow-x: auto;
}
.productsDisplayArea table {
    border-collapse: collapse;
}
.productsDisplayArea table p {
    margin: 0;
    padding: 0;
}
.productsDisplayArea table tr td {
    color: #333;
    font-size: 14px;
    border: 1px solid #374f7f;
    padding: 13px;
    height: auto !important;
}
.productsDisplayArea table tr:nth-child(1) td:first-child {
    border-left-color: #6b8fba;
}
.productsDisplayArea table tr th, .productsDisplayArea table tr:nth-child(1) {
    height: auto !important;
    font-weight: 400;
    color: #fff;
    font-size: 14px;
    background: #374f7f;
    border: 1px solid #fff;
    border-bottom: #374f7f;
    padding: 13px;
}
.productsDisplayArea table tr:nth-child(1) td{
  border:1px solid #FFFFFF;
  border-bottom:none
}
.productsDisplayArea table tr:nth-child(1) td {
    color: #fff;
    font-size: 14px;
}
</style>"""
                            
                            # 组合table和CSS样式
                            content = f'<div class="productsDisplayArea">\n{str(table_copy)}\n</div>\n\n{css_styles}'
                        else:
                            # 如果没有table，保持原样不变
                            content = str(element)
                        
                        extracted_content[selector] = content
                    else:
                        # 其他选择器使用原有逻辑
                        content = str(elements[0])
                        extracted_content[selector] = content if content.strip() else ""
                else:
                    extracted_content[selector] = ""
            
            return extracted_content
        except Exception as e:
            print(f"[ERROR] 解析HTML内容失败: {e}")
            return {}
    
    def download_image(self, img_url, base_url):
        """下载图片到assets目录"""
        try:
            # 确保assets目录存在
            assets_dir = self.output_folder / "doxygen" / "main" / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            
            # 解析图片URL
            if img_url.startswith("http"):
                full_img_url = img_url
            else:
                full_img_url = urljoin(base_url, img_url)
            
            # 从URL中提取文件名
            parsed_url = urlparse(full_img_url)
            filename = os.path.basename(parsed_url.path)
            
            if not os.path.splitext(filename)[1]:
                filename += ".jpg"
            
            # 生成唯一的文件名
            base_name, ext = os.path.splitext(filename)
            counter = 1
            final_filename = filename
            while (assets_dir / final_filename).exists():
                final_filename = f"{base_name}_{counter}{ext}"
                counter += 1
            
            # 尝试从base.json加载PHPSESSID
            phpsessid = None
            try:
                base_config_path = self.output_folder.parent.parent / "config" / "base.json"
                if base_config_path.exists():
                    with open(base_config_path, "r", encoding="utf-8") as f:
                        base_config = json.load(f)
                        phpsessid = base_config.get("PHPSESSID")
            except Exception as e:
                pass  # 忽略PHPSESSID加载失败
            
            # 下载图片
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": base_url,
            }
            
            cookies = {}
            if phpsessid:
                cookies["PHPSESSID"] = phpsessid
            
            response = requests.get(full_img_url, headers=headers, cookies=cookies, timeout=30)
            response.raise_for_status()
            
            # 保存图片
            img_path = assets_dir / final_filename
            with open(img_path, "wb") as f:
                f.write(response.content)
            
            return final_filename
        except Exception as e:
            print(f"[ERROR] 下载图片失败 {img_url}: {e}")
            return None
    
    def download_chip_image(self, html_content, base_url):
        """下载芯片主图片"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # 查找.productsDetail下的img标签
            products_detail = soup.select(".productsDetail")
            if not products_detail:
                return None
            
            img_tag = products_detail[0].find("img")
            if not img_tag:
                return None
            
            src = img_tag.get("src")
            if not src:
                return None
            
            # 确保assets目录存在
            assets_dir = self.output_folder / "doxygen" / "main" / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            
            # 解析图片URL
            if src.startswith("http"):
                full_img_url = src
            else:
                full_img_url = urljoin(base_url, src)
            
            # 固定文件名为chip.png
            chip_img_path = assets_dir / "chip.png"
            
            # 尝试从base.json加载PHPSESSID
            phpsessid = None
            try:
                base_config_path = self.output_folder.parent.parent / "config" / "base.json"
                if base_config_path.exists():
                    with open(base_config_path, "r", encoding="utf-8") as f:
                        base_config = json.load(f)
                        phpsessid = base_config.get("PHPSESSID")
            except Exception as e:
                pass  # 忽略PHPSESSID加载失败
            
            # 下载图片
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": base_url,
            }
            
            cookies = {}
            if phpsessid:
                cookies["PHPSESSID"] = phpsessid
            
            response = requests.get(full_img_url, headers=headers, cookies=cookies, timeout=30)
            response.raise_for_status()
            
            # 保存图片
            with open(chip_img_path, "wb") as f:
                f.write(response.content)
            
            return "chip.png"
        except Exception as e:
            print(f"[ERROR] 下载芯片图片失败: {e}")
            return None
    
    def process_html_images(self, html_content, base_url):
        """处理HTML内容中的图片"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            downloaded_images = []
            
            # 查找所有img标签
            img_tags = soup.find_all("img")
            
            for img_tag in img_tags:
                src = img_tag.get("src")
                if src:
                    # 检查是否是已经处理过的路径（以/开头的相对路径）
                    if src.startswith("/") and not src.startswith("http"):
                        # 这是已经处理过的路径，跳过下载，直接使用
                        filename = src[1:]  # 去掉开头的斜杠
                        downloaded_images.append(filename)
                        continue
                    
                    # 下载图片
                    new_src = self.download_image(src, base_url)
                    if new_src:
                        # 更新图片路径，在HTML中使用./图片名的格式
                        img_tag["src"] = f"./{new_src}"
                        # 收集图片文件名（new_src现在就是纯文件名）
                        downloaded_images.append(new_src)
            
            return str(soup), downloaded_images
        except Exception as e:
            print(f"[ERROR] 处理HTML图片失败: {e}")
            return html_content, []
    
    def generate_overview_md(self, content_data, language="cn", title_only=False):
        """生成overview.md文件"""
        try:
            # 确保输出目录存在
            output_dir = self.output_folder / "doxygen" / "main" / "modules" / language
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / "00_overview.md"
            
            # 根据语言设置标题
            if language == "cn":
                title = "概览"
                product_overview = "产品概览"
                series_models = "系列型号"
                typical_applications = "典型应用"
                main_features = "主要特征"
                technical_resources = "技术资源"
                product_brief = "产品简介"
                datasheet = "数据手册"
                user_manual = "用户手册"
                errata_sheet = "勘误表"
                hardware_evaluation_board = "硬件评估板"
                software_development_kit = "软件开发包"
                application_note = "应用笔记"
                user_guide = "用户指南"
                product_brief_desc = "详细的产品规格和特性介绍"
                datasheet_desc = "详细的技术规格和电气特性"
                user_manual_desc = "开发指南和API参考"
                errata_sheet_desc = "已知问题和解决方案"
                hardware_evaluation_board_desc = "硬件参考设计"
                software_development_kit_desc = "SDK、驱动库和示例代码"
                application_note_desc = "典型应用实现方案"
                user_guide_desc = "开发指南和API参考"
                resource_download = "资源下载"
                resource_download_desc = "完整资源包下载"
            else:
                title = "Overview"
                product_overview = "Product Overview"
                series_models = "Product Display"
                typical_applications = "Typical Applications"
                main_features = "Main Features"
                technical_resources = "Technical Resources"
                product_brief = "Product Brief"
                datasheet = "Datasheet"
                user_manual = "User Manual"
                errata_sheet = "Errata Sheet"
                hardware_evaluation_board = "Hardware Evaluation Board"
                software_development_kit = "Software Development Kit"
                application_note = "Application Notes"
                user_guide = "User Guide"
                product_brief_desc = "Detailed product specifications and feature introduction"
                datasheet_desc = "Detailed technical specifications and electrical characteristics"
                user_manual_desc = "Development guide and API reference"
                errata_sheet_desc = "Known issues and solutions"
                hardware_evaluation_board_desc = "Hardware reference design"
                software_development_kit_desc = "SDK, driver library and example code"
                application_note_desc = "Typical application implementation solutions"
                user_guide_desc = "Development guide and API reference"
                resource_download = "Resource Download"
                resource_download_desc = "Complete resource package download"
            
            # 如果只需要标题，直接返回
            if title_only:
                md_content = f"# {title} {{#mainpage}}\n"
            else:
                # 生成Markdown内容
                md_content = f"""# {title} {{#mainpage}}

## {product_overview}
<div>
  <div class="product-image-container">
    ![{self.chip_name}{" Series" if language == 'en' else "系列"}](./chip.png)
  </div>
  <div class="product-info-container">
    <div class="product-title">{self.chip_name}</div>
    <div class="product-description">
    {content_data.get('.productsDetail p', '')}
    </div>"""
                
                # 添加查看更多链接
                if language == "cn" and self.cn_url:
                    md_content += f"""
    <div style="margin-top:20px">
    <a href="{self.cn_url}" target="_blank">查看更多</a>
    </div>"""
                elif language == "en" and self.en_url:
                    md_content += f"""
    <div style="margin-top:20px">
    <a href="{self.en_url}" target="_blank">View More</a>
    </div>"""
                
                md_content += """
  </div>
</div>

"""
                
                # 添加系列型号
                if content_data.get(".productsDisplayArea"):
                    md_content += f"""## {series_models}
\\htmlonly
{content_data.get('.productsDisplayArea', '')}
\\endhtmlonly

"""
                
                # 添加主要特征
                if content_data.get(".productsFeaturesMain"):
                    md_content += f"""## {main_features}
\\htmlonly
{content_data.get('.productsFeaturesMain', '')}
\\endhtmlonly

"""
                
                # 添加典型应用
                if content_data.get(".typicalApplicationsMain"):
                    md_content += f"""## {typical_applications}
{content_data.get('.typicalApplicationsMain', '')}

"""
                
                # 添加技术资源
                md_content += f"""## {technical_resources}
- [{product_brief}](@ref product_brief) - {product_brief_desc}
- [{datasheet}](@ref datasheet) - {datasheet_desc}
- [{user_manual}](@ref user_manual) - {user_manual_desc}
- [{errata_sheet}](@ref errata_sheet) - {errata_sheet_desc}
- [{hardware_evaluation_board}](@ref hardware_evaluation_board) - {hardware_evaluation_board_desc}
- [{software_development_kit}](@ref software_development_kit) - {software_development_kit_desc}
- [{application_note}](@ref application_note) - {application_note_desc}
- [{user_guide}](@ref user_guide) - {user_guide_desc}
- <a href="{self.zip_url}" target="_blank">**{resource_download}**</a> - {resource_download_desc}
"""
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            return True
        except Exception as e:
            print(f"[ERROR] 生成overview.md失败: {e}")
            return False
    
    def update_doxyfile_html_extra_files(self, image_files):
        """更新项目Doxyfile中的HTML_EXTRA_FILES配置，添加图片文件"""
        try:
            # 需要更新的Doxyfile文件
            doxyfile_files = ["Doxyfile_zh", "Doxyfile_en"]
            
            for doxyfile_name in doxyfile_files:
                doxyfile_path = self.output_folder / "doxygen" / "main" / doxyfile_name
                
                if doxyfile_path.exists():
                    # 读取Doxyfile内容
                    with open(doxyfile_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 构建新的HTML_EXTRA_FILES配置
                    # 默认的JS文件
                    js_files = [
                        "./js/custom_scripts.js",
                        "./js/nav_highlight.js",
                        "./js/custom_md.js",
                        "./assets/files.png",
                        "./assets/pdf.png",
                        "./assets/pack.png",
                    ]
                    
                    # 添加图片文件
                    image_paths = [f"./assets/{img}" for img in image_files]
                    
                    # 合并所有文件
                    all_files = js_files + image_paths
                    
                    # 构建配置字符串
                    html_extra_files_config = (
                        "HTML_EXTRA_FILES       = "
                        + " \\\n                         ".join(all_files)
                    )
                    
                    # 查找并替换现有的HTML_EXTRA_FILES配置
                    import re
                    
                    pattern = r"HTML_EXTRA_FILES\s*=.*?(?=\n\w|$)"
                    replacement = html_extra_files_config
                    
                    if re.search(pattern, content, re.DOTALL):
                        # 如果找到现有配置，替换它
                        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                    else:
                        # 如果没有找到，在文件末尾添加
                        new_content = content + f"\n\n{html_extra_files_config}\n"
                    
                    # 写回文件
                    with open(doxyfile_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
        except Exception as e:
            print(f"[ERROR] 更新Doxyfile HTML_EXTRA_FILES配置失败: {e}")
    
    def generate(self):
        """生成芯片数据"""
        try:
            # 定义要提取的CSS选择器
            selectors = [
                ".productsDetail p",
                ".productsDisplayArea",
                ".typicalApplicationsMain",
                ".productsFeaturesMain",
            ]
            
            # 备用选择器（如果主要选择器失败）
            fallback_selectors = {
                ".typicalApplicationsMain": [
                    ".typicalApplications",
                    ".applications",
                    ".typical-applications",
                ],
                ".productsFeaturesMain": [
                    ".productsFeatures",
                    ".features",
                    ".product-features",
                ],
                ".productsDisplayArea": [".productsDisplay", ".display", ".product-display"],
            }
            
            # 收集所有下载的图片
            all_downloaded_images = []
            
            # 判断执行方案
            if self.cn_url and self.en_url:
                # 方案1: 两个URL都有
                cn_content = self.get_web_content(self.cn_url) if self.cn_url else None
                en_content = self.get_web_content(self.en_url) if self.en_url else None
                
                cn_extracted = (
                    self.extract_content(cn_content, selectors, fallback_selectors)
                    if cn_content
                    else {}
                )
                en_extracted = (
                    self.extract_content(en_content, selectors, fallback_selectors)
                    if en_content
                    else {}
                )
                
                # 先下载chip.png（从.productsDetail img元素）
                if cn_content:
                    chip_path = self.download_chip_image(cn_content, self.cn_url)
                    if chip_path:
                        all_downloaded_images.append("chip.png")
                
                # 只处理中文页面图片下载和路径更新
                if cn_extracted:
                    for selector, content in cn_extracted.items():
                        if (
                            selector != ".productsDetail p"
                            and selector != ".productsDisplayArea"
                            and content
                        ):
                            processed_content, images = self.process_html_images(
                                content, self.cn_url
                            )
                            cn_extracted[selector] = processed_content
                            all_downloaded_images.extend(images)
                        elif selector == ".productsDisplayArea" and content:
                            # .productsDisplayArea 已经处理过img路径，直接收集图片文件名
                            soup = BeautifulSoup(content, "html.parser")
                            img_tags = soup.find_all("img")
                            for img_tag in img_tags:
                                src = img_tag.get("src")
                                if src and src.startswith("./"):
                                    filename = src[2:]  # 去掉开头的./
                                    all_downloaded_images.append(filename)
                                elif src and src.startswith("/"):
                                    filename = src[1:]  # 去掉开头的斜杠
                                    all_downloaded_images.append(filename)
                
                # 英文页面直接使用中文页面处理好的内容（包括图片路径）
                if en_extracted and cn_extracted:
                    for selector in en_extracted:
                        if selector != ".productsDetail p" and selector in cn_extracted:
                            # 对于包含图片的选择器，直接使用中文页面的处理结果
                            en_extracted[selector] = cn_extracted[selector]
                
                # 生成中文overview.md
                if cn_content:
                    self.generate_overview_md(cn_extracted, "cn")
                
                # 生成英文overview.md
                if en_content:
                    self.generate_overview_md(en_extracted, "en")
                    
            elif self.cn_url:
                # 方案2: 只有中文URL，英文内容直接使用中文内容
                cn_content = self.get_web_content(self.cn_url)
                cn_extracted = (
                    self.extract_content(cn_content, selectors, fallback_selectors)
                    if cn_content
                    else {}
                )
                
                # 先下载chip.png（从.productsDetail img元素）
                if cn_content:
                    chip_path = self.download_chip_image(cn_content, self.cn_url)
                    if chip_path:
                        all_downloaded_images.append("chip.png")
                
                # 处理中文页面图片下载和路径更新
                if cn_extracted:
                    for selector, content in cn_extracted.items():
                        if (
                            selector != ".productsDetail p"
                            and selector != ".productsDisplayArea"
                            and content
                        ):
                            processed_content, images = self.process_html_images(
                                content, self.cn_url
                            )
                            cn_extracted[selector] = processed_content
                            all_downloaded_images.extend(images)
                        elif selector == ".productsDisplayArea" and content:
                            # .productsDisplayArea 已经处理过img路径，直接收集图片文件名
                            soup = BeautifulSoup(content, "html.parser")
                            img_tags = soup.find_all("img")
                            for img_tag in img_tags:
                                src = img_tag.get("src")
                                if src and src.startswith("./"):
                                    filename = src[2:]  # 去掉开头的./
                                    all_downloaded_images.append(filename)
                                elif src and src.startswith("/"):
                                    filename = src[1:]  # 去掉开头的斜杠
                                    all_downloaded_images.append(filename)
                
                # 英文内容直接使用中文内容（不进行翻译）
                en_extracted = cn_extracted.copy()
                
                # 生成中文overview.md
                if cn_content:
                    self.generate_overview_md(cn_extracted, "cn")
                
                # 生成英文overview.md
                self.generate_overview_md(en_extracted, "en")
                
            else:
                # 方案3: 只有英文URL
                en_content = self.get_web_content(self.en_url)
                en_extracted = (
                    self.extract_content(en_content, selectors, fallback_selectors)
                    if en_content
                    else {}
                )
                cn_extracted = {}
                
                # 只有英文URL时，需要处理图片下载
                if en_extracted:
                    for selector, content in en_extracted.items():
                        if (
                            selector != ".productsDetail p"
                            and selector != ".productsDisplayArea"
                            and content
                        ):
                            processed_content, images = self.process_html_images(
                                content, self.en_url
                            )
                            en_extracted[selector] = processed_content
                            all_downloaded_images.extend(images)
                        elif selector == ".productsDisplayArea" and content:
                            # .productsDisplayArea 已经处理过img路径，直接收集图片文件名
                            soup = BeautifulSoup(content, "html.parser")
                            img_tags = soup.find_all("img")
                            for img_tag in img_tags:
                                src = img_tag.get("src")
                                if src and src.startswith("./"):
                                    filename = src[2:]  # 去掉开头的./
                                    all_downloaded_images.append(filename)
                                elif src and src.startswith("/"):
                                    filename = src[1:]  # 去掉开头的斜杠
                                    all_downloaded_images.append(filename)
                
                # 生成英文overview.md
                if en_content:
                    self.generate_overview_md(en_extracted, "en")
                
                # 生成只包含标题的中文文件
                self.generate_overview_md({}, "cn", title_only=True)
            
            # 更新Doxyfile中的HTML_EXTRA_FILES配置
            if all_downloaded_images:
                self.update_doxyfile_html_extra_files(all_downloaded_images)
            
            return True
        except Exception as e:
            print(f"[ERROR] 生成芯片数据失败: {e}")
            return False


def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            expected_count=3,
            usage_message="python get_chip_data.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        # 解析芯片配置JSON
        try:
            chip_config = json.loads(chip_config_json)
        except json.JSONDecodeError as e:
            print(f"芯片配置JSON解析失败: {e}")
            sys.exit(1)
        
        # 创建生成器并执行
        generator = ChipDataGenerator(output_folder, chip_config)
        generator.generate()
        
        print("芯片数据生成完成！")
        
    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
