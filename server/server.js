import express from 'express';
import cors from 'cors';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');
const DB_PATH = process.env.DATABASE_PATH || path.join(ROOT_DIR, 'fidelitygate.db');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Helper to run python fidelitygate.cli commands
function runPythonCli(args) {
  return new Promise((resolve, reject) => {
    const pythonExe = process.platform === 'win32' ? 'python' : 'python3';
    
    const child = spawn(pythonExe, ['-m', 'fidelitygate.cli', ...args], {
      cwd: ROOT_DIR,
      env: { ...process.env, PYTHONPATH: ROOT_DIR, DATABASE_PATH: DB_PATH }
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
      } catch (parseErr) {
        reject(new Error(`Failed to parse Python JSON output: ${parseErr.message}. Output was: ${stdout}`));
      }
    });
  });
}

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'FidelityGate Control Room API',
    database_path: DB_PATH,
    node_version: process.version
  });
});

// List scenarios
app.get('/api/scenarios', async (req, res) => {
  try {
    const result = await runPythonCli(['list-scenarios']);
    res.json(result);
  } catch (err) {
    console.error('Error fetching scenarios:', err);
    res.status(500).json({ error: err.message });
  }
});

// Run bounded investigation
app.post('/api/investigate', async (req, res) => {
  const { scenario_key, evaluations = 25 } = req.body;
  if (!scenario_key) {
    return res.status(400).json({ error: 'scenario_key is required' });
  }

  try {
    const result = await runPythonCli(['investigate', scenario_key, evaluations.toString(), DB_PATH]);
    res.json(result);
  } catch (err) {
    console.error(`Error investigating scenario ${scenario_key}:`, err);
    res.status(500).json({ error: err.message });
  }
});

// Run Adaptive Counterexample-Guided Investigation
app.post('/api/adaptive-investigate', async (req, res) => {
  const { scenario_key } = req.body;
  if (!scenario_key) {
    return res.status(400).json({ error: 'scenario_key is required' });
  }

  try {
    const result = await runPythonCli(['adaptive-investigate', scenario_key, DB_PATH]);
    res.json(result);
  } catch (err) {
    console.error(`Error in adaptive investigation for ${scenario_key}:`, err);
    res.status(500).json({ error: err.message });
  }
});

// Run Four-Way Baseline Comparison
app.get('/api/baselines', async (req, res) => {
  try {
    const result = await runPythonCli(['baselines']);
    res.json(result);
  } catch (err) {
    console.error('Error fetching baselines:', err);
    res.status(500).json({ error: err.message });
  }
});

// Counterexample search endpoint
app.post('/api/counterexample', async (req, res) => {
  const { scenario_key } = req.body;
  if (!scenario_key) {
    return res.status(400).json({ error: 'scenario_key is required' });
  }

  try {
    const result = await runPythonCli(['counterexample', scenario_key]);
    res.json(result);
  } catch (err) {
    console.error('Error searching counterexample:', err);
    res.status(500).json({ error: err.message });
  }
});

// Run full evaluation benchmark
app.post('/api/evaluate-all', async (req, res) => {
  const { evaluations = 25 } = req.body;
  try {
    const result = await runPythonCli(['evaluate-all', evaluations.toString(), DB_PATH]);
    res.json(result);
  } catch (err) {
    console.error('Error running evaluate-all:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get recent runs (audit log)
app.get('/api/runs', async (req, res) => {
  const limit = req.query.limit || 50;
  try {
    const result = await runPythonCli(['recent-runs', limit.toString(), DB_PATH]);
    res.json(result);
  } catch (err) {
    console.error('Error fetching recent runs:', err);
    res.status(500).json({ error: err.message });
  }
});

// Diagnostics & System status
app.get('/api/diagnostics', (req, res) => {
  let dbExists = false;
  let dbSize = 0;
  try {
    if (fs.existsSync(DB_PATH)) {
      dbExists = true;
      const stats = fs.statSync(DB_PATH);
      dbSize = stats.size;
    }
  } catch (e) {
    // ignore
  }

  res.json({
    status: 'operational',
    environment: {
      platform: process.platform,
      nodeVersion: process.version,
      memoryUsage: process.memoryUsage(),
      uptimeSeconds: Math.floor(process.uptime()),
    },
    database: {
      path: DB_PATH,
      exists: dbExists,
      sizeBytes: dbSize
    },
    safety_controls: {
      offline_capable: true,
      llm_api_configured: Boolean(process.env.LLM_API_KEY),
      read_only_infrastructure: true,
      deterministic_gate_policy: true
    }
  });
});

app.listen(PORT, () => {
  console.log(`[FidelityGate Express Server] Running on http://localhost:${PORT}`);
  console.log(`[FidelityGate Express Server] Target DB: ${DB_PATH}`);
});
