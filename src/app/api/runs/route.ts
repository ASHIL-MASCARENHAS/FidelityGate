import { NextRequest, NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET(req: NextRequest) {
  try {
    const limit = req.nextUrl.searchParams.get('limit') || '50';
    const result = await runPythonCli(['recent-runs', limit]);
    const runsList = Array.isArray(result) ? result : (result?.data || []);
    return NextResponse.json(runsList);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
