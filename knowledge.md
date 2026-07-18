# Cinematic Relationship Visualization Engine (CRVE) & Knowledge System

This document provides a comprehensive, field-by-field reference guide, architectural overview, and manual for understanding and generating valid JSON manifests for the **Cinematic Relationship Visualization Engine (CRVE)**. It covers everything from semantic NLP extraction to dynamic font loading and state-of-the-art D3/react-xarrows layout rendering.

---

## 1. End-to-End System Architecture

The CRVE pipeline transforms raw narration text into a high-fidelity cinematic knowledge graph video using a decoupled, multi-stage architecture:

```
[Raw Narrations Text]
        │
        ▼
1. Deterministic NLP Engine (Stanza / NetworkX / BanglaProcessor)
   Extracts Entities (Nodes) and Relations (Links) without AI hallucination.
        │
        ▼
2. Directorial Layer (Director Brain)
   Determines layout types, importance weights, scene mood presets, and camera moves.
        │
        ▼
3. Remotion Adapter (remotion_adapter.py)
   Performs dynamic Google Drive font sync and serializes everything to a standard JSON Manifest.
        │
        ▼
4. Frontend Rendering Engine (Remotion / React / react-xarrows)
   Builds coordinates, manages staggered reveals, handles coordinates math, and renders video.
```

### Font Sync and Registration
* **Source:** Google Drive directory (`/content/drive/MyDrive/Counterism_Studio_V4/fonts`)
* **Local Fallback:** Local public storage (`public/fonts/`).
* **Detection:** Automatically scans font files at runtime and classifies them as Bangla (if filename contains `bangla`, `bn`) or English (if filename contains `english`, `en`, `eng`, `enlgish`).
* **Deterministic Selection:** To prevent visual flickering between render nodes, a node’s unique ID is hashed (`zlib.adler32`). This hash dynamically maps the node to a specific font index in the appropriate language list, guaranteeing 100% reproducible font styling across multiple render sessions.
* **Loading:** `src/Root.tsx` registers these files dynamically in the browser at runtime using dynamic CSS stylesheet `@font-face` injections.

---

## 2. Complete Field-by-Field JSON Reference

The root JSON manifest is a single structured configuration. Below is the comprehensive guide for every object and field:

### 2.1. Root Object Settings

| Field | Type | Description |
| :--- | :--- | :--- |
| `project_id` | `string` | Unique identifier for the current project. |
| `global_settings` | `object` | Global scene sizing and framerate options. |
| `scenes` | `array` | List of Scene configurations rendering sequentially. |

#### `global_settings` details:
* `width` (integer, e.g., `1920`): Output width of the video canvas.
* `height` (integer, e.g., `1080`): Output height of the video canvas.
* `fps` (integer, e.g., `30`): Target framerate.

---

### 2.2. Scene Object Settings

Each scene represents a unique timeline block with its own background, visual knowledge graph overlays, and camera tracks.

| Field | Type | Description |
| :--- | :--- | :--- |
| `scene_id` | `string` | ID of the scene (e.g. `SCENE_1` or `দৃশ্য_১`). Activates specific thematic styles. |
| `duration_in_frames` | `integer` | Total frames for this scene (e.g., `300` for 10 seconds at 30fps). |
| `background` | `object` | Procedural or image-based canvas background configuration. |
| `overlays` | `array` | List of content layers rendering in this scene. |
| `camera` | `object` | Camera position and movement script. |

#### `background` details:
* `background_type` (string): Usually `"procedural"`.
* `procedural_config` (object): Configures the procedural background (e.g., `{"variant": "neon_grid"}`).

---

### 2.3. Overlay Object Settings (Type: `"crve"`)

An overlay of type `"crve"` activates the Cinematic Relationship Visualization Engine.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `string` | Unique ID of this overlay layer. |
| `type` | `string` | Must be `"crve"` to route this overlay to the CRVE layout engine. |
| `content` | `string` | Narrative metadata describing the cinematic theme or focus. |
| `start` | `integer` | Start frame for this overlay relative to the scene (usually `0`). |
| `duration` | `integer` | Duration in frames for this overlay layer. |
| `position` | `object` | Anchor position `{ "x": 1370, "y": 540 }` designed to respect broadcast-safe areas. |
| `nodes` | `array` | List of node entities to display in the scene's graph. |
| `links` | `array` | List of connections/arrows linking the nodes together. |
| `layout_type` | `string` | The graph's layout distribution pattern (see Section 3.1). |
| `visual_theme` | `string` | Global visual styling theme (e.g., `"glassmorphism"`, `"neon"`). |
| `cinematic_mood` | `string` | Set to `"scientific"`, `"cyberpunk"`, `"danger"`, or `"luxury_hud"`. |
| `visual_metaphor` | `string` | Structural blueprint layout (e.g., `"force_graph"`, `"solar_system"`). |
| `lighting_style` | `string` | Atmospheric illumination preset (e.g., `"ambient"`, `"volumetric"`). |
| `background_fx` | `string` | Background elements inside the overlay (e.g., `"grid"`, `"none"`). |

