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

    def _scan_fonts(self) -> Dict[str, List[str]]:
        import os
        import shutil

        dirs_to_check = [
            "/content/drive/MyDrive/Counterism_Studio_V4/fonts",
            "public/fonts",
            "./public/fonts"
        ]
        bangla_fonts = []
        english_fonts = []

        default_bangla = "Sohid_bangla"
        default_english = "Audiowide-Regular_english"

        # Programmatically sync from drive to local public/fonts if available
        drive_dir = "/content/drive/MyDrive/Counterism_Studio_V4/fonts"
        local_dir = "public/fonts"
        if os.path.exists(drive_dir) and os.path.isdir(drive_dir):
            if os.path.exists(local_dir) and os.path.isdir(local_dir):
                for filename in os.listdir(drive_dir):
                    src_file = os.path.join(drive_dir, filename)
                    dst_file = os.path.join(local_dir, filename)
                    if os.path.isfile(src_file) and os.path.splitext(filename)[1].lower() in ['.ttf', '.otf', '.woff', '.woff2']:
                        try:
                            shutil.copy2(src_file, dst_file)
                        except Exception as e:
                            print(f"Warning: Failed to copy {filename} to {local_dir}: {e}")

        # Scan for available fonts
        for d in dirs_to_check:
            if os.path.exists(d) and os.path.isdir(d):
                for filename in os.listdir(d):
                    name, ext = os.path.splitext(filename)
                    if ext.lower() in ['.ttf', '.otf', '.woff', '.woff2']:
                        lower_name = name.lower()
                        if 'bangla' in lower_name or 'bn' in lower_name:
                            if name not in bangla_fonts:
                                bangla_fonts.append(name)
                        elif 'english' in lower_name or 'en' in lower_name or 'eng' in lower_name or 'enlgish' in lower_name:
                            if name not in english_fonts:
                                english_fonts.append(name)
                if bangla_fonts or english_fonts:
                    break

        if not bangla_fonts:
            bangla_fonts.append(default_bangla)
        if not english_fonts:
            english_fonts.append(default_english)

        return {
            "bangla": bangla_fonts,
            "english": english_fonts
        }

    def adapt(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        import zlib
        scanned_fonts = self._scan_fonts()
        scenes = []
        for p_scene in plan_data["scenes"]:
            # Convert VisualObjects into CRVE-compatible overlays
            nodes = []
            for obj in p_scene["visual_objects"]:
                is_bn = self._is_bangla(obj["label"])
                font_list = scanned_fonts["bangla"] if is_bn else scanned_fonts["english"]

                # Pick font dynamically based on a deterministic hash to ensure absolute reproducibility
                font_hash = zlib.adler32(obj["id"].encode('utf-8'))
                font_idx = font_hash % len(font_list)
                font = font_list[font_idx]

                nodes.append({
                    "id": obj["id"],
                    "label": obj["label"],
                    "type": obj["type"],
                    "importance": obj["importance"],
                    "scale": obj["scale"],
                    "depth": obj["depth"],
                    "font": font,
                    "font_size": obj.get("font_size"),
                    "style_preset": obj.get("style_preset", "glass_disc")
                })

            links = []
            for rel in p_scene["relationships"]:
                is_dict = isinstance(rel, dict)
                rel_type = rel["type"] if is_dict else rel.type
                rel_strength = rel["strength"] if is_dict else rel.strength
                rel_source = rel["source_id"] if is_dict else rel.source_id
                rel_target = rel["target_id"] if is_dict else rel.target_id

                link_obj = {
                    "id": f"{rel_source}_{rel_target}",
                    "source": rel_source,
                    "target": rel_target,
                    "relationship": rel_type,
                    "strength": rel_strength
                }

                # Support decoupled frame controls
                frame_start = rel.get("revealFrameStart") if is_dict else getattr(rel, "revealFrameStart", None)
                duration = rel.get("revealDuration") if is_dict else getattr(rel, "revealDuration", None)

                if frame_start is not None:
                    link_obj["revealFrameStart"] = frame_start
                if duration is not None:
                    link_obj["revealDuration"] = duration

                links.append(link_obj)

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
                "visual_theme": p_scene.get("visual_theme", "glassmorphism"),
                "cinematic_mood": p_scene.get("cinematic_mood", "documentary"),
                "visual_metaphor": p_scene.get("visual_metaphor", "force_graph"),
                "lighting_style": p_scene.get("lighting_style", "ambient"),
                "background_fx": p_scene.get("background_fx", "none")
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
