import React, { useEffect } from 'react';
import { Composition, delayRender, continueRender, staticFile } from 'remotion';
import { Scene } from './Scene';
import template from '../remotion_template.json';

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
      {template.scenes.map((scene: any) => (
        <Composition
          key={scene.scene_id}
          id={scene.scene_id}
          component={Scene}
          durationInFrames={scene.duration_in_frames}
          fps={template.global_settings.fps}
          width={template.global_settings.width}
          height={template.global_settings.height}
          defaultProps={{
            sceneData: scene
          }}
        />
      ))}
    </>
  );
};
