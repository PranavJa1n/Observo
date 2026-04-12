import React, { useRef, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Sphere, Line } from '@react-three/drei';
import { ArrowRight, Terminal, Command } from 'lucide-react';
import { Link } from 'react-router-dom';
import * as THREE from 'three';

// Represents the Observo HDBSCAN Clustering Engine
function ClusteringEngine() {
  const NODES_COUNT = 150;
  
  // 3 main clusters for "normal" log patterns, and 1 for "noise/anomalies"
  const clusterCenters = [
    new THREE.Vector3(-2.5, 1.5, 1),   // Cluster 1 (Blue)
    new THREE.Vector3(2.5, -1.5, -1),  // Cluster 2 (Purple)
    new THREE.Vector3(0, -2.5, 2),     // Cluster 3 (Orange)
  ];

  const nodes = useMemo(() => {
    return Array.from({ length: NODES_COUNT }).map(() => {
      // 10% chance to be an anomaly (HDBSCAN Noise)
      const isAnomaly = Math.random() > 0.9;
      // Assign to a random base cluster
      const clusterId = isAnomaly ? -1 : Math.floor(Math.random() * 3);
      
      // Random chaotic starting position
      const initialPos = new THREE.Vector3(
        (Math.random() - 0.5) * 12,
        (Math.random() - 0.5) * 12,
        (Math.random() - 0.5) * 12
      );

      // Tight offset within its assigned cluster
      const clusterOffset = new THREE.Vector3(
        (Math.random() - 0.5) * 1.5,
        (Math.random() - 0.5) * 1.5,
        (Math.random() - 0.5) * 1.5
      );

      // Color based on cluster ID
      let color;
      if (isAnomaly) color = '#ff4b4b'; // Red
      else if (clusterId === 0) color = '#667eea'; // Blue
      else if (clusterId === 1) color = '#9b51e0'; // Purple
      else color = '#ea580c'; // Orange

      // Random float speeds
      const speed = Math.random() * 0.5 + 0.5;
      const timeOffset = Math.random() * Math.PI * 2;

      return {
        initialPos,
        clusterId,
        clusterOffset,
        color,
        isAnomaly,
        speed,
        timeOffset,
        scatterOffset: new THREE.Vector3(0, 0, 0),
        scatterVelocity: new THREE.Vector3(0, 0, 0),
        ref: React.createRef()
      };
    });
  }, []);

  useFrame(({ clock, pointer }) => {
    const t = clock.getElapsedTime();
    
    // Cycle between 0 (Chaos) and 1 (Clustered) over time
    const cycle = (Math.sin(t * 0.5) + 1) / 2;
    const progress = Math.pow(Math.sin(cycle * Math.PI / 2), 2);

    nodes.forEach(node => {
      if (!node.ref.current) return;

      let basePos = new THREE.Vector3();

      if (node.isAnomaly) {
        basePos.x = node.initialPos.x + Math.sin(t * node.speed + node.timeOffset) * 2;
        basePos.y = node.initialPos.y + Math.cos(t * node.speed + node.timeOffset) * 2;
        basePos.z = node.initialPos.z + Math.sin(t * 0.5 + node.timeOffset) * 2;
      } else {
        const targetPos = clusterCenters[node.clusterId].clone().add(node.clusterOffset);
        targetPos.x += Math.sin(t * node.speed + node.timeOffset) * 0.2;
        targetPos.y += Math.cos(t * node.speed + node.timeOffset) * 0.2;
        basePos.lerpVectors(node.initialPos, targetPos, progress);
      }

      // Mouse Interaction: Determine 2D distance from mouse proxy to the node
      const currentX = basePos.x + node.scatterOffset.x;
      const currentY = basePos.y + node.scatterOffset.y;
      
      // Rough projection of normal mapped pointer [-1, 1] to 3D bounds at Z=0
      const mouseX = pointer.x * 8; 
      const mouseY = pointer.y * 5;
      
      const dX = currentX - mouseX;
      const dY = currentY - mouseY;
      const dist = Math.sqrt(dX * dX + dY * dY);

      // If mouse is near, add explosive escape velocity
      if (dist < 2.0 && dist > 0.01) { 
        const force = (2.0 - dist) * 0.08;
        node.scatterVelocity.x += (dX / dist) * force;
        node.scatterVelocity.y += (dY / dist) * force;
        node.scatterVelocity.z += (Math.random() - 0.5) * force * 2;
      }

      // Apply velocities to offsets
      node.scatterOffset.add(node.scatterVelocity);
      
      // Physics: Friction slows down the velocity
      node.scatterVelocity.multiplyScalar(0.92);
      
      // Physics: Spring tension pulls the offset back to 0 (reform cluster)
      node.scatterOffset.multiplyScalar(0.92);

      // Render Final Position
      node.ref.current.position.copy(basePos).add(node.scatterOffset);
    });
  });

  return (
    <group>
      {nodes.map((n, i) => (
        <Sphere key={i} ref={n.ref} args={[n.isAnomaly ? 0.15 : 0.08, 16, 16]}>
          <meshStandardMaterial 
            color={n.color}
            emissive={n.color}
            emissiveIntensity={n.isAnomaly ? 2 : 0.8}
            roughness={0.2}
          />
        </Sphere>
      ))}
    </group>
  );
}

export default function Hero() {
  return (
    <section style={{ 
      minHeight: '80vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      gap: '40px',
      position: 'relative'
    }}>
      <div style={{ flex: '1', zIndex: 10 }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div style={{ 
            display: 'inline-block',
            padding: '6px 12px',
            borderRadius: '20px',
            background: 'var(--icon-bg)',
            color: 'var(--accent-purple-light)',
            fontWeight: 600,
            fontSize: '0.9rem',
            marginBottom: '20px',
            border: '1px solid var(--card-border)'
          }}>
            v1.0 is Live
          </div>
          <h1 style={{ fontSize: '4rem', lineHeight: '1.1', marginBottom: '24px' }}>
            Transform <span className="text-gradient">log chaos</span> into clarity with AI.
          </h1>
          <p style={{ fontSize: '1.25rem', color: 'var(--text-muted)', marginBottom: '40px', lineHeight: '1.6', maxWidth: '600px' }}>
            Observo automatically clusters similar logs, detects anomalies, and uses Agentic AI to explain what's wrong and exactly how to fix it within seconds.
          </p>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <a href="#install" className="primary-button">
              Get Started <ArrowRight size={20} />
            </a>
            <Link to="/commands" className="secondary-button" style={{ borderColor: 'var(--accent-purple-light)' }}>
              <Command size={20} color="var(--accent-purple-light)" /> CLI Commands
            </Link>
            <a href="https://github.com/PranavJa1n/Observo" target="_blank" rel="noopener noreferrer" className="secondary-button">
              <Terminal size={20} /> View GitHub
            </a>
          </div>
        </motion.div>
      </div>
      
      <div style={{ flex: '1', height: '500px', width: '100%', position: 'relative' }}>
        <Canvas camera={{ position: [0, 0, 8], fov: 50 }}>
          <ambientLight intensity={0.2} />
          <pointLight position={[10, 10, 10]} intensity={1.5} color="#ffffff" />
          <pointLight position={[-10, -10, -10]} intensity={1} color="#667eea" />
          
          <Float floatIntensity={1} speed={1} rotationIntensity={0.5}>
            <React.Suspense fallback={null}>
              <ClusteringEngine />
            </React.Suspense>
          </Float>
        </Canvas>
      </div>
    </section>
  );
}
