import { NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET() {
  try {
    const result = await runPythonCli(['health']);
    return NextResponse.json({
      ...result,
      frontend: 'healthy',
      layer: 'Layer 1: Trustworthy Network Data Ingestion and Provenance',
    });
  } catch (err: any) {
    return NextResponse.json({
      status: 'degraded',
      error: err.message,
    }, { status: 500 });
  }
}

