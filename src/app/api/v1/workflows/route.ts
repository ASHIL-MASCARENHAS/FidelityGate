import { NextRequest, NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const queryString = searchParams.toString();
    const targetUrl = `${FASTAPI_URL}/api/v1/workflows${queryString ? `?${queryString}` : ''}`;

    try {
      const apiRes = await fetch(targetUrl, {
        headers: { Accept: 'application/json' },
        cache: 'no-store',
      });
      if (apiRes.ok) {
        const data = await apiRes.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fallback to CLI bridge if FastAPI is offline
    }

    const limit = searchParams.get('limit') || '50';
    const result = await runPythonCli(['list-workflows', limit]);
    return NextResponse.json(result);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));
    const targetUrl = `${FASTAPI_URL}/api/v1/workflows`;

    try {
      const apiRes = await fetch(targetUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(body),
        cache: 'no-store',
      });
      if (apiRes.ok) {
        const data = await apiRes.json();
        return NextResponse.json(data, { status: apiRes.status });
      }
    } catch {
      // Fallback to CLI bridge if FastAPI is offline
    }

    const scenario = body.scenario_id || body.scenario || 'wan_congestion';
    const reviewer = body.reviewer_id || 'operator-local';
    const autoApprove = body.auto_approve_for_testing ? '--auto-approve' : '';

    const args = ['run-workflow', '--scenario', scenario, '--reviewer', reviewer];
    if (autoApprove) args.push(autoApprove);

    const result = await runPythonCli(args);
    return NextResponse.json(result, { status: 201 });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

