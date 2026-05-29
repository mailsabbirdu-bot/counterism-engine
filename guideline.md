# 📖 Counterism Studio V4 Master Guideline

This document defines the comprehensive JSON schema for `remotion_template.json`, the brain of the automated cinematic pipeline.

---

## 🏗️ Root Configuration
| Key | Type | Description |
| :--- | :--- | :--- |
| `project_name` | `string` | Human-readable project identifier. |
| `global_settings` | `object` | Resolution and FPS configurations. |
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
| `procedural_config` | `object` | `{ speed: number, type: string }`. |
| `duration_in_frames` | `number` | Total frames for this scene. (Note: If background_type is "video", this will be automatically updated to match the video length). |
| `overlays` | `array` | Collection of all visual layers. |

---

## ✨ Overlay Types & Presets

### 1. `text` (Cinematic Typography)
| Field | Type | Options / Description |
| :--- | :--- | :--- |
| `content` | `string` | The text message. |
| `splitMode` | `string` | `"word"` \| `"char"` (How text animates). |
| `animation` | `string` | `"cinematicGlow"`, `"slideUp"`, `"wordByWord"`. |
| `stagger` | `number` | Seconds between item entrance (e.g., `0.05`). |
| `font` | `string` | Any Google Font name (e.g., `"Montserrat"`). |
| `fontSize` | `string` | CSS font size (e.g., `"120px"`). |
| `style` | `string` | Tailwind CSS classes for styling. |

### 2. `ui_panel` (Glassmorphism UI)
| Field | Type | Options / Description |
| :--- | :--- | :--- |
| `title` | `string` | Header text. |
| `description` | `string` | Body content. |
| `iconType` | `string` | `"terminal"`, `"security"`, `"activity"`, `"cpu"`, `"box"`. |
| `nodeId` | `string` | Custom ID displayed on the panel. |
| `variant` | `string` | `"glass"` (Frosted) \| `"dark"` (High contrast). |
| `initialProgress` | `number` | Start value for the progress bar (0-100). |
| `targetProgress` | `number` | End value for the progress bar (0-100). |
| `position` | `object` | `{ x: number, y: number }`. |

### 3. `shape` (GSAP Graphics)
| Field | Type | Options / Description |
| :--- | :--- | :--- |
| `shape_type` | `string` | `"circle"`, `"rect"`, `"triangle"`. |
| `animation` | `string` | `"pulse"`, `"float"`, `"morph"`. |
| `size` | `number` | Radius or half-width/height. |
| `color` | `string` | Hex code (e.g., `"#3b82f6"`). |
| `position` | `object` | `{ x: number, y: number }`. |
| `decorated` | `boolean` | Adds concentric decorative rings. |

### 4. `chart` (Nivo Data Viz)
| Field | Type | Options / Description |
| :--- | :--- | :--- |
| `chart_type` | `string` | `"line"` \| `"bar"`. |
| `title` | `string` | Chart header. |
| `data` | `array` | Nivo-compatible data structure. |
| `colors` | `object` | `{ "scheme": "nivo" \| "spectral" \| "category10" }`. |
| `width`, `height` | `number` | Dimensions of the chart. |

### 5. `graph` (D3 Procedural)
| Field | Type | Options / Description |
| :--- | :--- | :--- |
| `nodes` | `number` | Complexity of the node-link system. |
| `links` | `number` | Number of connections. |
| `speed` | `number` | Rotation/motion speed multiplier. |
| `nodeColor` | `string` | Hex color for nodes. |
| `linkColor` | `string` | RGBA color for links. |

### 6. `video` & `image` (Media Overlays)
| Field | Type | Options / Description |
| :--- | :--- | :--- |
| `src` | `string` | Path relative to `public/`. |
| `audio_enabled` | `boolean` | Enable/disable audio for video overlay. |
| `position` | `object` | `{ x: number, y: number }`. |
| `width`, `height` | `number` | Dimensions. |
| `borderRadius` | `number` | Corner rounding. |
| `shadow` | `boolean` | Enable drop shadow. |
| `border` | `object` | `{ width: number, color: string }`. |

---

## 🎥 Camera System (Cinematic)
| Key | Type | Description |
| :--- | :--- | :--- |
| `camera` | `object` | Optional scene-level camera configuration. |

### `camera` object
- `enabled`: `boolean`
- `perspective`: `number` (Default: 1000. Higher = flatter perspective).
- `keyframes`: `array` of camera states.
  - `frame`: `number`
  - `x`, `y`, `z`: `number` (Translation).
  - `zoom`: `number` (Default: 1).
  - `rotationX`, `rotationY`, `rotationZ`: `number` (Degrees).
  - `easing`: `string` (`"linear"`, `"ease"`, `"bezier"`).

---

## 🎨 Shared Fields (All Overlays)
- `id`: `string` (Unique layer identifier)
- `start`: `number` (Frame to appear)
- `duration`: `number` (Frames to stay visible)
- `depth`: `number` (Optional. Z-axis position for parallax. Positive is closer to camera).
- `zIndex`: `number` (Layer stacking order; higher values appear on top. Default values: Shape=10, Graph=25, Chart=30, UI=40, Text=50, Media=100)
