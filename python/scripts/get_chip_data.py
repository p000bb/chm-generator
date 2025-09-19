#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_chip_data.py - 国民技术芯片信息爬取脚本
功能：从国民技术官网爬取芯片信息并生成技术文档
"""

import os
import requests
import re
import sys
import copy
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


# 添加当前目录到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from common_utils import (
    ArgumentParser, timing_decorator, Logger, ConfigManager, 
    PathUtils, FileUtils, BaseGenerator
)

class NationTechChipCrawler(BaseGenerator):
    """国民技术芯片信息爬取器"""
    
    def __init__(self, output_folder, chip_config):
        """初始化爬取器"""
        super().__init__("", output_folder, chip_config)
        
        # 从芯片配置中获取URL信息
        self.cn_url = chip_config.get('Cn_WebUrl', '')
        self.en_url = chip_config.get('En_WebUrl', '')
        self.zip_url = chip_config.get('Zip_Url', '')
        self.chip_name = chip_config.get('chipName', '')
        
    def get_web_content(self, url, timeout=30, page_type="未知"):
        """获取网页内容，支持身份认证和重试机制"""
        try:
            
            # 根据页面类型设置不同的请求头
            if page_type == "英文官网":
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
                    "Accept-Encoding": "identity",  # 禁用压缩
                    "Referer": "https://nsing.com.sg/",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0"
                }
            else:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": "https://www.nationstech.com/",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0"
                }
            
            # 创建session以保持Cookie
            session = requests.Session()
            session.headers.update(headers)
            
            
            # 先访问主页建立session（对于英文网站）
            if page_type == "英文官网" and "nsing.com.sg" in url:
                try:
                    session.get("https://nsing.com.sg/", timeout=10)
                    time.sleep(1)  # 等待1秒
                except Exception as e:
                    Logger.warning(f"[{page_type}] 访问主页失败: {e}")
            
            # 访问目标页面
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            
            # 直接使用UTF-8解码
            try:
                content = response.content.decode('utf-8')
            except UnicodeDecodeError as e:
                # 尝试其他编码
                try:
                    content = response.content.decode('gbk')
                except UnicodeDecodeError:
                    content = response.content.decode('utf-8', errors='ignore')
            
            return content
        except requests.exceptions.Timeout:
            Logger.error(f"[{page_type}] 网页访问超时: {url}")
            return None
        except requests.exceptions.ConnectionError:
            Logger.error(f"[{page_type}] 网络连接失败: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            Logger.error(f"[{page_type}] HTTP错误: {url}, 状态码: {e.response.status_code}")
            return None
        except Exception as e:
            Logger.error(f"[{page_type}] 获取网页内容失败: {url}, 错误: {e}")
            return None
    
    def extract_content_with_fallback(self, html_content, selectors, fallback_selectors=None, page_type="未知"):
        """使用精确的CSS选择器爬取内容，支持备用选择器机制"""
        if not html_content:
            Logger.warning(f"[{page_type}] HTML内容为空，无法提取内容")
            return {}
        
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            extracted_content = {}
            
            
            success_count = 0
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
                    success_count += 1
                    
                    if selector == ".productsDetail p":
                        # 产品详情描述：提取产品简介文本
                        products_detail_p = soup.select(".productsDetail p")
                        if products_detail_p:
                            content = products_detail_p[0].get_text(strip=True)
                            extracted_content[selector] = content
                        else:
                            extracted_content[selector] = ""
                    elif selector == ".productsFeaturesMain":
                        # 主要特征：保持原始HTML格式
                        content = str(elements[0])
                        extracted_content[selector] = content if content.strip() else ""
                    elif selector == ".typicalApplicationsMain":
                        # 典型应用列表：特殊处理逻辑
                        content = self._extract_typical_applications(elements[0], page_type)
                        extracted_content[selector] = content
                    elif selector == ".productsDisplayArea":
                        # 产品展示表格：保持完整HTML格式
                        element = elements[0]
                        content = self._process_products_display_area(str(element))
                        extracted_content[selector] = content
                    else:
                        # 其他选择器使用原有逻辑
                        content = str(elements[0])
                        extracted_content[selector] = content if content.strip() else ""
                else:
                    extracted_content[selector] = ""
                    
            
            return extracted_content
        except Exception as e:
            Logger.error(f"[{page_type}] 解析HTML内容失败: {e}")
            return {}
    
    def _extract_typical_applications(self, element, page_type="未知"):
        """提取典型应用列表，支持多种备用方案"""
        content = ""
        
        # 方法1: 优先查找.MsoListParagraph元素
        mso_list_elements = element.select(".MsoListParagraph")
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
            p_elements = element.find_all("p")
            if p_elements:
                text_contents = []
                for p_elem in p_elements:
                    text = p_elem.get_text(strip=True)
                    if text and len(text) > 5:
                        text_contents.append(text)
                
                if text_contents:
                    content = "\n".join([f"• {text}" for text in text_contents])
        
        # 方法3: 如果还没有内容，尝试查找li标签
        if not content:
            li_elements = element.find_all("li")
            if li_elements:
                text_contents = []
                for li_elem in li_elements:
                    text = li_elem.get_text(strip=True)
                    if text and len(text) > 5:
                        text_contents.append(text)
                
                if text_contents:
                    content = "\n".join([f"• {text}" for text in text_contents])
        
        # 方法4: 最后尝试直接获取文本并按行分割
        if not content:
            full_text = element.get_text()
            lines = [
                line.strip() for line in full_text.split('\n')
                if line.strip() and len(line.strip()) > 5
            ]
            if lines:
                content = "\n".join([f"• {line}" for line in lines])
        
        if not content:
            Logger.warning(f"[{page_type}] 典型应用内容为空")
        
        return content
    
    
    def _process_products_display_area(self, html_content):
        """处理产品展示表格，保持完整HTML格式并清理样式"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # 检查是否包含table
            table_element = soup.find("table")
            if table_element:
                # 如果包含table，只保留table内容
                table_copy = copy.copy(table_element)
                
                # 处理table内的所有img标签，转换路径为相对路径格式
                for img_tag in table_copy.find_all("img"):
                    src = img_tag.get("src")
                    if src:
                        # 转换图片路径为相对路径格式
                        last_slash_index = src.rfind("/")
                        if last_slash_index != -1:
                            new_src = "./" + src[last_slash_index + 1:]
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
                
                # 添加CSS样式
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
                return f'<div class="productsDisplayArea">\n{str(table_copy)}\n</div>\n\n{css_styles}'
            else:
                # 如果不包含table，处理所有img标签的src
                for img_tag in soup.find_all("img"):
                    src = img_tag.get("src")
                    if src:
                        # 转换图片路径为相对路径格式
                        last_slash_index = src.rfind("/")
                        if last_slash_index != -1:
                            new_src = "./" + src[last_slash_index + 1:]
                            img_tag["src"] = new_src
                        else:
                            new_src = "./" + src
                            img_tag["src"] = new_src
                
                return str(soup)
        except Exception as e:
            Logger.error(f"处理产品展示表格失败: {e}")
            return html_content
    
    def download_chip_main_image(self, html_content, base_url, page_type="未知"):
        """下载芯片主图，固定命名为chip.png"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # 查找.productsDetail下的img标签
            products_detail = soup.select(".productsDetail")
            if not products_detail:
                Logger.warning(f"[{page_type}] 未找到.productsDetail元素")
                return None
            
            img_tag = products_detail[0].find("img")
            if not img_tag:
                Logger.warning(f"[{page_type}] 未找到.productsDetail下的img标签")
                return None
            
            src = img_tag.get("src")
            if not src:
                Logger.warning(f"[{page_type}] img标签没有src属性")
                return None
            
            
            # 确保assets目录存在
            assets_dir = self.output_folder / "doxygen" / "main" / "assets"
            PathUtils.ensure_dir(assets_dir)
            
            # 解析图片URL
            if src.startswith("http"):
                full_img_url = src
            else:
                full_img_url = urljoin(base_url, src)
            
            
            # 固定文件名为chip.png
            chip_img_path = assets_dir / "chip.png"
            
            # 下载图片
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": base_url,
            }
            
            response = requests.get(full_img_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 保存图片（直接覆盖）
            with open(chip_img_path, "wb") as f:
                f.write(response.content)
            
            return "chip.png"
        except Exception as e:
            Logger.error(f"[{page_type}] 下载芯片主图失败: {e}")
            return None
    
    def download_all_images(self, html_content, base_url, page_type="未知"):
        """下载所有图片资源到doxygen/main/assets/目录"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            downloaded_images = []
            
            # 查找所有img标签
            img_tags = soup.find_all("img")
            
            if not img_tags:
                return str(soup), downloaded_images
            
            # 确保assets目录存在
            assets_dir = self.output_folder / "doxygen" / "main" / "assets"
            PathUtils.ensure_dir(assets_dir)
            
            success_count = 0
            for i, img_tag in enumerate(img_tags):
                src = img_tag.get("src")
                if src:
                    
                    # 先下载图片，不管src是什么格式
                    downloaded_filename = self._download_single_image(src, base_url, assets_dir, page_type)
                    if downloaded_filename:
                        # 下载成功，更新图片路径为相对路径格式
                        img_tag["src"] = f"./{downloaded_filename}"
                        downloaded_images.append(downloaded_filename)
                        success_count += 1
                    else:
                        # 如果下载失败，只保留文件名
                        last_slash_index = src.rfind("/")
                        if last_slash_index != -1:
                            new_src = "./" + src[last_slash_index + 1:]
                        else:
                            new_src = "./" + src
                        img_tag["src"] = new_src
            
            return str(soup), downloaded_images
        except Exception as e:
            Logger.error(f"[{page_type}] 下载图片失败: {e}")
            return html_content, []
    
    def process_products_display_area_images(self, html_content, base_url, page_type="未知"):
        """专门处理.productsDisplayArea中的图片下载"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            downloaded_images = []
            
            # 查找.productsDisplayArea元素
            elements = soup.select(".productsDisplayArea")
            if not elements:
                return html_content, downloaded_images
            
            element = elements[0]
            # 查找其中的img标签
            img_tags = element.find_all("img")
            
            if not img_tags:
                return html_content, downloaded_images
            
            # 确保assets目录存在
            assets_dir = self.output_folder / "doxygen" / "main" / "assets"
            PathUtils.ensure_dir(assets_dir)
            
            
            success_count = 0
            for i, img_tag in enumerate(img_tags):
                src = img_tag.get("src")
                if src:
                    
                    # 下载图片
                    downloaded_filename = self._download_single_image(src, base_url, assets_dir, page_type)
                    if downloaded_filename:
                        # 下载成功，更新图片路径为相对路径格式
                        img_tag["src"] = f"./{downloaded_filename}"
                        downloaded_images.append(downloaded_filename)
                        success_count += 1
                    else:
                        # 如果下载失败，只保留文件名
                        last_slash_index = src.rfind("/")
                        if last_slash_index != -1:
                            new_src = "./" + src[last_slash_index + 1:]
                        else:
                            new_src = "./" + src
                        img_tag["src"] = new_src
            
            # 重新生成.productsDisplayArea的HTML内容
            processed_html = self._process_products_display_area(str(element))
            return processed_html, downloaded_images
            
        except Exception as e:
            Logger.error(f"[{page_type}] 处理.productsDisplayArea图片失败: {e}")
            return html_content, []
    
    def _download_single_image(self, img_url, base_url, assets_dir, page_type="未知", max_retries=3):
        """下载单个图片，支持重试机制"""
        for attempt in range(max_retries):
            try:
                # 解析图片URL
                if img_url.startswith("http"):
                    full_img_url = img_url
                elif img_url.startswith("/"):
                    # 如果是以/开头的绝对路径，根据base_url判断使用哪个域名
                    if "nsing.com.sg" in base_url:
                        full_img_url = f"https://nsing.com.sg{img_url}"
                    else:
                        full_img_url = f"https://www.nationstech.com{img_url}"
                elif img_url.startswith("./"):
                    # 如果是./开头的相对路径，去掉./前缀，根据base_url判断使用哪个域名
                    clean_url = img_url[2:]  # 去掉"./"前缀
                    if "nsing.com.sg" in base_url:
                        full_img_url = f"https://nsing.com.sg/{clean_url}"
                    else:
                        full_img_url = f"https://www.nationstech.com/{clean_url}"
                else:
                    # 普通相对路径，使用urljoin
                    full_img_url = urljoin(base_url, img_url)
                
                # 从URL中提取文件名
                parsed_url = urlparse(full_img_url)
                filename = os.path.basename(parsed_url.path)
                
                if not filename:
                    filename = "image.jpg"
                
                if not os.path.splitext(filename)[1]:
                    filename += ".jpg"
                
                # 设置请求头
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Referer": base_url,
                }
                
                # 下载图片
                response = requests.get(full_img_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # 保存图片（直接覆盖）
                img_path = assets_dir / filename
                with open(img_path, "wb") as f:
                    f.write(response.content)
                
                return filename
                
            except Exception as e:
                if attempt < max_retries - 1:
                    # 不是最后一次尝试，记录警告并等待后重试
                    time.sleep(1)  # 等待1秒后重试
                else:
                    # 最后一次尝试失败，记录错误
                    Logger.error(f"[{page_type}] 下载图片失败，已重试{max_retries}次: {img_url}, 错误: {e}")
                    return None
    
    def generate_overview_md(self, content_data, language="cn", title_only=False):
        """生成Markdown文档"""
        try:
            # 确保输出目录存在
            output_dir = self.output_folder / "doxygen" / "main" / "modules" / language
            PathUtils.ensure_dir(output_dir)
            
            output_path = output_dir / "00_overview.md"
            
            # 根据语言设置标题和内容
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
                FileUtils.write_file(output_path, md_content)
                return True
            else:
                # 生成完整的Markdown内容
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
                
                # 添加"查看更多"链接
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
            FileUtils.write_file(output_path, md_content)
            return True
        except Exception as e:
            Logger.error(f"生成overview.md失败: {e}")
            return False
    
    def update_doxyfile_config(self, image_files):
        """更新Doxyfile配置，添加所有下载的图片文件"""
        try:
            # 需要更新的Doxyfile文件
            doxyfile_files = ["Doxyfile_zh", "Doxyfile_en"]
            
            for doxyfile_name in doxyfile_files:
                doxyfile_path = self.output_folder / "doxygen" / "main" / doxyfile_name
                
                if doxyfile_path.exists():
                    # 读取Doxyfile内容
                    content = FileUtils.read_file_with_encoding(doxyfile_path)
                    
                    # 构建新的HTML_EXTRA_FILES配置
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
                    
                    # 使用正则表达式替换现有配置或添加新配置
                    pattern = r"HTML_EXTRA_FILES\s*=.*?(?=\n\w|$)"
                    replacement = html_extra_files_config
                    
                    if re.search(pattern, content, re.DOTALL):
                        # 如果找到现有配置，替换它
                        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                    else:
                        # 如果没有找到，在文件末尾添加
                        new_content = content + f"\n\n{html_extra_files_config}\n"
                    
                    # 写回文件
                    FileUtils.write_file(doxyfile_path, new_content)
                    
        except Exception as e:
            Logger.error(f"更新Doxyfile配置失败: {e}")
    
    def crawl_and_generate(self):
        """执行完整的爬取和生成流程"""
        try:
            # 定义精确的CSS选择器
            selectors = [
                ".productsDetail p",
                ".productsDisplayArea",
                ".typicalApplicationsMain",
                ".productsFeaturesMain",
            ]
            
            # 定义备用选择器机制
            fallback_selectors = {
                ".typicalApplicationsMain": [
                    ".typicalApplications",
                    ".applications",
                    ".typical-applications",
                    ".app-list",
                    ".application-list",
                    ".typical-apps",
                    ".apps"
                ],
                ".productsFeaturesMain": [
                    ".productsFeatures",
                    ".features",
                    ".product-features",
                    ".feature-list",
                    ".specs",
                    ".specifications",
                    ".characteristics"
                ],
                ".productsDisplayArea": [
                    ".productsDisplay",
                    ".display",
                    ".product-display",
                    ".product-table",
                    ".model-list",
                    ".product-list",
                    ".models"
                ],
                ".productsDetail p": [
                    ".product-detail p",
                    ".description p",
                    ".intro p",
                    ".overview p",
                    ".summary p",
                    ".product-info p",
                    ".product-description p"
                ]
            }
            
            # 收集所有下载的图片
            all_downloaded_images = []
            
            # 多语言处理策略
            if self.cn_url and self.en_url:
                # 方案1：同时有中英文URL时，分别爬取两个页面
                
                # 爬取中文页面
                cn_content = self.get_web_content(self.cn_url, page_type="中文官网")
                cn_extracted = self.extract_content_with_fallback(cn_content, selectors, fallback_selectors, page_type="中文官网") if cn_content else {}
                
                # 爬取英文页面
                en_content = self.get_web_content(self.en_url, page_type="英文官网")
                en_extracted = self.extract_content_with_fallback(en_content, selectors, fallback_selectors, page_type="英文官网") if en_content else {}
                
                # 下载芯片主图
                if cn_content:
                    chip_image = self.download_chip_main_image(cn_content, self.cn_url, page_type="中文官网")
                    if chip_image:
                        all_downloaded_images.append(chip_image)
                
                # 处理中文页面图片
                if cn_extracted:
                    for selector, content in cn_extracted.items():
                        if selector != ".productsDetail p" and content:
                            if selector == ".productsDisplayArea":
                                # 对于.productsDisplayArea，需要从原始HTML中重新提取并处理图片
                                processed_content, images = self.process_products_display_area_images(cn_content, self.cn_url, page_type="中文官网")
                                cn_extracted[selector] = processed_content
                                all_downloaded_images.extend(images)
                            else:
                                # 其他选择器直接处理
                                processed_content, images = self.download_all_images(content, self.cn_url, page_type="中文官网")
                                cn_extracted[selector] = processed_content
                                all_downloaded_images.extend(images)
                
                # 处理英文页面图片
                if en_extracted:
                    for selector, content in en_extracted.items():
                        if selector != ".productsDetail p" and content:
                            if selector == ".productsDisplayArea":
                                # 对于.productsDisplayArea，需要从原始HTML中重新提取并处理图片
                                processed_content, images = self.process_products_display_area_images(en_content, self.en_url, page_type="英文官网")
                                en_extracted[selector] = processed_content
                                all_downloaded_images.extend(images)
                            else:
                                # 其他选择器直接处理
                                processed_content, images = self.download_all_images(content, self.en_url, page_type="英文官网")
                                en_extracted[selector] = processed_content
                                all_downloaded_images.extend(images)
                
                # 生成中文overview.md
                if cn_content:
                    self.generate_overview_md(cn_extracted, "cn")
                
                # 生成英文overview.md
                if en_content:
                    self.generate_overview_md(en_extracted, "en")
                    
            elif self.cn_url:
                # 方案2：只有中文URL时，英文内容直接复制中文内容
                
                # 爬取中文页面
                cn_content = self.get_web_content(self.cn_url, page_type="中文官网")
                cn_extracted = self.extract_content_with_fallback(cn_content, selectors, fallback_selectors, page_type="中文官网") if cn_content else {}
                
                # 下载芯片主图
                if cn_content:
                    chip_image = self.download_chip_main_image(cn_content, self.cn_url, page_type="中文官网")
                    if chip_image:
                        all_downloaded_images.append(chip_image)
                
                # 处理中文页面图片
                if cn_extracted:
                    for selector, content in cn_extracted.items():
                        if selector != ".productsDetail p" and content:
                            if selector == ".productsDisplayArea":
                                # 对于.productsDisplayArea，需要从原始HTML中重新提取并处理图片
                                processed_content, images = self.process_products_display_area_images(cn_content, self.cn_url, page_type="中文官网")
                                cn_extracted[selector] = processed_content
                                all_downloaded_images.extend(images)
                            else:
                                # 其他选择器直接处理
                                processed_content, images = self.download_all_images(content, self.cn_url, page_type="中文官网")
                                cn_extracted[selector] = processed_content
                                all_downloaded_images.extend(images)
                
                # 英文内容直接使用中文内容
                en_extracted = cn_extracted.copy()
                
                # 生成中文overview.md
                if cn_content:
                    self.generate_overview_md(cn_extracted, "cn")
                
                # 生成英文overview.md
                self.generate_overview_md(en_extracted, "en")
                
            else:
                # 方案3：只有英文URL时，仅处理英文页面
                
                # 爬取英文页面
                en_content = self.get_web_content(self.en_url, page_type="英文官网")
                en_extracted = self.extract_content_with_fallback(en_content, selectors, fallback_selectors, page_type="英文官网") if en_content else {}
                # 下载芯片主图
                if en_content:
                    chip_image = self.download_chip_main_image(en_content, self.en_url, page_type="英文官网")
                    if chip_image:
                        all_downloaded_images.append(chip_image)
                
                # 处理英文页面图片
                if en_extracted:
                    for selector, content in en_extracted.items():
                        if selector != ".productsDetail p" and content:
                            if selector == ".productsDisplayArea":
                                # 对于.productsDisplayArea，需要从原始HTML中重新提取并处理图片
                                processed_content, images = self.process_products_display_area_images(en_content, self.en_url, page_type="英文官网")
                                en_extracted[selector] = processed_content
                                all_downloaded_images.extend(images)
                            else:
                                # 其他选择器直接处理
                                processed_content, images = self.download_all_images(content, self.en_url, page_type="英文官网")
                                en_extracted[selector] = processed_content
                                all_downloaded_images.extend(images)
                
                # 生成英文overview.md
                if en_content:
                    self.generate_overview_md(en_extracted, "en")
                
                # 生成只包含标题的中文文件
                self.generate_overview_md({}, "cn", title_only=True)
            
            # 更新Doxyfile配置
            if all_downloaded_images:
                self.update_doxyfile_config(all_downloaded_images)
            
            return True
        except Exception as e:
            Logger.error(f"爬取和生成失败: {e}")
            return False


@timing_decorator
def main():
    """主函数"""
    try:
        # 解析命令行参数
        input_folder, output_folder, chip_config_json = ArgumentParser.parse_standard_args(
            3, "python get_chip_data.py <input_folder> <output_folder> <chip_config_json>"
        )
        
        config_manager = ConfigManager()
        chip_config = config_manager.load_chip_config(chip_config_json)
        
        # 创建爬取器并执行
        crawler = NationTechChipCrawler(output_folder, chip_config)
        
        if not crawler.crawl_and_generate():
            sys.exit(1)
        
    except Exception as e:
        Logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
