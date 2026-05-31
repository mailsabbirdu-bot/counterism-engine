import pkg from '@remotion/bundler';
const { bundle } = pkg;
import { renderMedia, getCompositions } from '@remotion/renderer';
import path from 'path';
import fs from 'fs';
import { execSync } from 'child_process';
import { enableTailwind } from '@remotion/tailwind';

// Parse command line arguments
const args = process.argv.slice(2);
const templateArg = args.find(arg => arg.startsWith('--template='))?.split('=')[1];
const outputArg = args.find(arg => arg.startsWith('--output='))?.split('=')[1];
const concurrencyArg = args.find(arg => arg.startsWith('--concurrency='))?.split('=')[1];

const templatePath = templateArg && path.isAbsolute(templateArg)
  ? templateArg
  : path.join(process.cwd(), templateArg || 'remotion_template.json');

if (!fs.existsSync(templatePath)) {
  console.error(`❌ Template file not found: ${templatePath}`);
  process.exit(1);
}

const template = JSON.parse(fs.readFileSync(templatePath, 'utf8'));

const getVideoDuration = (path: string): number => {
  try {
    const stdout = execSync(
      `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${path}"`
    );
    return parseFloat(stdout.toString().trim());
  } catch (e) {
    return 0;
  }
};

const start = async () => {
  try {
    console.log(`🚀 Starting Counterism Studio V4 Rendering Pipeline (Template: ${path.basename(templatePath)})...`);

    const entry = path.join(process.cwd(), 'src/index.ts');
    const publicDir = path.join(process.cwd(), 'public');

    console.log('📦 Bundling project...');
    const bundleLocation = await bundle({
      entryPoint: entry,
      publicDir: publicDir,
      webpackOverride: (config) => enableTailwind(config),
    });

    console.log(`📡 Bundle Location: ${bundleLocation}`);
    console.log(`📂 Public Directory: ${publicDir}`);

    console.log('🚚 Ensuring public assets are correctly placed in bundle root...');
    try {
      // Manually copy public content to bundle root to bypass potential bundling quirks in Colab
      execSync(`cp -R ${publicDir}/* ${bundleLocation}/ 2>/dev/null || true`);
      console.log('✅ Manual asset synchronization complete.');
    } catch (e) {
      console.warn('⚠️  Manual asset copy encountered an issue, continuing with bundler defaults.');
    }

    console.log('\n📦 Inspecting Bundle for Public Assets:');
    if (fs.existsSync(bundleLocation)) {
      const bundleFiles = fs.readdirSync(bundleLocation);
      console.log(`- Bundle Files: ${bundleFiles.join(', ')}`);

      // Check for assets directory or files
      const assetsPath = path.join(bundleLocation, 'assets');
      if (fs.existsSync(assetsPath)) {
        console.log(`- Assets folder found: ${fs.readdirSync(assetsPath).slice(0, 5).join(', ')}...`);
      }
    }

    console.log('\n🔍 Pre-render Asset Verification & Duration Adjustment:');
    let assetsMissing = false;
    const fps = template.global_settings?.fps || 30;

    for (const scene of template.scenes) {
      console.log(`\n--- Scene: ${scene.scene_id} ---`);

      // Verify background video and update duration
      if (scene.background_type === 'video' && scene.video_path) {
        const bgPath = path.join(process.cwd(), 'public', scene.video_path);
        if (fs.existsSync(bgPath)) {
          const stats = fs.statSync(bgPath);
          console.log(`✅ Background Video FOUND: ${scene.video_path} (${(stats.size / (1024 * 1024)).toFixed(2)} MB)`);

          // Primary Rule: duration_in_frames = background video duration
          try {
            const stdout = execSync(
              `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${bgPath}"`
            );
            const durationInSeconds = parseFloat(stdout.toString().trim());
            if (!isNaN(durationInSeconds)) {
              const frames = Math.floor(durationInSeconds * fps);
              console.log(`📏 Adjusting duration: ${scene.duration_in_frames} -> ${frames} frames (Based on video)`);
              scene.duration_in_frames = frames;
            }
          } catch (e) {
            console.warn(`⚠️ Could not probe duration for ${bgPath}, using default.`);
          }
        } else {
          console.error(`❌ Background Video MISSING: ${bgPath}`);
          assetsMissing = true;
        }
      }

      // Verify overlays
      if (scene.overlays) {
        for (const overlay of scene.overlays) {
          if ((overlay.type === 'video' || overlay.type === 'image') && overlay.src) {
            const overlayPath = path.join(process.cwd(), 'public', overlay.src);
            if (fs.existsSync(overlayPath)) {
              const stats = fs.statSync(overlayPath);
              console.log(`✅ Overlay Asset [${overlay.id}] FOUND: ${overlay.src} (${(stats.size / (1024 * 1024)).toFixed(2)} MB)`);
            } else {
              console.error(`❌ Overlay Asset [${overlay.id}] MISSING: ${overlayPath}`);
              assetsMissing = true;
            }
          }
        }
      }
    }

    if (assetsMissing) {
      console.warn('\n⚠️  WARNING: Some assets are missing. Rendering may fail or show placeholders.');
    } else {
      console.log('\n✨ All assets verified successfully!');
    }

    console.log('\n🔍 Extracting compositions...');
    // We pass the potentially modified 'template' object here so compositions get the updated durations
    const compositions = await getCompositions(bundleLocation, {
      inputProps: { templateData: template }
    });

    const outputDir = path.join(process.cwd(), 'renders/overlays/remotion');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const concurrency = concurrencyArg ? parseInt(concurrencyArg, 10) : 1;

    for (const scene of template.scenes) {
      console.log(`\n🎬 Processing Scene: ${scene.scene_id}`);

      const compositionId = scene.scene_id.replace(/_/g, '-');
      const composition = compositions.find((c) => c.id === compositionId);
      if (!composition) {
        console.error(`❌ Composition ${scene.scene_id} not found`);
        continue;
      }

      // Determine output location
      let outputLocation: string;
      if (outputArg && template.scenes.length === 1) {
        outputLocation = path.join(outputDir, outputArg);
      } else {
        outputLocation = path.join(
          outputDir,
          `updated_scene_${scene.scene_id}.mp4`
        );
      }

      console.log(`⏳ Rendering ${scene.scene_id} (Concurrency: ${concurrency})...`);

      const renderOptions: any = {
        composition,
        serveUrl: bundleLocation,
        codec: 'h264',
        outputLocation,
        inputProps: { sceneData: scene, templateData: template },
        concurrency: concurrency,
        publicDir: path.join(process.cwd(), 'public'),
        onProgress: ({ progress }: { progress: number }) => {
          process.stdout.write(`\rProgress: ${(progress * 100).toFixed(1)}%`);
        },
        onLog: (log: any) => {
          console.log(`[Browser Log] ${log.level}: ${log.text}`);
        },
      };

      await renderMedia(renderOptions);

      console.log(`\n✅ Finished: ${outputLocation}`);
    }

    console.log('\n🏁 All scenes rendered successfully!');
  } catch (error) {
    console.error('❌ Error in start function:', error);
    process.exit(1);
  }
};

start().catch((err) => {
  console.error('❌ Render failed:', err);
  process.exit(1);
});
