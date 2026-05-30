# 📖 Counterism Studio V4 Master Guideline

This document defines the comprehensive JSON schema for `remotion_template.json`, the architectural brain of the automated cinematic pipeline.

---

## 🏗️ Root Configuration
| Key | Type | Description |
| :--- | :--- | :--- |
| `project_name` | `string` | Human-readable project identifier. |
| `global_settings` | `object` | Global canvas and timing configurations. |
| `scenes` | `array` | List of scene objects to process. |

### `global_settings`
- `width`: `number` (Default: 1920)
- `height`: `number` (Default: 1080)
- `fps`: `number` (Default: 30)

---

## 🎬 Scene Schema
| Key | Type | Description |
| :--- | :--- | :--- |
| `scene_id` | `string` | Unique ID (used for output filename). |
| `background_type` | `string` | `"video"` \| `"procedural"` \| `"none"`. |
| `video_path` | `string` | (Required for video) Path relative to `public/`. |
| `audio_enabled` | `boolean` | Enable/disable audio for background video. |
| `procedural_config` | `object` | `{ speed: number, variant: string, primaryColor: string, secondaryColor: string }`. |
| `duration_in_frames` | `number` | Total frames for this scene. (VITAL: If `background_type` is "video", the engine automatically overrides this with the video's actual duration). |
| `camera` | `object` | (Optional) Cinematic camera configuration for the scene. |
| `overlays` | `array` | Collection of all visual layers (Text, UI, Charts, etc.). |

---

## 🎥 Professional Cinematic Camera
The V4 Camera Engine uses a **Hybrid 3D Transform Stack**. It treats the background and overlays as layers in 3D space, allowing for frame-perfect centering and targeting.

### 1. `camera` root configuration
- `enabled`: `boolean`
- `perspective`: `number` (Default: 1000. Depth of field simulation).
- `smoothing`: `number` (0 to 1). Strength of the internal path smoother.
- `presets`: `string` (Optional). Use a pre-defined move:
  - `"slow_push"`, `"slow_pull"`, `"ken_burns"`, `"dramatic_reveal"`, `"whip_pan_left"`, `"whip_pan_right"`.
- `motionBlur`: `object`
  - `enabled`: `boolean`
  - `intensity`: `number` (0.1 to 2.0). Velocity-aware sampling.
- `shake`: `object`
  - `enabled`: `boolean`
  - `intensity`: `number` (1-10). Multi-frequency handheld motion.

### 2. `camera.keyframes` (Manual Precision)
Each keyframe interpolates to the next using the specified `easing`.
- `frame`: `number` (Absolute frame index).
- `lookAt`: `string` \| `object`.
  - If a **string**: Matches an overlay's `id`. The camera will automatically center that element.
  - If an **object**: `{ x: number, y: number }`.
- `zoom`: `number` (Default: 1.0. 2.0 = 200% magnification).
- `rotationX`, `rotationY`, `rotationZ`: `number` (Degrees).
- `easing`: `"linear"`, `"ease"`, `"bezier"`, `"step"`, `"quintic"`.

### 3. `camera.shots` (High-Level Choreography)
The `shots` system allows for automated cinematic "cuts" or smooth pans between targets.
- `targetId`: `string`. The ID of the overlay to focus on.
- `startFrame`: `number`. When to begin moving to this target.
- `duration`: `number`. How long to hold on this target.
- `zoom`: `number`. Zoom level for this specific shot.
- `inDuration`: `number`. Frames spent transitioning into this shot.
- `outDuration`: `number`. Frames spent transitioning out.

---

## ✨ Overlay Types & Standardization
**VITAL:** All overlays in V4 are **Center-Anchored**. When you set `position: {x, y}`, the mathematical center of the element is placed exactly at those coordinates. This ensures the camera's `lookAt` system is frame-perfect.

### 1. `text` (Cinematic Typography)
- `content`: `string`. Supports multi-line.
- `animation`: `"cinematicGlow"`, `"slideUp"`, `"wordByWord"`.
- `splitMode`: `"word"` \| `"char"`.
- `font`: `string`. Google Font name.
- `fontSize`: `string`. e.g., `"120px"`.
- `style`: `string`. Tailwind classes (e.g., `"text-blue-500 font-black uppercase tracking-tighter"`).
- `position`: `{ x: number, y: number }`.

### 2. `ui_panel` (Glassmorphism UI)
- `title`, `description`, `iconType` (terminal, cpu, activity, security, box), `nodeId`.
- `variant`: `"glass"` \| `"dark"`.
- `initialProgress`, `targetProgress`: `0-100`.
- `position`: `{ x: number, y: number }`.

### 3. `chart` (Nivo Data Viz)
- `chart_type`: `"line"` \| `"bar"`.
- `title`, `subtitle`: Header strings.
- `data`: Standard Nivo data array.
- `width`, `height`: Canvas size.
- `position`: `{ x: number, y: number }`.

### 4. `video` & `image` (Media Overlays)
- `src`: Path in `public/`.
- `width`, `height`: Size in pixels.
- `borderRadius`: `number`.
- `shadow`: `boolean`.
- `border`: `{ width: number, color: string }`.
- `position`: `{ x: number, y: number }`.

---

## 🎨 Shared Layer Properties
- `id`: `string` (**CRITICAL**: Must be unique for `lookAt` targeting).
- `start`: `number` (Entry frame).
- `duration`: `number` (Visibility duration).
- `depth`: `number` (Optional. Z-axis displacement for parallax effects. Positive moves closer to camera).
- `zIndex`: `number` (Stacking order).
  - Recommended: Background (0), Shapes (10), Graphs (25), Charts (30), UI (40), Text (50), Media (100).
