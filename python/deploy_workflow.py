import os
import sys
import json
import requests
from config import N8N_CONFIG

def list_all_json_files(root_dir):
    json_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.json'):
                rel_path = os.path.relpath(os.path.join(dirpath, filename), root_dir)
                json_files.append(rel_path)
    return json_files

def load_workflow_template(template_name, templates_dir='workflow_templates'):
    file_path = os.path.join(os.path.dirname(__file__), templates_dir, template_name)
    if not os.path.exists(file_path):
        print(f"模板文件不存在: {file_path}")
        sys.exit(1)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def deploy_workflow_to_n8n(workflow_json, template_name=None):
    # 只保留 n8n API 支持的字段
    allowed_keys = {"name", "nodes", "connections", "settings", "tags"}
    filtered_json = {k: v for k, v in workflow_json.items() if k in allowed_keys}
    # 自动补全 name 字段
    if "name" not in filtered_json:
        if template_name:
            filtered_json["name"] = os.path.splitext(os.path.basename(template_name))[0]
        else:
            filtered_json["name"] = "自动导入流程"
    # 自动补全 settings 字段
    if "settings" not in filtered_json:
        filtered_json["settings"] = {
            "executionOrder": "v1",
            "saveDataErrorExecution": "all",
            "saveDataSuccessExecution": "all",
            "saveExecutionProgress": True,
            "saveManualExecutions": True,
            "timezone": "Asia/Shanghai"
        }
    url = f"{N8N_CONFIG['base_url']}/api/v1/workflows"
    headers = {
        'Content-Type': 'application/json',
        'X-N8N-API-KEY': N8N_CONFIG['api_key']
    }
    response = requests.post(url, headers=headers, json=filtered_json)
    try:
        result = response.json()
    except Exception:
        result = response.text
    return response.status_code, result

if __name__ == '__main__':
    templates_dir = os.path.join(os.path.dirname(__file__), 'workflow_templates')
    if len(sys.argv) < 2:
        print("用法: python deploy_workflow.py <模板文件相对路径>")
        print("可用模板:")
        for f in list_all_json_files(templates_dir):
            print(f"  {f}")
        sys.exit(1)
    template_name = sys.argv[1]
    workflow_json = load_workflow_template(template_name)
    status, result = deploy_workflow_to_n8n(workflow_json, template_name)
    print(f'部署结果: 状态码={status}, 返回={result}') 