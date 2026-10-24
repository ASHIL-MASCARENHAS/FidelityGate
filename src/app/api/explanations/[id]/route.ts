import { NextRequest, NextResponse } from 'next/server';
import { fetchBackend } from '@/lib/backend-client';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const id = params.id;
    if (!id || id === 'None' || id === 'undefined' || id === 'null') {
      return NextResponse.json({ detail: 'Invalid explanation ID' }, { status: 400 });
    }

    try {
      const apiRes = await fetchBackend(`/api/v1/explanations/${encodeURIComponent(id)}`);
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
