/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/app/api/meditation/route.ts
import { NextResponse } from 'next/server';

import type { NextRequest } from 'next/server';
import { coherentMeditationEngine } from '@/lib/meditation/coherentMeditation';

export async function POST(request: NextRequest) {
  try {
    const { action, ...payload } = await request.json();

    switch (action) {
      case 'start_session': {
        const session = await coherentMeditationEngine.startMeditationSession(
          payload.sessionId,
          payload.participants,
          payload.targetOmega
        );
        return NextResponse.json({ success: true, session });
      }

      case 'update_biofeedback': {
        await coherentMeditationEngine.updateParticipantBiofeedback(
          payload.participantId || 'user_local',
          payload.biofeedback
        );
        return NextResponse.json({ success: true });
      }

      case 'end_session': {
        await coherentMeditationEngine.endMeditationSession(payload.sessionId);
        return NextResponse.json({ success: true });
      }

      case 'get_dashboard': {
        const dashboard = coherentMeditationEngine.getMeditationDashboard();
        return NextResponse.json({ success: true, dashboard });
      }

      default:
        return NextResponse.json({ error: 'Unknown meditation action' }, { status: 400 });
    }
  } catch (error: unknown) {
    console.error('❌ Meditation API error:', error);
    return NextResponse.json(
      { error: 'Meditation operation failed', details: error.message },
      { status: 500 }
    );
  }
}
