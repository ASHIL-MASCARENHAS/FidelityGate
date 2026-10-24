import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('\x1b[36m%s\x1b[0m', '══════════════════════════════════════════════════════════════');
console.log('\x1b[36m%s\x1b[0m', '  ◈ FidelityGate — Starting Canonical Control Room Stack');
console.log('\x1b[36m%s\x1b[0m', '  • Canonical FastAPI Backend: http://127.0.0.1:8000');
console.log('\x1b[36m%s\x1b[0m', '  • Next.js App Router UI:     http://localhost:3000');
console.log('\x1b[36m%s\x1b[0m', '  • API Documentation (Docs):  http://127.0.0.1:8000/docs');
console.log('\x1b[36m%s\x1b[0m', '══════════════════════════════════════════════════════════════');

const isWin = process.platform === 'win32';
const pythonExe = process.env.PYTHON_EXEC_PATH || (isWin ? 'python' : 'python3');
const npmCmd = isWin ? 'npm.cmd' : 'npm';

// 1. Start Canonical FastAPI Backend
const backend = spawn(pythonExe, ['-m', 'uvicorn', 'fidelitygate.api.app:app', '--host', '127.0.0.1', '--port', '8000'], {
  stdio: 'inherit',
  shell: true,
  cwd: __dirname,
  env: { ...process.env, PYTHONPATH: __dirname }
});

// 2. Start Next.js App Router Frontend
const frontend = spawn(npmCmd, ['run', 'dev'], {
  stdio: 'inherit',
  shell: true,
  cwd: __dirname,
});

function cleanup() {
  console.log('\nShutting down FidelityGate services...');
  backend.kill();
  frontend.kill();
  process.exit();
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
