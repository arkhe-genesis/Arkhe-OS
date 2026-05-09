import { IDEAndAIParser, IDETool, DevEvent } from './ide_ai_parser';

describe('IDEAndAIParser', () => {
    it('should parse valid events and calculate coherence with decay', () => {
        const parser = new IDEAndAIParser();
        const now = Date.now();
        const events: DevEvent[] = [
            {
                tool: IDETool.CURSOR,
                event_type: 'edit',
                file_path: 'src/main.ts',
                timestamp: now - 10000,
                session_id: 'test_session'
            },
            {
                tool: IDETool.CURSOR,
                event_type: 'completion_accept',
                file_path: 'src/main.ts',
                timestamp: now - 5000,
                session_id: 'test_session'
            }
        ];

        const result = parser.parse(JSON.stringify(events), 'test');

        expect(result.success).toBe(true);
        expect(result.graph).toBeDefined();
        if (result.graph) {
            expect(result.graph.nodes.length).toBe(2);
            expect(result.metrics.coherenceScore).toBeGreaterThan(0);
        }
    });

    it('should handle invalid JSON', () => {
        const parser = new IDEAndAIParser();
        const result = parser.parse('invalid json', 'test');
        expect(result.success).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
    });

    it('should redact secrets', () => {
        const parser = new IDEAndAIParser({redact_content: true, hash_file_paths: false});
        const events: DevEvent[] = [
            {
                tool: IDETool.CURSOR,
                event_type: 'edit',
                file_path: 'src/main.ts',
                content_snippet: 'const token = "ghp_1234567890abcdefghijklmnopqrstuvwx"',
                timestamp: Date.now(),
                session_id: 'test_session'
            }
        ];
        const result = parser.parse(JSON.stringify(events), 'test');
        expect(result.graph?.nodes[0].attributes.content).toContain('[REDACTED]');
        expect(result.graph?.nodes[0].attributes.content).not.toContain('ghp_1234567890abcdefghijklmnopqrstuvwx');
    });
});
