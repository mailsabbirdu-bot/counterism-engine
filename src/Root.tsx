import React, { useEffect } from 'react';
import { Composition, delayRender, continueRender, staticFile, getInputProps } from 'remotion';
import { Scene } from './Scene';
import defaultTemplate from '../remotion_template.json';

const inputProps = getInputProps();
// Support both { templateData: ... } and direct template JSON
const template = (inputProps as any)?.scenes
  ? inputProps
  : ((inputProps as any)?.templateData || defaultTemplate);

const processCameraAutomation = (scene: any) => {
    const mapOverlay = scene.overlays.find((o: any) => o.type === 'map');
    if (!mapOverlay || (scene.camera && scene.camera.shots && scene.camera.shots.length > 0)) {
        return scene;
    }

    const duration = scene.duration_in_frames;
    const isTransit = mapOverlay.routes && mapOverlay.routes.length > 0;

    // Automated Documentary-style Camera Sequence
    const shots = [];

    if (isTransit) {
        // Stage 1: Reveal Context (Wide)
        shots.push({
            targetId: mapOverlay.id,
            startFrame: 0,
            duration: 45,
            zoom: 0.5, // Start wide
            style: 'slow_push' as const
        });

        // Stage 2: Follow Pulse (Tight)
        shots.push({
            targetId: mapOverlay.id,
            startFrame: 60,
            duration: duration - 120,
            zoom: 2.0,
            trackMap: 'pulse' as const,
            style: 'static' as const
        });

        // Stage 3: Arrive & Zoom Out
        shots.push({
            targetId: mapOverlay.id,
            startFrame: duration - 60,
            duration: 60,
            zoom: 1.2,
            trackMap: 'focus' as const,
            style: 'slow_pull' as const
        });
    } else {
        // Stage 1: Dramatic Entry (World/Country -> Focus)
        shots.push({
            targetId: mapOverlay.id,
            startFrame: 0,
            duration: 90,
            zoom: 0.6,
            style: 'dramatic_reveal' as const
        });

        // Stage 2: Detailed Hold
        shots.push({
            targetId: mapOverlay.id,
            startFrame: 100,
            duration: duration - 100,
            zoom: 1.5,
            trackMap: 'focus' as const,
            style: 'slow_push' as const
        });
    }

    return {
        ...scene,
        camera: {
            ...scene.camera,
            enabled: true,
            shots: [...(scene.camera?.shots || []), ...shots]
        }
    };
};

export const RemotionRoot: React.FC = () => {
  // Pre-load fonts from template
  useEffect(() => {
    const fontsToLoad = new Set<string>();
    template.scenes.forEach((scene: any) => {
      scene.overlays.forEach((overlay: any) => {
        if (overlay.type === 'text' && overlay.font) {
          fontsToLoad.add(overlay.font);
        }
      });
    });

    const handle = delayRender('Loading Fonts');

    Promise.all(Array.from(fontsToLoad).map(async (fontName) => {
      try {
        console.log(`Loading font: ${fontName}`);
        // For Remotion V4 and standard Google Fonts, we can often just inject a link tag
        // or use the @remotion/google-fonts package if we know the font at compile time.
        // For dynamic loading, let's use the WebFont loader pattern or simply a dynamic link tag.

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = `https://fonts.googleapis.com/css2?family=${fontName.replace(/ /g, '+')}:wght@400;700&display=swap`;
        document.head.appendChild(link);

        // Wait for font to load
        await document.fonts.load(`1em ${fontName}`);
        console.log(`Loaded font: ${fontName}`);
      } catch (e) {
        console.error(`Failed to load font: ${fontName}`, e);
      }
    })).then(() => {
      continueRender(handle);
    }).catch(err => {
      console.error("Critical font loading error", err);
      continueRender(handle);
    });
  }, []);

  return (
    <>
      {template.scenes.map((scene: any) => {
        const processedScene = processCameraAutomation(scene);
        return (
          <Composition
            key={scene.scene_id}
            id={scene.scene_id.replace(/_/g, '-')}
            component={Scene}
            durationInFrames={scene.duration_in_frames}
            fps={template.global_settings.fps}
            width={template.global_settings.width}
            height={template.global_settings.height}
            defaultProps={{
              sceneData: processedScene
            }}
          />
        );
      })}
    </>
  );
};
