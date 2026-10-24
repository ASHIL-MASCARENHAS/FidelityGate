'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { playTick, playConfirmation } from '@/lib/sound';
import { ShieldCheck, AlertTriangle, Radio } from 'lucide-react';

interface FocalNetworkTwin3DProps {
  soundEnabled?: boolean;
}

export function FocalNetworkTwin3D({ soundEnabled = false }: FocalNetworkTwin3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<'nominal' | 'counterexample'>('nominal');
  const [hasWebGL, setHasWebGL] = useState<boolean>(true);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      if (mediaQuery.matches) {
        setPrefersReducedMotion(true);
      }
    }
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || prefersReducedMotion) return;

    // Check WebGL support
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) {
        setHasWebGL(false);
        return;
      }
    } catch {
      setHasWebGL(false);
      return;
    }

    const width = container.clientWidth || 500;
    const height = container.clientHeight || 460;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(0, 0, 7.8);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 2. Lighting
    const ambientLight = new THREE.AmbientLight(0x0a1020, 2.5);
    scene.add(ambientLight);

    const cyanLight = new THREE.PointLight(0x00f0ff, 4.0, 15);
    cyanLight.position.set(3, 3, 4);
    scene.add(cyanLight);

    const blueRimLight = new THREE.PointLight(0x315cf5, 3.5, 12);
    blueRimLight.position.set(-3.5, -2, -2);
    scene.add(blueRimLight);

    // 3. Focal Group (tilts with mouse)
    const focalGroup = new THREE.Group();
    scene.add(focalGroup);

    // A. Centerpiece Core Sphere (Obsidian Dark Glass)
    const coreGeo = new THREE.SphereGeometry(1.6, 64, 64);
    const coreMat = new THREE.MeshPhysicalMaterial({
      color: 0x05070f,
      emissive: 0x001830,
      emissiveIntensity: 0.4,
      roughness: 0.12,
      metalness: 0.92,
      clearcoat: 1.0,
      clearcoatRoughness: 0.1,
    });
    const coreSphere = new THREE.Mesh(coreGeo, coreMat);
    focalGroup.add(coreSphere);

    // B. Geodesic Cybernetic Shell
    const shellGeo = new THREE.IcosahedronGeometry(1.72, 3);
    const shellMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      wireframe: true,
      transparent: true,
      opacity: 0.22,
    });
    const shellMesh = new THREE.Mesh(shellGeo, shellMat);
    focalGroup.add(shellMesh);

    // C. Atmospheric Glow Disc (BilloDesign Moon Horizon homage)
    const auraGeo = new THREE.RingGeometry(1.75, 2.6, 64);
    const auraMat = new THREE.MeshBasicMaterial({
      color: 0x00c8f8,
      transparent: true,
      opacity: 0.18,
      side: THREE.DoubleSide,
    });
    const auraMesh = new THREE.Mesh(auraGeo, auraMat);
    auraMesh.position.z = -0.3;
    focalGroup.add(auraMesh);

    // D. Concentric Orbital Routing Rings
    const ring1Geo = new THREE.TorusGeometry(2.35, 0.018, 16, 100);
    const ring1Mat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.65 });
    const ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
    ring1.rotation.x = Math.PI / 3;
    ring1.rotation.y = Math.PI / 6;
    focalGroup.add(ring1);

    const ring2Geo = new THREE.TorusGeometry(2.7, 0.015, 16, 100);
    const ring2Mat = new THREE.MeshBasicMaterial({ color: 0x315cf5, transparent: true, opacity: 0.55 });
    const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
    ring2.rotation.x = -Math.PI / 4;
    ring2.rotation.z = Math.PI / 5;
    focalGroup.add(ring2);

    const ring3Geo = new THREE.TorusGeometry(3.1, 0.012, 16, 100);
    const ring3Mat = new THREE.MeshBasicMaterial({ color: 0x60a5fa, transparent: true, opacity: 0.4 });
    const ring3 = new THREE.Mesh(ring3Geo, ring3Mat);
    ring3.rotation.y = Math.PI / 2.5;
    focalGroup.add(ring3);

    // E. Traveling Telemetry Packets (Orbiting particles)
    const packetGeo = new THREE.SphereGeometry(0.065, 16, 16);
    const packetMatCyan = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const packetMatAmber = new THREE.MeshBasicMaterial({ color: 0xf59e0b });

    const packet1 = new THREE.Mesh(packetGeo, packetMatCyan);
    const packet2 = new THREE.Mesh(packetGeo, packetMatAmber);
    const packet3 = new THREE.Mesh(packetGeo, packetMatCyan);
    focalGroup.add(packet1);
    focalGroup.add(packet2);
    focalGroup.add(packet3);

    // F. Node Satellites (PoP Gateways)
    const nodeData = [
      { name: 'Frankfurt PoP', angle: 0, radius: 2.35, ring: ring1 },
      { name: 'Milan Transit', angle: 2.1, radius: 2.7, ring: ring2 },
      { name: 'Zurich Egress', angle: 4.2, radius: 3.1, ring: ring3 },
    ];
    const nodeMeshes: THREE.Mesh[] = [];
    nodeData.forEach((d) => {
      const nodeGeo = new THREE.SphereGeometry(0.12, 16, 16);
      const nodeMat = new THREE.MeshStandardMaterial({
        color: 0x00f0ff,
        emissive: 0x00e5ff,
        emissiveIntensity: 0.8,
        roughness: 0.2,
      });
      const nodeMesh = new THREE.Mesh(nodeGeo, nodeMat);
      focalGroup.add(nodeMesh);
      nodeMeshes.push(nodeMesh);
    });

    // 4. Pointer Interaction
    let targetRotationX = 0;
    let targetRotationY = 0;
    let currentRotationX = 0;
    let currentRotationY = 0;

    const handlePointerMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      targetRotationY = x * 0.45;
      targetRotationX = -y * 0.35;
    };

    window.addEventListener('mousemove', handlePointerMove);

    // 5. Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      // Smooth pointer damping
      currentRotationX += (targetRotationX - currentRotationX) * 0.05;
      currentRotationY += (targetRotationY - currentRotationY) * 0.05;

      focalGroup.rotation.x = currentRotationX;
      focalGroup.rotation.y = currentRotationY + elapsed * 0.12;

      // Rotate sub-elements
      shellMesh.rotation.y -= delta * 0.15;
      ring1.rotation.z += delta * 0.2;
      ring2.rotation.z -= delta * 0.25;
      ring3.rotation.x += delta * 0.18;

      // Orbit packets
      const t1 = elapsed * 1.5;
      packet1.position.set(
        Math.cos(t1) * 2.35 * Math.cos(Math.PI / 6),
        Math.sin(t1) * 2.35 * Math.sin(Math.PI / 3),
        Math.sin(t1) * 2.35 * Math.cos(Math.PI / 3)
      );

      const t2 = elapsed * 1.1 + 1.2;
      packet2.position.set(
        Math.cos(t2) * 2.7 * Math.cos(Math.PI / 5),
        Math.sin(t2) * 2.7 * Math.cos(-Math.PI / 4),
        Math.sin(t2) * 2.7 * Math.sin(-Math.PI / 4)
      );

      const t3 = elapsed * 1.8 + 2.5;
      packet3.position.set(
        Math.cos(t3) * 3.1 * Math.sin(Math.PI / 2.5),
        Math.sin(t3) * 3.1,
        Math.cos(t3) * 3.1 * Math.cos(Math.PI / 2.5)
      );

      // Pulse aura opacity subtly
      auraMat.opacity = 0.18 + Math.sin(elapsed * 2) * 0.05;

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || 500;
      const h = container.clientHeight || 460;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('mousemove', handlePointerMove);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animId);
      renderer.dispose();
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [prefersReducedMotion]);

  const toggleMode = () => {
    playConfirmation(soundEnabled);
    setMode((prev) => (prev === 'nominal' ? 'counterexample' : 'nominal'));
  };

  return (
    <div className="relative w-full h-[440px] sm:h-[480px] lg:h-[520px] flex items-center justify-center select-none">
      {/* Glow aura backdrop */}
      <div
        className={`absolute inset-0 rounded-full blur-3xl opacity-30 transition-colors duration-700 pointer-events-none ${
          mode === 'counterexample' ? 'bg-amber-500/25' : 'bg-cyan-500/25'
        }`}
      />

      {/* 3D WebGL Canvas Container */}
      <div
        ref={containerRef}
        className="w-full h-full cursor-grab active:cursor-grabbing relative z-10"
        title="Interactive 3D Digital Twin - Move pointer to tilt"
      />

      {/* Accessible Fallback when WebGL or reduced-motion is requested */}
      {(!hasWebGL || prefersReducedMotion) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center z-10 p-6 text-center">
          <div className="w-56 h-56 rounded-full border-2 border-cyan-400/40 bg-paper dark:bg-paper-dark/80 flex items-center justify-center shadow-2xl relative overflow-hidden">
            <div className="absolute inset-4 rounded-full border border-cobalt/40 border-dashed animate-spin-slow" />
            <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-cyan-500 to-cobalt flex items-center justify-center shadow-lg">
              <Radio className="w-10 h-10 text-white animate-pulse" />
            </div>
          </div>
          <span className="text-xs text-muted-fg dark:text-muted-dark mt-4">
            Digital-Twin Telemetry Sphere (Accessible Fallback)
          </span>
        </div>
      )}

      {/* Floating HUD Badges & Interactive Mode Controller */}
      <div className="absolute bottom-4 left-4 right-4 flex flex-wrap items-center justify-between gap-3 z-20 pointer-events-auto">
        {/* Node status indicator */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-surface/80 dark:bg-surface-dark/80 backdrop-blur-md border border-hairline dark:border-hairline-dark text-[11px] font-mono text-ink dark:text-ink-dark shadow-sm">
          <span
            className={`w-2 h-2 rounded-full ${
              mode === 'counterexample' ? 'bg-amber-400 animate-ping' : 'bg-cyan-400 animate-pulse'
            }`}
          />
          <span>{mode === 'counterexample' ? 'M/M/1 Counterexample Burst' : 'Nominal Data Plane'}</span>
        </div>

        {/* Interactive Mode Toggle */}
        <button
          onClick={toggleMode}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-cobalt hover:bg-cobalt-hover text-white text-[11px] font-mono font-medium tracking-tight shadow-md transition-all active:scale-95"
        >
          {mode === 'counterexample' ? (
            <>
              <AlertTriangle className="w-3.5 h-3.5 text-amber-300" />
              <span>Simulate Burst</span>
            </>
          ) : (
            <>
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-200" />
              <span>Verify Zero-Drift</span>
            </>
          )}
        </button>
      </div>

      {/* Pointer hint pill */}
      <div className="absolute top-4 right-4 z-20 hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-paper/60 dark:bg-paper-dark/60 backdrop-blur-sm border border-hairline/60 dark:border-hairline-dark/60 text-[11px] font-mono text-muted-fg dark:text-muted-dark">
        <span>Pointer Reactive</span>
      </div>
    </div>
  );
}
