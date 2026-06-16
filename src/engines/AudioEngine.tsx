import React, { useEffect, useState } from 'react';
import { Audio, Sequence, getInputProps } from 'remotion';
import { resolveAsset } from '../lib/resolveAsset';

interface AudioEntry {
  scene_id: string;
  file: string;
  start: number;
  end: number;
  volume: number;
  status?: string;
}

export const AudioEngine: React.FC<{ sceneId: string }> = ({ sceneId }) => {
  const [audioManifest, setAudioManifest] = useState<AudioEntry[]>([]);
  const props = getInputProps() as any;
  const template = props?.scenes ? props : (props?.templateData || {});

  useEffect(() => {
    if (template?.audio_sfx_manifest) {
        setAudioManifest(template.audio_sfx_manifest);
        return;
    }

    const fetchManifest = async () => {
      try {
        const url = resolveAsset('renders/audios/timestamp_audio.txt');
        const response = await fetch(url);
        if (response.ok) {
          const data = await response.json();
          setAudioManifest(data);
        }
      } catch (e) {}
    };

    fetchManifest();
  }, [template]);

  const sceneSfx = audioManifest.filter(entry =>
    entry.scene_id === sceneId && entry.status !== 'failed'
  );

  return (
    <>
      {sceneSfx.map((sfx, i) => (
        <Sequence from={sfx.start} durationInFrames={Math.max(1, sfx.end - sfx.start)} key={`${sfx.file}-${i}`}>
          <Audio
            src={resolveAsset(`renders/audios/${sfx.file}`)}
            volume={sfx.volume}
            // Mute error to prevent render crash on 404
            onError={() => {}}
          />
        </Sequence>
      ))}
    </>
  );
};
