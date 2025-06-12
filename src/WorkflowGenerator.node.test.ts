import { WorkflowGenerator } from './WorkflowGenerator.node';

describe('WorkflowGenerator', () => {
	it('should be defined', () => {
		expect(WorkflowGenerator).toBeDefined();
	});

	it('should have correct properties', () => {
		const node = new WorkflowGenerator();
		expect(node.description.displayName).toBe('Workflow Generator');
		expect(node.description.name).toBe('workflowGenerator');
		expect(node.description.group).toContain('transform');
	});
}); 