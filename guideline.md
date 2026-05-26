# 📖 Counterism Studio V4 JSON Guideline

This document defines the schema and expected values for `remotion_template.json`.

---

## 🏗️ Root Object
| Key | Type | Description |
| :--- | :--- | :--- |
| `project_name` | `string` | Name of the automation project |
| `global_settings` | `object` | Project-wide render configurations |
| `scenes` | `array` | List of scene objects to be processed |

---

## ⚙️ global_settings
| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `width` | `number` | `1920` | Video width in pixels |
| `height` | `number` | `1080` | Video height in pixels |
| `fps` | `number` | `30` | Frames per second |

---

## 🎬 scene
| Key | Type | Description |
| :--- | :--- | :--- |
| `scene_id` | `string` | Unique identifier (e.g., `SC_01`) |
| `video_path` | `string` | Path to background video relative to root |
| `duration_in_frames` | `number` | Total duration of the scene |
| `overlays` | `array` | List of overlay elements |

---

## ✨ Overlays (Types & Properties)

### 1. `text`
Used for cinematic typography.
- `type`: `"text"`
- `content`: `string` (The text to display)
- `start`: `number` (Start frame)
- `duration`: `number` (Duration in frames)
- `font`: `string` (Google Font name, e.g., `"Inter"`)
- `animation`: `"wordByWord" | "slideUp" | "fadeIn"`
- `style`: `object` (Tailwind-like classes or CSS)

### 2. `ui_panel`
Glassmorphism UI overlays.
- `type`: `"ui_panel"`
- `title`: `string`
- `description`: `string`
- `position`: `{ x: number, y: number }`
- `variant`: `"glass" | "dark" | "outline"`

### 3. `shape`
GSAP-driven SVG graphics.
- `type`: `"shape"`
- `shape_type`: `"circle" | "rect" | "line"`
- `animation`: `"morph" | "draw" | "pulse"`
- `color`: `string` (Hex code)

### 4. `chart`
Nivo-driven data visualizations.
- `type`: `"chart"`
- `chart_type`: `"bar" | "line" | "pie"`
- `data`: `array` (Nivo-compatible data format)

### 5. `graph`
D3.js procedural node systems.
- `type`: `"graph"`
- `nodes`: `number` (Number of nodes)
- `links`: `number` (Number of links)
- `speed`: `number` (Animation speed multiplier)
