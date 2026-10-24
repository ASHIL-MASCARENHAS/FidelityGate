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
      const apiRes = await fetchBackend(`/api/v1/workflows/${id}/outcome`);
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
