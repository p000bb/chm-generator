#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_decompression.py - 自动解压所选源文件一级目录下面的zip包
"""

import os
import sys
import time


def main():
    """主函数"""
    # 获取当前脚本的文件名
    script_name = os.path.basename(__file__)
    print(f"当前脚本文件名: {script_name}")

    # 等待2秒钟
    print("脚本执行中...")
    time.sleep(2)

    print("脚本执行完成！")


if __name__ == "__main__":
    main()
