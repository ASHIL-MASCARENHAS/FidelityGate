import { NextRequest, NextResponse } from 'next/server';
import { fetchBackend } from '@/lib/backend-client';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    try {
      const apiRes = await fetchBackend(`/api/v1/workflows/${id}`);
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
