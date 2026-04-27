// arkhe-dashboard/src/app/api/simulate/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { ethicalSimulator } from '@/lib/simulator/ethicalSimulator';

export async function POST(request: NextRequest) {
  try {
    const { scenario, baseMetrics } = await request.json();
    const result = await ethicalSimulator.simulate(scenario, baseMetrics);
    return NextResponse.json({ success: true, result });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
