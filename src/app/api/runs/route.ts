import { NextRequest, NextResponse } from 'next/server';
import { fetchBackend } from '@/lib/backend-client';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET(req: NextRequest) {
  try {
    const limit = req.nextUrl.searchParams.get('limit') || '50';

    try {
      const res = await fetchBackend(`/api/v1/runs?limit=${limit}`);
      if (res.ok) {
        const data = await res.json();
        const runsList = Array.isArray(data) ? data : (data?.data || []);
        return NextResponse.json(runsList);
      }
    } catch {
      // Fallback to CLI bridge in local development
    }

    const result = await runPythonCli(['recent-runs', limit]);
    const runsList = Array.isArray(result) ? result : (result?.data || []);
    return NextResponse.json(runsList);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
