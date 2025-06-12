// 导入所需的模块
import * as path from 'path';
import { spawn } from 'child_process';

// 定义 WorkflowGenerator 类
class WorkflowGenerator {
    private pythonPath: string;
    private scriptPath: string;

    constructor() {
        console.log('WorkflowGenerator 构造函数被调用');
        // 使用正确的conda环境中的Python
        this.pythonPath = 'C:\\Users\\liangwei\\miniconda3\\envs\\ai-agent-n8n\\python.exe';
        // 使用正确的脚本路径
        this.scriptPath = path.resolve(__dirname, '..', 'python', 'n8n_generator.py');
        console.log('Python 路径:', this.pythonPath);
        console.log('脚本路径:', this.scriptPath);
    }

    async execute(description: string): Promise<void> {
        try {
            console.log('开始执行工作流生成...');
            console.log('工作流描述:', description);

            // 检查 Python 路径是否存在
            if (!this.pythonPath) {
                throw new Error('Python 路径未设置');
            }

            // 检查脚本路径是否存在
            if (!this.scriptPath) {
                throw new Error('脚本路径未设置');
            }

            // 执行 Python 脚本
            const pythonProcess = spawn(this.pythonPath, [this.scriptPath, description], {
                env: {
                    ...process.env,
                    PYTHONIOENCODING: 'utf-8',
                    PYTHONUNBUFFERED: '1'  // 禁用 Python 输出缓冲
                },
                stdio: ['pipe', 'pipe', 'pipe']  // 使用管道进行通信
            });

            let output = '';
            let error = '';

            // 处理标准输出
            pythonProcess.stdout.on('data', (data) => {
                const chunk = data.toString('utf-8');
                output += chunk;
                console.log('Python输出:', chunk);
            });

            // 处理标准错误
            pythonProcess.stderr.on('data', (data) => {
                const chunk = data.toString('utf-8');
                error += chunk;
                console.error('Python错误:', chunk);
            });

            // 等待 Python 进程完成
            await new Promise<void>((resolve, reject) => {
                pythonProcess.on('close', (code) => {
                    if (code === 0) {
                        console.log('Python 脚本执行成功');
                        console.log('完整输出:', output);
                        resolve();
                    } else {
                        console.error('Python 脚本执行失败');
                        console.error('完整错误:', error);
                        reject(new Error(`Python脚本执行失败: ${error}`));
                    }
                });

                pythonProcess.on('error', (err) => {
                    console.error('启动 Python 进程失败:', err);
                    reject(err);
                });
            });
        } catch (error) {
            console.error('执行过程中发生错误:', error);
            throw error;
        }
    }
}

// 模拟 n8n 节点执行
async function main() {
    try {
        // 模拟上游节点发送的数据
        const items = [
            {
                json: {
                    description: "创建一个工作流，每分钟调用一次 https://api.example.com/data 接口获取数据，将返回的数据保存为 JSON 文件。文件名为 data_当前时间戳.json，保存在 D:/output 目录下"
                }
            }
        ];

        console.log('模拟接收到上游节点数据:', JSON.stringify(items, null, 2));

        // 创建节点实例
        const generator = new WorkflowGenerator();
        
        // 处理每个输入项
        for (const item of items) {
            if (item.json && item.json.description) {
                console.log('开始处理工作流描述...');
                await generator.execute(item.json.description);
                console.log('工作流生成完成');
            } else {
                console.warn('跳过无效的输入项:', item);
            }
        }
        
    } catch (error) {
        console.error('节点执行过程中发生错误:', error);
    }
}

main(); 