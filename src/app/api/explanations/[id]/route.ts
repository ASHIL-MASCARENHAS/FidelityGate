import { NextRequest, NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const id = params.id;
    if (!id || id === 'None' || id === 'undefined' || id === 'null') {
      return NextResponse.json({ detail: 'Invalid explanation ID' }, { status: 400 });
    }

    const targetUrl = `${FASTAPI_URL}/api/v1/explanations/${encodeURIComponent(id)}`;

    try {
      const apiRes = await fetch(targetUrl, {
        headers: { Accept: 'application/json' },
        cache: 'no-store',
      });
      const data = await apiRes.json().catch(() => ({}));
      return NextResponse.json(data, { status: apiRes.status });
    } catch {
      // Fallback to CLI bridge if FastAPI is offline
    }

    const result = await runPythonCli(['get-explanation', id]);
    if (result.error) {
      return NextResponse.json({ detail: result.error, error: result.error }, { status: 404 });
    }
    return NextResponse.json(result.explanation || result);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

