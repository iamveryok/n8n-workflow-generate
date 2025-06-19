#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试 simple_auto_generator
"""

from simple_auto_generator import SimpleAutoGenerator

# 测试自然语言输入
# description = "从本地文件系统读取文件，目录是D:\\typescript_code\\n8n\\packages\\nodes-base\\nodes\\HttpRequest\\HttpRequest.node.json，获取前10条数据并保存到D:/typescript_code/n8n-workflow-generate/python/data/目录，然后通过merge节点合并数据"
# description = "每5分钟查询MySQL数据库user表，获取前10条数据并保存到D:/typescript_code/n8n-workflow-generate/python/data/目录，文件以时间戳命名"
description = "每5分钟通过set节点生成随机json，然后通过code节点将json转为流，再写入文件到D盘"
generator = SimpleAutoGenerator()
result = generator.auto_generate_and_deploy(description)
print("✅ 测试完成！") 