---

### 2.4. Node Object Settings

Nodes represent semantic entities. They are drawn as premium glassmorphic or glowing text cards.

| Field | Type | Required/Optional | Description |
| :--- | :--- | :--- | :--- |
| `id` | `string` | **Required** | Unique string identifier. Links use this to declare sources/targets. |
| `label` | `string` | **Required** | The actual text shown on the node (supports full English & Bangla). |
| `type` | `string` | **Required** | Semantic role. One of: `danger_core`, `abstract_core`, `map_marker`, `terrain`, `particles`, `structures`. |
| `importance` | `float` | **Required** | Hierarchical size weight (typically `1.0` to `3.0`). |
| `scale` | `float` | Optional | Initial scale modifier (typically `1.0`). |
| `depth` | `float` | Optional | Z-axis coordinate value for 2.5D visual depth layering. |
| `font` | `string` | Optional | Custom font family override. If null, the engine deterministically picks a loaded Google Drive font based on the language. |
| `font_size` | `float` or `null` | Optional | **If null:** Font size is calculated dynamically on the frontend relative to importance: `14 + (importance * 3.5)`. **If set:** Hardcodes a static font size, bypassing responsive scaling. |
| `style_preset` | `string` | Optional | Stylistic visual card borders/effects (e.g., `"core_pulse"`, `"glass_disc"`, `"cyber_eye"`, `"neural_synapse"`, `"tactical_triangle"`). |

---

### 2.5. Link (Edge) Object Settings

Links define semantic relationships. They are animated as glowing connections with arrows pointing from the source to the target node.

| Field | Type | Required/Optional | Description |
| :--- | :--- | :--- | :--- |
| `id` | `string` | **Required** | Unique identifier for the link (usually `sourceId_targetId`). |
| `source` | `string` | **Required** | The exact `id` of the source node. |
| `target` | `string` | **Required** | The exact `id` of the target node. |
| `relationship` | `string` | Optional | Semantic relation class (e.g., `containment`, `construction_flow`, `aggregation`, `reveal`). |
| `strength` | `float` | Optional | Visual intensity of the line (determines thickness and opacity scale). |

---

### 2.6. Camera Object Settings

Specifies programmatic pan, zoom, or tracking movements for the viewer's camera viewport.

| Field | Type | Description |
| :--- | :--- | :--- |
| `enabled` | `boolean` | Must be `true` to active procedural camera motion. |
| `shots` | `array` | List of sequential camera movements. |

#### `shots` details:
* `targetId` (string): The overlay element to target and frame.
* `startFrame` (integer): Start frame of the movement relative to the scene (always `0` to prevent Remotion state crashes).
* `style` (string): Camera movement type (`zoom_out`, `pan_up`, `descend`, `orbit`, `push_in`).
* `zoom` (float): Dynamic zoom multiplier (typically `1.0` to `1.5`).
* `duration` (integer): Duration of the camera track.

---

## 3. High-Quality Presentation Rules

### 3.1. Layout Types & Per-Scene Overrides
To ensure high visual variety and narrative pacing, the layout and aesthetics are dynamically customized per scene based on the active `scene_id` or Bangla representation:

* **Scene 1 (`SCENE_1` / `দৃশ্য_১`) ── Solar System / Scientific Preset**
  * Nodes are distributed like planetary orbits revolving around a central central hero node.
  * *Theme Colors:* Cyber blue and emerald lights, using subtle circular grid overlays.
* **Scene 2 (`SCENE_2` / `দৃশ্য_২`) ── Radial / Cyberpunk Preset**
  * Nodes are distributed in a ring topology around the core concept.
  * *Theme Colors:* Hot neon pink and bright cyan, utilizing glowing glassmorphic card borders.
* **Scene 3 (`SCENE_3` / `দৃশ্য_৩`) ── Force-Directed / Danger Preset**
  * Dynamic particle layout representing highly tension-filled, volatile connections.
  * *Theme Colors:* Warn orange, hazard yellow, and active red pulses, including a continuous blinking hazard bar on the card's edge.
* **Scene 4 (`SCENE_4` / `দৃশ্য_৪`) ── Timeline / Luxury HUD Preset**
  * Structured left-to-right chronological flow indicating sequences.
  * *Theme Colors:* Luxury gold and amber HUD lines, featuring sharp technological corner brackets.

