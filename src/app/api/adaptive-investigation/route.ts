import { NextRequest, NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const scenarioKey = searchParams.get('scenario') || searchParams.get('scenario_key') || 'wan_congestion';

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

    const result = await runPythonCli(['adaptive-investigate', scenarioKey]);
    return NextResponse.json(result);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

