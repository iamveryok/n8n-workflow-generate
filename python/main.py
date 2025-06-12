from n8n_generator import N8NGenerator
import json
import logging
import traceback

logger = logging.getLogger(__name__)

def main():
    try:
        generator = N8NGenerator()
        
        print("欢迎使用AI驱动的n8n工作流生成器！")
        print("请输入您想要实现的工作流描述：")
        
        while True:
            description = input("\n> ")
            if description.lower() in ['exit', 'quit', '退出']:
                break
                
            try:
                result = generator.generate_and_deploy(description)
                print("\n工作流生成并部署成功！")
                print("\n工作流配置：")
                print(json.dumps(result["workflow_config"], indent=2, ensure_ascii=False))
                print("\n部署结果：")
                print(json.dumps(result["deployment_result"], indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"\n错误：{str(e)}")
                print("\n详细错误信息：")
                print(traceback.format_exc())
            
            print("\n继续输入新的工作流描述，或输入'exit'退出：")
    except Exception as e:
        print(f"程序初始化失败：{str(e)}")
        print("\n详细错误信息：")
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 