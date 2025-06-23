#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试 simple_auto_generator
"""

from simple_auto_generator import SimpleAutoGenerator


# n8n 的 Function 节点运行环境是沙箱（sandbox），并不支持 Node.js 的 Readable（即 require('stream').Readable）等 Node 原生模块。
# Function 节点只能用纯 JavaScript，不支持引入 Node.js 的 stream、fs 等模块。
#description = "每5小时生成随机json，然后将json转为流，再写入文件到D盘"

# description = "当有外部系统通过Webhook推送数据时，自动将数据写入MySQL数据库的user表"

description = "每小时检查FTP服务器上的/usr/logs目录，如果有新文件则自动下载到本地"


generator = SimpleAutoGenerator()
result = generator.auto_generate_and_deploy(description)
print("✅ 测试完成！") 