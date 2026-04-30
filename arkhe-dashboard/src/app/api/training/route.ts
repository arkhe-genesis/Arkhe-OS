/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();
    return NextResponse.json({ success: true, payload });
  } catch (_error) {
    return NextResponse.json({ error: 'Training API failed' }, { status: 500 });
  }
}
