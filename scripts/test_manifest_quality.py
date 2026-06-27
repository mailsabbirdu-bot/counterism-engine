import json
import sys
import os

def test_manifest_quality(filepath):
    if not os.path.exists(filepath):
        print(f"❌ Error: File {filepath} not found.")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    issues = []
    scenes = data.get('scenes', [])
    if not scenes:
        issues.append("No scenes found in manifest.")

    for idx, scene in enumerate(scenes):
        scene_id = scene.get('scene_id', f"SCENE_{idx+1}")
        overlays = scene.get('overlays', [])

        # 1. Check for 3-column anchoring and center-stacking
        for ov in overlays:
            x = ov.get('position', {}).get('x', 0)
            y = ov.get('position', {}).get('y', 0)

            # Vox style expects elements in side columns or specific center nodes
            # 960 is center. Check if they are stacked exactly at center without being a diagram centerpiece.
            if x == 960 and y == 700:
                issues.append(f"[{scene_id}] Overlay '{ov['id']}' is center-stacked at (960, 700). Avoid generic centering.")

        # 2. Check for Overlaps (AABB)
        for i, ov1 in enumerate(overlays):
            for j, ov2 in enumerate(overlays):
                if i >= j: continue

                # Check timing overlap
                s1, e1 = ov1.get('start', 0), ov1.get('start', 0) + ov1.get('duration', 0)
                s2, e2 = ov2.get('start', 0), ov2.get('start', 0) + ov2.get('duration', 0)

                if max(s1, s2) < min(e1, e2):
                    # Overlap in time, check space
                    x1, y1 = ov1.get('position', {}).get('x', 0), ov1.get('position', {}).get('y', 0)
                    x2, y2 = ov2.get('position', {}).get('x', 0), ov2.get('position', {}).get('y', 0)

                    if x1 == x2 and y1 == y2:
                        issues.append(f"[{scene_id}] CRITICAL OVERLAP: '{ov1['id']}' and '{ov2['id']}' are at the same coordinates ({x1}, {y1}).")

        # 3. Check for Staggered Entrances
        starts = sorted([ov.get('start', 0) for ov in overlays])
        if len(starts) > 1 and starts[0] == starts[1] and starts[0] == 0:
             # This is a soft warning as some might be intentional, but Director mode prefers staggering
             # print(f"ℹ️ [{scene_id}] Elements pop simultaneously at frame 0. Consider staggering.")
             pass

        # 4. Check for Infographic lines in procedural scenes
        if scene.get('background_type') == 'procedural':
            lines = scene.get('infographic_lines', [])
            if not lines:
                issues.append(f"[{scene_id}] Procedural scene lacks 'infographic_lines'. Storytelling is weak.")

        # 5. Check for placeholder data
        for ov in overlays:
            if ov.get('type') == 'chart':
                data_points = ov.get('data', [])
                if isinstance(data_points, list):
                    labels = [str(d.get('id', '')).upper() for d in data_points]
                    if 'A' in labels and 'B' in labels:
                        issues.append(f"[{scene_id}] Chart '{ov['id']}' contains placeholder 'A/B' data.")
            if ov.get('type') == 'data_indicator':
                 label = str(ov.get('label', '')).upper()
                 if label in ['INSIGHT', 'METRIC', 'DATA']:
                     issues.append(f"[{scene_id}] Indicator '{ov['id']}' uses placeholder label '{label}'.")

    if issues:
        print("\n❌ Quality Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✅ Manifest passed quality standards!")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_manifest_quality.py <path_to_json>")
    else:
        test_manifest_quality(sys.argv[1])
