import React, { useEffect, useRef } from 'react';
import { useCurrentFrame, AbsoluteFill, useVideoConfig } from 'remotion';
import { gsap } from 'gsap';

export const ShapesEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const containerRef = useRef<SVGSVGElement>(null);
  const shapeRef = useRef<SVGGElement>(null);

  useEffect(() => {
    if (!shapeRef.current) return;

    if (overlay.animation === 'pulse') {
      gsap.to(shapeRef.current, {
        scale: 1.2,
        opacity: 0.8,
        duration: 1.5,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      });
    } else if (overlay.animation === 'morph') {
       // Advanced morphing logic would require specific paths,
       // here we simulate it with complex transformations
       gsap.to(shapeRef.current, {
         rotation: 360,
         borderRadius: "20%",
         duration: 4,
         repeat: -1,
         ease: "none"
       });
    } else if (overlay.animation === 'float') {
      gsap.to(shapeRef.current, {
        y: "-=30",
        x: "+=20",
        duration: 2,
        repeat: -1,
        yoyo: true,
        ease: "power1.inOut"
      });
    }
  }, [overlay.animation]);

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  const renderShape = () => {
    const color = overlay.color || "#3b82f6";
    const x = overlay.position?.x || width / 2;
    const y = overlay.position?.y || height / 2;
    const size = overlay.size || 100;

    switch (overlay.shape_type) {
      case 'circle':
        return (
          <circle
            cx={x}
            cy={y}
            r={size}
            fill="none"
            stroke={color}
            strokeWidth="2"
            className="drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]"
          />
        );
      case 'rect':
        return (
          <rect
            x={x - size}
            y={y - size}
            width={size * 2}
            height={size * 2}
            fill="none"
            stroke={color}
            strokeWidth="2"
            rx={overlay.radius || 0}
            className="drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]"
          />
        );
      case 'line':
        return (
          <line
            x1={x - size}
            y1={y}
            x2={x + size}
            y2={y}
            stroke={color}
            strokeWidth="2"
            strokeDasharray="10 5"
          />
        );
      default:
        return null;
    }
  };

  return (
    <AbsoluteFill className="pointer-events-none">
      <svg ref={containerRef} width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
        <g ref={shapeRef} style={{ transformOrigin: `${overlay.position?.x || width/2}px ${overlay.position?.y || height/2}px` }}>
          {renderShape()}

          {/* Secondary decorative elements */}
          {overlay.decorated && (
             <g opacity="0.3">
                <circle cx={overlay.position?.x || width/2} cy={overlay.position?.y || height/2} r={(overlay.size || 100) + 20} fill="none" stroke={overlay.color} strokeWidth="1" strokeDasharray="4 4" />
                <circle cx={overlay.position?.x || width/2} cy={overlay.position?.y || height/2} r={(overlay.size || 100) + 40} fill="none" stroke={overlay.color} strokeWidth="0.5" />
             </g>
          )}
        </g>
      </svg>
    </AbsoluteFill>
  );
};
