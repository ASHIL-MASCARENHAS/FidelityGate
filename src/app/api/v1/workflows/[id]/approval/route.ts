import { NextRequest, NextResponse } from 'next/server';
import { runPythonCli } from '@/lib/python-bridge';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const targetUrl = `${FASTAPI_URL}/api/v1/workflows/${id}/approval`;

    try {
      const apiRes = await fetch(targetUrl, {
        headers: { Accept: 'application/json' },
        cache: 'no-store',
      });
      if (apiRes.ok) {
        const data = await apiRes.json();
        return NextResponse.json(data);
      }
      if (apiRes.status === 404) {
        return NextResponse.json({ detail: `No approval record found for workflow '${id}'.` }, { status: 404 });
      }
    } catch {
      // Fallback to CLI bridge
    }

    const result = await runPythonCli(['get-workflow', id]);
    if (result && result.approval) {
      return NextResponse.json(result.approval);
    }
    return NextResponse.json({ detail: `No approval record found for workflow '${id}'.` }, { status: 404 });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await req.json().catch(() => ({}));
    const targetUrl = `${FASTAPI_URL}/api/v1/workflows/${id}/approval`;

    try {
      const apiRes = await fetch(targetUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(body),
        cache: 'no-store',
      });
      if (apiRes.ok) {
        const data = await apiRes.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fallback to CLI bridge
    }

    const decision = body.decision || 'APPROVED';
    const reviewer = body.reviewer_id || 'operator-local';
    const comment = body.reviewer_comment || '';

    const args = ['approve-workflow', id, '--decision', decision, '--reviewer', reviewer];
    if (comment) args.push('--comment', comment);

    const result = await runPythonCli(args);
    if (result && result.error) {
      return NextResponse.json({ detail: result.error }, { status: 400 });
    }
    const summaryData = result?.summary || result;
    return NextResponse.json(summaryData);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
