import React from 'react';
import { AbsoluteFill } from 'remotion';

interface VisualEyeDebugProps {
  analysis: any;
}

export const VisualEyeDebug: React.FC<VisualEyeDebugProps> = ({ analysis }) => {
  if (!analysis) return null;

  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {analysis.objects?.map((obj: any, i: number) => (
        <div
          key={`obj-${i}`}
          style={{
            position: 'absolute',
            left: obj.bbox.x,
            top: obj.bbox.y,
            width: obj.bbox.width,
            height: obj.bbox.height,
            border: '2px solid #ff00ff',
            boxSizing: 'border-box',
          }}
        >
          <span style={{ background: '#ff00ff', color: 'white', fontSize: 12, padding: '2px 4px', position: 'absolute', top: -20 }}>
            {obj.type} ({Math.round(obj.confidence * 100)}%)
          </span>
        </div>
      ))}

      {analysis.safe_text_regions?.map((region: any, i: number) => (
        <div
          key={`safe-${i}`}
          style={{
            position: 'absolute',
            left: region.x,
            top: region.y,
            width: region.width,
            height: region.height,
            border: '2px dashed #00ffff',
            boxSizing: 'border-box',
            backgroundColor: 'rgba(0, 255, 255, 0.1)',
          }}
        >
          <span style={{ background: '#00ffff', color: 'black', fontSize: 12, padding: '2px 4px', position: 'absolute', top: -20 }}>
            Safe Zone ({Math.round(region.confidence * 100)}%)
          </span>
        </div>
      ))}
    </AbsoluteFill>
  );
};
