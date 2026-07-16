import json
from typing import Dict, Any, List

class RemotionAdapter:
    """
    Converts a VisualizationPlan into a Remotion-ready manifest.
    This is the final bridge before rendering.
    """
    def __init__(self):
        pass

    def _is_bangla(self, text: str) -> bool:
        return any("\u0980" <= char <= "\u09FF" for char in str(text))

    def adapt(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        scenes = []
        for p_scene in plan_data["scenes"]:
            # Convert VisualObjects into CRVE-compatible overlays
            nodes = []
            for obj in p_scene["visual_objects"]:
                font = "Sohid_bangla" if self._is_bangla(obj["label"]) else "Audiowide-Regular_english"

                nodes.append({
                    "id": obj["id"],
                    "label": obj["label"],
                    "type": obj["type"],
                    "importance": obj["importance"],
                    "scale": obj["scale"],
                    "depth": obj["depth"],
                    "font": font,
                    "style_preset": obj.get("style_preset", "glass_disc")
                })

            links = []
            for rel in p_scene["relationships"]:
                links.append({
                    "id": f"{rel['source_id']}_{rel['target_id']}",
                    "source": rel["source_id"],
                    "target": rel["target_id"],
                    "relationship": rel["type"],
                    "strength": rel["strength"]
                })

            # Create the CRVE overlay
            crve_overlay = {
                "id": f"crve_{p_scene['scene_id']}",
                "type": "crve",
                "content": p_scene.get("theme", "Semantic Concept"),
                "start": 0,
                "duration": p_scene["duration"],
                "position": {"x": 1370, "y": 540}, # QA-Optimized Broadcast Position
                "nodes": nodes,
                "links": links,
                "layout_type": p_scene.get("layout_type", "force"),
                "visual_theme": p_scene.get("visual_theme", "glassmorphism")
            }

            scenes.append({
                "scene_id": p_scene["scene_id"],
                "duration_in_frames": p_scene["duration"],
                "background": {"background_type": "procedural", "procedural_config": {"variant": "neon_grid"}},
                "overlays": [crve_overlay],
                "camera": {
                    "enabled": True,
                    "shots": [
                        {
                            "targetId": crve_overlay["id"],
                            "startFrame": 0,
                            "style": p_scene["camera"]["movement"],
                            "zoom": p_scene["camera"]["zoom"],
                            "duration": p_scene["camera"]["duration"]
                        }
                    ]
                }
            })

        return {
            "project_id": plan_data["project_id"],
            "global_settings": {"width": 1920, "height": 1080, "fps": 30},
            "scenes": scenes
        }

def main():
    import sys
    import os

    plan_path = "semantic_visualizer/output/visualization_plan.json"
    output_path = "remotion_render_crve.json"

    if os.path.exists(plan_path):
        with open(plan_path, 'r') as f:
            plan = json.load(f)

        adapter = RemotionAdapter()
        manifest = adapter.adapt(plan)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"✅ Remotion manifest generated: {output_path}")
    else:
        print(f"❌ Visualization plan not found at {plan_path}")

if __name__ == "__main__":
    main()
