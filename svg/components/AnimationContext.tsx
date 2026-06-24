import React, { createContext, useContext, useMemo } from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';

interface AnimationContextValue {
  frame: number;
  fps: number;
  width: number;
  height: number;
}

const AnimationContext = createContext<AnimationContextValue | null>(null);

export const AnimationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const value = useMemo(() => ({
    frame,
    fps,
    width,
    height
  }), [frame, fps, width, height]);

  return (
    <AnimationContext.Provider value={value}>
      {children}
    </AnimationContext.Provider>
  );
};

export const useAnimation = () => {
  const context = useContext(AnimationContext);
  if (!context) {
    throw new Error('useAnimation must be used within an AnimationProvider');
  }
  return context;
};