### 3.2. Sequential Information Flow & Staggered Reveal
To prevent cognitive overload, information is revealed incrementally in a natural flow:
* **Topological Relaxation:** Nodes are ranked in hierarchical dependency order (`nodeRanks`).
* **Reveal Staggering:** Nodes animate and scale into view dynamically relative to their rank delay (`rank * 35` frames). Parent nodes appear first, followed by child nodes.
* **Safe-Zone Clamping:** Coordinates of all active nodes are clamped to the broadcast safe-zone (`[260, 1660]` on X and `[160, 920]` on Y) to prevent truncation on widescreen displays.
* **Header Title Anchoring:** Disconnected/unlinked header nodes are cleanly aligned at the top center of the screen (`x = 0, y = -260`) to act as clean cinematic headers rather than scattering into the graph.

### 3.3. Premium Connection Lines (react-xarrows)
* Connection paths are drawn dynamically using `react-xarrows` vectors rather than custom SVG paths.
* **Perfect Target Alignment:** The scale transformation is stripped from the main container and applied to individual nodes. This allows standard browser coordinates (`getBoundingClientRect()`) to correctly detect the edge of nodes and align the connection line beautifully.
* **Real-time Synchronization:** Connection lines are recalculated on every frame using a `useXarrow()` handle wrapped inside `requestAnimationFrame` to maintain performance and prevent infinite render loops.
* **Link Reveal Rules:** Connection lines fade in smoothly using opacities calculated against active narration windows, and only draw once both the source and target nodes are fully revealed.

---

## 4. Manifest Example

Below is a complete, fully-compliant manifest JSON showing the interaction of fields:

```json
{
  "project_id": "knowledge_system_unified",
  "global_settings": {
    "width": 1920,
    "height": 1080,
    "fps": 30
  },
  "scenes": [
    {
      "scene_id": "SCENE_1",
      "duration_in_frames": 300,
      "background": {
        "background_type": "procedural",
        "procedural_config": {
          "variant": "neon_grid"
        }
      },
      "overlays": [
        {
          "id": "crve_SCENE_1",
          "type": "crve",
          "content": "calm introduction",
          "start": 0,
          "duration": 300,
          "position": {
            "x": 1370,
            "y": 540
          },
          "nodes": [
            {
              "id": "প্ল্যানেট",
              "label": "প্ল্যানেট",
              "type": "abstract_core",
              "importance": 1.0,
              "scale": 1.0,
              "depth": 0.0,
              "font": "Sohid_bangla",
              "font_size": null,
              "style_preset": "core_pulse"
            },
            {
              "id": "মেগাসিটি",
              "label": "মেগাসিটি",
              "type": "structures",
              "importance": 2.0,
              "scale": 1.0,
              "depth": 0.0,
              "font": "Sohid_bangla",
              "font_size": null,
              "style_preset": "core_pulse"
            },
            {
              "id": "ঢাকা",
              "label": "ঢাকা",
              "type": "map_marker",
              "importance": 2.0,
              "scale": 1.0,
              "depth": -500.0,
              "font": "Sohid_bangla",
              "font_size": null,
              "style_preset": "core_pulse"
            }
          ],
          "links": [
            {
              "id": "ঢাকা_মেগাসিটি",
              "source": "ঢাকা",
              "target": "মেগাসিটি",
              "relationship": "containment",
              "strength": 1.0
            }
          ],
          "layout_type": "force",
          "visual_theme": "glassmorphism",
          "cinematic_mood": "documentary",
          "visual_metaphor": "force_graph",
          "lighting_style": "ambient",
          "background_fx": "grid"
        }
      ],
      "camera": {
        "enabled": true,
        "shots": [
          {
            "targetId": "crve_SCENE_1",
            "startFrame": 0,
            "style": "zoom_out",
            "zoom": 1.0,
            "duration": 150
          }
        ]
      }
    }
  ]
}
```

---

## 5. Development Guidelines & Integration

When extending the system, always adhere to the following core practices:

1. **Keep Font Size Dynamic:** Unless a layout explicitly demands a fixed, locked pixel height, always pass `"font_size": null` in the manifest so the frontend handles responsive design.
2. **Handle Multilingual Input gracefully:** The layout engine determines fallback fonts (`Sohid_bangla` for Bengali script, `Audiowide-Regular_english` for Latin script) on-the-fly, so ensure filenames remain structured as detected.
3. **Keep the React scale clean:** If you modify node rendering containers, do not add global parent scale animations or parent absolute-transform CSS directly. This breaks coordinate tracking in `react-xarrows`. Keep the container at `1:1` scale and animate the node components individually.
