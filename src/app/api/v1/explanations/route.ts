import { NextRequest, NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

function cleanStr(val: any): string | undefined {
  if (val === undefined || val === null) return undefined;
  const s = String(val).trim();
  if (s === '' || s === 'None' || s === 'null' || s === 'undefined') return undefined;
  return s;
}

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = cleanStr(searchParams.get('id') || searchParams.get('explanation_id'));
    const limit = cleanStr(searchParams.get('limit')) || '50';

    const targetUrl = id
      ? `${FASTAPI_URL}/api/v1/explanations/${encodeURIComponent(id)}`
      : `${FASTAPI_URL}/api/v1/explanations?limit=${encodeURIComponent(limit)}`;

    try {
      const apiRes = await fetch(targetUrl, {
        headers: { Accept: 'application/json' },
        cache: 'no-store',
      });
      const data = await apiRes.json().catch(() => ({}));
      return NextResponse.json(data, { status: apiRes.status });
    } catch {
      // Fallback to CLI bridge if FastAPI is offline
    }

    if (id) {
      const result = await runPythonCli(['get-explanation', id]);
      if (result.error) {
        return NextResponse.json({ detail: result.error, error: result.error }, { status: 404 });
      }
      return NextResponse.json(result.explanation || result);
    }

    const result = await runPythonCli(['list-explanations', limit]);
    return NextResponse.json(result);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));

    const cleanTargetId = cleanStr(body.adaptive_run_id || body.evaluation_id || body.run_id);
    const cleanScenarioId = cleanStr(body.scenario_id || body.scenario);

    if (!cleanTargetId && !cleanScenarioId) {
      return NextResponse.json(
        { detail: "Must provide at least one of 'evaluation_id', 'adaptive_run_id', 'run_id', or 'scenario_id'." },
        { status: 400 }
      );
    }

    const proxyBody: Record<string, any> = {
      compute_sensitivity: body.compute_sensitivity !== false,
    };
    if (cleanTargetId) {
      if (cleanTargetId.startsWith('adapt-')) {
        proxyBody.adaptive_run_id = cleanTargetId;
      } else if (cleanTargetId.startsWith('eval-')) {
        proxyBody.evaluation_id = cleanTargetId;
      } else {
        proxyBody.run_id = cleanTargetId;
      }
    }
    if (cleanScenarioId) {
      proxyBody.scenario_id = cleanScenarioId;
    }

    const targetUrl = `${FASTAPI_URL}/api/v1/explanations`;

    try {
      const apiRes = await fetch(targetUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(proxyBody),
        cache: 'no-store',
      });
      const data = await apiRes.json().catch(() => ({}));
      return NextResponse.json(data, { status: apiRes.status });
    } catch {
      // Fallback to CLI bridge if FastAPI is offline
    }

    const result = await runPythonCli([
      'explain-decision',
      cleanTargetId || 'None',
      cleanScenarioId || 'None',
      proxyBody.compute_sensitivity ? '1' : '0',
    ]);

    if (result.error) {
      const is404 =
        result.error.includes('not found') || result.error.includes('No completed evaluations');
      return NextResponse.json({ detail: result.error, error: result.error }, { status: is404 ? 404 : 400 });
    }

    return NextResponse.json(result.explanation || result, { status: 201 });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
