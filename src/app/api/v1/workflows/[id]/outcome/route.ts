import { NextRequest, NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const targetUrl = `${FASTAPI_URL}/api/v1/workflows/${id}/outcome`;

    try {
      const apiRes = await fetch(targetUrl, {
        headers: { Accept: 'application/json' },
        cache: 'no-store',
      });
      if (apiRes.ok) {
        const data = await apiRes.json();
        return NextResponse.json(data);
      }
      if (apiRes.status === 404) {
        return NextResponse.json(
          { detail: `No outcome report found for workflow '${id}'. Intervention may not have executed yet.` },
          { status: 404 }
        );
      }
    } catch {
      // Fallback to CLI bridge
    }

    const result = await runPythonCli(['get-workflow-outcome', id]);
    if (result && result.error) {
      const status = result.error.includes('No outcome found') ? 404 : 500;
      return NextResponse.json({ detail: result.error }, { status });
    }
    const outcomeData = result?.outcome || result;
    return NextResponse.json(outcomeData);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

