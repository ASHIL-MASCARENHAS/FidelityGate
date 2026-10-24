import { NextResponse } from 'next/server';
import { fetchBackend } from '@/lib/backend-client';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET() {
  try {
    const res = await fetchBackend('/api/v1/health');
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json({
        ...data,
        frontend: 'healthy',
        layer: 'Layer 1: Trustworthy Network Data Ingestion and Provenance',
      });
    }
  } catch {
    // Fallback to CLI bridge in local development
  }

  try {
    const result = await runPythonCli(['health']);
    return NextResponse.json({
      ...result,
      frontend: 'healthy',
      layer: 'Layer 1: Trustworthy Network Data Ingestion and Provenance',
    });
  } catch (err: any) {
    return NextResponse.json(
      {
        status: 'degraded',
        error: err.message,
      },
      { status: 500 }
    );
  }
}
