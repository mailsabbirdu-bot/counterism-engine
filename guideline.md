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

## 🎥 Professional Cinematic Camera (V4)
The V4 Camera Engine utilizes a **Mathematical Pivot-Centering Architecture**. Unlike standard transforms that cause "drift" during zoom-pans, V4 dynamically calculates the `transform-origin` based on the focal target and applies a compensating translation to the viewport center.

### 1. 🚀 Performance Optimization (CPU/Colab)
- **Hardware Acceleration:** Uses `translate3d` and `scale3d` to bypass main-thread layout recalculations.
- **Hinting:** Applies `will-change: transform` and `backface-visibility: hidden` to the overlay container to prevent jitter/flicker on low-power environments.
- **Native Remotion Primitives:** Animations are driven by `interpolate` and `spring` for deterministic, frame-accurate rendering.

### 2. `camera` Configuration
- `enabled`: `boolean`
- `perspective`: `number` (Default: 1000). Controls 3D depth perception.
- `motionBlur`: `object`
  - `enabled`: `boolean`
  - `intensity`: `number` (Default: 0.8). Uses sub-frame velocity deltas to calculate realistic blur.
- `shake`: `object`
  - `enabled`: `boolean`
  - `intensity`: `number` (Default: 1.0). Seeded Simplex-noise handheld motion.
  - `speed`: `number` (Default: 1.0). Frequency of the shake.

### 3. 🎯 Focal Precision (`keyframes` & `shots`)
- `lookAt`: `string` | `object`.
  - **ID Targeting:** Provide the `id` of any overlay (e.g., `"TEXT-01"`). The camera will lock onto its mathematical center.
  - **Coordinate Targeting:** `{ "x": 960, "y": 540 }`.
- `zoom`: `number` (1.0 = Default, 4.0 = Extreme detail).
- `easing`: `"linear"`, `"ease"`, `"bezier"`, `"step"`, `"quintic"`.

### 4. `camera.shots` (Cinematic Choreography)
The `shots` system handles smooth transitions between focal points automatically:
- `targetId`: `string`. Overlay ID to focus on.
- `startFrame`: `number`. When the shot starts.
- `duration`: `number`. How long to stay on target.
- `zoom`: `number`. Magnification for this specific shot.
- `inDuration`: `number`. Transition time into the shot.

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
- `cameraFocus`: `object` (** Framing Intelligence **).
  - `zoom`: `number`. Preferred zoom level when this element is targeted.
  - `offsetX`, `offsetY`: `number`. Pixel offsets from the element's center.
  - `preferredDuration`: `number`. Suggested hold time for AI generators.
  - `moveStyle`: `"smooth"` \| `"whip"` \| `"dramatic"`. Preferred transition feel.

> **Note:** The `cameraFocus` property allows you to move framing knowledge into the overlay itself. When a `shot` or `lookAt` targets an ID, the engine automatically reads these values to provide perfect, context-aware framing.
