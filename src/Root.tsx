import React, { useEffect, useMemo } from 'react';
import { Composition, delayRender, continueRender, staticFile, getInputProps } from 'remotion';
import { Scene } from './Scene';
import defaultTemplate from '../remotion_template.json';

// Import Global SVG Styles once
import '../svg/styles/svgAnimations.css';

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

    // Font Loading with Timeout and Individual Error Handling
    const fontPromises = Array.from(fontsToLoad).map(async (fontName) => {
      try {
        console.log(`Loading font: ${fontName}`);

        // 1. Try to load as a local font from /public/fonts/
        const extensions = ['ttf', 'otf', 'woff2', 'woff'];
        const nameVariants = [
            fontName,
            fontName.replace(/ /g, '_'),
            fontName.replace(/ /g, '-'),
            fontName.toLowerCase().replace(/ /g, '_'),
            fontName.toLowerCase().replace(/ /g, '-')
        ];

        let loadedLocally = false;

        for (const variant of Array.from(new Set(nameVariants))) {
            for (const ext of extensions) {
                const urls = [
                    staticFile(`fonts/${variant}.${ext}`),
                    staticFile(`fonts/drive_fonts/${variant}.${ext}`),
                    `/fonts/${variant}.${ext}`, // Direct path fallback
                    `./fonts/${variant}.${ext}`, // Relative path fallback
                ];

                for (const url of urls) {
                    try {
                        // Encode URL to handle spaces/special chars
                        const safeUrl = url.includes('%') ? url : encodeURI(url);
                        const fontFace = new FontFace(fontName, `url(${safeUrl})`);
                        await fontFace.load();
                        document.fonts.add(fontFace);
                        console.log(`✅ Success: Loaded local font "${fontName}" from variant "${variant}" via ${safeUrl}`);
                        loadedLocally = true;
                        break;
                    } catch (e) {
                        // Try next URL/extension/variant
                    }
                }
                if (loadedLocally) break;
            }
            if (loadedLocally) break;
        }

        // 1b. Fallback: Try injecting @font-face style if FontFace API is being picky
        if (!loadedLocally) {
            console.log(`⚠️ FontFace API failed for ${fontName}, trying @font-face injection...`);
            const style = document.createElement('style');
            // Try a likely filename
            const variant = fontName.replace(/ /g, '_');
            const safeUrl = encodeURI(staticFile(`fonts/${variant}.ttf`));
            style.appendChild(document.createTextNode(`
                @font-face {
                    font-family: '${fontName}';
                    src: url('${safeUrl}') format('truetype');
                }
            `));
            document.head.appendChild(style);

            try {
                await document.fonts.load(`1em ${fontName}`);
                console.log(`✅ Success: Loaded local font "${fontName}" via @font-face injection.`);
                loadedLocally = true;
            } catch (e) {
                // Style injection failed too
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
    });

    const timeout = new Promise((resolve) => setTimeout(resolve, 5000));
    Promise.race([Promise.all(fontPromises), timeout]).then(() => {
      continueRender(handle);
    }).catch(err => {
      console.error("Critical font loading error", err);
      continueRender(handle);
    });
  }, []);

  return (
    <>
      {template.scenes.map((scene: any) => {
        console.log(`[Root] Initializing Composition for Scene: ${scene.scene_id} (${scene.duration_in_frames} frames)`);
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
