import pkg from '@remotion/bundler';
const { bundle } = pkg;
import { renderMedia, getCompositions } from '@remotion/renderer';
import path from 'path';
import fs from 'fs';
import { enableTailwind } from '@remotion/tailwind';

const templatePath = path.join(process.cwd(), 'remotion_template.json');
const template = JSON.parse(fs.readFileSync(templatePath, 'utf8'));

const start = async () => {
  console.log('🚀 Starting Counterism Studio V4 Rendering Pipeline...');

  const entry = path.join(process.cwd(), 'src/index.ts');
  console.log('📦 Bundling project...');
  const bundleLocation = await bundle({
    entryPoint: entry,
    webpackOverride: (config) => enableTailwind(config),
  });

  const compositions = await getCompositions(bundleLocation);

  const outputDir = path.join(process.cwd(), 'renders/overlays/remotion');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  for (const scene of template.scenes) {
    console.log(`\n🎬 Processing Scene: ${scene.scene_id}`);

    const composition = compositions.find((c) => c.id === scene.scene_id);
    if (!composition) {
      console.error(`❌ Composition ${scene.scene_id} not found`);
      continue;
    }

    const outputLocation = path.join(
      outputDir,
      `updated_scene_${scene.scene_id}.mp4`
    );

    console.log(`⏳ Rendering ${scene.scene_id}...`);

    await renderMedia({
      composition,
      serveUrl: bundleLocation,
      codec: 'h264',
      outputLocation,
      inputProps: { sceneData: scene },
      concurrency: 2, // Maximize CPU usage on Colab (usually 2-4 cores)
      onProgress: ({ progress }: { progress: number }) => {
        process.stdout.write(`\rProgress: ${(progress * 100).toFixed(1)}%`);
      },
    });

    console.log(`\n✅ Finished: ${outputLocation}`);
  }

  console.log('\n🏁 All scenes rendered successfully!');
};

start().catch((err) => {
  console.error('❌ Render failed:', err);
  process.exit(1);
});
