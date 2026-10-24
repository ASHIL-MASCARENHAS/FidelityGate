import { NextResponse } from 'next/server';
import { fetchBackend } from '@/lib/backend-client';
import { runPythonCli } from '@/lib/python-bridge';
import { DEFAULT_SCENARIOS } from '@/config/site';

export async function GET() {
  try {
    const res = await fetchBackend('/api/v1/scenarios');
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
  } catch {
    // Fallback to CLI or static fixtures
  }

  try {
    const result = await runPythonCli(['list-scenarios']);
    return NextResponse.json(result);
  } catch {
    // Fallback to static typed fixtures
    return NextResponse.json({ status: 'success', data: DEFAULT_SCENARIOS });
  }
}
