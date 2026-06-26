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
const sceneIdArg = args.find(arg => arg.startsWith('--scene='))?.split('=')[1];

const GOOGLE_DRIVE_MANIFEST = '/content/drive/MyDrive/Counterism_Studio_V4/manifests/remotion_render.json';
const GOOGLE_DRIVE_RENDER_DIR = '/content/drive/MyDrive/Counterism_Studio_V4/renders/overlays/remotion';

const templatePath = templateArg && path.isAbsolute(templateArg)
  ? templateArg
  : templateArg
    ? path.join(process.cwd(), templateArg)
    : GOOGLE_DRIVE_MANIFEST;

if (!fs.existsSync(templatePath)) {
  console.error(`❌ Template file not found: ${templatePath}`);
  process.exit(1);
}

const template = JSON.parse(fs.readFileSync(templatePath, 'utf8'));

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

    console.log('🚚 Ensuring public assets are correctly placed in bundle root (Follow symlinks)...');
    try {
      // Create a public/ subdirectory in the bundle to match staticFile expectations
      const bundlePublicDir = path.join(bundleLocation, 'public');
      if (!fs.existsSync(bundlePublicDir)) fs.mkdirSync(bundlePublicDir, { recursive: true });

      // Copy assets to both root and public/ to be safe
      execSync(`cp -RL ${publicDir}/. ${bundleLocation}/`);
      execSync(`cp -RL ${publicDir}/. ${bundlePublicDir}/`);

      console.log('✅ Manual asset synchronization complete (Symlinks followed).');
    } catch (e) {
      console.warn('⚠️  Manual asset copy encountered an issue:', e instanceof Error ? e.message : String(e));
      console.log('Continuing with bundler defaults...');
    }

    console.log('\n🔍 Pre-render Asset Verification:');
    let assetsMissing = false;

    if (!template.scenes || !Array.isArray(template.scenes)) {
        console.error('❌ FATAL: Template contains no scenes or "scenes" is not an array.');
        process.exit(1);
    }

    for (const scene of template.scenes) {
      console.log(`\n--- Scene: ${scene.scene_id} ---`);

      // Verify background video
      if (scene.background_type === 'video' && scene.video_path) {
        const bgPath = path.join(process.cwd(), 'public', scene.video_path);
        try {
          const realPath = fs.realpathSync(bgPath);
          const stats = fs.statSync(realPath);
          console.log(`✅ Background Video FOUND: ${scene.video_path} (${(stats.size / (1024 * 1024)).toFixed(2)} MB)`);
        } catch (e) {
          console.error(`❌ Background Video MISSING: ${bgPath}`);
          assetsMissing = true;
        }
      }

      // Verify overlays
      if (scene.overlays) {
        for (const overlay of scene.overlays) {
          // Verify Fonts
          if (overlay.type === 'text' && overlay.font) {
            const fontFound = [
                path.join(process.cwd(), 'public/fonts', `${overlay.font}.ttf`),
                path.join(process.cwd(), 'public/fonts', `${overlay.font}.otf`),
                path.join(process.cwd(), 'public/fonts', `${overlay.font}.woff`),
                path.join(process.cwd(), 'public/fonts', `${overlay.font}.woff2`),
            ].some(p => fs.existsSync(p));

            if (fontFound) {
              console.log(`✅ Font FOUND: ${overlay.font}`);
            } else {
              console.error(`❌ Font MISSING: ${overlay.font} (Expected in public/fonts/)`);
              assetsMissing = true;
            }
          }

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

    // Verify SFX
    if (template.audio_sfx_manifest && Array.isArray(template.audio_sfx_manifest)) {
        console.log('\n🎵 Verifying SFX Assets:');
        for (const sfx of template.audio_sfx_manifest) {
            const sfxPath = path.join(process.cwd(), 'public/renders/audios', sfx.file);
            if (!fs.existsSync(sfxPath)) {
                console.error(`❌ SFX Missing: ${sfx.file} (Expected in public/renders/audios/)`);
                assetsMissing = true;
            }
        }
    }

    if (assetsMissing) {
      console.warn('\n⚠️  WARNING: Some assets are missing. Rendering may fail or show placeholders.');
    } else {
      console.log('\n✨ All assets verified successfully!');
    }

    console.log('\n🔍 Extracting compositions...');
    const compositions = await getCompositions(bundleLocation, {
      inputProps: { templateData: template }
    });

    const resumeEnabled = !args.includes('--no-resume');
    const customChunkSize = args.find(arg => arg.startsWith('--chunk-size='))?.split('=')[1];
    const CHUNK_SIZE = customChunkSize ? parseInt(customChunkSize, 10) : 300;

    let outputDir = path.join(process.cwd(), 'renders/overlays/remotion');

    // Auto-detect Google Drive for persistence
    if (fs.existsSync('/content/drive/MyDrive')) {
      outputDir = GOOGLE_DRIVE_RENDER_DIR;
      console.log(`📡 Persistent Output Enabled: ${outputDir}`);
    }

    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const concurrency = concurrencyArg ? parseInt(concurrencyArg, 10) : 1;

    for (const scene of template.scenes) {
      const normalizedId = scene.scene_id.replace(/_/g, '-');

      if (sceneIdArg && scene.scene_id !== sceneIdArg && normalizedId !== sceneIdArg) {
          continue;
      }
      console.log(`\n🎬 Processing Scene: ${scene.scene_id}`);

      const composition = compositions.find((c) => c.id === normalizedId);
      if (!composition) {
        console.error(`❌ Composition ${normalizedId} not found (Scene ID: ${scene.scene_id})`);
        continue;
      }

      // Determine final output location
      let outputLocation: string;
      // FIX: Respect --output if we are specifically rendering ONE scene via --scene
      if (outputArg && (template.scenes.length === 1 || sceneIdArg)) {
        // If relative, join it with outputDir (which points to Drive if available)
        outputLocation = path.isAbsolute(outputArg) ? outputArg : path.join(outputDir, outputArg);

        // Ensure absolute for directory creation
        const absoluteOutput = path.resolve(process.cwd(), outputLocation);
        const parentDir = path.dirname(absoluteOutput);

        if (!fs.existsSync(parentDir)) {
             console.log(`📂 Creating parent directory for output: ${parentDir}`);
             fs.mkdirSync(parentDir, { recursive: true });
        }
      } else {
        outputLocation = path.join(
          outputDir,
          `updated_scene_${scene.scene_id}.mp4`
        );
      }

      // 🛑 SCENE RESUME CHECK
      if (resumeEnabled && fs.existsSync(outputLocation)) {
        console.log(`⏭️  Skipping Scene [${scene.scene_id}]: Final output already exists.`);
        continue;
      }

      console.log(`⏳ Rendering ${scene.scene_id} (Duration: ${composition.durationInFrames} frames)...`);

      // 🧩 CHUNKED RENDERING LOGIC
      const chunksDir = path.join(outputDir, '.chunks', scene.scene_id);
      if (!fs.existsSync(chunksDir)) fs.mkdirSync(chunksDir, { recursive: true });

      const totalFrames = composition.durationInFrames;
      const chunkPaths: string[] = [];
      const numChunks = Math.ceil(totalFrames / CHUNK_SIZE);

      for (let i = 0; i < numChunks; i++) {
        const startFrame = i * CHUNK_SIZE;
        const endFrame = Math.min((i + 1) * CHUNK_SIZE - 1, totalFrames - 1);
        const chunkPath = path.join(chunksDir, `chunk_${i}_${startFrame}_${endFrame}.mp4`);
        chunkPaths.push(chunkPath);

        if (resumeEnabled && fs.existsSync(chunkPath)) {
          console.log(`  ✅ Chunk ${i+1}/${numChunks} already exists, skipping.`);
          continue;
        }

        console.log(`  🎬 Rendering Chunk ${i+1}/${numChunks} (Frames: ${startFrame}-${endFrame})...`);

        await renderMedia({
          composition,
          serveUrl: bundleLocation,
          codec: 'h264',
          outputLocation: chunkPath,
          inputProps: { sceneData: scene, templateData: template },
          concurrency: concurrency,
          frameRange: [startFrame, endFrame],
          publicDir: path.join(process.cwd(), 'public'),
          onProgress: ({ progress }: { progress: number }) => {
            process.stdout.write(`    \rProgress: ${(progress * 100).toFixed(1)}%`);
          },
        } as any);
        console.log(''); // New line after progress
      }

      // 🧵 MERGING CHUNKS
      console.log(`🧵 Merging ${chunkPaths.length} chunks into final video...`);
      const listFilePath = path.join(chunksDir, 'chunks.txt');
      const listContent = chunkPaths.map(p => `file '${p}'`).join('\n');
      fs.writeFileSync(listFilePath, listContent);

      try {
        // Use remotion's bundled ffmpeg concat demuxer for lossless merging
        execSync(`npx remotion ffmpeg -y -f concat -safe 0 -i "${listFilePath}" -c copy "${outputLocation}" -hide_banner -loglevel error`);
        console.log(`✅ Scene Complete: ${outputLocation}`);

        // Clean up chunks if successful
        // execSync(`rm -rf "${chunksDir}"`);
      } catch (mergeError) {
        console.error(`❌ Merge failed for ${scene.scene_id}:`, mergeError);
      }
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
