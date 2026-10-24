import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Sparkles, Radio, Activity, Zap, RotateCw, ZoomIn, ShieldCheck, AlertTriangle, XCircle, Sliders } from 'lucide-react';

export default function SplineTwinCenterpiece({
  decision = 'ACCEPT',
  nominalLatency = 18,
  worstLatency = 24,
  fidelityScore = 94.2,
  syncStatus = 'SYNCHRONIZED'
}) {
  const mountRef = useRef(null);
  const [signalSpeed, setSignalSpeed] = useState(1.0);
  const [activeSignalType, setActiveSignalType] = useState('quantum_telemetry');
  const [autoRotate, setAutoRotate] = useState(true);

  // Status colors
  const statusColorHex =
    decision === 'ACCEPT' ? 0x39d3a4 : decision === 'GATHER_EVIDENCE' ? 0xf3b64b : 0xff667d;

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x080d17, 0.04);

    const width = mount.clientWidth;
    const height = mount.clientHeight || 380;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0.5, 9.5);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    // 2. Centerpiece Platform / Cybernetic Grid
    const grid = new THREE.GridHelper(16, 16, 0x1a334d, 0x0c1724);
    grid.position.y = -2.4;
    scene.add(grid);

    // 3. Node 1: Physical Infrastructure Node (Left)
    const physicalGroup = new THREE.Group();
    physicalGroup.position.set(-2.8, 0, 0);

    const physCoreGeo = new THREE.SphereGeometry(0.7, 32, 32);
    const physCoreMat = new THREE.MeshStandardMaterial({
      color: 0x06b6d4,
      emissive: 0x0891b2,
      emissiveIntensity: 0.5,
      metalness: 0.8,
      roughness: 0.2,
      wireframe: false,
    });
    const physCore = new THREE.Mesh(physCoreGeo, physCoreMat);
    physicalGroup.add(physCore);

    // Physical Geodesic Wireframe Shell
    const physShellGeo = new THREE.IcosahedronGeometry(0.95, 2);
    const physShellMat = new THREE.MeshBasicMaterial({
      color: 0x22d3ee,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    });
    const physShell = new THREE.Mesh(physShellGeo, physShellMat);
    physicalGroup.add(physShell);

    // Orbital Ring for Node 1
    const physRingGeo = new THREE.TorusGeometry(1.2, 0.02, 16, 64);
    const physRingMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.7 });
    const physRing = new THREE.Mesh(physRingGeo, physRingMat);
    physRing.rotation.x = Math.PI / 2.2;
    physicalGroup.add(physRing);

    scene.add(physicalGroup);

    // 4. Node 2: Digital Twin System Node (Right)
    const twinGroup = new THREE.Group();
    twinGroup.position.set(2.8, 0, 0);

    const twinCoreGeo = new THREE.SphereGeometry(0.7, 32, 32);
    const twinCoreMat = new THREE.MeshStandardMaterial({
      color: statusColorHex,
      emissive: statusColorHex,
      emissiveIntensity: 0.6,
      metalness: 0.85,
      roughness: 0.15,
    });
    const twinCore = new THREE.Mesh(twinCoreGeo, twinCoreMat);
    twinGroup.add(twinCore);

    // Digital Hologram Cage for Node 2
    const twinCageGeo = new THREE.DodecahedronGeometry(0.98, 1);
    const twinCageMat = new THREE.MeshBasicMaterial({
      color: statusColorHex,
      wireframe: true,
      transparent: true,
      opacity: 0.45,
    });
    const twinCage = new THREE.Mesh(twinCageGeo, twinCageMat);
    twinGroup.add(twinCage);

    // Dual Orbital Rings for Node 2
    const twinRingGeo = new THREE.TorusGeometry(1.2, 0.025, 16, 64);
    const twinRingMat = new THREE.MeshBasicMaterial({ color: statusColorHex, transparent: true, opacity: 0.8 });
    const twinRing = new THREE.Mesh(twinRingGeo, twinRingMat);
    twinRing.rotation.x = Math.PI / 1.8;
    twinGroup.add(twinRing);

    const twinRing2 = new THREE.Mesh(twinRingGeo, twinRingMat);
    twinRing2.rotation.y = Math.PI / 3;
    twinGroup.add(twinRing2);

    scene.add(twinGroup);

    // 5. Visual Signal Beam Between the Two Nodes
    const distance = 5.6; // from -2.8 to 2.8
    const beamPath = new THREE.LineCurve3(new THREE.Vector3(-2.8, 0, 0), new THREE.Vector3(2.8, 0, 0));

    // Outer Glow Cylinder for the Signal Channel
    const beamGeo = new THREE.CylinderGeometry(0.08, 0.08, distance, 32);
    const beamMat = new THREE.MeshBasicMaterial({
      color: 0x54d6e8,
      transparent: true,
      opacity: 0.3,
    });
    const beamCylinder = new THREE.Mesh(beamGeo, beamMat);
    beamCylinder.rotation.z = Math.PI / 2;
    scene.add(beamCylinder);

    // Secondary Core Laser Line
    const laserGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-2.8, 0, 0),
      new THREE.Vector3(2.8, 0, 0),
    ]);
    const laserMat = new THREE.LineBasicMaterial({
      color: statusColorHex,
      linewidth: 3,
      transparent: true,
      opacity: 0.9,
    });
    const laserLine = new THREE.Line(laserGeo, laserMat);
    scene.add(laserLine);

    // Flowing Signal Wave (Particle Stream traveling along the signal beam)
    const particleCount = 45;
    const particlesGeo = new THREE.SphereGeometry(0.07, 12, 12);
    const particleMat = new THREE.MeshBasicMaterial({
      color: statusColorHex,
      transparent: true,
      opacity: 0.95,
    });

    const signalParticles = [];
    for (let i = 0; i < particleCount; i++) {
      const p = new THREE.Mesh(particlesGeo, particleMat);
      scene.add(p);
      signalParticles.push({
        mesh: p,
        progress: i / particleCount,
        speed: 0.008 * signalSpeed,
        offsetY: Math.sin(i) * 0.1,
        offsetZ: Math.cos(i) * 0.1,
      });
    }

    // 6. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const leftLight = new THREE.PointLight(0x06b6d4, 2.2, 15);
    leftLight.position.set(-2.8, 2, 3);
    scene.add(leftLight);

    const rightLight = new THREE.PointLight(statusColorHex, 2.5, 15);
    rightLight.position.set(2.8, 2, 3);
    scene.add(rightLight);

    // 7. Interactive Orbit Controls (Mouse Drag)
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;
    let targetRotY = 0;
    let targetRotX = 0;

    const onMouseDown = (e) => {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
      mount.style.cursor = 'grabbing';
    };

    const onMouseUp = () => {
      isDragging = false;
      mount.style.cursor = 'grab';
    };

    const onMouseMove = (e) => {
      if (!isDragging) return;
      const dx = e.clientX - prevX;
      const dy = e.clientY - prevY;
      prevX = e.clientX;
      prevY = e.clientY;

      targetRotY += dx * 0.006;
      targetRotX += dy * 0.006;
      targetRotX = Math.max(-0.4, Math.min(0.4, targetRotX));
    };

    const onWheel = (e) => {
      e.preventDefault();
      camera.position.z += e.deltaY * 0.005;
      camera.position.z = Math.max(6, Math.min(14, camera.position.z));
    };

    mount.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('mousemove', onMouseMove);
    mount.addEventListener('wheel', onWheel, { passive: false });

    // 8. Animation Loop
    let animId;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Scene rotation
      if (autoRotate && !isDragging) {
        scene.rotation.y = Math.sin(elapsed * 0.3) * 0.2;
        scene.rotation.x = Math.cos(elapsed * 0.2) * 0.05;
      } else {
        scene.rotation.y = targetRotY;
        scene.rotation.x = targetRotX;
      }

      // Rotate Physical Node elements
      physShell.rotation.y += 0.01;
      physShell.rotation.x += 0.005;
      physRing.rotation.z += 0.02;

      // Rotate Twin Node elements
      twinCage.rotation.y -= 0.012;
      twinCage.rotation.z += 0.008;
      twinRing.rotation.z -= 0.025;
      twinRing2.rotation.x += 0.018;

      // Pulse twin node based on decision
      const pulseScale = 1 + Math.sin(elapsed * 4) * 0.06;
      twinCore.scale.set(pulseScale, pulseScale, pulseScale);

      // Signal beam pulse
      beamMat.opacity = 0.25 + Math.sin(elapsed * 8) * 0.15;

      // Animate flowing signal particles between the two nodes
      signalParticles.forEach((p) => {
        p.progress += 0.008 * signalSpeed;
        if (p.progress >= 1) p.progress = 0;

        // Position along the X-axis from -2.8 to 2.8
        const posX = -2.8 + p.progress * distance;
        // Harmonic wave oscillation along Y and Z
        const wave = Math.sin(p.progress * Math.PI * 4 + elapsed * 6) * 0.18;
        p.mesh.position.set(posX, wave + p.offsetY, p.offsetZ);
      });

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!mount) return;
      const w = mount.clientWidth;
      const h = mount.clientHeight || 380;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      mount.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('mousemove', onMouseMove);
      mount.removeEventListener('wheel', onWheel);
      if (renderer.domElement && mount.contains(renderer.domElement)) {
        mount.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [decision, signalSpeed, autoRotate]);

  return (
    <div className="relative w-full h-[400px] rounded-2xl overflow-hidden bg-gradient-to-b from-[#09111f] via-[#070d18] to-[#040810] border border-cyan-800/50 shadow-2xl group">
      {/* 3D WebGL Canvas */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Top Overlay Badge */}
      <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
        <div className="flex items-center space-x-2 bg-slate-900/90 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-cyan-700/60 text-xs font-mono text-cyan-300 pointer-events-auto shadow-lg">
          <Zap className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span className="font-bold">Spline 3D Centerpiece</span>
          <span className="text-slate-500">|</span>
          <span className="text-slate-300">Twin-System Visualization (Connected Nodes & Signal)</span>
        </div>

        <div className="flex items-center space-x-2 pointer-events-auto">
          {/* Signal Speed Toggle */}
          <button
            onClick={() => setSignalSpeed((prev) => (prev === 1.0 ? 1.8 : prev === 1.8 ? 0.5 : 1.0))}
            className="px-2.5 py-1.5 rounded-xl bg-slate-900/80 backdrop-blur-md border border-slate-700 hover:border-cyan-500 text-[11px] font-mono text-slate-300 transition-all"
            title="Adjust Signal Particle Speed"
          >
            Signal: <b className="text-cyan-400">{signalSpeed}x</b>
          </button>

          {/* Auto Rotate Toggle */}
          <button
            onClick={() => setAutoRotate(!autoRotate)}
            className={`p-2 rounded-xl backdrop-blur-md border text-xs transition-all ${
              autoRotate
                ? 'bg-cyan-500/20 border-cyan-400/60 text-cyan-300 shadow-[0_0_10px_rgba(84,214,232,0.3)]'
                : 'bg-slate-900/80 border-slate-700 text-slate-400'
            }`}
            title="Toggle Auto-Orbit"
          >
            <RotateCw className={`w-3.5 h-3.5 ${autoRotate ? 'animate-spin' : ''}`} style={{ animationDuration: '8s' }} />
          </button>
        </div>
      </div>

      {/* Node 1 Label Overlay (Physical Infrastructure) */}
      <div className="absolute bottom-4 left-4 pointer-events-none bg-slate-900/85 backdrop-blur-md border border-cyan-500/40 p-2.5 rounded-xl text-xs font-mono shadow-xl">
        <div className="flex items-center space-x-1.5 text-cyan-400 font-bold">
          <Radio className="w-3.5 h-3.5 animate-ping" />
          <span>Physical System Node</span>
        </div>
        <p className="text-[10px] text-slate-400 mt-0.5">Core Telemetry & Live Traffic Ingress</p>
        <div className="mt-1 flex items-center space-x-2 text-[11px] text-slate-300">
          <span>Latency: <b className="text-white">{nominalLatency} ms</b></span>
          <span className="text-slate-600">•</span>
          <span className="text-emerald-400">Online</span>
        </div>
      </div>

      {/* Center Signal Pulse Label */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none flex flex-col items-center">
        <div className="px-3 py-1 rounded-full bg-slate-950/80 backdrop-blur-md border border-cyan-500/50 text-[10px] font-mono font-bold text-cyan-300 uppercase tracking-widest shadow-[0_0_15px_rgba(84,214,232,0.3)] flex items-center space-x-1.5">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          <span>Visual Signal Stream</span>
        </div>
      </div>

      {/* Node 2 Label Overlay (Digital Twin Model) */}
      <div className="absolute bottom-4 right-4 pointer-events-none bg-slate-900/85 backdrop-blur-md border border-cyan-500/40 p-2.5 rounded-xl text-xs font-mono text-right shadow-xl">
        <div className="flex items-center justify-end space-x-1.5 text-cyan-400 font-bold">
          <span>Digital Twin Node</span>
          <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
        </div>
        <p className="text-[10px] text-slate-400 mt-0.5">Queueing Delay & Sweep Engine</p>
        <div className="mt-1 flex items-center justify-end space-x-2 text-[11px] text-slate-300">
          <span>Worst: <b className="text-amber-400">{worstLatency} ms</b></span>
          <span className="text-slate-600">•</span>
          <span className={decision === 'ACCEPT' ? 'text-emerald-400' : 'text-amber-400 font-bold'}>
            {decision.replace('_', ' ')}
          </span>
        </div>
      </div>
    </div>
  );
}
