import { NextRequest, NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const limit = searchParams.get('limit') || '50';
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

