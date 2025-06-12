import {
	ICredentialType,
	INodeProperties,
} from 'n8n-workflow';

export class WorkflowGenerator implements ICredentialType {
	name = 'workflowGeneratorApi';
	displayName = 'Workflow Generator API';
	documentationUrl = 'https://docs.n8n.io/credentials/workflowGenerator';
	properties: INodeProperties[] = [
		{
			displayName: 'API Key',
			name: 'apiKey',
			type: 'string',
			typeOptions: {
				password: true,
			},
			default: '',
		},
		{
			displayName: 'API Base URL',
			name: 'apiBaseUrl',
			type: 'string',
			default: 'http://localhost:5678',
		},
	];
} 