import { NextRequest, NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const targetUrl = `${FASTAPI_URL}/api/v1/workflows/${id}`;

    try {
      const apiRes = await fetch(targetUrl, {
        headers: { Accept: 'application/json' },
        cache: 'no-store',
      });
      if (apiRes.ok) {
        const data = await apiRes.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fallback to CLI bridge if FastAPI is offline
    }

    const result = await runPythonCli(['get-workflow', id]);
    if (result && result.error) {
      return NextResponse.json({ detail: result.error }, { status: 404 });
    }
    const summaryData = result?.summary || result;
    return NextResponse.json(summaryData);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
