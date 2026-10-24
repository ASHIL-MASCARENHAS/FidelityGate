import { NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';
import { DEFAULT_SCENARIOS } from '@/config/site';

export async function GET() {
  try {
    const result = await runPythonCli(['list-scenarios']);
    return NextResponse.json(result);
  } catch (err: any) {
    // Fallback to static typed fixtures
    return NextResponse.json({ status: 'success', data: DEFAULT_SCENARIOS });
  }
}
