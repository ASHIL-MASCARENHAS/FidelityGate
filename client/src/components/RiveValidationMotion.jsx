import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, ShieldCheck, AlertTriangle, XCircle, RotateCw, Radio, Play, Sliders, Waves, Layers } from 'lucide-react';

const VALIDATION_STATES = [
  { id: 'STANDBY', label: 'Standby / Idle', color: '#64748b', desc: 'Awaiting candidate intervention request.' },
  { id: 'SYNC', label: 'Synchronizing Signals', color: '#06b6d4', desc: 'Phase-aligning physical telemetry with twin state.' },
  { id: 'SWEEP', label: 'Evaluating Envelope', color: '#8b5cf6', desc: 'Executing bounded parameter variations.' },
  { id: 'ACCEPT', label: 'State: ACCEPT', color: '#39d3a4', desc: 'Unconditionally verified within SLO & stability bounds.' },
  { id: 'GATHER_EVIDENCE', label: 'State: GATHER_EVIDENCE', color: '#f3b64b', desc: 'Nominal passes; uncertainty variations breach SLO.' },
  { id: 'ABSTAIN', label: 'State: ABSTAIN', color: '#ff667d', desc: 'Candidate cannot be justified; fail-closed safety activated.' },
];

export default function RiveValidationMotion({ currentDecision = 'GATHER_EVIDENCE' }) {
  const [currentState, setCurrentState] = useState('SYNC');
  const [syncFreq, setSyncFreq] = useState(60); // Hz
  const canvasRef = useRef(null);

  // Sync canvas animation for synchronization signals
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;
    let t = 0;

    const render = () => {
      animId = requestAnimationFrame(render);
      t += 0.05 * (syncFreq / 60);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const w = canvas.width;
      const h = canvas.height;
      const midY = h / 2;

      // Draw background grid lines
      ctx.strokeStyle = '#101a2a';
      ctx.lineWidth = 1;
      for (let x = 0; x < w; x += 30) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }

      // Signal 1: Physical System Carrier Wave (Cyan)
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      for (let x = 0; x < w; x++) {
        const y = midY + Math.sin(x * 0.03 + t) * 35 * Math.sin(t * 0.4);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Signal 2: Digital-Twin Synchronized Wave
      const activeColor =
        currentState === 'ACCEPT'
          ? '#39d3a4'
          : currentState === 'GATHER_EVIDENCE'
          ? '#f3b64b'
          : currentState === 'ABSTAIN'
          ? '#ff667d'
          : '#8b5cf6';

      ctx.strokeStyle = activeColor;
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = 0; x < w; x++) {
        const phaseShift = currentState === 'SYNC' ? Math.sin(t * 2) * 0.3 : 0;
        const y = midY + Math.sin(x * 0.03 + t + phaseShift) * 35 * Math.sin(t * 0.4);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Signal Packet Blips
      const packetX = ((t * 80) % w);
      ctx.fillStyle = activeColor;
      ctx.shadowColor = activeColor;
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.arc(packetX, midY, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    };

    render();

    return () => cancelAnimationFrame(animId);
  }, [currentState, syncFreq]);

  const activeStateObj = VALIDATION_STATES.find((s) => s.id === currentState) || VALIDATION_STATES[1];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs font-bold uppercase tracking-wider mb-1">
            <Waves className="w-4 h-4" />
            <span>Rive-Grade Motion & State Transitions</span>
          </div>
          <h2 className="text-xl font-extrabold text-white tracking-tight">Synchronization Signals & State Machine</h2>
          <p className="text-xs text-slate-400">
            Real-time synchronization wave monitor and animated state transitions between validation outcomes.
          </p>
        </div>

        {/* State Pills */}
        <div className="flex items-center space-x-1.5 bg-[#09111e] p-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <span className="text-slate-400 text-[11px] px-2">CURRENT:</span>
          <span
            className="px-2.5 py-1 rounded-lg font-bold text-slate-950 uppercase"
            style={{ backgroundColor: activeStateObj.color }}
          >
            {activeStateObj.label}
          </span>
        </div>
      </div>

      {/* Main Interactive Stage */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: State HUD / Cyber Dial (Span 1) */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col items-center justify-between text-center relative overflow-hidden">
          <div className="w-full flex items-center justify-between mb-2">
            <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">Validation HUD</span>
            <span className="text-[10px] font-mono text-slate-400">State Machine v2.4</span>
          </div>

          {/* Animated Concentric HUD Dial */}
          <div className="relative w-56 h-56 flex items-center justify-center my-4">
            {/* Outer Rotating Dashed Ring */}
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 20, ease: 'linear' }}
              className="absolute inset-0 rounded-full border-2 border-dashed border-slate-700/60"
            />

            {/* Middle Counter-Rotating Ring */}
            <motion.div
              animate={{ rotate: -360 }}
              transition={{ repeat: Infinity, duration: 12, ease: 'linear' }}
              className="absolute inset-3 rounded-full border border-cyan-800/60"
            />

            {/* Inner Glowing Active Ring */}
            <motion.div
              animate={{ scale: [1, 1.05, 1], opacity: [0.7, 1, 0.7] }}
              transition={{ repeat: Infinity, duration: 2.5 }}
              className="absolute inset-8 rounded-full border-2"
              style={{ borderColor: activeStateObj.color, boxShadow: `0 0 25px ${activeStateObj.color}33` }}
            />

            {/* Center State Icon & Readout */}
            <div className="relative z-10 flex flex-col items-center">
              {currentState === 'ACCEPT' ? (
                <ShieldCheck className="w-10 h-10 text-emerald-400 animate-bounce" />
              ) : currentState === 'GATHER_EVIDENCE' ? (
                <AlertTriangle className="w-10 h-10 text-amber-400 animate-pulse" />
              ) : currentState === 'ABSTAIN' ? (
                <XCircle className="w-10 h-10 text-rose-400 animate-pulse" />
              ) : (
                <Radio className="w-10 h-10 text-cyan-400 animate-spin" style={{ animationDuration: '6s' }} />
              )}
              <span className="text-xs font-mono font-bold mt-2 text-white">
                {activeStateObj.id}
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                {syncFreq} Hz Carrier
              </span>
            </div>
          </div>

          {/* Active State Description */}
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 w-full text-xs text-slate-300">
            {activeStateObj.desc}
          </div>
        </div>

        {/* Right Column: Synchronization Waveform Canvas & Controls (Span 2) */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
                Synchronization Signal Stream
              </h3>
            </div>
            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="flex items-center space-x-1.5 text-cyan-400">
                <span className="w-2.5 h-0.5 bg-cyan-400" />
                <span>Physical Carrier</span>
              </span>
              <span className="flex items-center space-x-1.5" style={{ color: activeStateObj.color }}>
                <span className="w-2.5 h-0.5" style={{ backgroundColor: activeStateObj.color }} />
                <span>Twin Feedback</span>
              </span>
            </div>
          </div>

          {/* Real-Time HTML5 Canvas Waveform */}
          <div className="h-52 w-full rounded-xl overflow-hidden bg-[#070d17] border border-cyan-900/40 relative">
            <canvas ref={canvasRef} width={640} height={208} className="w-full h-full" />
            <div className="absolute top-2 left-2 text-[10px] font-mono text-cyan-500/70">
              PHASE OFFSET: {currentState === 'SYNC' ? '0.12 rad' : '0.00 rad'} • DRIFT: 0.04%
            </div>
          </div>

          {/* State Transition Triggers */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <span className="text-xs font-mono text-slate-400 block">Trigger State Transition:</span>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {VALIDATION_STATES.map((st) => (
                <button
                  key={st.id}
                  onClick={() => setCurrentState(st.id)}
                  className={`px-3 py-2 rounded-xl text-xs font-mono font-semibold border transition-all text-left flex items-center justify-between ${
                    currentState === st.id
                      ? 'bg-slate-800 border-cyan-400 text-white shadow-[0_0_12px_rgba(84,214,232,0.2)]'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                  }`}
                >
                  <span className="truncate">{st.id}</span>
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: st.color }} />
                </button>
              ))}
            </div>
          </div>

          {/* Sync Frequency Slider */}
          <div className="flex items-center space-x-4 pt-2">
            <span className="text-xs font-mono text-slate-400 whitespace-nowrap">Signal Frequency:</span>
            <input
              type="range"
              min="20"
              max="120"
              value={syncFreq}
              onChange={(e) => setSyncFreq(Number(e.target.value))}
              className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <span className="text-xs font-mono font-bold text-cyan-300 w-14 text-right">
              {syncFreq} Hz
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
