import { NextRequest, NextResponse } from 'next/server';
import { fetchBackend } from '@/lib/backend-client';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const queryString = searchParams.toString();
    const endpoint = `/api/v1/workflows${queryString ? `?${queryString}` : ''}`;

    try {
      const apiRes = await fetchBackend(endpoint);
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

    try {
      const apiRes = await fetchBackend('/api/v1/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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
