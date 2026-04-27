// arkhe-dashboard/src/app/api/ethics/predict/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { ethicalPredictiveModel } from '@/lib/tfjs/ethical-predictive-model';
import { EthicalMetrics, PredictionResult } from '@/types/ethics';

export async function POST(request: NextRequest) {
  try {
    const body: EthicalMetrics = await request.json();

    const prediction: PredictionResult = await ethicalPredictiveModel.predict(body);

    return NextResponse.json({
      success: true,
      data: prediction,
      timestamp: Date.now(),
    });
  } catch (error) {
    console.error('❌ Error in ethical prediction:', error);
    return NextResponse.json(
      { error: 'Prediction failed', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
