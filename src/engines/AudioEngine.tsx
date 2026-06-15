import React, { useEffect, useState } from 'react';
import { Audio, staticFile, Sequence } from 'remotion';

interface AudioEntry {
  scene_id: string;
  file: string;
  start: number;
  end: number;
  volume: number;
}

export const AudioEngine: React.FC<{ sceneId: string }> = ({ sceneId }) => {
  const [audioManifest, setAudioManifest] = useState<AudioEntry[]>([]);

  useEffect(() => {
    // Attempt to fetch the manifest from the public folder
    // This is linked to drive/renders/audios/timestamp_audio.txt
    const fetchManifest = async () => {
      try {
        const response = await fetch(staticFile('renders/audios/timestamp_audio.txt'));
        if (response.ok) {
          const data = await response.json();
          setAudioManifest(data);
        }
      } catch (e) {
        // No SFX manifest found, which is fine
        console.log("No SFX manifest detected for this project.");
      }
    };

    fetchManifest();
  }, []);

  const sceneSfx = audioManifest.filter(entry => entry.scene_id === sceneId);

  return (
    <>
      {sceneSfx.map((sfx, i) => (
        <Sequence from={sfx.start} durationInFrames={sfx.end - sfx.start} key={`${sfx.file}-${i}`}>
          <Audio
            src={staticFile(`renders/audios/${sfx.file}`)}
            volume={sfx.volume}
          />
        </Sequence>
      ))}
    </>
  );
};
