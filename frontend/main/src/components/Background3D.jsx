import React from 'react';

export default function Background3D() {
  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100%',
      minHeight: '100vh',
      zIndex: -1,
      pointerEvents: 'none',
      background: 'radial-gradient(ellipse at top, var(--rad-color), transparent 80%)',
    }}>
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundImage: `
          linear-gradient(var(--grid-color) 1px, transparent 1px),
          linear-gradient(90deg, var(--grid-color) 1px, transparent 1px)
        `,
        backgroundSize: '40px 40px',
        maskImage: 'linear-gradient(to bottom, black 0%, transparent 60%)',
        WebkitMaskImage: 'linear-gradient(to bottom, black 0%, transparent 60%)'
      }} />
    </div>
  );
}
