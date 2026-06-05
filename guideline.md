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

### 🎬 Camera Presets
V4 includes a collection of professional camera move presets that can be applied to any scene using the `camera.preset` field. These presets are designed to provide high-quality movement without manual keyframing.

| Preset | Description | Best Use Case |
| :--- | :--- | :--- |
| `slow_push` | A gentle zoom-in (1.0x to 1.2x) over the scene duration. | Use for **emphasis** and building tension. Ideal for headlines or single data points. |
| `slow_pull` | A gentle zoom-out (1.2x to 1.0x). | Use for **revealing context** or transitioning away from a specific detail. |
| `ken_burns` | A classic pan-and-zoom move from one corner to the opposite. | Use for **atmospheric backgrounds** or high-resolution images to create life and movement. |
| `dramatic_reveal` | Starts with a tight, tilted zoom and pulls back to a centered wide shot. | Use for **introductions** or high-impact scene openings. |
| `handheld_static` | A subtle, organic drift with micro-rotations. | Use for **realism** and "humanizing" the shot. Perfect for long-duration data displays. |
| `whip_pan_right` | A high-velocity horizontal blur entering from the left. | Use for **high-energy transitions** between scenes. |
| `whip_pan_left` | A high-velocity horizontal blur entering from the right. | Use for **high-energy transitions** between scenes. |

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
- `style`: `string`. Cinematic move style.
  - `"push_in"`, `"pull_out"`, `"pan_left"`, `"pan_right"`, `"tilt_up"`, `"tilt_down"`, `"orbit"`, `"whip_pan"`, `"dramatic_reveal"`, `"static"`.
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
- `title`, `description`, `iconType` (`terminal`, `cpu`, `activity`, `security`, `box`), `nodeId`.
- `variant`: `"glass"` \| `"dark"`.
- `initialProgress`, `targetProgress`: `0-100`. (Animates a progress bar inside the panel).
- `position`: `{ x: number, y: number }`.

### 3. `chart` (Nivo Data Viz)
Comprehensive data visualization system for documentaries and infographics.
- `chart_type`:
  - **Comparison:** `"horizontalBar"` (rankings), `"verticalBar"` (categories), `"groupedBar"` (multi-series), `"stackedBar"` (composition), `"barRace"` (dynamic rankings).
  - **Time Series:** `"line"` (trends), `"multiLine"` (multi-trends), `"area"` (magnitude), `"stackedArea"` (changing composition), `"forecast"` (predictions).
  - **Composition:** `"pie"` (few categories), `"donut"` (composition + center), `"treemap"` (large hierarchies), `"sunburst"` (nested hierarchies).
  - **Distribution:** `"histogram"` (density), `"boxPlot"` (outliers), `"violinPlot"` (density spread).
  - **Relational/Flow:** `"scatter"` (correlation), `"bubble"` (3D data), `"sankey"` (flow), `"chord"` (connections).
  - **Advanced:** `"network"` (relationships), `"choropleth"` (geographic density), `"bubbleMap"` (point-based geography).
- `title`, `subtitle`: Header strings.
- `data`: Standard Nivo data array/object.
- `keys`: `string[]` (Required for bar/chord/barRace).
- `indexBy`: `string` (Required for bar/barRace).
- `width`, `height`: Canvas size.
- `position`: `{ x: number, y: number }`.

### 4. `data_indicator` (Modern Metrics)
Fluid, Framer-motion driven indicators for single metrics.
- `indicator_type`:
  - **Numeric:** `"kpiNumber"` (single big stat), `"percentageCounter"` (0-100 progress), `"comparisonKPI"` (two values side-by-side), `"deltaIndicator"` (+/- % change), `"countdown"` (approaching event).
  - **Progress:** `"progressBar"` (horizontal growth), `"circularProgress"` (conic-fill circle), `"semiGauge"` (speedometer-style), `"milestoneTracker"` (step-by-step phases).
  - **Cards & Timelines:** `"dashboardCard"` (summary tile), `"timeline"` (chronological event list), `"milestoneTimeline"` (major historical stages).
- `value`, `label`, `prefix`, `suffix`: Data fields.
- `milestones`, `events`: Arrays for trackers and timelines.
- `position`: `{ x: number, y: number }`.

### 5. `graph` (Force-Directed Graph)
- `nodes`: `number` (Default: 30).
- `links`: `number` (Default: 40).
- `nodeColor`: `string` (Hex or rgba).
- `linkColor`: `string` (Hex or rgba).
- `speed`: `number` (Default: 0.05). Rotation speed.
- `position`: `{ x: number, y: number }`.

### 6. `shape` (Geometric Motion)
- `shape_type`: `"circle"` \| `"rect"` \| `"line"`.
- `animation`: `"pulse"` \| `"float"` \| `"morph"`.
- `decorated`: `boolean`. Adds orbit rings and decorative elements.
- `color`: `string`.
- `size`: `number`.
- `position`: `{ x: number, y: number }`.

### 7. `map` (Advanced Vector Geospatial Engine)
High-fidelity SVG mapping system using D3, real-world GeoJSON/TopoJSON data, and OpenStreetMap tiles.
- `center`: `[longitude, latitude]` (Default: `[0, 20]`).
- `scale`: `number` (Default: `200`). Controls zoom level (World: 200, Continent: 800, Country: 4000+, Street: 1000000+).
- `focus`: `string` (Optional). Name of the area to focus on. If provided, the engine attempts to load high-detail GeoJSON from the local cache and auto-fits the view.
- `useOsmTiles`: `boolean` (Optional). Enables OpenStreetMap street-level tile rendering behind the vector layers.
- `mapTheme`: `"dark"` | `"light"` | `"cinematic"`. Applies color filters to OSM tiles to match the project aesthetic.
- `showNeighbors`: `boolean` (Optional). If true, loads and displays neighboring areas defined in the map metadata.
- `topojson_url`: `string` (Optional). URL to a custom TopoJSON file.
- `object_name`: `string` (Optional). The key of the geometry object inside the TopoJSON (e.g., `"districts"`, `"countries"`).
- `cities`: `array` of `{ name: string, coords: [lon, lat] }`.
- `routes`: `array` of:
  - `from`, `to`: City names defined in `cities`.
  - `label`: `string`. Displayed with real-time distance telemetry.
  - `type`: `"air"` | `"sea"` | `"land"`. Affects line style and animation speed.
- `highlights`: `string[]`. List of area names to highlight.
- `width`, `height`: Canvas dimensions.
- `position`: `{ x: number, y: number }`.

### 8. `video` & `image` (Media Overlays)
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
  - `fitMode`: `"contain"` \| `"cover"`. How the element should fit the framing.
  - `focusBounds`: `boolean`. If true, framing is calculated from element dimensions.
  - `preferredDuration`: `number`. Suggested hold time for AI generators.
  - `moveStyle`: `"smooth"` \| `"whip"` \| `"dramatic"`. Preferred transition feel.

> **Note:** The `cameraFocus` property allows you to move framing knowledge into the overlay itself. When a `shot` or `lookAt` targets an ID, the engine automatically reads these values to provide perfect, context-aware framing.
