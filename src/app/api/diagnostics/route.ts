import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  const dbPath = process.env.DATABASE_PATH || path.join(process.cwd(), 'fidelitygate.db');
  let dbExists = false;
  let dbSize = 0;

  try {
    if (fs.existsSync(dbPath)) {
      dbExists = true;
      const stats = fs.statSync(dbPath);
      dbSize = stats.size;
    }
  } catch (e) {
    // ignore
  }

  return NextResponse.json({
    status: 'operational',
    environment: {
      platform: process.platform,
      nodeVersion: process.version,
      memoryUsage: process.memoryUsage(),
      uptimeSeconds: Math.floor(process.uptime()),
    },
    database: {
      path: dbPath,
      exists: dbExists,
      sizeBytes: dbSize,
    },
    safety_controls: {
      offline_capable: true,
      llm_api_configured: Boolean(process.env.LLM_API_KEY),
      read_only_infrastructure: true,
      deterministic_gate_policy: true,
    },
  });
}
