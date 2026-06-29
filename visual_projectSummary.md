# Visual Eye Phase 1: Scene Perception Layer

## Overview
Visual Eye is an optional enhancement layer for the Remotion documentary engine. It provides a "visual brain" that analyzes background videos to suggest optimal placement for overlays and identify key objects in the scene.

## Architecture
The system consists of a Python-based analyzer and a TypeScript-based resolver.

### Python Backend (`/visual_eye/`)
- **analyzer.py**: Orchestrates the analysis pipeline (load video, detect objects, find safe zones).
- **detector.py**: Interface for object detection and scene classification.
- **safe_zone.py**: Logic for identifying areas with low visual complexity suitable for text.
- **schema.py**: Pydantic models for structured analysis output.
- **fallback.py**: Error handling and default empty data.

### Remotion Integration (`src/services/`)
- **SmartPositionResolver.ts**: Resolves the final position of an overlay based on manual settings, AI suggestions, and fallbacks.

## Features
- **Object Detection**: Identifies common classes (buildings, people, vehicles, etc.).
- **Scene Classification**: Categorizes the type of environment.
- **Safe Zone Detection**: Suggests areas for text placement to maximize legibility.
- **Debug Mode**: Optional visualization of analysis data during development.

## Schema
Analysis results are saved as `scene_SC_XX_analysis.json` in the configured Drive directory.

```json
{
  "version": "1.0",
  "status": "success",
  "scene_type": "urban_city",
  "objects": [...],
  "safe_text_regions": [...]
}
```

## Backward Compatibility
Visual Eye is completely optional. If analysis data is missing or detection fails, the engine falls back to the original `position` data provided in the manifest.
