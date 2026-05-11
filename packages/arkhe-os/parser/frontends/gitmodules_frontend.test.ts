import { GitModulesParser } from './gitmodules_frontend.js';
import { LFIRNodeType } from '../lfir.js';

describe('GitModulesParser', () => {
    let parser: GitModulesParser;

    beforeEach(() => {
        parser = new GitModulesParser('https://github.com/super-repo/main');

        // Mock the checkReachabilityAndDrift method to avoid hitting the network
        // during automated test runs while still validating the main parser logic.
        jest.spyOn(parser, 'checkReachabilityAndDrift').mockImplementation(async (url: string) => {
            if (url.includes('unreachable')) {
                return { reachable: false, driftDays: undefined };
            } else if (url.includes('drift')) {
                return { reachable: true, driftDays: 45 };
            } else if (url.includes('bad-git')) {
                return { reachable: true, driftDays: undefined };
            } else {
                return { reachable: true, driftDays: 5 };
            }
        });
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    it('should parse basic INI format correctly', async () => {
        const source = `
[submodule "module_a"]
    path = lib/module_a
    url = https://github.com/user/module_a.git
    branch = main
        `;
        const result = await parser.parse(source);

        expect(result.success).toBe(true);
        expect(result.graph).toBeDefined();

        const nodes = result.graph!.nodes;
        expect(nodes.length).toBe(2); // root + 1 submodule

        const modNode = nodes.find(n => n.id === 'submodule/module_a');
        expect(modNode).toBeDefined();
        expect(modNode!.type).toBe(LFIRNodeType.Module);
        expect(modNode!.attributes['path']).toBe('lib/module_a');
        expect(modNode!.attributes['url']).toBe('https://github.com/user/module_a.git');
        expect(modNode!.attributes['branch']).toBe('main');
    });

    it('should resolve relative URLs against super repo origin', () => {
        expect(parser.resolveRelativeUrl('../other-repo.git', 'https://github.com/org/super-repo'))
            .toBe('https://github.com/org/other-repo.git');

        expect(parser.resolveRelativeUrl('../../org2/other-repo', 'https://github.com/org/super-repo.git'))
            .toBe('https://github.com/org2/other-repo.git');

        // Absolute URL should remain unchanged
        expect(parser.resolveRelativeUrl('https://github.com/external/repo.git', 'https://github.com/org/super-repo'))
            .toBe('https://github.com/external/repo.git');
    });

    it('should redact credentials from URLs', () => {
        expect(parser.redactUrl('https://token123@github.com/user/repo.git'))
            .toBe('https://[REDACTED]@github.com/user/repo.git');

        expect(parser.redactUrl('https://user:pass@gitlab.com/user/repo.git'))
            .toBe('https://[REDACTED]@gitlab.com/user/repo.git');

        // Valid URLs without credentials should remain unchanged
        expect(parser.redactUrl('https://github.com/user/repo.git'))
            .toBe('https://github.com/user/repo.git');

        // Invalid or SSH URLs should remain unchanged
        expect(parser.redactUrl('git@github.com:user/repo.git'))
            .toBe('git@github.com:user/repo.git');
    });

    it('should detect unsafe paths and raise fatal error', async () => {
        const source = `
[submodule "malicious"]
    path = ../../etc/passwd
    url = https://github.com/user/malicious.git
        `;
        const result = await parser.parse(source);

        expect(result.success).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
        expect(result.errors[0].code).toBe('UNSAFE_PATH');

        // Root node should still exist but no submodule nodes
        expect(result.graph!.nodes.length).toBe(1);
    });

    it('should assign coherence score 1.0 for ignore=all submodules', async () => {
        const source = `
[submodule "ignored_mod"]
    path = lib/ignored
    url = https://github.com/user/unreachable.git
    ignore = all
        `;
        const result = await parser.parse(source);

        expect(result.success).toBe(true);
        const modNode = result.graph!.nodes.find(n => n.id === 'submodule/ignored_mod');

        expect(modNode!.attributes['coherence_score']).toBe(1.0);
        expect(modNode!.attributes['coherence_justification']).toContain('Ignored intentionally');
    });

    it('should assign correct heuristic coherence based on mock URL states', async () => {
        const source = `
[submodule "mod_drift"]
    path = lib/drift
    url = https://github.com/user/drift.git
[submodule "mod_unreachable"]
    path = lib/unreachable
    url = https://github.com/user/unreachable.git
[submodule "mod_healthy"]
    path = lib/healthy
    url = https://github.com/user/healthy.git
[submodule "mod_bad_git"]
    path = lib/bad
    url = https://github.com/user/bad-git.git
        `;
        const result = await parser.parse(source);

        expect(result.success).toBe(true);
        const nodes = result.graph!.nodes;

        const driftNode = nodes.find(n => n.id === 'submodule/mod_drift');
        expect(driftNode!.attributes['coherence_score']).toBe(0.5); // drift=45d

        const unreachNode = nodes.find(n => n.id === 'submodule/mod_unreachable');
        expect(unreachNode!.attributes['coherence_score']).toBe(0.0);

        const healthyNode = nodes.find(n => n.id === 'submodule/mod_healthy');
        expect(healthyNode!.attributes['coherence_score']).toBe(1.0); // drift=5d

        const badGitNode = nodes.find(n => n.id === 'submodule/mod_bad_git');
        expect(badGitNode!.attributes['coherence_score']).toBe(0.8); // fallback

        // Overall coherence should be average: (0.5 + 0.0 + 1.0 + 0.8) / 4 = 0.575
        const rootNode = nodes.find(n => n.id === 'gitmodules/.gitmodules');
        expect(rootNode!.attributes['coherence_score']).toBeCloseTo(0.575);
    });
});
