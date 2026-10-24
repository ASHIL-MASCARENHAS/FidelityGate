import { NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET() {
  try {
    const result = await runPythonCli(['baselines']);
    return NextResponse.json(result);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
