# 📖 Counterism Studio V4 Master Guideline (2026 Edition)

This is the definitive guide for configuring the `remotion_template.json`.

---

## 🏗️ Root Object
- `project_name`: `string`
- `global_settings`: `{ width: number, height: number, fps: number }`
- `scenes`: `array`

---

## 🎬 Scene Configuration
- `scene_id`: `string` (Unique ID for filename output)
- `background_type`: `"video"` | `"procedural"` | `"none"`
- `video_path`: `string` (Required if `background_type` is `"video"`. Relative to `public/`)
- `procedural_config`: `object` (Optional for `"procedural"`)
  - `particles`: `number` (Default: 50)
  - `primaryColor`: `string` (Hex)
  - `secondaryColor`: `string` (Hex)
- `duration_in_frames`: `number` (Total scene length)
- `overlays`: `array` (List of visual layers)

---

## ✨ Overlay Engines

### 1. 🔤 Text Engine
- `type`: `"text"`
- `content`: `string`
- `splitMode`: `"word"` | `"char"`
- `animation`: `"cinematicGlow"` | `"slideUp"` | `"wordByWord"`
- `stagger`: `number` (Delay in seconds between items, e.g., 0.05)
- `font`: `string` (Google Font name, e.g., "Montserrat")
- `style`: `string` (Tailwind classes. PRO TIP: Use `text-9xl` for impact)

### 2. 🖥️ UI System
- `type`: `"ui_panel"`
- `title`: `string`
- `description`: `string`
- `iconType`: `"terminal"` | `"security"` | `"activity"` | `"cpu"` | `"box"`
- `nodeId`: `string` (Custom identifier)
- `variant`: `"glass"` (Frosted) | `"dark"` (High contrast)
- `initialProgress`: `number` (0-100)
- `targetProgress`: `number` (0-100)
- `position`: `{ x: number, y: number }`

### 3. 🔷 Shapes Engine (GSAP)
- `type`: `"shape"`
- `shape_type`: `"circle"` | `"rect"` | `"line"`
- `animation`: `"pulse"` | `"float"` | `"morph"`
- `size`: `number`
- `color`: `string` (Hex)
- `decorated`: `boolean` (Adds concentric rings)
- `position`: `{ x: number, y: number }`

### 4. 📊 Charts Engine (Nivo)
- `type`: `"chart"`
- `chart_type`: `"line"` | `"bar"`
- `title`: `string`
- `subtitle`: `string`
- `data`: `array` (Nivo-compliant schema)
- `colors`: `{ scheme: "nivo" | "spectral" | "category10" }`
- `width`: `number`
- `height`: `number`
- `position`: `{ x: number, y: number }`

### 5. 🕸️ Graphs Engine (D3)
- `type`: `"graph"`
- `nodes`: `number` (Density of nodes)
- `links`: `number` (Density of links)
- `speed`: `number` (Rotation speed)
- `nodeColor`: `string` (Hex)
- `linkColor`: `string` (RGBA string)

---

## 🎯 Pro Tips for Evaluation
- **Font Size:** Use at least `text-7xl` or `text-9xl` for main titles to evaluate glow effects.
- **Duration:** Set `duration_in_frames` to at least `240` (8 seconds at 30fps) to see animations clearly.
- **Stagger:** A stagger of `0.1` for words and `0.03` for characters is optimal.
