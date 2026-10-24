'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { Radio, Activity, Zap, RotateCw } from 'lucide-react';
import { GateDecision } from '@/types';
import { useChartTheme } from '@/lib/chart-theme';

interface SplineTwinCenterpieceProps {
  decision?: GateDecision;
  nominalLatency?: number;
  worstLatency?: number;
  fidelityScore?: number;
  syncStatus?: string;
}

export function SplineTwinCenterpiece({
  decision = 'ACCEPT',
  nominalLatency = 18,
  worstLatency = 24,
  fidelityScore = 94.2,
  syncStatus = 'SYNCHRONIZED',
}: SplineTwinCenterpieceProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [signalSpeed, setSignalSpeed] = useState(1.0);
  const [autoRotate, setAutoRotate] = useState(true);
  const { isDark } = useChartTheme();

  // Scene palette.
  //
  // Dark is the original set, untouched. Light is built on the same principle
  // that makes dark read well: the spheres are *lit*, not self-lit. Emissive is
  // kept low so the point lights still produce a terminator and a specular
  // highlight -- a high emissive flattens a sphere into a flat disc. Wireframe
  // shells, rings and the laser take a deeper tone than their core so they stay
  // legible both against the pale backdrop and where they cross the sphere.
  const palette = useMemo(
    () =>
      isDark
        ? {
            fog: 0x080d17,
            fogDensity: 0.04,
            gridMajor: 0x1a334d,
            gridMinor: 0x0c1724,
            physCore: 0x06b6d4,
            physEmissive: 0x0891b2,
            physEmissiveIntensity: 0.5,
            physShell: 0x22d3ee,
            physShellOpacity: 0.35,
            physRing: 0x38bdf8,
            physRingOpacity: 0.7,
            twinRingOpacity: 0.8,
            cageOpacity: 0.45,
            beam: 0x54d6e8,
            beamOpacity: 0.3,
            ambient: 0.8,
            pointIntensity: 2.2,
            keyIntensity: 0,
            metalness: 0.8,
            roughness: 0.18,
            accept: 0x39d3a4,
            evidence: 0xf3b64b,
            abstain: 0xff667d,
            acceptDeep: 0x39d3a4,
            evidenceDeep: 0xf3b64b,
            abstainDeep: 0xff667d,
          }
        : {
            fog: 0xf5f7fb,
            fogDensity: 0.01,
            gridMajor: 0xaeb6c6,
            gridMinor: 0xcfd5e1,
            physCore: 0x38bdf8,
            physEmissive: 0x0ea5e9,
            physEmissiveIntensity: 0.1,
            physShell: 0x0284c7,
            physShellOpacity: 0.75,
            physRing: 0x1d4ed8,
            physRingOpacity: 0.9,
            twinRingOpacity: 0.95,
            cageOpacity: 0.75,
            beam: 0x38bdf8,
            beamOpacity: 0.26,
            ambient: 0.55,
            pointIntensity: 2.4,
            keyIntensity: 1.25,
            metalness: 0.3,
            roughness: 0.26,
            accept: 0x34d399,
            evidence: 0xfbbf24,
            abstain: 0xf87171,
            acceptDeep: 0x047857,
            evidenceDeep: 0xb45309,
            abstainDeep: 0xb91c1c,
          },
    [isDark],
  );

  const statusColorHex =
    decision === 'ACCEPT'
      ? palette.accept
      : decision === 'GATHER_EVIDENCE'
        ? palette.evidence
        : palette.abstain;

  // Line work (cage, rings, laser) sits a shade deeper than the core so it
  // stays readable where it overlaps the sphere. In dark the two are equal.
  const statusLineHex =
    decision === 'ACCEPT'
      ? palette.acceptDeep
      : decision === 'GATHER_EVIDENCE'
        ? palette.evidenceDeep
        : palette.abstainDeep;

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(palette.fog, palette.fogDensity);

    const width = mount.clientWidth;
    const height = mount.clientHeight || 380;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0.5, 9.5);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    // 2. Centerpiece Platform / Cybernetic Grid
    const grid = new THREE.GridHelper(16, 16, palette.gridMajor, palette.gridMinor);
    grid.position.y = -2.4;
    scene.add(grid);

    // 3. Node 1: Physical Infrastructure Node (Left)
    const physicalGroup = new THREE.Group();
    physicalGroup.position.set(-2.8, 0, 0);

    const physCoreGeo = new THREE.SphereGeometry(0.7, 32, 32);
    const physCoreMat = new THREE.MeshStandardMaterial({
      color: palette.physCore,
      emissive: palette.physEmissive,
      emissiveIntensity: palette.physEmissiveIntensity,
      metalness: palette.metalness,
      roughness: palette.roughness,
    });
    const physCore = new THREE.Mesh(physCoreGeo, physCoreMat);
    physicalGroup.add(physCore);

    // Physical Geodesic Wireframe Shell
    const physShellGeo = new THREE.IcosahedronGeometry(0.95, 2);
    const physShellMat = new THREE.MeshBasicMaterial({
      color: palette.physShell,
      wireframe: true,
      transparent: true,
      opacity: palette.physShellOpacity,
    });
    const physShell = new THREE.Mesh(physShellGeo, physShellMat);
    physicalGroup.add(physShell);

    // Orbital Ring for Node 1
    const physRingGeo = new THREE.TorusGeometry(1.2, 0.02, 16, 64);
    const physRingMat = new THREE.MeshBasicMaterial({
      color: palette.physRing,
      transparent: true,
      opacity: palette.physRingOpacity,
    });
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
      emissiveIntensity: palette.physEmissiveIntensity + 0.1,
      metalness: palette.metalness,
      roughness: palette.roughness,
    });
    const twinCore = new THREE.Mesh(twinCoreGeo, twinCoreMat);
    twinGroup.add(twinCore);

    // Digital Hologram Cage for Node 2
    const twinCageGeo = new THREE.DodecahedronGeometry(0.98, 1);
    const twinCageMat = new THREE.MeshBasicMaterial({
      color: statusLineHex,
      wireframe: true,
      transparent: true,
      opacity: palette.cageOpacity,
    });
    const twinCage = new THREE.Mesh(twinCageGeo, twinCageMat);
    twinGroup.add(twinCage);

    // Dual Orbital Rings for Node 2
    const twinRingGeo = new THREE.TorusGeometry(1.2, 0.025, 16, 64);
    const twinRingMat = new THREE.MeshBasicMaterial({
      color: statusLineHex,
      transparent: true,
      opacity: palette.twinRingOpacity,
    });
    const twinRing = new THREE.Mesh(twinRingGeo, twinRingMat);
    twinRing.rotation.x = Math.PI / 1.8;
    twinGroup.add(twinRing);

    const twinRing2 = new THREE.Mesh(twinRingGeo, twinRingMat);
    twinRing2.rotation.y = Math.PI / 3;
    twinGroup.add(twinRing2);

    scene.add(twinGroup);

    // 5. Visual Signal Beam Between the Two Nodes
    const distance = 5.6; // from -2.8 to 2.8

    // Outer Glow Cylinder for the Signal Channel
    const beamGeo = new THREE.CylinderGeometry(0.08, 0.08, distance, 32);
    const beamMat = new THREE.MeshBasicMaterial({
      color: palette.beam,
      transparent: true,
      opacity: palette.beamOpacity,
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
      color: statusLineHex,
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

    const signalParticles: {
      mesh: THREE.Mesh;
      progress: number;
      speed: number;
      offsetY: number;
      offsetZ: number;
    }[] = [];

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
    const ambientLight = new THREE.AmbientLight(0xffffff, palette.ambient);
    scene.add(ambientLight);

    const leftLight = new THREE.PointLight(palette.physCore, palette.pointIntensity, 15);
    leftLight.position.set(-2.8, 2, 3);
    scene.add(leftLight);

    const rightLight = new THREE.PointLight(statusColorHex, palette.pointIntensity * 1.15, 15);
    rightLight.position.set(2.8, 2, 3);
    scene.add(rightLight);

    // Light mode gets a white key from upper left. The two point lights are
    // tinted and sit at the nodes, so on their own they wash the spheres flat;
    // the key is what gives each one a lit side and a shaded side.
    if (palette.keyIntensity > 0) {
      const keyLight = new THREE.DirectionalLight(0xffffff, palette.keyIntensity);
      keyLight.position.set(-4, 6, 6);
      scene.add(keyLight);

      const fillLight = new THREE.DirectionalLight(0xdbe4f5, palette.keyIntensity * 0.35);
      fillLight.position.set(5, -2, 4);
      scene.add(fillLight);
    }

    // 7. Interactive Orbit Controls (Mouse Drag)
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;
    let targetRotY = 0;
    let targetRotX = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
      mount.style.cursor = 'grabbing';
    };

    const onMouseUp = () => {
      isDragging = false;
      mount.style.cursor = 'grab';
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - prevX;
      const dy = e.clientY - prevY;
      prevX = e.clientX;
      prevY = e.clientY;

      targetRotY += dx * 0.006;
      targetRotX += dy * 0.006;
      targetRotX = Math.max(-0.4, Math.min(0.4, targetRotX));
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      camera.position.z += e.deltaY * 0.005;
      camera.position.z = Math.max(6, Math.min(14, camera.position.z));
    };

    mount.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('mousemove', onMouseMove);
    mount.addEventListener('wheel', onWheel, { passive: false });

    // 8. Animation Loop
    let animId: number;
    const clock = new THREE.Clock();

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
      beamMat.opacity = palette.beamOpacity - 0.05 + Math.sin(elapsed * 8) * 0.15;

      // Animate flowing signal particles between the two nodes
      signalParticles.forEach((p) => {
        p.progress += 0.008 * signalSpeed;
        if (p.progress >= 1) p.progress = 0;

        const posX = -2.8 + p.progress * distance;
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
  }, [decision, signalSpeed, autoRotate, statusColorHex, statusLineHex, palette]);

  return (
    <div className="relative w-full h-[400px] rounded-xl overflow-hidden border border-hairline dark:border-hairline-dark bg-gradient-to-b from-[#FBFBFD] via-[#F2F4F9] to-[#E8EBF2] dark:from-[#09111f] dark:via-[#070d18] dark:to-[#040810] shadow-fine dark:shadow-2xl group">
      {/* 3D WebGL Canvas */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Top Overlay Badge */}
      <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-2 bg-surface/92 dark:bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-lg border border-hairline dark:border-cyan-700/60 pointer-events-auto shadow-fine dark:shadow-lg">
          <Zap className="w-4 h-4 shrink-0 text-cobalt dark:text-cyan-400" />
          <span className="text-[13px] font-semibold tracking-[-0.01em] text-ink dark:text-ink-dark">
            Twin-system centerpiece
          </span>
          <span aria-hidden="true" className="w-px h-3.5 bg-hairline dark:bg-slate-700" />
          <span className="hidden lg:inline text-xs text-muted-fg dark:text-slate-400">
            Connected nodes &amp; signal
          </span>
        </div>

        <div className="flex items-center space-x-2 pointer-events-auto">
          {/* Signal Speed Toggle */}
          <button
            onClick={() =>
              setSignalSpeed((prev) => (prev === 1.0 ? 1.8 : prev === 1.8 ? 0.5 : 1.0))
            }
            className="h-8 px-2.5 rounded-lg bg-surface/92 dark:bg-slate-900/80 backdrop-blur-md border border-hairline dark:border-slate-700 hover:border-cobalt dark:hover:border-cyan-500 text-xs text-muted-fg dark:text-slate-300 transition-colors"
            title="Adjust signal particle speed"
          >
            Signal{' '}
            <b className="t-metric font-semibold text-ink dark:text-cyan-400">{signalSpeed}x</b>
          </button>

          {/* Auto Rotate Toggle */}
          <button
            onClick={() => setAutoRotate(!autoRotate)}
            className={`w-8 h-8 inline-flex items-center justify-center rounded-lg backdrop-blur-md border transition-colors ${
              autoRotate
                ? 'bg-cobalt-subtle dark:bg-cyan-500/20 border-cobalt/40 dark:border-cyan-400/60 text-cobalt dark:text-cyan-300'
                : 'bg-surface/92 dark:bg-slate-900/80 border-hairline dark:border-slate-700 text-muted-fg dark:text-slate-400'
            }`}
            title="Toggle auto-orbit"
            aria-label="Toggle auto-orbit"
          >
            <RotateCw
              className={`w-3.5 h-3.5 ${autoRotate ? 'animate-spin' : ''}`}
              style={{ animationDuration: '8s' }}
            />
          </button>
        </div>
      </div>

      {/* Node 1 Label Overlay (Physical Infrastructure) */}
      <div className="absolute bottom-4 left-4 pointer-events-none bg-surface/92 dark:bg-slate-900/85 backdrop-blur-md border border-hairline dark:border-cyan-500/40 px-3 py-2.5 rounded-lg shadow-fine dark:shadow-xl">
        <div className="flex items-center gap-1.5 text-cobalt dark:text-cyan-400">
          <Radio className="w-3.5 h-3.5" />
          <span className="text-[13px] font-semibold tracking-[-0.01em]">Physical system node</span>
        </div>
        <p className="text-xs text-muted-fg dark:text-slate-400 mt-1">
          Core telemetry &amp; live traffic ingress
        </p>
        <div className="mt-1.5 flex items-center gap-2 text-xs text-muted-fg dark:text-slate-300">
          <span>
            Latency{' '}
            <b className="t-metric font-semibold text-ink dark:text-white">{nominalLatency} ms</b>
          </span>
          <span aria-hidden="true" className="w-px h-3 bg-hairline dark:bg-slate-600" />
          <span className="text-emerald-verdict font-medium">Online</span>
        </div>
      </div>

      {/* Center Signal Pulse Label */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none flex flex-col items-center">
        <div className="px-3 py-1.5 rounded-full bg-surface/92 dark:bg-slate-950/80 backdrop-blur-md border border-hairline dark:border-cyan-500/50 shadow-fine dark:shadow-[0_0_15px_rgba(84,214,232,0.3)] flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-cobalt dark:bg-cyan-400 animate-pulse" />
          <span className="text-xs font-medium text-ink dark:text-cyan-300">
            Visual signal stream
          </span>
        </div>
      </div>

      {/* Node 2 Label Overlay (Digital Twin Model) */}
      <div className="absolute bottom-4 right-4 pointer-events-none bg-surface/92 dark:bg-slate-900/85 backdrop-blur-md border border-hairline dark:border-cyan-500/40 px-3 py-2.5 rounded-lg text-right shadow-fine dark:shadow-xl">
        <div className="flex items-center justify-end gap-1.5 text-cobalt dark:text-cyan-400">
          <span className="text-[13px] font-semibold tracking-[-0.01em]">Digital twin node</span>
          <Activity className="w-3.5 h-3.5" />
        </div>
        <p className="text-xs text-muted-fg dark:text-slate-400 mt-1">
          Queueing delay &amp; sweep engine
        </p>
        <div className="mt-1.5 flex items-center justify-end gap-2 text-xs text-muted-fg dark:text-slate-300">
          <span>
            Worst <b className="t-metric font-semibold text-amber-warning">{worstLatency} ms</b>
          </span>
          <span aria-hidden="true" className="w-px h-3 bg-hairline dark:bg-slate-600" />
          <span
            className={`font-medium ${
              decision === 'ACCEPT' ? 'text-emerald-verdict' : 'text-amber-warning'
            }`}
          >
            {decision.replace('_', ' ')}
          </span>
        </div>
      </div>
    </div>
  );
}
export default SplineTwinCenterpiece;
