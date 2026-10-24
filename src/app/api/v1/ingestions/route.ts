import { NextRequest, NextResponse } from 'next/server';
import { fetchBackend } from '@/lib/backend-client';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const limit = searchParams.get('limit') || '50';

    try {
      const res = await fetchBackend(`/api/v1/ingestions?limit=${limit}`);
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fallback to CLI bridge in local development
    }

    const result = await runPythonCli(['list-ingestions', limit]);
    return NextResponse.json(result);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const {
      relative_path,
      source_id = 'cisco-ie-telemetry',
      dataset_version = 'master',
      scenario_id = ''
    } = body;

    if (!relative_path) {
      return NextResponse.json({ error: 'relative_path is required' }, { status: 400 });
    }

    try {
      const res = await fetchBackend('/api/v1/ingestions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          relative_path,
          source_id,
          dataset_version,
          scenario_id: scenario_id || undefined,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
      }
    } catch {
      // Fallback to CLI bridge in local development
    }

    const result = await runPythonCli([
      'ingest',
      relative_path,
      source_id,
      dataset_version,
      scenario_id || ''
    ]);

    if (result.status === 'FAILED') {
      return NextResponse.json(result, { status: 400 });
    }
    return NextResponse.json(result, { status: 201 });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
