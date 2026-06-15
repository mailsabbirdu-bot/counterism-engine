import React, { useEffect, useState } from 'react';
import { Audio, staticFile, Sequence, getInputProps } from 'remotion';

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
    // 1. Try to get manifest from injected props (fastest & reliable)
    if (template?.audio_sfx_manifest) {
        setAudioManifest(template.audio_sfx_manifest);
        return;
    }

    // 2. Fallback: Attempt to fetch the manifest from the public folder
    const fetchManifest = async () => {
      try {
        const response = await fetch(staticFile('renders/audios/timestamp_audio.txt'));
        if (response.ok) {
          const data = await response.json();
          setAudioManifest(data);
        }
      } catch (e) {
        // No SFX manifest found, which is fine
      }
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
            src={staticFile(`renders/audios/${sfx.file}`)}
            volume={sfx.volume}
            // Mute error to keep terminal output clean
            onError={() => {}}
          />
        </Sequence>
      ))}
    </>
  );
};
