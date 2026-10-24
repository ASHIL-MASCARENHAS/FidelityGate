'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Radio, ShieldCheck, Sparkles, AlertCircle } from 'lucide-react';

interface InteractiveNetworkGlobeProps {
  className?: string;
  soundEnabled?: boolean;
}

interface NetworkHub {
  id: string;
  name: string;
  city: string;
  lat: number;
  lon: number;
  color: string;
  nominalLatencyMs: number;
}

const NETWORK_HUBS: NetworkHub[] = [
  { id: 'fra', name: 'Frankfurt Core', city: 'Frankfurt, DE', lat: 50.11, lon: 8.68, color: '#55D9F4', nominalLatencyMs: 2.1 },
  { id: 'lon', name: 'London Transit', city: 'London, UK', lat: 51.50, lon: -0.12, color: '#4169F5', nominalLatencyMs: 3.4 },
  { id: 'nyc', name: 'New York Edge', city: 'New York, US', lat: 40.71, lon: -74.00, color: '#55D9F4', nominalLatencyMs: 18.2 },
  { id: 'sfo', name: 'Silicon Valley Gateway', city: 'San Jose, US', lat: 37.33, lon: -121.88, color: '#4169F5', nominalLatencyMs: 22.5 },
  { id: 'tyo', name: 'Tokyo Spine', city: 'Tokyo, JP', lat: 35.68, lon: 139.76, color: '#55D9F4', nominalLatencyMs: 14.8 },
  { id: 'sin', name: 'Singapore Regional IX', city: 'Singapore, SG', lat: 1.35, lon: 103.82, color: '#4169F5', nominalLatencyMs: 8.9 },
  { id: 'zrh', name: 'Zurich Secure PoP', city: 'Zurich, CH', lat: 47.37, lon: 8.54, color: '#22C58B', nominalLatencyMs: 1.8 },
  { id: 'sao', name: 'São Paulo Transit', city: 'São Paulo, BR', lat: -23.55, lon: -46.63, color: '#F2A93B', nominalLatencyMs: 31.0 },
  { id: 'syd', name: 'Sydney Edge', city: 'Sydney, AU', lat: -33.86, lon: 151.20, color: '#55D9F4', nominalLatencyMs: 28.4 },
  { id: 'bom', name: 'Mumbai Edge', city: 'Mumbai, IN', lat: 19.07, lon: 72.87, color: '#4169F5', nominalLatencyMs: 16.7 },
];

const NETWORK_ARCS: [string, string][] = [
  ['lon', 'fra'],
  ['fra', 'zrh'],
  ['lon', 'nyc'],
  ['nyc', 'sfo'],
  ['sfo', 'tyo'],
  ['tyo', 'sin'],
  ['sin', 'bom'],
  ['bom', 'fra'],
  ['nyc', 'sao'],
  ['sin', 'syd'],
];

function latLonToVector3(lat: number, lon: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);
  return new THREE.Vector3(x, y, z);
}

function isLand(lat: number, lon: number): boolean {
  // North America
  if (lat >= 15 && lat <= 72 && lon >= -168 && lon <= -52) {
    if (lat < 30 && lon < -105) return false;
    if (lat < 25 && lon > -80) return false;
    if (lat > 50 && lon > -60) return false;
    return true;
  }
  // South America
  if (lat >= -56 && lat <= 13 && lon >= -82 && lon <= -34) {
    if (lat > 0 && lon < -75) return false;
    if (lat < -20 && lon > -40) return false;
    return true;
  }
  // Europe
  if (lat >= 36 && lat <= 71 && lon >= -11 && lon <= 42) {
    if (lat < 45 && lon < -10) return false;
    return true;
  }
  // Africa
  if (lat >= -35 && lat <= 37 && lon >= -18 && lon <= 52) {
    if (lat > 32 && lon < -5) return false;
    if (lat < 0 && lon > 42) return false;
    return true;
  }
  // Asia
  if (lat >= 5 && lat <= 77 && lon >= 42 && lon <= 180) {
    if (lat < 10 && lon < 95) return false;
    return true;
  }
  // Australia & New Zealand
  if (lat >= -45 && lat <= -11 && lon >= 112 && lon <= 154) return true;
  if (lat >= -47 && lat <= -34 && lon >= 166 && lon <= 179) return true;
  // Japan / Indonesia / Philippines
  if (lat >= 30 && lat <= 46 && lon >= 129 && lon <= 146) return true;
  if (lat >= -10 && lat <= 6 && lon >= 95 && lon <= 141) return true;
  if (lat >= 5 && lat <= 19 && lon >= 120 && lon <= 127) return true;

  return false;
}

