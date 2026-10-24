import { spawn } from 'child_process';
import path from 'path';

export function runPythonCli(args: string[]): Promise<any> {
  return new Promise((resolve, reject) => {
    const pythonExe = process.env.PYTHON_EXEC_PATH || (process.platform === 'win32' ? 'python' : 'python3');
    const rootDir = process.cwd();
    const dbPath = process.env.DATABASE_PATH || path.join(rootDir, 'fidelitygate.db');

    const child = spawn(pythonExe, ['-m', 'fidelitygate.cli', ...args], {
      cwd: rootDir,
      env: { ...process.env, PYTHONPATH: rootDir, DATABASE_PATH: dbPath }
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('error', (err) => {
      reject(new Error(`Failed to spawn Python process: ${err.message}`));
    });

    child.on('close', (code) => {
      if (code !== 0) {
        return reject(new Error(`Python process exited with code ${code}: ${stderr || stdout}`));
      }
      try {
        const json = JSON.parse(stdout.trim());
        resolve(json);
      } catch (parseErr: any) {
        reject(new Error(`Failed to parse Python JSON output: ${parseErr.message}. Output was: ${stdout}`));
      }
    });
  });
}
