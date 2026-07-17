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
  // Rank 0 displays first, then Rank 1, Rank 2, etc. with a substantial spacing (35 frames)
  const nodeRank = (node as any).rank ?? 0;
  const rankDelay = isHeader ? 0 : nodeRank * 35;
  const relativeFrame = frame - startFrame;
  const entryFrame = Math.max(0, relativeFrame - rankDelay);

  const entryScale = spring({
      frame: entryFrame,
      fps: 30,
      config: { damping: 16, stiffness: 60 }
  });

  const nodeOpacity = interpolate(entryScale, [0, 1], [0, active ? 1 : 0.4]);
  const finalOpacity = nodeOpacity * progress;

  const mood = MOOD_REGISTRY[cinematic_mood || 'documentary'] || MOOD_REGISTRY['documentary'];
  const glowColor = active ? mood.colors.primary : "rgba(255, 255, 255, 0.2)";

  // Language Detection (English vs Bangla)
  const isBangla = /[\u0980-\u09FF]/.test(node.label);
  const fontStyle = {
    fontFamily: font || (isBangla ? 'Sohid_bangla, sans-serif' : 'Audiowide-Regular_english, Inter, sans-serif')
  };

  if (isHeader) {
    // Elegant glassmorphic title card with unique stylistic accents depending on cinematic_mood
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
        {/* Animated dynamic line indicator */}
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 h-[2px]"
          style={{
            width: '120px',
            background: `linear-gradient(90deg, transparent, ${mood.colors.primary}, transparent)`,
            boxShadow: `0 0 10px ${mood.colors.primary}`
          }}
        />

        {/* Cinematic subtitle label */}
        <span
          className="text-xs uppercase tracking-[0.4em] mb-2 font-bold opacity-60"
          style={{ color: mood.colors.primary }}
        >
          {cinematic_mood} perspective
        </span>

        {/* Majestic Title text */}
        <h1
          className="text-4xl font-extrabold text-white tracking-widest text-center uppercase"
          style={{
            textShadow: active ? `0 0 30px ${mood.colors.primary}` : 'none',
          }}
        >
          {node.label}
        </h1>

        {/* Accent dots and lines below */}
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

  // Beautiful Mood-specific custom card presets for relationship nodes!
  return (
    <div
      className="px-6 py-3 rounded-lg border flex items-center justify-center font-bold text-lg select-none relative"
      style={{
        ...fontStyle,
        color: '#ffffff',
        opacity: finalOpacity,
        transform: `scale(${entryScale})`,
        transition: 'all 0.3s ease',
        background: active
          ? `linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01))`
          : 'rgba(0, 0, 0, 0.4)',
        borderColor: active ? `${mood.colors.primary}50` : 'rgba(255, 255, 255, 0.1)',
        boxShadow: active
          ? `0 10px 30px rgba(0,0,0,0.2), inset 0 0 15px ${mood.colors.primary}20, 0 0 25px ${mood.colors.primary}30`
          : 'none',
      }}
    >
      {/* Corner aesthetic brackets for Scientific or Cyberpunk */}
      {active && (cinematic_mood === 'scientific' || cinematic_mood === 'cyberpunk') && (
        <>
          <div className="absolute -top-1 -left-1 w-2 h-2 border-t-2 border-l-2" style={{ borderColor: mood.colors.primary }} />
          <div className="absolute -bottom-1 -right-1 w-2 h-2 border-b-2 border-r-2" style={{ borderColor: mood.colors.primary }} />
        </>
      )}

      {/* Warning blinker for Danger mood */}
      {active && cinematic_mood === 'danger' && (
        <div
          className="absolute -left-2 top-1/2 -translate-y-1/2 w-[4px] h-[70%] rounded-full animate-pulse"
          style={{
            backgroundColor: mood.colors.accent,
            boxShadow: `0 0 8px ${mood.colors.accent}`
          }}
        />
      )}

      {/* Main Text Content */}
      <span
        className="tracking-wider uppercase"
        style={{
          fontSize: active ? '21px' : '17px',
          textShadow: active ? `0 0 10px ${mood.colors.primary}` : 'none',
        }}
      >
        {node.label}
      </span>
    </div>
  );
};
