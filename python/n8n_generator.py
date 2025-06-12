import json
import requests
import logging
import time
from openai import OpenAI
from config import OPENROUTER_CONFIG, N8N_CONFIG
import os
import sys
from typing import Dict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# 设置标准输出和标准错误的编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

class N8NGenerator:
    def __init__(self):
        logger.info("初始化N8NGenerator...")
        try:
            self.client = OpenAI(
                api_key=OPENROUTER_CONFIG["api_key"],
                base_url=OPENROUTER_CONFIG["api_base"],
                timeout=120.0
            )
            logger.info("OpenAI客户端初始化成功")
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {str(e)}")
            raise

        self.n8n_base_url = N8N_CONFIG["base_url"]
        self.n8n_api_key = N8N_CONFIG["api_key"]
        logger.info(f"N8N配置加载完成，基础URL: {self.n8n_base_url}")

        # 确保配置目录存在
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
        os.makedirs(self.config_dir, exist_ok=True)

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
                    logger.error(f"达到最大重试次数 ({max_retries})，操作失败")
                    raise
                
                logger.warning(f"操作失败，{delay}秒后进行第{retries}次重试: {str(e)}")
                time.sleep(delay)
                delay *= 2

    def _clean_workflow_json(self, workflow_config: Dict) -> Dict:
        """清理和规范化工作流 JSON，确保其符合 n8n 要求"""
        logger.info("开始清理工作流 JSON...")
        
        # 验证节点和连接
        if not workflow_config.get("nodes"):
            raise ValueError("工作流必须包含至少一个节点")
        
        if not workflow_config.get("connections"):
            raise ValueError("工作流必须包含节点之间的连接关系")
        
        nodes = workflow_config.get("nodes", [])

        for node in nodes:
            parameters = node.get("parameters", {})

            # 1. 将空的 'options: {}' 转换为 'options: []'
            if "options" in parameters and isinstance(parameters["options"], dict) and not parameters["options"]:
                parameters["options"] = []  # 转换为空列表

            # 2. 确保 readBinaryFile 节点有 path 参数 (如果模型生成了此节点)
            if node.get("type") == "n8n-nodes-base.readBinaryFile":
                if "path" not in parameters:
                    parameters["path"] = "/path/to/your/input.csv"  # 提供默认值

            # 3. 确保集合类型参数是 [] 而不是 {{}}
            # 例如 bodyParameters.values, conditions.boolean
            for param_name, param_value in parameters.items():
                if isinstance(param_value, dict) and not param_value:
                    # 检查是否是 n8n 中常见的集合类型参数，可以根据需要扩展列表
                    if param_name in ["bodyParameters", "conditions"]:
                        # 检查其子字段，例如 bodyParameters 内部的 values
                        if "values" in param_value and isinstance(param_value["values"], dict) and not param_value["values"]:
                            param_value["values"] = []
                        if "boolean" in param_value and isinstance(param_value["boolean"], dict) and not param_value["boolean"]:
                            param_value["boolean"] = []

            node["parameters"] = parameters
        workflow_config["nodes"] = nodes
        
        # 移除 n8n API 创建工作流时不允许的顶层属性
        properties_to_remove = ["versionId", "id", "staticData", "meta", "pinData", "createdAt", "updatedAt", "triggerCount"]
        for prop in properties_to_remove:
            if prop in workflow_config:
                del workflow_config[prop]

        # 移除 'active' 属性，因为它在创建时通常是只读的或不允许设置
        if "active" in workflow_config:
            del workflow_config["active"]

        logger.info("工作流 JSON 清理完成")
        return workflow_config

    def generate_workflow(self, description: str) -> dict:
        """根据自然语言描述生成n8n工作流配置"""
        logger.info(f"开始生成工作流，描述: {description}")
        
        prompt = f"""
你是n8n自动化专家。请根据用户的自然语言描述，生成一个完整的 n8n 工作流配置（JSON），包括 name、settings、nodes、connections 等字段。节点类型、参数和连接方式请根据用户需求自动判断和生成。settings 字段需包含 executionOrder、saveDataErrorExecution、saveDataSuccessExecution、saveExecutionProgress、saveManualExecutions、timezone。只返回 JSON，不要包含其他文本。

用户需求：{description}
            
            示例格式：
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
        // ... 节点列表 ...
                ],
                "connections": {{
        // ... 节点连接 ...
    }}
}}
"""
        
        def _generate():
            logger.info("正在调用OpenRouter API...")
            response = self.client.chat.completions.create(
                model=OPENROUTER_CONFIG["model"],
                messages=[
                    {"role": "system", "content": "你是一个专业的n8n工作流配置专家。请根据用户描述生成完整的工作流配置，只返回有效的JSON格式，不要添加任何其他文本。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            logger.info(f"OpenRouter API响应内容: {content}")
            
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
                
                workflow_config = json.loads(content)
                logger.info("成功解析工作流配置JSON")
                # 不再修正connections字段，直接使用AI生成的
                # workflow_config["connections"] = self._fix_connections_format(
                #     workflow_config.get("connections", {}),
                #     workflow_config.get("nodes", [])
                # )
                return workflow_config
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
                logger.error(f"清理后的响应内容: {content}")
                raise ValueError("AI生成的配置不是有效的JSON格式")

        return self._retry_with_backoff(_generate)

    def deploy_workflow(self, workflow_config: dict) -> dict:
        """部署工作流到n8n"""
        logger.info("开始部署工作流...")
        headers = {
            "Content-Type": "application/json"
        }
        if self.n8n_api_key:
            headers["X-N8N-API-KEY"] = self.n8n_api_key

        def _deploy():
            logger.info(f"正在发送请求到N8N服务器: {self.n8n_base_url}/api/v1/workflows")
            response = requests.post(
                f"{self.n8n_base_url}/api/v1/workflows",
                headers=headers,
                json=workflow_config,
                timeout=60
            )
            
            if response.status_code not in (200, 201):
                logger.error(f"部署失败，状态码: {response.status_code}")
                logger.error(f"错误响应: {response.text}")
                raise Exception(f"部署失败: {response.text}")
            
            logger.info("工作流部署成功")
            return response.json()

        return self._retry_with_backoff(_deploy)

    def generate_and_deploy(self, description: str) -> dict:
        """生成并部署工作流"""
        try:
            logger.info("开始生成和部署工作流...")
            workflow_config = self.generate_workflow(description)
            deployment_result = self.deploy_workflow(workflow_config)
            logger.info("工作流生成和部署完成")
            # 保存工作流配置JSON到config目录
            try:
                save_dir = os.path.join(os.path.dirname(__file__), 'config')
                os.makedirs(save_dir, exist_ok=True)
                wf_name = workflow_config.get('name', 'workflow')
                file_path = os.path.join(save_dir, f"{wf_name}_部署结果.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'workflow_config': workflow_config,
                        'deployment_result': deployment_result
                    }, f, ensure_ascii=False, indent=2)
                logger.info(f"工作流配置已保存到: {file_path}")
            except Exception as e:
                logger.error(f"保存工作流配置JSON失败: {str(e)}")
            return {
                "workflow_config": workflow_config,
                "deployment_result": deployment_result
            }
        except Exception as e:
            logger.error(f"生成和部署过程中发生错误: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        generator = N8NGenerator()
        # 示例描述，你可以根据需要修改
        description = "创建一个工作流，每分钟调用一次 https://api.example.com/data 接口获取数据，将返回的数据保存为 JSON 文件。文件名为 data_当前时间戳.json，保存在 D:/output 目录下。"
        
        # 由于 main 函数只接受一个参数，这里直接传递 description
        # 如果你需要模拟 test_node.ts 的行为，请在 test_node.ts 中直接调用 generate_and_deploy 方法

        # 为了在命令行中测试，这里调用 generate_and_deploy
        result = generator.generate_and_deploy(description)
        # logger.info("工作流生成并部署成功") # 移除此行，确保只有JSON输出
        print(json.dumps(result, ensure_ascii=False, indent=2)) # 将结果以JSON格式打印到标准输出

    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}") 