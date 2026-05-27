import pkg from '@remotion/bundler';
const { bundle } = pkg;
import { renderMedia, getCompositions } from '@remotion/renderer';
import path from 'path';
import fs from 'fs';
import { enableTailwind } from '@remotion/tailwind';

// Parse command line arguments
const args = process.argv.slice(2);
const templateArg = args.find(arg => arg.startsWith('--template='))?.split('=')[1];
const outputArg = args.find(arg => arg.startsWith('--output='))?.split('=')[1];

const templatePath = path.join(process.cwd(), templateArg || 'remotion_template.json');
if (!fs.existsSync(templatePath)) {
  console.error(`❌ Template file not found: ${templatePath}`);
  process.exit(1);
}

const template = JSON.parse(fs.readFileSync(templatePath, 'utf8'));

const start = async () => {
  try {
    console.log(`🚀 Starting Counterism Studio V4 Rendering Pipeline (Template: ${path.basename(templatePath)})...`);

    const entry = path.join(process.cwd(), 'src/index.ts');
    console.log('📦 Bundling project...');
    const bundleLocation = await bundle({
      entryPoint: entry,
      webpackOverride: (config) => enableTailwind(config),
    });

    console.log('🔍 Extracting compositions...');
    const compositions = await getCompositions(bundleLocation, {
      inputProps: { templateData: template }
    });

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

      console.log(`⏳ Rendering ${scene.scene_id}...`);

      const renderOptions: any = {
        composition,
        serveUrl: bundleLocation,
        codec: 'h264',
        outputLocation,
        inputProps: { sceneData: scene, templateData: template },
        concurrency: 2,
        publicDir: path.join(process.cwd(), 'public'),
        onProgress: ({ progress }: { progress: number }) => {
          process.stdout.write(`\rProgress: ${(progress * 100).toFixed(1)}%`);
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
