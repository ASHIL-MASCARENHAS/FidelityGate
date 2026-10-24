import { NextRequest, NextResponse } from 'next/server';
import { fetchBackend } from '@/lib/backend-client';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const scenarioKey = searchParams.get('scenario') || searchParams.get('scenario_key') || 'wan_congestion';

    try {
      const res = await fetchBackend(`/api/v1/adaptive-investigate?scenario_key=${encodeURIComponent(scenarioKey)}`);
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fallback to CLI bridge in local development
    }

    const result = await runPythonCli(['adaptive-investigate', scenarioKey]);
    return NextResponse.json(result);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));
    const scenarioKey = body.scenario_key || body.scenario || 'wan_congestion';

    try {
      const res = await fetchBackend('/api/v1/adaptive-investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_key: scenarioKey }),
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fallback to CLI bridge in local development
    }

    const result = await runPythonCli(['adaptive-investigate', scenarioKey]);
    return NextResponse.json(result);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
