import sys
import os
import json
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from n8n_generator import N8NGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI()

# 初始化 N8N 生成器
n8n_generator = N8NGenerator()

class WorkflowRequest(BaseModel):
    description: str

@app.post("/generate_workflow")
async def generate_workflow(request: WorkflowRequest) -> Dict[str, Any]:
    """生成工作流"""
    try:
        logger.info(f"收到工作流生成请求: {request.description}")
        result = n8n_generator.generate_and_deploy(request.description)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"生成工作流时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python api_service.py <api_name> <parameters_json>")
        sys.exit(1)

    api_name = sys.argv[1]
    try:
        params = json.loads(sys.argv[2])
    except json.JSONDecodeError:
        print("参数必须是有效的 JSON 格式")
        sys.exit(1)

    print(f"Python script started")
    print(f"Command line arguments: {sys.argv}")
    print(f"Parsed API name: {api_name}")
    print(f"Parsed parameters: {params}")

    try:
        print(f"正在调用API: {api_name}")
        print(f"参数: {params}")

        if api_name == "generate_workflow":
            result = n8n_generator.generate_and_deploy(params["description"])
            print(json.dumps({"status": "success", "data": result}))
        else:
            print(json.dumps({"error": f"未知的 API: {api_name}"}))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": f"Error processing request: {str(e)}"}))
        sys.exit(1)

if __name__ == "__main__":
    main() 