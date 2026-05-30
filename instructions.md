# 🚀 Counterism Studio V4 - Advanced Instructions

## 🛠️ Installation & Setup
1. **Node Environment**: Use Node 18+.
2. **Install Dependencies**:
   ```bash
   npm install
   ```
3. **FFmpeg**: Required for duration probing and video rendering.
   ```bash
   sudo apt-get install ffmpeg # Linux
   brew install ffmpeg         # macOS
   ```

## 🎬 Rendering Operations
The V4 engine features an intelligent rendering pipeline in `render.ts`.

### Basic Render
Renders the default `remotion_template.json`:
```bash
npm run render
```

### Advanced CLI Arguments
- `--template=path/to/config.json`: Use a specific JSON template.
- `--output=filename.mp4`: Overrides the output name (only for single-scene templates).
- `--concurrency=1`: (Recommended for Colab) Limits browser instances to prevent CPU/Memory exhaustion.

### Output Location
All final renders are saved to: `renders/overlays/remotion/`

## 🎥 Camera Engine Architecture
The cinematic camera in V4 is a hybrid 3D system.

### Center-Anchoring Logic
Unlike standard CSS where elements are top-left anchored, V4 elements are **Center-Anchored**.
- To place an element at `(400, 250)`, the engine internally applies `left: 400px; top: 250px; transform: translate(-50%, -50%)`.
- This ensures that when the camera targets an element via `lookAt`, the center of the element aligns perfectly with the center of the screen.

### Cinematic Features
- **Shot Synthesizer**: Uses high-level `shots` to automate camera moves.
- **Motion Blur**: Implemented via a velocity-sampling CSS filter. It calculates movement between frame `t` and `t + 0.5`.
- **Handheld Shake**: Procedural noise generated from multi-frequency sine waves.
- **Background Sync**: The background video/procedural layer is automatically scaled (`coverScale`) and synced to camera pans using a 2D-safe transform to avoid black bars.

## 🧪 Preview & Verification
### Studio Preview
Launch the real-time interactive preview:
```bash
npm start
```
Access specific scenes via: `http://localhost:3000/compositions/{scene_id}`

### Headless Verification (CLI)
To capture a specific frame for verification without rendering the whole video:
```bash
npx remotion still {scene_id} out.png --input-props='{"sceneData":...}'
```

## ⚠️ Troubleshooting
- **Black Frames**: Usually caused by missing assets in the `public/` directory or incorrect `start` frames.
- **Jittery Camera**: Ensure `smoothing` is enabled in the camera config.
- **Out of Memory**: In Colab, always use `--concurrency=1`.
- **Asset 404**: The engine uses `resolveAsset()`. Ensure paths in JSON do **not** include a leading `/public/` prefix. Use `video.mp4` instead of `/public/video.mp4`.
