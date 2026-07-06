import React, { useEffect, useState } from 'react';
import { Composition, delayRender, continueRender, staticFile, getInputProps } from 'remotion';
import { Scene } from './Scene';
import { SvgAssetPreloader } from '../svg/services/SvgAssetPreloader';
import { SvgScene } from '../svg/types';
import defaultTemplate from '../remotion_template.json';

// Import Global SVG Styles once
import '../svg/styles/svgAnimations.css';

const inputProps = getInputProps();
const template = (inputProps as any)?.scenes
  ? inputProps
  : ((inputProps as any)?.templateData || defaultTemplate);

const processCameraAutomation = (scene: any) => {
    return scene;
};

export const RemotionRoot: React.FC = () => {
  // Pre-load fonts and SVGs
  useEffect(() => {
    const handle = delayRender('Loading Assets');

    const assetsPromises: Promise<any>[] = [];

    // 1. Font Loading
    const fontsToLoad = new Set<string>();
    template.scenes.forEach((scene: any) => {
      (scene.overlays || []).forEach((overlay: any) => {
        if (overlay.font) {
          fontsToLoad.add(overlay.font);
        }
      });
    });

    const fontPromises = Array.from(fontsToLoad).map(async (fontName) => {
      try {
        const extensions = ['ttf', 'otf', 'woff2', 'woff'];
        const variant = fontName.replace(/ /g, '_');
        let loaded = false;

        for (const ext of extensions) {
            try {
                const url = staticFile(`fonts/${variant}.${ext}`);
                const fontFace = new FontFace(fontName, `url(${url})`);
                await fontFace.load();
                document.fonts.add(fontFace);
                loaded = true;
                break;
            } catch (e) {}
        }

        if (!loaded) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = `https://fonts.googleapis.com/css2?family=${fontName.replace(/ /g, '+')}:wght@400;700&display=swap`;
            document.head.appendChild(link);
            await document.fonts.load(`1em ${fontName}`);
        }
      } catch (e) {
        console.error(`Failed to load font: ${fontName}`, e);
      }
    });
    assetsPromises.push(...fontPromises);

    // 2. SVG Preloading (Critical for deterministic rendering)
    const svgPromises = template.scenes.map(async (scene: any) => {
        try {
            await SvgAssetPreloader.preloadScene(scene as SvgScene);
        } catch (e) {
            console.error(`Failed to preload SVGs for scene ${scene.scene_id}`, e);
        }
    });
    assetsPromises.push(...svgPromises);

    const timeout = new Promise((resolve) => setTimeout(resolve, 10000));
    Promise.race([Promise.all(assetsPromises), timeout]).then(() => {
      continueRender(handle);
    }).catch(err => {
      console.error("Critical asset loading error", err);
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
            fps={template.global_settings?.fps || 30}
            width={template.global_settings?.width || 1920}
            height={template.global_settings?.height || 1080}
            defaultProps={{
              sceneData: processedScene
            }}
          />
        );
      })}
    </>
  );
};
