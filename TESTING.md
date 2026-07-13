# 🎬 Counterism Studio V4: Testing Guide

Welcome to the Cinematic Knowledge System. This project is a multi-stage pipeline that transforms raw narration into high-end documentary motion graphics.

---

## 1. Quick Start: Full Pipeline Demo

We've provided a single script to run the entire semantic-to-visual intelligence pipeline.

```bash
# Run the demo (Dhaka Megacity Example)
python3 scripts/run_demo_pipeline.py
```

This will generate:
1. `semantic_model.json` (Structured NLP)
2. `knowledge_graph.json` (Relationship Map)
3. `visualization_plan.json` (Directorial Blueprint)

---

## 2. Component-Level Testing

### A. Semantic Understanding (NLP)
Extract entities, actions, and relationships from any script. Supports English and Bangla.

```bash
python3 -m semantic_engine.main "Your narration script here..."
```

### B. Cinematic Visualizer (Director Brain)
Convert a knowledge graph into a film director's shot plan (2.5D layering, camera movements, motion grammar).

```bash
# Ensure input files exist in semantic_visualizer/input/
PYTHONPATH=. python3 semantic_visualizer/main.py
```

### C. Production QA (Titan Guard)
Validate and auto-repair your Remotion manifest files.

```bash
python3 scripts/test_manifest_quality.py manifests/your_manifest.json public/
```

---

## 3. Visual Rendering (Remotion)

To see the **CRVE (Cinematic Relationship Visualization Engine)** in action:

1. Open the Remotion Preview:
   ```bash
   npm run start
   ```
2. Navigate to the `crve-demo` composition.
3. Observe the `ParticleStream`, `EnergyBeam`, and `HUDConnector` relationship styles.

---

## 4. Manual Script Splitting
The engine supports multi-scene splitting using markers.

**Example script format:**
```text
দৃশ্য ১: ঢাকা শহর...
দৃশ্য ২: কংক্রিটের পাহাড়...
```

Run this through `semantic_engine` to see how it unifies entities across scenes.
