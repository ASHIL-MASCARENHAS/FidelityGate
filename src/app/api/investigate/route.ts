import { NextRequest, NextResponse } from 'next/server';
import { fetchBackend } from '@/lib/backend-client';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const scenarioKey = searchParams.get('scenario') || searchParams.get('scenario_key');
    const evaluations = searchParams.get('evaluations') || '25';

    if (!scenarioKey) {
      return NextResponse.json({ error: 'scenario parameter is required' }, { status: 400 });
    }

    try {
      const res = await fetchBackend(
        `/api/v1/investigate?scenario_key=${encodeURIComponent(scenarioKey)}&evaluations=${encodeURIComponent(evaluations)}`
      );
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fallback to CLI bridge in local development
    }

    const result = await runPythonCli(['investigate', scenarioKey, evaluations]);
    return NextResponse.json(result);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { scenario_key, scenario, evaluations = 25 } = body;
    const targetKey = scenario_key || scenario;

    if (!targetKey) {
      return NextResponse.json({ error: 'scenario_key is required' }, { status: 400 });
    }

    try {
      const res = await fetchBackend('/api/v1/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_key: targetKey, evaluations }),
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fallback to CLI bridge in local development
    }

    const result = await runPythonCli(['investigate', targetKey, evaluations.toString()]);
    return NextResponse.json(result);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
