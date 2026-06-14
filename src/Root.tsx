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
    return scene;
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

        // 1. Try to load as a local font from /public/fonts/
        // We try common extensions and use direct FontFace loading which is more robust
        const extensions = ['ttf', 'otf', 'woff2', 'woff'];
        let loadedLocally = false;

        for (const ext of extensions) {
            try {
                const fontUrl = staticFile(`fonts/${fontName}.${ext}`);
                // Simple check for drive_fonts path as well
                const driveFontUrl = staticFile(`fonts/drive_fonts/${fontName}.${ext}`);

                for (const url of [fontUrl, driveFontUrl]) {
                    const fontFace = new FontFace(fontName, `url(${url})`);
                    try {
                        await fontFace.load();
                        document.fonts.add(fontFace);
                        console.log(`Found and loaded local font: ${fontName} via ${url}`);
                        loadedLocally = true;
                        break;
                    } catch (e) {
                        // Extension/URL didn't work, continue
                    }
                }
                if (loadedLocally) break;
            } catch (e) {
                // Ignore and try next
            }
        }

        if (!loadedLocally) {
            // 2. Fallback to Google Fonts
            console.log(`Local font not found, falling back to Google Fonts for ${fontName}`);
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = `https://fonts.googleapis.com/css2?family=${fontName.replace(/ /g, '+')}:wght@400;700&display=swap`;
            document.head.appendChild(link);

            // Wait for font to load
            await document.fonts.load(`1em ${fontName}`);
        }

        console.log(`Successfully loaded font: ${fontName}`);
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
