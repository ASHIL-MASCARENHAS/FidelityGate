import { NextRequest, NextResponse } from 'next/server';
import { fetchBackend } from '@/lib/backend-client';
import { runPythonCli } from '@/lib/python-bridge';

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    try {
      const apiRes = await fetchBackend(`/api/v1/workflows/${id}/approval`);
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

    try {
      const apiRes = await fetchBackend(`/api/v1/workflows/${id}/approval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (apiRes.ok) {
        const data = await apiRes.json();
        return NextResponse.json(data);
      }
      if (apiRes.status === 400) {
        const errData = await apiRes.json().catch(() => ({}));
        return NextResponse.json(errData, { status: 400 });
      }
    } catch {
      // Fallback to CLI bridge
    }

    const decision = body.decision || 'APPROVE';
    const reviewer = body.reviewer_id || 'operator-local';
    const notes = body.notes || '';
    const autoExecute = body.auto_execute_simulation !== false ? '--execute' : '';

    const args = ['submit-approval', id, decision, reviewer, '--notes', notes];
    if (autoExecute) args.push(autoExecute);

    const result = await runPythonCli(args);
    const summaryData = result?.summary || result;
    return NextResponse.json(summaryData);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
