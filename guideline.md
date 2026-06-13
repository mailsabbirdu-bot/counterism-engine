# 📖 Counterism Studio V4 Ultimate Master Guideline

This document serves as the definitive technical specification for the Counterism Studio V4 Remotion engine. It defines the JSON schema for `remotion_template.json`, the architectural principles of the cinematic pipeline, and best practices for creating professional-grade automated documentaries.

---

## 🏗️ Architectural Core Principles

### 1. 🎯 Mathematical Pivot-Centering
Every visual element in Studio V4 is **Center-Anchored**.
- **Standard Layout:** `top: 0, left: 0` + `transform: translate(-50%, -50%)`.
- **Why:** This ensures that when the Camera Engine's `lookAt` system targets an element (using its `{x, y}` position), the focal point is mathematically perfect. It eliminates "zoom-drift" common in standard CSS transforms.

### 2. 🎥 V4 Camera Engine (Cinematic V4)
The camera is a 3D pivot-based system that operates in a virtual 1920x1080 space.
- **Hardware Acceleration:** Uses `translate3d`, `scale3d`, and `rotateZ` to bypass CPU layout recalculations.
- **Velocity-Aware Motion Blur:** Calculates blur intensity based on sub-frame velocity deltas (`(pos_t0.5 - pos_t0) * zoom`).
- **Organic Shake:** Seeded simplex-noise handheld simulation for realism.
- **Perspective:** Standardized at `2000px` for optimal 3D parallax without extreme distortion.

### 3. ⚡ CPU Optimization (Google Colab Ready)
- **Native Primitives:** Uses Remotion's `interpolate` and `spring` for 60fps performance on high-latency CPU environments.
- **No Framer Motion:** Heavy animation libraries have been removed to minimize main-thread blocking.
- **Rounded Blurs:** CSS blur filters are rounded to the nearest pixel to reduce rendering cost.

---

## 📁 Root Configuration Schema

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `project_name` | `string` | - | Identifier for the render job. |
| `global_settings` | `object` | - | Canvas and engine-wide constants. |
| `scenes` | `array` | - | Collection of scene objects. |

### `global_settings` Details
- `width`: `number` (1920)
- `height`: `number` (1080)
- `fps`: `number` (30)

---

## 🎬 Scene Configuration

| Key | Type | Description |
| :--- | :--- | :--- |
| `scene_id` | `string` | Unique ID. Becomes the output filename. |
| `background_type` | `string` | `"video"`, `"procedural"`, or `"none"`. |
| `video_path` | `string` | Path in `public/`. (Engine automatically syncs scene duration to video). |
| `audio_enabled` | `boolean` | If true, background video audio is mixed into the final render. |
| `procedural_config` | `object` | Config for the dynamic background engine. |
| `duration_in_frames` | `number` | Total scene length (if not video-driven). |
| `camera` | `object` | Focal and movement configuration. |
| `overlays` | `array` | List of visual components. |

### `procedural_config` Variants
- `"neon_grid"`, `"dark_particles"`, `"gradient_wave"`, `"cosmic_dust"`, `"liquid_gradient"`.
- Supports: `primaryColor`, `secondaryColor`, `speed`, `intensity`.

---

## 🎥 Camera Keyframes & Shots

### `camera` Root Properties
- `enabled`: `boolean`.
- `motionBlur`: `{ enabled: boolean, intensity: number (0-2) }`.
- `shake`: `{ enabled: boolean, intensity: number, speed: number }`.
- `preset`: `CameraPreset` (Optional).

### 🎬 Camera Presets
| Name | Effect |
| :--- | :--- |
| `slow_push` | 1.0x -> 1.2x zoom. Building tension. |
| `slow_pull` | 1.2x -> 1.0x zoom. Revealing context. |
| `ken_burns` | Diagonal pan + zoom. Atmospheric depth. |
| `dramatic_reveal` | RotateX (25deg) -> Pull back & Center. High impact. |
| `handheld_static` | Subtle organic drift. Realism. |
| `whip_pan` | Ultra-fast move with motion blur streak. |

### 🎯 `camera.shots` (High-Level Automation)
The `shots` array allows you to choreograph the camera by targeting overlay IDs.
```json
{
  "targetId": "OVERLAY_ID",
  "startFrame": 0,
  "duration": 90,
  "zoom": 1.5,
  "style": "dramatic_reveal",
  "inDuration": 30
}
```
- **Styles:** `push_in`, `pull_out`, `pan_left`, `pan_right`, `tilt_up`, `tilt_down`, `orbit`, `whip_pan`, `dramatic_reveal`, `static`.

---

## ✨ Overlay Types (Standard V4 Engine)

### 1. `text` (Cinematic Typography)
- `content`: `string`. (Supports `\n`).
- `font`: `string`. Google Font name (auto-loaded).
- `fontSize`: `string`. e.g., `"120px"`.
- `animation`: `"cinematicGlow"`, `"slideUp"`, `"wordByWord"`.
- `style`: `string`. Tailwind classes.
- `position`: `{ x: number, y: number }`.

### 2. `ui_panel` (Documentary UI)
- `title`, `description`: Text content.
- `iconType`: `"activity"`, `"terminal"`, `"cpu"`, `"security"`, `"box"`.
- `variant`: `"glass"` (Blur) or `"dark"` (Opaque).
- `initialProgress`, `targetProgress`: `0-100`. Animates internal bar.

### 3. `chart` (Nivo Data Viz)
- `chart_type`:
  - `"verticalBar"`, `"horizontalBar"`, `"groupedBar"`, `"stackedBar"`, `"barRace"`.
  - `"line"`, `"area"`, `"stackedArea"`, `"forecast"`.
  - `"pie"`, `"donut"`, `"treemap"`, `"sunburst"`.
  - `"histogram"`, `"boxPlot"`, `"violinPlot"`.
  - `"scatter"`, `"bubble"`, `"sankey"`, `"chord"`, `"network"`.
- `data`: Standard Nivo format.
- `keys`, `indexBy`: Mapping keys.
- `title`, `subtitle`: Canvas headers.

### 4. `data_indicator` (Modern Metrics)
- `indicator_type`:
  - `"kpiNumber"`, `"percentageCounter"`, `"comparisonKPI"`, `"deltaIndicator"`, `"countdown"`.
  - `"progressBar"`, `"circularProgress"`, `"semiGauge"`, `"milestoneTracker"`.
  - `"dashboardCard"`, `"timeline"`, `"milestoneTimeline"`.
- `value`, `label`, `prefix`, `suffix`.
- `milestones`, `events`: Arrays for trackers.

### 5. `graph` (Abstract Tech)
- `nodes`, `links`: Density counts.
- `nodeColor`, `linkColor`: Hex/RGBA.
- `speed`: Rotation velocity.

### 6. `shape` (Motion Graphics)
- `shape_type`: `"circle"`, `"rect"`, `"line"`.
- `animation`: `"pulse"`, `"float"`, `"morph"`.
- `decorated`: `boolean`. Adds technical orbital rings.

### 7. `video` & `image` (Media)
- `src`: Path or URL.
- `borderRadius`, `shadow`, `border`.
- `position`, `width`, `height`.

---

## 🎨 Common Properties (All Overlays)
- `id`: `string` (**CRITICAL**: Must be unique for camera targeting).
- `start`, `duration`: Visibility timing.
- `zIndex`: Stacking order.
- `depth`: `number` (Z-axis offset for parallax).
- `cameraFocus`:
  - `zoom`: Preferred magnification for this element.
  - `offsetX`, `offsetY`: Framing offsets.
  - `moveStyle`: `"smooth"`, `"whip"`, `"dramatic"`.
