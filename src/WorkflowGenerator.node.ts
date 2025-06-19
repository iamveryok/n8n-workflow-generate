import {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	NodeOperationError,
} from 'n8n-workflow';

export class WorkflowGenerator implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Workflow Generator',
		name: 'workflowGenerator',
		icon: 'file:WorkflowGenerator.svg',
		group: ['transform'],
		version: 1,
		subtitle: '={{$parameter["operation"]}}',
		description: 'Generate n8n workflows from natural language descriptions',
		defaults: {
			name: 'Workflow Generator',
		},
		inputs: ['main'],
		outputs: ['main'],
		credentials: [
			{
				name: 'workflowGeneratorApi',
				required: true,
			},
		],
		properties: [
			{
				displayName: 'Operation',
				name: 'operation',
				type: 'options',
				noDataExpression: true,
				options: [
					{
						name: 'Generate Workflow',
						value: 'generate',
						description: 'Generate a new workflow from description',
						action: 'Generate a new workflow from description',
					},
				],
				default: 'generate',
			},
			{
				displayName: 'Workflow Description',
				name: 'description',
				type: 'string',
				default: '',
				required: true,
				displayOptions: {
					show: {
						operation: ['generate'],
					},
				},
				description: 'Natural language description of the workflow to generate',
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];
		const operation = this.getNodeParameter('operation', 0) as string;
		console.log('[WorkflowGenerator] operation:', operation);

		for (let i = 0; i < items.length; i++) {
			try {
				if (operation === 'generate') {
					const description = this.getNodeParameter('description', i) as string;
					console.log('[WorkflowGenerator] description:', description);
					
					// 创建 Python 进程
					const { spawn } = require('child_process');
					const path = require('path');
					
					// 获取 Python 脚本路径
					const scriptPath = path.resolve(__dirname, '..', 'python', 'simple_auto_generator.py');
					
					// 执行 Python 脚本，明确指定 Conda 环境中的 python.exe 路径
					const pythonProcess = spawn('C:\\Users\\liangwei\\miniconda3\\envs\\ai-agent-n8n\\python.exe', [scriptPath, description], {
						env: {
							...process.env,
							PYTHONIOENCODING: 'utf-8',
							PYTHONUNBUFFERED: '1'
						}
					});
					
					let output = '';
					let error = '';
					
					// 处理标准输出
					pythonProcess.stdout.on('data', (data) => {
						output += data.toString('utf-8');
					});
					
					// 处理标准错误
					pythonProcess.stderr.on('data', (data) => {
						error += data.toString('utf-8');
					});
					
					// 等待 Python 进程完成
					await new Promise<void>((resolve, reject) => {
						pythonProcess.on('close', (code) => {
							if (code === 0) {
								resolve();
							} else {
								console.error('[WorkflowGenerator] Python script failed:', error);
								reject(new Error(`Python script failed: ${error}`));
							}
						});
					});
					
					// 解析输出
					try {
						console.log('[WorkflowGenerator] Python output (first 500 chars):', output.slice(0, 500));
						const match = output.match(/JSON_RESULT_START\s*([\s\S]*?)\s*JSON_RESULT_END/);
						const jsonStr = match ? match[1] : output;
						console.log('[WorkflowGenerator] Extracted JSON string (first 500 chars):', jsonStr.slice(0, 500));
						const result = JSON.parse(jsonStr);
						console.log('[WorkflowGenerator] Parsed result type:', Array.isArray(result) ? 'array' : typeof result);
						if (Array.isArray(result)) {
							for (const item of result) {
								returnData.push({ json: item });
							}
						} else {
							returnData.push({ json: result });
						}
					} catch (e) {
						console.error('[WorkflowGenerator] JSON parse error:', e, 'Raw output:', output.slice(0, 500));
						throw new NodeOperationError(this.getNode(), 'Failed to parse Python script output as JSON: ' + output.slice(0, 500));
					}
				}
			} catch (error) {
				console.error('[WorkflowGenerator] Exception:', error);
				if (this.continueOnFail()) {
					returnData.push({
						json: {
							error: error.message,
						},
					});
					continue;
				}
				throw error;
			}
		}

		return [returnData];
	}
} 