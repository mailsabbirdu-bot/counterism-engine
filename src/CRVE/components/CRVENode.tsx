import React from 'react';
import { useCurrentFrame, interpolate, spring } from 'remotion';
import { CRVENodeData } from '../lib/types';
import { MOOD_REGISTRY, CinematicMood } from '../lib/moodRegistry';

interface CRVENodeProps {
  node: CRVENodeData;
  progress: number;
  active: boolean;
  font?: string;
  cinematic_mood?: CinematicMood;
  index: number;
  startFrame?: number;
}

export const CRVENode: React.FC<CRVENodeProps> = ({ node, progress, active, font, cinematic_mood, index, startFrame = 0 }) => {
  const frame = useCurrentFrame();

  const isHeader = (node as any).isHeaderNode;

  // Topological rank-based entry to follow the proper flow of information
  const nodeRank = (node as any).rank ?? 0;
  const rankDelay = isHeader ? 0 : nodeRank * 35;
  const relativeFrame = frame - startFrame;
  const entryFrame = Math.max(0, relativeFrame - rankDelay);

  const entryScale = spring({
      frame: entryFrame,
      fps: 30,
      config: { damping: 16, stiffness: 60 }
  });

  // Calculate dynamic continuous active window fade-in/out opacity
  const getActiveWindowOpacity = () => {
      const windows = (node as any).active_windows;
      if (!windows) return 1.0;

      let maxOpacity = 0.0;
      const cushion = 10;
      for (const [s, e] of windows) {
          if (frame >= s && frame <= e) {
              const fromStart = frame - s;
              const fromEnd = e - frame;
              const fadeIn = interpolate(fromStart, [0, cushion], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
              const fadeOut = interpolate(fromEnd, [0, cushion], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
              const currentOpacity = Math.min(fadeIn, fadeOut);
              if (currentOpacity > maxOpacity) {
                  maxOpacity = currentOpacity;
              }
          }
      }
      return maxOpacity;
  };

  const windowOpacity = getActiveWindowOpacity();
  const activeTargetOpacity = (node as any).active_windows ? windowOpacity : (active ? 1 : 0.4);

  const nodeOpacity = interpolate(entryScale, [0, 1], [0, activeTargetOpacity]);
  const finalOpacity = nodeOpacity * progress;

  const mood = MOOD_REGISTRY[cinematic_mood || 'documentary'] || MOOD_REGISTRY['documentary'];

  // Language Detection (English vs Bangla)
  const isBangla = /[\u0980-\u09FF]/.test(node.label);
  const fontStyle = {
    fontFamily: font || (isBangla ? 'Sohid_bangla, sans-serif' : 'Audiowide-Regular_english, Inter, sans-serif')
  };

  const baseSize = node.font_size || (14 + (node.importance ?? 1) * 3.5);
  const displayFontSize = active ? `${baseSize * 1.15}px` : `${baseSize}px`;

  // Determine distinctive type category
  const isCauseNode = node.type === 'danger_core' || node.type === 'abstract_core' || node.id.includes('cause') || node.type.includes('cause');
  let nodeCategory = String(node.type).toLowerCase();
  if (isCauseNode) {
    nodeCategory = 'cause';
  }

  // Header render block
  if (isHeader) {
    return (
      <div
        className="flex flex-col items-center justify-center p-6 rounded-2xl relative select-none"
        style={{
          background: 'radial-gradient(100% 100% at 50% 0%, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0) 100%)',
          backdropFilter: 'blur(16px)',
          border: `1px solid rgba(255, 255, 255, 0.08)`,
          boxShadow: `0 20px 50px rgba(0, 0, 0, 0.3)`,
          minWidth: '420px',
          ...fontStyle,
          opacity: finalOpacity,
          transform: `scale(${entryScale})`
        }}
      >
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 h-[2px]"
          style={{
            width: '120px',
            background: `linear-gradient(90deg, transparent, ${mood.colors.primary}, transparent)`,
            boxShadow: `0 0 10px ${mood.colors.primary}`
          }}
        />
        <span
          className="text-xs uppercase tracking-[0.4em] mb-2 font-bold opacity-60"
          style={{ color: mood.colors.primary }}
        >
          {cinematic_mood} perspective
        </span>
        <h1
          className="font-extrabold text-white tracking-widest text-center uppercase"
          style={{
            fontSize: node.font_size ? `${node.font_size}px` : '36px',
            textShadow: active ? `0 0 30px ${mood.colors.primary}` : 'none',
          }}
        >
          {node.label}
        </h1>
        <div className="flex items-center gap-4 mt-4 w-full justify-center">
          <div className="h-[1px] w-16 bg-white opacity-20" />
          <div
            className="w-2 h-2 rounded-full"
            style={{
              backgroundColor: mood.colors.primary,
              boxShadow: `0 0 8px ${mood.colors.primary}`
            }}
          />
          <div className="h-[1px] w-16 bg-white opacity-20" />
        </div>
      </div>
    );
  }

  // Define dynamic ultra-high modern styles per distinct node type
  let containerStyle: React.CSSProperties = {};
  let childrenAccents: React.ReactNode = null;

  switch (nodeCategory) {
    case 'cause': // Crimson/Amber Warning Panel Style
      containerStyle = {
        background: active
          ? 'repeating-linear-gradient(45deg, rgba(244, 63, 94, 0.04) 0px, rgba(244, 63, 94, 0.04) 8px, rgba(0, 0, 0, 0.6) 8px, rgba(0, 0, 0, 0.6) 16px)'
          : 'rgba(20, 10, 10, 0.7)',
        borderColor: active ? '#f43f5e' : 'rgba(244, 63, 94, 0.2)',
        borderLeft: active ? '5px solid #f43f5e' : '1px solid rgba(244, 63, 94, 0.2)',
        boxShadow: active ? '0 12px 35px rgba(244, 63, 94, 0.25), inset 0 0 12px rgba(244, 63, 94, 0.1)' : 'none',
        borderRadius: '6px',
      };
      childrenAccents = active ? (
        <>
          <div className="absolute top-1 right-2 flex gap-1">
            <span className="w-1 h-1 rounded-full bg-[#f43f5e] animate-ping" />
            <span className="w-1.5 h-1.5 rounded-full bg-[#f43f5e]" />
          </div>
          <span className="absolute bottom-1 left-2 text-[8px] tracking-[0.2em] font-extrabold text-[#f43f5e] opacity-70">ALERT.CORE</span>
        </>
      ) : null;
      break;

    case 'hero': // Cyberpunk Tech Neon Cyan Panel Style
      containerStyle = {
        background: active
          ? 'linear-gradient(135deg, rgba(0, 245, 255, 0.08), rgba(0, 245, 255, 0.01))'
          : 'rgba(10, 20, 25, 0.7)',
        borderColor: active ? '#00f5ff' : 'rgba(0, 245, 255, 0.2)',
        borderLeft: active ? '6px solid #00f5ff' : '1px solid rgba(0, 245, 255, 0.2)',
        boxShadow: active ? '0 15px 40px rgba(0, 245, 255, 0.3), inset 0 0 15px rgba(0, 245, 255, 0.15)' : 'none',
        borderRadius: '8px',
      };
      childrenAccents = active ? (
        <>
          <div className="absolute top-1 right-1 w-2 h-2 border-r-[2px] border-t-[2px] border-[#00f5ff]" />
          <div className="absolute bottom-1 left-1 w-2 h-2 border-l-[2px] border-b-[2px] border-[#00f5ff]" />
          {/* Subtle grid of background dots */}
          <div className="absolute inset-0 pointer-events-none opacity-20" style={{ backgroundImage: 'radial-gradient(rgba(0, 245, 255, 0.4) 1px, transparent 0)', backgroundSize: '8px 8px' }} />
          <span className="absolute bottom-1 right-2 text-[8px] tracking-[0.2em] font-extrabold text-[#00f5ff]">HERO.TARGET</span>
        </>
      ) : null;
      break;

    case 'organization': // Tech Gold Matte Card Style
      containerStyle = {
        background: active
          ? 'linear-gradient(135deg, rgba(234, 179, 8, 0.06), rgba(0, 0, 0, 0.65))'
          : 'rgba(25, 20, 10, 0.7)',
        borderColor: active ? '#eab308' : 'rgba(234, 179, 8, 0.2)',
        borderRight: active ? '4px solid #eab308' : '1px solid rgba(234, 179, 8, 0.2)',
        boxShadow: active ? '0 10px 30px rgba(234, 179, 8, 0.15)' : 'none',
        borderRadius: '6px',
      };
      childrenAccents = active ? (
        <>
          <div className="absolute top-1 left-2 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 bg-[#eab308] rotate-45" />
            <span className="text-[7px] text-[#eab308] tracking-widest uppercase">ORG.ENTITY</span>
          </div>
          <div className="absolute bottom-1 right-2 w-1.5 h-1.5 border-r border-b border-[#eab308] opacity-60" />
        </>
      ) : null;
      break;

    case 'location': // GIS Emerald Marker Tag Style
      containerStyle = {
        background: active
          ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.06), rgba(0, 0, 0, 0.65))'
          : 'rgba(10, 25, 15, 0.7)',
        borderColor: active ? '#10b981' : 'rgba(16, 185, 129, 0.2)',
        boxShadow: active ? '0 12px 30px rgba(16, 185, 129, 0.15)' : 'none',
        borderRadius: '30px', // High rounded tag
      };
      childrenAccents = active ? (
        <>
          {/* Map coordinate pulse dot */}
          <div className="absolute left-2 w-2 h-2 rounded-full bg-[#10b981] animate-ping" />
          <div className="absolute left-2 w-2 h-2 rounded-full bg-[#10b981]" />
          <span className="absolute right-3 top-1 text-[7px] text-[#10b981] tracking-widest uppercase">LOC.NODE</span>
        </>
      ) : null;
      break;

    case 'metric': // Quantum Purple HUD Style
      containerStyle = {
        background: active ? 'rgba(139, 92, 246, 0.05)' : 'rgba(20, 10, 25, 0.7)',
        borderColor: active ? '#8b5cf6' : 'rgba(139, 92, 246, 0.2)',
        boxShadow: active ? '0 8px 25px rgba(139, 92, 246, 0.15)' : 'none',
        borderRadius: '4px',
        borderLeft: active ? '3px solid #8b5cf6' : '1px solid rgba(139, 92, 246, 0.2)',
        borderRight: active ? '3px solid #8b5cf6' : '1px solid rgba(139, 92, 246, 0.2)',
      };
      childrenAccents = active ? (
        <span className="absolute top-0.5 right-1.5 text-[6px] font-mono text-[#8b5cf6] opacity-80">SYS.VAL_99</span>
      ) : null;
      break;

    case 'event': // Sunset Milestones Capsule style
      containerStyle = {
        background: active ? 'rgba(249, 115, 22, 0.05)' : 'rgba(25, 15, 10, 0.7)',
        borderColor: active ? '#f97316' : 'rgba(249, 115, 22, 0.2)',
        borderRadius: '16px',
        boxShadow: active ? '0 10px 25px rgba(249, 115, 22, 0.15)' : 'none',
      };
      childrenAccents = active ? (
        <>
          <div className="absolute -left-1 w-2 h-[1px] bg-[#f97316]" />
          <div className="absolute -right-1 w-2 h-[1px] bg-[#f97316]" />
        </>
      ) : null;
      break;

    case 'concept':
    default: // Premium Minimalist Glass Disc style
      containerStyle = {
        background: active
          ? 'rgba(255, 255, 255, 0.03)'
          : 'rgba(0, 0, 0, 0.4)',
        borderColor: active ? 'rgba(255, 255, 255, 0.35)' : 'rgba(255, 255, 255, 0.08)',
        backdropFilter: 'blur(10px)',
        borderRadius: '6px',
        boxShadow: active ? '0 10px 30px rgba(255, 255, 255, 0.08), inset 0 0 10px rgba(255,255,255,0.05)' : 'none',
      };
      childrenAccents = active ? (
        <>
          <div className="absolute -top-1 -left-1 w-1.5 h-1.5 border-t border-l border-white opacity-80" />
          <div className="absolute -bottom-1 -right-1 w-1.5 h-1.5 border-b border-r border-white opacity-80" />
        </>
      ) : null;
      break;
  }

  // Padding shift for location tags to avoid overlapping map coordinate pulse dot
  const paddingLeft = nodeCategory === 'location' ? 'pl-8' : 'px-6';

  return (
    <div
      className={`${paddingLeft} py-3 border flex items-center justify-center font-bold text-lg select-none relative`}
      style={{
        ...fontStyle,
        color: '#ffffff',
        opacity: finalOpacity,
        transform: `scale(${entryScale})`,
        transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        ...containerStyle
      }}
    >
      {/* Node Category Accent Overlays */}
      {childrenAccents}

      {/* Main Text Content */}
      <span
        className="tracking-wider uppercase"
        style={{
          fontSize: displayFontSize,
          textShadow: active
            ? (nodeCategory === 'hero' ? '0 0 12px rgba(0, 245, 255, 0.6)' : (nodeCategory === 'cause' ? '0 0 12px rgba(244, 63, 94, 0.6)' : 'none'))
            : 'none',
        }}
      >
        {node.label}
      </span>
    </div>
  );
};
