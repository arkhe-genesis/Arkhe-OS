// arkhe-dashboard/src/app/api/inter-cathedral/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { interCathedralProtocol } from '@/lib/quantum/interCathedralProtocol';

export async function POST(request: NextRequest) {
  try {
    const { action, ...payload } = await request.json();

    switch (action) {
      case 'register_local': {
        interCathedralProtocol.registerLocalNode(payload.node);
        return NextResponse.json({ success: true, message: 'Local node registered' });
      }

      case 'register_remote': {
        interCathedralProtocol.registerRemoteNode(payload.node);
        return NextResponse.json({ success: true, message: 'Remote node registered' });
      }

      case 'teleport': {
        const result = await interCathedralProtocol.initiateQuantumTeleportation(
          payload.targetNodeId,
          new Float32Array(payload.coherenceState)
        );
        return NextResponse.json({ success: result.success, result });
      }

      case 'sync_all': {
        const results = await interCathedralProtocol.syncWithAllRemoteNodes(
          payload.omega,
          payload.kEth
        );
        return NextResponse.json({
          success: true,
          results: Object.fromEntries(
            Array.from(results.entries()).map(([k, v]) => [k, {
              success: v.success,
              fidelity: v.fidelity,
              latency_ms: v.latency_ms,
            }])
          ),
        });
      }

      case 'get_dashboard': {
        const dashboard = interCathedralProtocol.getProtocolDashboard();
        return NextResponse.json({ success: true, dashboard });
      }

      default:
        return NextResponse.json({ error: 'Unknown inter-cathedral action' }, { status: 400 });
    }
  } catch (error: any) {
    console.error('❌ Inter-cathedral protocol error:', error);
    return NextResponse.json(
      { error: 'Protocol operation failed', details: error.message },
      { status: 500 }
    );
  }
}
