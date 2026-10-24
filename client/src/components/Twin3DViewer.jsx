import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { RotateCw, ZoomIn, ZoomOut, Eye, Sparkles, ShieldAlert, Cpu } from 'lucide-react';

export default function Twin3DViewer({ decision = 'ACCEPT', nominalLatency = 18, worstLatency = 24, peakUtil = 76 }) {
  const mountRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [autoRotate, setAutoRotate] = useState(true);

  // Status colors mapped to hex
  const decisionColorHex = decision === 'ACCEPT' ? 0x39d3a4 : decision === 'GATHER_EVIDENCE' ? 0xf3b64b : 0xff667d;

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    // Scene & Camera
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x080d17, 0.035);

    const width = mount.clientWidth;
    const height = mount.clientHeight || 340;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 11);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    // Grid Floor
    const grid = new THREE.GridHelper(20, 20, 0x1f344d, 0x101b2a);
    grid.position.y = -3.2;
    scene.add(grid);

    // Node definitions
    const nodesData = [
      { id: 'branch_a', name: 'Branch A', role: 'Edge Ingress', pos: [-3.8, 1.8, 0], color: 0x54d6e8, load: '380 Mbps' },
      { id: 'branch_b', name: 'Branch B', role: 'Edge Ingress', pos: [-3.8, -1.8, 0], color: 0x54d6e8, load: '380 Mbps' },
      { id: 'wan_edge', name: 'WAN Edge', role: 'Traffic Aggregator', pos: [-1.4, 0, 0.5], color: 0x54d6e8, load: '760 Mbps' },
      { id: 'core', name: 'Core Router', role: 'Backbone Transit', pos: [1.2, 0, 0], color: 0x38bdf8, load: '1000 Mbps' },
      { id: 'cloud', name: 'Cloud Fabric', role: 'Egress / SaaS', pos: [3.8, 1.8, 0.3], color: 0x39d3a4, load: '520 Mbps' },
      { id: 'twin', name: 'Twin Decision Gate', role: 'Decision Engine', pos: [3.8, -1.8, 0.3], color: decisionColorHex, load: 'Evaluator' }
    ];

    const nodeMeshes = [];
    const interactiveObjects = [];

    // Create 3D Nodes
    nodesData.forEach((data) => {
      const group = new THREE.Group();
      group.position.set(...data.pos);

      // Core sphere
      const isGate = data.id === 'twin';
      const sphereGeo = new THREE.SphereGeometry(isGate ? 0.45 : 0.35, 32, 32);
      const sphereMat = new THREE.MeshStandardMaterial({
        color: isGate ? decisionColorHex : data.color,
        emissive: isGate ? decisionColorHex : data.color,
        emissiveIntensity: isGate ? 0.7 : 0.4,
        roughness: 0.2,
        metalness: 0.8,
      });
      const sphere = new THREE.Mesh(sphereGeo, sphereMat);
      sphere.userData = data;
      group.add(sphere);
      interactiveObjects.push(sphere);

      // Outer Wireframe Ring
      const ringGeo = new THREE.TorusGeometry(isGate ? 0.7 : 0.55, 0.02, 16, 64);
      const ringMat = new THREE.MeshBasicMaterial({
        color: isGate ? decisionColorHex : 0x54d6e8,
        transparent: true,
        opacity: 0.6,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = Math.PI / 2;
      group.add(ring);

      // Second inclined ring for gate
      if (isGate) {
        const ring2 = new THREE.Mesh(ringGeo, ringMat);
        ring2.rotation.y = Math.PI / 3;
        group.add(ring2);
      }

      scene.add(group);
      nodeMeshes.push({ group, ring, isGate, data });
    });

    // Edges (Network Links)
    const links = [
      { from: [-3.8, 1.8, 0], to: [-1.4, 0, 0.5] },
      { from: [-3.8, -1.8, 0], to: [-1.4, 0, 0.5] },
      { from: [-1.4, 0, 0.5], to: [1.2, 0, 0] },
      { from: [1.2, 0, 0], to: [3.8, 1.8, 0.3] },
      { from: [1.2, 0, 0], to: [3.8, -1.8, 0.3] },
    ];

    const curves = [];
    links.forEach((link) => {
      const vFrom = new THREE.Vector3(...link.from);
      const vTo = new THREE.Vector3(...link.to);
      const mid = new THREE.Vector3().addVectors(vFrom, vTo).multiplyScalar(0.5);
      mid.z += 0.4; // slight curve upwards
      const curve = new THREE.QuadraticBezierCurve3(vFrom, mid, vTo);
      curves.push(curve);

      // Line geometry
      const points = curve.getPoints(30);
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineBasicMaterial({
        color: 0x244565,
        transparent: true,
        opacity: 0.7,
        linewidth: 2,
      });
      const line = new THREE.Line(lineGeo, lineMat);
      scene.add(line);
    });

    // Data Packets (Flying animated particles along curves)
    const packetCount = 20;
    const packetGeo = new THREE.SphereGeometry(0.08, 12, 12);
    const packetMat = new THREE.MeshBasicMaterial({ color: 0x70e1ef });
    const packets = [];

    for (let i = 0; i < packetCount; i++) {
      const pMesh = new THREE.Mesh(packetGeo, packetMat);
      scene.add(pMesh);
      packets.push({
        mesh: pMesh,
        curveIndex: i % curves.length,
        progress: (i / packetCount) % 1,
        speed: 0.005 + Math.random() * 0.004,
      });
    }

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x54d6e8, 2.5, 20);
    pointLight.position.set(0, 4, 6);
    scene.add(pointLight);

    const gateLight = new THREE.PointLight(decisionColorHex, 2.0, 10);
    gateLight.position.set(3.8, -1.8, 1.5);
    scene.add(gateLight);

    // Mouse Interaction / Raycasting
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const onMouseMove = (event) => {
      const rect = mount.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / mount.clientWidth) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / mount.clientHeight) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(interactiveObjects);

      if (intersects.length > 0) {
        setHoveredNode(intersects[0].object.userData);
        mount.style.cursor = 'pointer';
      } else {
        setHoveredNode(null);
        mount.style.cursor = 'grab';
      }
    };

    mount.addEventListener('mousemove', onMouseMove);

    // Orbit Drag Controls (lightweight custom)
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let rotY = 0;
    let rotX = 0;

    const onMouseDown = (e) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
      mount.style.cursor = 'grabbing';
    };

    const onMouseUp = () => {
      isDragging = false;
      mount.style.cursor = 'grab';
    };

    const onDragMove = (e) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;

      rotY += deltaX * 0.006;
      rotX += deltaY * 0.006;
      rotX = Math.max(-0.6, Math.min(0.6, rotX));
    };

    const onWheel = (e) => {
      e.preventDefault();
      camera.position.z += e.deltaY * 0.005;
      camera.position.z = Math.max(6, Math.min(18, camera.position.z));
    };

    mount.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('mousemove', onDragMove);
    mount.addEventListener('wheel', onWheel, { passive: false });

    // Animation Loop
    let animationFrameId;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Slow auto-rotation or drag rotation
      if (autoRotate && !isDragging) {
        scene.rotation.y = Math.sin(elapsedTime * 0.25) * 0.15;
        scene.rotation.x = Math.cos(elapsedTime * 0.2) * 0.06;
      } else {
        scene.rotation.y = rotY;
        scene.rotation.x = rotX;
      }

      // Rotate node rings
      nodeMeshes.forEach(({ ring, isGate }) => {
        ring.rotation.z += 0.015;
        if (isGate) {
          ring.scale.setScalar(1 + Math.sin(elapsedTime * 4) * 0.08);
        }
      });

      // Move packet particles along curves
      packets.forEach((p) => {
        p.progress += p.speed;
        if (p.progress >= 1) p.progress = 0;
        const curve = curves[p.curveIndex];
        const point = curve.getPoint(p.progress);
        p.mesh.position.copy(point);
      });

      renderer.render(scene, camera);
    };

    animate();

    // Handle Resize
    const handleResize = () => {
      if (!mount) return;
      const w = mount.clientWidth;
      const h = mount.clientHeight || 340;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      mount.removeEventListener('mousemove', onMouseMove);
      mount.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('mousemove', onDragMove);
      mount.removeEventListener('wheel', onWheel);
      if (renderer.domElement && mount.contains(renderer.domElement)) {
        mount.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [decision, autoRotate]);

  return (
    <div className="relative w-full h-[360px] rounded-2xl overflow-hidden bg-gradient-to-b from-[#0b1424] to-[#070b13] border border-cyan-900/40 shadow-inner group">
      {/* 3D Canvas Mount */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Top Floating Controls */}
      <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
        <div className="flex items-center space-x-2 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-cyan-800/40 text-xs font-mono text-cyan-300 pointer-events-auto shadow-lg">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-spin" style={{ animationDuration: '6s' }} />
          <span>Interactive 3D Digital Twin</span>
          <span className="text-slate-500">|</span>
          <span className="text-[11px] text-slate-400">Drag to orbit • Scroll to zoom</span>
        </div>

        <div className="flex items-center space-x-1.5 pointer-events-auto">
          <button
            onClick={() => setAutoRotate(!autoRotate)}
            className={`p-2 rounded-xl backdrop-blur-md border text-xs transition-all ${
              autoRotate
                ? 'bg-cyan-500/20 border-cyan-400/50 text-cyan-300 shadow-[0_0_10px_rgba(84,214,232,0.2)]'
                : 'bg-slate-900/80 border-slate-700/60 text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle Auto-Orbit"
          >
            <RotateCw className={`w-3.5 h-3.5 ${autoRotate ? 'animate-spin' : ''}`} style={{ animationDuration: '8s' }} />
          </button>
        </div>
      </div>

      {/* Hover Node Tooltip Overlay */}
      {hoveredNode && (
        <div className="absolute bottom-3 left-3 bg-[#0d1728]/95 backdrop-blur-md border border-cyan-500/50 p-3 rounded-xl shadow-2xl text-xs max-w-xs animate-in fade-in duration-150">
          <div className="flex items-center justify-between mb-1">
            <span className="font-bold text-white text-sm">{hoveredNode.name}</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
              {hoveredNode.role}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-800 text-[11px] font-mono">
            <div>
              <span className="text-slate-400">Nominal Load:</span>
              <p className="text-cyan-300 font-semibold">{hoveredNode.load}</p>
            </div>
            <div>
              <span className="text-slate-400">Status:</span>
              <p className="text-emerald-400 font-semibold">Active Telemetry</p>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Right Twin Telemetry Pill */}
      <div className="absolute bottom-3 right-3 bg-slate-950/80 backdrop-blur-md border border-slate-800/80 px-3 py-1.5 rounded-xl text-[11px] font-mono flex items-center space-x-3 text-slate-300">
        <span className="flex items-center space-x-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
          <span>Nominal: <b className="text-cyan-300">{nominalLatency}ms</b></span>
        </span>
        <span className="text-slate-600">•</span>
        <span>Worst: <b className="text-amber-400">{worstLatency}ms</b></span>
        <span className="text-slate-600">•</span>
        <span>Peak: <b className="text-indigo-400">{peakUtil}%</b></span>
      </div>
    </div>
  );
}
