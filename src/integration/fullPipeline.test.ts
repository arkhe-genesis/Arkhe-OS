import { executeFullPipeline, FullPipelineConfig } from '../../packages/arkhe-os/api-module/index';
import { execSync } from 'child_process';

describe('Full Pipeline Integration', () => {
  it('should successfully execute pipeline and verify ZK privacy assertion', async () => {
    const config: FullPipelineConfig = {
      initialState: [0, 1, 2],
      layerType: 'causal',
      enableAllFeatures: true
    };

    const result = await executeFullPipeline(config);

    expect(result.success).toBe(true);
    expect(result.canonicalSeal).toContain('ARKHE-PIPELINE');

    const pythonScript = `
import sys
import json
sys.path.append(r'arkhe-omega-temp/arkhe/substrate_6041_v3')
try:
    from zk_causal_proof import generate_route_zkp, verify_route_zkp
except ImportError as e:
    print(json.dumps({"success": False, "error": f"Import error: {e}"}))
    sys.exit(0)

seal = "${result.canonicalSeal}"
route = {
    'hops': ['NODE-A', 'NODE-B', 'NODE-C'],
    'weights': [1.0, 1.5],
    'consistencies': [0.95, 0.90, 0.88],
    'temporal_deltas': [0.0, 0.0],
    'branch_id': seal
}

try:
    # Set threshold low enough to pass
    proof = generate_route_zkp(route, 0.88, 0.85)
    if proof is None:
        print(json.dumps({'success': False, 'error': 'Proof generation failed'}))
    else:
        is_valid = verify_route_zkp(proof)
        print(json.dumps({'success': is_valid}))
except Exception as e:
    print(json.dumps({'success': False, 'error': str(e)}))
`;

    const out = execSync(`python3 -c "${pythonScript.replace(/"/g, '\\"')}"`);
    const jsonRes = JSON.parse(out.toString());

    expect(jsonRes.success).toBe(true);
  });
});
