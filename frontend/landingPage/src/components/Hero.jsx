import React, { useRef, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float } from '@react-three/drei';
import { ArrowRight, Terminal, Command } from 'lucide-react';
import { Link } from 'react-router-dom';

function LogStream() {
  const groupRef = useRef();

  // Create an array of random block lengths to look like log text
  const blocks = useMemo(() => Array.from({ length: 30 }).map(() => ({
    x: (Math.random() - 0.5) * 4,
    y: (Math.random() - 0.5) * 10,
    z: (Math.random() - 0.5) * 4,
    width: Math.random() * 2 + 0.5,
    speed: Math.random() * 0.05 + 0.02
  })), []);

  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.children.forEach((mesh, index) => {
        mesh.position.y += blocks[index].speed;
        // reset if it goes too high
        if (mesh.position.y > 5) {
          mesh.position.y = -5;
        }
      });
    }
  });

  return (
    <group ref={groupRef}>
      {blocks.map((b, i) => (
        <mesh key={i} position={[b.x, b.y, b.z]}>
          <boxGeometry args={[b.width, 0.15, 0.5]} />
          <meshStandardMaterial 
            color={i % 3 === 0 ? "#ea580c" : "#9b51e0"} 
            emissive={i % 3 === 0 ? "#ea580c" : "#9b51e0"}
            emissiveIntensity={0.5}
            transparent
            opacity={0.8}
            wireframe={i % 4 === 0}
          />
        </mesh>
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
        <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
          <ambientLight intensity={0.2} />
          <pointLight position={[10, 10, 10]} intensity={1.5} color="#9b51e0" />
          <Float floatIntensity={1.5} speed={1.5}>
            <LogStream />
          </Float>
        </Canvas>
      </div>
    </section>
  );
}
