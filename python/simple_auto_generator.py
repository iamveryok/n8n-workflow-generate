#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版自动化 n8n 工作流生成器
专门处理定时调用API并保存文件的需求
"""

import json
import sys
import os
import re
import requests
import time
from typing import Dict, Any, List
from config import N8N_CONFIG, OPENROUTER_CONFIG
from openai import OpenAI

# 常见"错误节点类型"到"实际 n8n 节点类型"的映射表
NODE_TYPE_ALIAS_MAP = {
    "n8n-nodes-base.readBinaryFile": "n8n-nodes-base.readWriteFile",
    "n8n-nodes-base.readFile": "n8n-nodes-base.readWriteFile",
    "n8n-nodes-base.writeFile": "n8n-nodes-base.readWriteFile",
    "n8n-nodes-base.writeBinaryFile": "n8n-nodes-base.readWriteFile",  # 如需统一写入也可映射
    "n8n-nodes-base.cron": "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.manual": "n8n-nodes-base.manualTrigger",
    # 可根据实际情况继续补充
}

class SimpleAutoGenerator:
    def __init__(self):
        """初始化简化版生成器"""
        print("开始初始化 SimpleAutoGenerator...")
        
        self.n8n_base_url = N8N_CONFIG["base_url"]
        self.n8n_api_key = N8N_CONFIG["api_key"]
        print(f"N8N配置信息:")
        print(f"  基础URL: {self.n8n_base_url}")
        print(f"  API密钥: {self.n8n_api_key[:20]}..." if self.n8n_api_key else "  API密钥: 未设置")
        
        # 初始化OpenAI客户端
        try:
            print("正在初始化OpenAI客户端...")
            self.client = OpenAI(
                api_key=OPENROUTER_CONFIG["api_key"],
                base_url=OPENROUTER_CONFIG["api_base"],
                timeout=120.0
            )
            print("OpenAI客户端初始化成功")
            print(f"  API基础URL: {OPENROUTER_CONFIG['api_base']}")
            print(f"  模型: {OPENROUTER_CONFIG['model']}")
        except Exception as e:
            print(f"OpenAI客户端初始化失败: {str(e)}")
            raise
        
        # 加载base_node.json
        print("正在加载base_node.json文件...")
        self.base_nodes = self.load_base_nodes()
        print(f"成功加载 {len(self.base_nodes)} 个节点规范")
        
        print("SimpleAutoGenerator 初始化完成！")
    
    def load_base_nodes(self) -> Dict:
        """加载base_node.json文件"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            base_node_path = os.path.join(base_dir, 'base_node.json')
            print(f"  读取base_node.json文件: {base_node_path}")
            with open(base_node_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            nodes = data.get('nodes', [])
            print(f"  解析到 {len(nodes)} 个节点定义")
            # 构建节点类型映射
            node_dict = {node['type']: node for node in nodes}
            print(f"  构建节点类型映射，共 {len(node_dict)} 个唯一节点类型")
            # 显示一些节点类型示例
            sample_types = list(node_dict.keys())[:5]
            print(f"  节点类型示例: {sample_types}")
            return node_dict
        except FileNotFoundError:
            print("找不到base_node.json文件")
            return {}
        except json.JSONDecodeError as e:
            print(f"base_node.json文件格式错误: {e}")
            return {}
        except Exception as e:
            print(f"加载base_node.json失败: {e}")
            return {}
    
    def _retry_with_backoff(self, func, max_retries=3, initial_delay=1):
        """使用指数退避的重试机制"""
        retries = 0
        delay = initial_delay
        
        while retries < max_retries:
            try:
                return func()
            except Exception as e:
                retries += 1
                if retries == max_retries:
                    print(f"达到最大重试次数 ({max_retries})，操作失败")
                    raise
                
                print(f"操作失败，{delay}秒后进行第{retries}次重试: {str(e)}")
                time.sleep(delay)
                delay *= 2
    
    def analyze_nodes_with_ai(self, description: str) -> List[str]:
        """使用大模型分析需要哪些节点类型"""
        print("\n步骤1: 使用大模型分析需要的节点类型...")
        print(f"用户需求: {description}")
        
        prompt = f"""
你是n8n自动化专家。请分析用户的自然语言描述，确定需要使用的n8n节点类型。

用户需求：{description}

请分析并返回需要的节点类型列表，格式为JSON数组，只包含节点类型名称。

常见的n8n节点类型包括：
- 触发器节点：n8n-nodes-base.cron（定时）、n8n-nodes-base.webhook（Webhook）、n8n-nodes-base.manualTrigger（手动）
- 数据获取：n8n-nodes-base.httpRequest（HTTP请求）、n8n-nodes-base.mySql（MySQL）、n8n-nodes-base.postgres（PostgreSQL）
- 数据处理：n8n-nodes-base.function（函数）、n8n-nodes-base.if（条件判断）、n8n-nodes-base.set（设置字段）
- 数据输出：n8n-nodes-base.writeBinaryFile（写入文件）、n8n-nodes-base.emailSend（发送邮件）

请根据用户需求选择合适的节点类型，只返回JSON数组格式，例如：
["n8n-nodes-base.cron", "n8n-nodes-base.httpRequest", "n8n-nodes-base.writeBinaryFile"]
"""
        
        def _analyze():
            print("  正在调用大模型分析节点类型...")
            print(f"  使用模型: {OPENROUTER_CONFIG['model']}")
            
            response = self.client.chat.completions.create(
                model=OPENROUTER_CONFIG["model"],
                messages=[
                    {"role": "system", "content": "你是一个专业的n8n节点分析专家。请根据用户需求分析需要的节点类型，只返回JSON数组格式。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            print(f"  大模型原始响应: {content}")
            
            try:
                # 清理响应内容
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                print(f"  清理后的响应: {content}")
                
                node_types = json.loads(content)
                if isinstance(node_types, list):
                    print("  成功解析节点类型列表")
                    print(f"  分析结果: {node_types}")
                    return node_types
                else:
                    raise ValueError("返回格式不是数组")
            except json.JSONDecodeError as e:
                print(f"  JSON解析失败: {str(e)}")
                print(f"  响应内容: {content}")
                raise ValueError("大模型返回的不是有效的JSON格式")

        return self._retry_with_backoff(_analyze)
    
    def get_node_parameters(self, node_types: List[str]) -> Dict:
        """从base_node.json获取节点参数规范"""
        print("\n步骤2: 从base_node.json获取节点参数规范...")
        print(f"需要查找的节点类型: {node_types}")
        
        node_specs = {}
        for node_type in node_types:
            real_type = self.get_real_node_type(node_type)
            print(f"\n查找节点: {node_type}（实际查找: {real_type}）")
            if real_type in self.base_nodes:
                node_specs[node_type] = self.base_nodes[real_type]
                spec = self.base_nodes[real_type]
                print(f"  找到节点规范: {real_type}")
                print(f"  节点名称: {spec.get('nodeName', 'Unknown')}")
                print(f"  描述: {spec.get('description', 'No description')}")
                if isinstance(spec.get('parameters', []), list):
                    param_count = len(spec.get('parameters', []))
                elif isinstance(spec.get('parameters', {}), dict):
                    param_count = len(spec.get('parameters', {}).keys())
                else:
                    param_count = 0
                print(f"  参数数量: {param_count}")
            else:
                print(f"  未找到节点规范: {real_type}")
                print(f"  可用的节点类型: {list(self.base_nodes.keys())[:5]}...")
        
        print(f"\n参数规范获取结果:")
        print(f"  成功获取 {len(node_specs)} 个节点的参数规范")
        print(f"  缺失 {len(node_types) - len(node_specs)} 个节点的参数规范")
        
        return node_specs
    
    def generate_workflow_with_ai(self, description: str, node_specs: Dict) -> Dict:
        """使用大模型根据节点规范生成工作流配置"""
        print("\n步骤3: 使用大模型根据节点规范生成工作流配置...")
        print(f"用户需求: {description}")
        print(f"节点规范数量: {len(node_specs)}")
        
        # 构建节点规范信息
        specs_info = ""
        for node_type, spec in node_specs.items():
            specs_info += f"\n节点类型: {node_type}\n"
            specs_info += f"描述: {spec.get('description', '无描述')}\n"
            specs_info += "参数规范:\n"
            params = spec.get('parameters', [])
            if isinstance(params, list):
                for param in params:
                    specs_info += f"  - {param['name']} ({param['type']}): {param['description']}\n"
            elif isinstance(params, dict):
                # 兼容 JSON Schema 格式
                def parse_schema(schema, prefix=''):
                    lines = []
                    if 'properties' in schema:
                        for k, v in schema['properties'].items():
                            name = f"{prefix}{k}"
                            typ = v.get('type', 'unknown')
                            desc = v.get('description', '')
                            lines.append(f"  - {name} ({typ}): {desc}")
                            # 递归嵌套
                            lines += parse_schema(v, prefix=name + '.')
                    return lines
                specs_info += '\n'.join(parse_schema(params)) + '\n'
            else:
                specs_info += "  - 无参数\n"
        
        print("构建的节点规范信息:")
        print(specs_info)
        
        prompt = f"""
你是n8n自动化专家。请根据用户的自然语言描述和节点参数规范，生成一个完整的 n8n 工作流配置（JSON）。

用户需求：{description}

节点参数规范：{specs_info}

重要说明：
- 请严格按照提供的节点参数规范来配置节点
- 使用节点规范中指定的type字段作为节点类型
- 根据参数规范设置正确的参数值
- 对于options类型的参数，必须使用规范中指定的可选值之一
- 对于有默认值的参数，如果不指定则使用默认值
- 每个节点都需要包含id字段（可以使用UUID格式）
- 每个节点都需要包含position字段（如[250, 300]）用于在n8n界面中显示位置
- 如果节点需要credentials（如数据库连接），请通过credentials字段引用预配置的连接
- 连接关系应该使用节点名称而不是数字ID
- 确保所有必需的字段都正确设置

请根据用户需求和节点规范，生成完整的工作流配置：
- 使用提供的节点类型（注意使用实际的n8n节点类型名称）
- 按照参数规范设置正确的参数值
- 建立正确的节点连接关系
- 包含完整的settings配置

要求：
- 只返回JSON格式，不要包含其他文本
- 包含完整的name、settings、nodes、connections字段
- settings需包含executionOrder、saveDataErrorExecution、saveDataSuccessExecution、saveExecutionProgress、saveManualExecutions、timezone
- 节点之间要有正确的连接关系
- 严格按照参数规范设置参数
- 使用实际的n8n节点类型名称

示例格式:

{{
  "name": "工作流名称",
  "settings": {{
    "executionOrder": "v1",
    "saveDataErrorExecution": "all",
    "saveDataSuccessExecution": "all",
    "saveExecutionProgress": true,
    "saveManualExecutions": true,
    "timezone": "UTC"
  }},
  "nodes": [
    {{
      "id": "uuid-1",
      "name": "节点名称",
      "type": "节点类型",
      "typeVersion": 1,
      "position": [250, 300],
      "parameters": {{
        "_comment": "根据节点规范设置的参数"
      }}
    }}
  ],
  "connections": {{
    "节点名称": {{
      "main": [
        [
          {{
            "node": "目标节点名称",
            "type": "main",
            "index": 0
          }}
        ]
      ]
    }}
  }}
}}
"""
        
        def _generate():
            print("  正在调用大模型生成工作流...")
            print(f"  使用模型: {OPENROUTER_CONFIG['model']}")
            
            response = self.client.chat.completions.create(
                model=OPENROUTER_CONFIG["model"],
                messages=[
                    {"role": "system", "content": "你是一个专业的n8n工作流配置专家。请根据用户需求和节点参数规范生成完整的工作流配置，严格按照参数规范设置参数。只返回有效的JSON格式，不要添加任何其他文本。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            
            content = response.choices[0].message.content
            print(f"  大模型原始响应: {content}")
            
            try:
                # 尝试清理响应内容，移除可能的markdown代码块标记
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                print(f"  清理后的响应: {content}")
                
                workflow_config = json.loads(content)
                print("  成功解析工作流配置JSON")
                print("  工作流信息:")
                print(f"    名称: {workflow_config.get('name', 'Unknown')}")
                print(f"    节点数量: {len(workflow_config.get('nodes', []))}")
                print(f"    连接数量: {len(workflow_config.get('connections', {}))}")
                return workflow_config
            except json.JSONDecodeError as e:
                print(f"  JSON解析失败: {str(e)}")
                print(f"  清理后的响应内容: {content}")
                raise ValueError("大模型生成的配置不是有效的JSON格式")

        return self._retry_with_backoff(_generate)
    
    def _clean_workflow_json(self, workflow_config: Dict) -> Dict:
        """清理和规范化工作流 JSON，确保其符合 n8n 要求"""
        print("\n步骤4: 清理和规范化工作流 JSON...")
        
        # 验证节点和连接
        if not workflow_config.get("nodes"):
            raise ValueError("工作流必须包含至少一个节点")
        
        if not workflow_config.get("connections"):
            raise ValueError("工作流必须包含节点之间的连接关系")
        
        print("清理前的工作流信息:")
        print(f"  节点数量: {len(workflow_config.get('nodes', []))}")
        print(f"  连接数量: {len(workflow_config.get('connections', {}))}")
        
        nodes = workflow_config.get("nodes", [])

        for i, node in enumerate(nodes):
            print(f"  清理节点 {i+1}: {node.get('name', 'Unknown')} ({node.get('type', 'Unknown')})")
            parameters = node.get("parameters", {})

            # 验证参数是否符合规范
            node_type = node.get("type")
            if node_type in self.base_nodes:
                node_spec = self.base_nodes[node_type]
                for param_name, param_value in parameters.items():
                    # 查找对应的参数规范
                    param_spec = None
                    for spec_param in node_spec.get('parameters', []):
                        if spec_param['name'] == param_name:
                            param_spec = spec_param
                            break
                    
                    if param_spec:
                        # 检查options类型参数的值是否在允许范围内
                        if param_spec.get('type') == 'options' and param_spec.get('options'):
                            if param_value not in param_spec['options']:
                                print(f"    参数 {param_name} 的值 '{param_value}' 不在允许范围内")
                                print(f"      允许的值: {param_spec['options']}")
                                # 使用默认值或第一个允许值
                                if param_spec.get('default') in param_spec['options']:
                                    parameters[param_name] = param_spec['default']
                                    print(f"      已修正为默认值: {param_spec['default']}")
                                else:
                                    parameters[param_name] = param_spec['options'][0]
                                    print(f"      已修正为第一个允许值: {param_spec['options'][0]}")

            # 1. 将空的 'options: {}' 转换为 'options: []'
            if "options" in parameters and isinstance(parameters["options"], dict) and not parameters["options"]:
                parameters["options"] = []  # 转换为空列表
                print("    转换空options对象为数组")

            # 2. 确保集合类型参数是 [] 而不是 {}
            for param_name, param_value in parameters.items():
                if isinstance(param_value, dict) and not param_value:
                    # 检查是否是 n8n 中常见的集合类型参数
                    if param_name in ["bodyParameters", "conditions"]:
                        # 检查其子字段
                        if "values" in param_value and isinstance(param_value["values"], dict) and not param_value["values"]:
                            param_value["values"] = []
                            print(f"    转换 {param_name}.values 为空数组")
                        if "boolean" in param_value and isinstance(param_value["boolean"], dict) and not param_value["boolean"]:
                            param_value["boolean"] = []
                            print(f"    转换 {param_name}.boolean 为空数组")

            node["parameters"] = parameters
        workflow_config["nodes"] = nodes
        
        # 移除 n8n API 创建工作流时不允许的顶层属性
        properties_to_remove = ["versionId", "id", "staticData", "meta", "pinData", "createdAt", "updatedAt", "triggerCount"]
        for prop in properties_to_remove:
            if prop in workflow_config:
                del workflow_config[prop]
                print(f"  移除不允许的属性: {prop}")

        # 移除 'active' 属性，因为它在创建时通常是只读的或不允许设置
        if "active" in workflow_config:
            del workflow_config["active"]
            print("  移除active属性")

        print("工作流 JSON 清理完成")
        return workflow_config
    
    def deploy_workflow(self, workflow_config: dict) -> dict:
        """部署工作流到n8n"""
        print("\n步骤5: 部署工作流到n8n...")
        headers = {
            "Content-Type": "application/json"
        }
        if self.n8n_api_key:
            headers["X-N8N-API-KEY"] = self.n8n_api_key
            print("使用API密钥认证")
        else:
            print("未设置API密钥，使用无认证模式")

        def _deploy():
            print(f"  正在发送请求到N8N服务器: {self.n8n_base_url}/api/v1/workflows")
            print(f"  请求头: {list(headers.keys())}")
            
            response = requests.post(
                f"{self.n8n_base_url}/api/v1/workflows",
                headers=headers,
                json=workflow_config,
                timeout=60
            )
            
            print(f"  响应状态码: {response.status_code}")
            
            if response.status_code not in (200, 201):
                print(f"  部署失败，状态码: {response.status_code}")
                print(f"  错误响应: {response.text}")
                raise Exception(f"部署失败: {response.text}")
            
            result = response.json()
            print("  工作流部署成功")
            print("  部署结果:")
            print(f"    工作流ID: {result.get('id', 'Unknown')}")
            print(f"    工作流名称: {result.get('name', 'Unknown')}")
            print(f"    激活状态: {result.get('active', 'Unknown')}")
            return result

        return self._retry_with_backoff(_deploy)
    
    def auto_generate_and_deploy(self, description: str) -> Dict:
        """自动生成并部署工作流"""
        print(f"\n开始处理用户需求: {description}")
        print("=" * 80)
        
        # 步骤1: 使用大模型分析需要的节点类型
        node_types = self.analyze_nodes_with_ai(description)
        print(f"步骤1完成 - 分析结果: {node_types}")
        
        # 步骤2: 从base_node.json获取节点参数规范
        node_specs = self.get_node_parameters(node_types)
        print(f"步骤2完成 - 获取到 {len(node_specs)} 个节点的参数规范")
        
        # 步骤3: 使用大模型根据规范生成工作流配置
        workflow_config = self.generate_workflow_with_ai(description, node_specs)
        print(f"步骤3完成 - 工作流配置生成完成")
        
        # 步骤4: 清理工作流配置
        cleaned_config = self._clean_workflow_json(workflow_config)
        print(f"步骤4完成 - 工作流配置清理完成")
        
        # 步骤5: 保存工作流配置到config目录
        print("\n步骤5: 保存工作流配置到config目录...")
        try:
            save_dir = os.path.join(os.path.dirname(__file__), 'config')
            os.makedirs(save_dir, exist_ok=True)
            print(f"  确保目录存在: {save_dir}")
            
            # 生成文件名（使用时间戳避免重复）
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            workflow_name = workflow_config['name'].replace(' ', '_')
            config_file_path = os.path.join(save_dir, f"{workflow_name}_{timestamp}.json")
            
            # 只保存n8n工作流配置
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_config, f, ensure_ascii=False, indent=2)
            
            print(f"  工作流配置已保存到: {config_file_path}")
            
        except Exception as e:
            print(f"  保存工作流配置失败: {e}")
        
        # 步骤6: 部署到n8n
        deployment_result = self.deploy_workflow(cleaned_config)
        print(f"步骤6完成 - 部署成功！")
        
        print("\n" + "=" * 80)
        print("所有步骤完成！")
        
        result = {
            'description': description,
            'workflow_config': cleaned_config,
            'deployment_result': deployment_result,
            'config_file': config_file_path
        }
        
        # 只返回 result，不再 print 日志
        return result

    def get_real_node_type(self, node_type: str) -> str:
        """根据别名映射表获取实际 n8n 节点类型"""
        return NODE_TYPE_ALIAS_MAP.get(node_type, node_type)

def main():
    import sys
    import json
    if len(sys.argv) < 2:
        sys.exit(1)
    description = sys.argv[1]
    generator = SimpleAutoGenerator()
    try:
        result = generator.auto_generate_and_deploy(description)
        # 只输出 workflow_config，包裹 JSON_RESULT_START/END，便于 TS 端正则提取
        sys.stdout.write("JSON_RESULT_START\n")
        sys.stdout.write(json.dumps(result['workflow_config'], ensure_ascii=False))
        sys.stdout.write("\nJSON_RESULT_END\n")
        sys.stdout.flush()
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    import sys
    sys.stderr = open('nul', 'w')  # Windows 下屏蔽所有错误输出
    main() 