export function InteractiveNetworkGlobe({ className = '', soundEnabled = false }: InteractiveNetworkGlobeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hasWebGL, setHasWebGL] = useState<boolean>(true);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(false);
  const [selectedHub, setSelectedHub] = useState<NetworkHub>(NETWORK_HUBS[0]);
  const [isHovered, setIsHovered] = useState<boolean>(false);

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
    if (!container) return;

    // Check WebGL availability safely
    try {
      const testCanvas = document.createElement('canvas');
      const gl = testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl');
      if (!gl) {
        setHasWebGL(false);
        return;
      }
    } catch {
      setHasWebGL(false);
      return;
    }

    const width = container.clientWidth || 540;
    const height = container.clientHeight || 540;

    // Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 6.2);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Root Globe Group for interactive rotation
    const globeGroup = new THREE.Group();
    // Default tilt towards Europe / Atlantic
    globeGroup.rotation.x = 0.28;
    globeGroup.rotation.y = -0.65;
    scene.add(globeGroup);

    const GLOBE_RADIUS = 2.0;

    // 1. Dark Core Sphere
    const coreGeo = new THREE.SphereGeometry(GLOBE_RADIUS - 0.02, 64, 64);
    const coreMat = new THREE.MeshPhysicalMaterial({
      color: 0x070c18,
      emissive: 0x050e1f,
      emissiveIntensity: 0.5,
      roughness: 0.18,
      metalness: 0.85,
      clearcoat: 0.6,
      clearcoatRoughness: 0.2,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    globeGroup.add(coreMesh);

    // 2. Electric Blue / Cyan Thin Atmosphere Glow
    const atmosGeo = new THREE.SphereGeometry(GLOBE_RADIUS + 0.04, 48, 48);
    const atmosMat = new THREE.MeshBasicMaterial({
      color: 0x55d9f4,
      transparent: true,
      opacity: 0.07,
      wireframe: false,
      side: THREE.BackSide,
    });
    const atmosMesh = new THREE.Mesh(atmosGeo, atmosMat);
    atmosMesh.scale.set(1.08, 1.08, 1.08);
    scene.add(atmosMesh);

    // 3. Spherical Reference Grid Lines (Latitudes & Longitudes)
    const gridMat = new THREE.LineBasicMaterial({
      color: 0x22334a,
      transparent: true,
      opacity: 0.35,
    });

    // Latitude rings
    [-60, -30, 0, 30, 60].forEach((lat) => {
      const ringRadius = GLOBE_RADIUS * Math.cos(lat * (Math.PI / 180));
      const ringY = GLOBE_RADIUS * Math.sin(lat * (Math.PI / 180));
      const ringCurve = new THREE.EllipseCurve(0, 0, ringRadius, ringRadius, 0, 2 * Math.PI, false, 0);
      const points = ringCurve.getPoints(64).map((p) => new THREE.Vector3(p.x, ringY, p.y));
      const ringGeo = new THREE.BufferGeometry().setFromPoints(points);
      const ring = new THREE.Line(ringGeo, gridMat);
      globeGroup.add(ring);
    });

    // 4. Dotted Geographic Landmasses (True Continents)
    const landPositions: number[] = [];
    const step = 2.4;
    for (let lat = -78; lat <= 78; lat += step) {
      for (let lon = -180; lon <= 180; lon += step) {
        if (isLand(lat, lon)) {
          const pos = latLonToVector3(lat, lon, GLOBE_RADIUS);
          landPositions.push(pos.x, pos.y, pos.z);
        }
      }
    }

    const dotGeo = new THREE.BufferGeometry();
    dotGeo.setAttribute('position', new THREE.Float32BufferAttribute(landPositions, 3));
    const dotMat = new THREE.PointsMaterial({
      color: 0x4169f5,
      size: 0.038,
      transparent: true,
      opacity: 0.72,
    });
    const landPoints = new THREE.Points(dotGeo, dotMat);
    globeGroup.add(landPoints);

    // 5. Hub Nodes and Great-Circle Arcs
    const hubMap = new Map<string, THREE.Vector3>();
    NETWORK_HUBS.forEach((hub) => {
      const pos = latLonToVector3(hub.lat, hub.lon, GLOBE_RADIUS);
      hubMap.set(hub.id, pos);

      // Node marker dot
      const markerGeo = new THREE.SphereGeometry(0.045, 16, 16);
      const markerMat = new THREE.MeshBasicMaterial({ color: hub.color });
      const markerMesh = new THREE.Mesh(markerGeo, markerMat);
      markerMesh.position.copy(pos);
      globeGroup.add(markerMesh);

      // Outer pulse ring
      const ringGeo = new THREE.RingGeometry(0.06, 0.08, 16);
      const ringMat = new THREE.MeshBasicMaterial({
        color: hub.color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.45,
      });
      const pulseRing = new THREE.Mesh(ringGeo, ringMat);
      pulseRing.position.copy(pos.clone().multiplyScalar(1.01));
      pulseRing.lookAt(new THREE.Vector3(0, 0, 0));
      globeGroup.add(pulseRing);
    });

    // 6. Curved Connection Arcs & Travelling Signal Particles
    interface ArcTrack {
      curve: THREE.CubicBezierCurve3;
      particle: THREE.Mesh;
      speed: number;
      offset: number;
    }
    const arcTracks: ArcTrack[] = [];

    const arcMat = new THREE.LineBasicMaterial({
      color: 0x55d9f4,
      transparent: true,
      opacity: 0.38,
    });

    const particleGeo = new THREE.SphereGeometry(0.032, 12, 12);
    const particleMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
    });

    NETWORK_ARCS.forEach(([fromId, toId], index) => {
      const p1 = hubMap.get(fromId);
      const p2 = hubMap.get(toId);
      if (!p1 || !p2) return;

      const distance = p1.distanceTo(p2);
      const mid = p1.clone().add(p2).multiplyScalar(0.5);
      const midLength = mid.length();
      // Arch higher for longer links
      const arcElevation = GLOBE_RADIUS + Math.max(0.25, distance * 0.28);
      mid.normalize().multiplyScalar(arcElevation);

      const control1 = p1.clone().lerp(mid, 0.5).normalize().multiplyScalar(arcElevation * 0.96);
      const control2 = p2.clone().lerp(mid, 0.5).normalize().multiplyScalar(arcElevation * 0.96);

      const curve = new THREE.CubicBezierCurve3(p1, control1, control2, p2);
      const curvePoints = curve.getPoints(40);
      const curveGeo = new THREE.BufferGeometry().setFromPoints(curvePoints);
      const curveLine = new THREE.Line(curveGeo, arcMat);
      globeGroup.add(curveLine);

      // Signal Particle travelling along this arc
      const particle = new THREE.Mesh(particleGeo, particleMat.clone());
      globeGroup.add(particle);

      arcTracks.push({
        curve,
        particle,
        speed: 0.25 + (index % 3) * 0.08,
        offset: (index * 0.17) % 1.0,
      });
    });

    // Interactive Drag to Rotate
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let targetRotationY = globeGroup.rotation.y;
    let targetRotationX = globeGroup.rotation.x;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;

      targetRotationY += deltaX * 0.005;
      targetRotationX += deltaY * 0.005;
      targetRotationX = Math.max(-1.1, Math.min(1.1, targetRotationX));

      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const dom = renderer.domElement;
    dom.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    // Touch support for mobile / tablets
    const onTouchStart = (e: TouchEvent) => {
      if (e.touches.length === 1) {
        isDragging = true;
        prevMouseX = e.touches[0].clientX;
        prevMouseY = e.touches[0].clientY;
      }
    };

    const onTouchMove = (e: TouchEvent) => {
      if (!isDragging || e.touches.length !== 1) return;
      const deltaX = e.touches[0].clientX - prevMouseX;
      const deltaY = e.touches[0].clientY - prevMouseY;

      targetRotationY += deltaX * 0.006;
      targetRotationX += deltaY * 0.006;
      targetRotationX = Math.max(-1.1, Math.min(1.1, targetRotationX));

      prevMouseX = e.touches[0].clientX;
      prevMouseY = e.touches[0].clientY;
    };

    dom.addEventListener('touchstart', onTouchStart, { passive: true });
    window.addEventListener('touchmove', onTouchMove, { passive: true });
    window.addEventListener('touchend', onMouseUp);

    // Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      // Smooth auto-rotation when not dragging
      if (!isDragging && !prefersReducedMotion) {
        targetRotationY += 0.0022;
      }

      // Smooth damping interpolation
      globeGroup.rotation.y += (targetRotationY - globeGroup.rotation.y) * 0.08;
      globeGroup.rotation.x += (targetRotationX - globeGroup.rotation.x) * 0.08;

      // Animate travelling signal particles along network arcs
      if (!prefersReducedMotion) {
        arcTracks.forEach((track) => {
          const t = (elapsed * track.speed + track.offset) % 1.0;
          const pos = track.curve.getPoint(t);
          track.particle.position.copy(pos);
          const pMat = track.particle.material as THREE.MeshBasicMaterial;
          pMat.color.set(t > 0.5 ? 0x55d9f4 : 0x4169f5);
        });
      }

      renderer.render(scene, camera);
    };

    animate();

    // Resize handler
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      dom.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      dom.removeEventListener('touchstart', onTouchStart);
      window.removeEventListener('touchmove', onTouchMove);
      window.removeEventListener('touchend', onMouseUp);

      // Clean up GPU resources
      coreGeo.dispose();
      coreMat.dispose();
      atmosGeo.dispose();
      atmosMat.dispose();
      dotGeo.dispose();
      dotMat.dispose();
      arcMat.dispose();
      particleGeo.dispose();
      particleMat.dispose();
      gridMat.dispose();
      renderer.dispose();
      if (container) {
        container.innerHTML = '';
      }
    };
  }, [prefersReducedMotion]);

  if (!hasWebGL) {
    // Polished Non-WebGL Fallback
    return (
      <div className={`relative w-full aspect-square max-w-[500px] mx-auto rounded-3xl border border-hairline dark:border-hairline-dark bg-surface dark:bg-surface-dark flex flex-col items-center justify-center p-8 text-center ${className}`}>
        <div className="w-24 h-24 rounded-full border-2 border-dashed border-cobalt/40 flex items-center justify-center mb-4 text-cobalt">
          <Radio className="w-10 h-10 animate-pulse" />
        </div>
        <h3 className="text-sm font-bold text-ink dark:text-ink-dark">Interactive 3D Network Globe</h3>
        <p className="text-xs text-muted-fg dark:text-muted-dark mt-2 max-w-xs">
          WebGL acceleration is disabled in this environment. The multi-commodity network topology remains active in the digital twin.
        </p>
        <span className="mt-4 px-3 py-1 rounded-full text-[11px] font-mono bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark text-muted-fg">
          Illustrative Visualization Fallback
        </span>
      </div>
    );
  }

  return (
    <div
      className={`relative w-full aspect-square max-w-[520px] mx-auto flex items-center justify-center select-none ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Three.js Canvas Container */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Floating Active Hub Telemetry Overlay Badge */}
      <div className="absolute top-4 left-4 p-3 rounded-xl bg-surface/90 dark:bg-surface-dark/90 backdrop-blur-md border border-hairline dark:border-hairline-dark shadow-elevation text-left pointer-events-none transition-all">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-accent animate-ping" />
          <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-cyan-accent">
            Core Network Mesh
          </span>
        </div>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="text-xs font-semibold text-ink dark:text-ink-dark">{selectedHub.name}</span>
          <span className="text-[10px] font-mono text-muted-fg dark:text-muted-dark">{selectedHub.city}</span>
        </div>
        <div className="mt-1 flex items-center gap-3 text-[10px] font-mono text-muted-fg dark:text-muted-dark">
          <span>Nominal RTT: <strong className="text-emerald-verdict">{selectedHub.nominalLatencyMs} ms</strong></span>
          <span>10 Monitored Arcs</span>
        </div>
      </div>

      {/* Illustrative Disclaimer Bottom Pill */}
      <div className="absolute bottom-4 right-4 px-3 py-1.5 rounded-full bg-surface/85 dark:bg-surface-dark/85 backdrop-blur-md border border-hairline dark:border-hairline-dark text-[10px] font-mono text-muted-fg dark:text-muted-dark shadow-sm pointer-events-none flex items-center gap-1.5">
        <Sparkles className="w-3 h-3 text-cobalt" />
        <span>Illustrative Global Network Topology</span>
      </div>

      {/* Interactive Drag Hint */}
      {isHovered && (
        <div className="absolute bottom-4 left-4 px-2.5 py-1 rounded-md bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark text-[10px] font-mono text-muted-fg dark:text-muted-dark pointer-events-none animate-fadeIn">
          Drag to rotate
        </div>
      )}
    </div>
  );
}

