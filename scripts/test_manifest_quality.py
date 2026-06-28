import json
import sys
import os
import re

def test_manifest_quality(filepath, public_dir=None):
    """
    Hardened Geometry-Aware QA suite for Studio V4 manifests.
    Validates assets, geometry, collisions, timing, typography, and data integrity.
    """
    print(f"\n" + "="*80)
    print(f"🎬 STUDIO V4 PRODUCTION QA: {os.path.basename(filepath)}")
    print("="*80)

    if not os.path.exists(filepath):
        print(f"❌ QA Error: File {filepath} not found.")
        return False

    if public_dir is None:
        public_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(filepath)), "public"))

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ QA Error: Failed to parse JSON: {e}")
        return False

    issues = [] # Fatal errors (FAIL)
    warnings = [] # Aesthetic suggestions

    # Scoring Metrics (0-100)
    scores = {
        "layout": 100,
        "collision": 100,
        "camera": 100,
        "timing": 100,
        "composition": 100,
        "assets": 100,
        "typography": 100
    }

    scenes = data.get('scenes', [])
    if not scenes:
        print("❌ CRITICAL: No scenes found in manifest.")
        return False

    TYPE_SIZES = {
        'text': (800, 200),
        'chart': (1000, 562), 'shadcn_chart': (1000, 562), # 16:9
        'ui_panel': (800, 600), # 4:3
        'data_indicator': (500, 375), 'shadcn_indicator': (500, 375), # 4:3
        'svg': (400, 400), 'kpi': (450, 400), 'kpi_card': (450, 400),
        'timeline': (1200, 300),
        'hub_network': (800, 800), 'flow_diagram': (1000, 562), 'process': (1000, 562),
        'media': (960, 540), 'image': (960, 540), 'video': (960, 540), # 16:9
        'label': (300, 100), 'callout': (400, 200),
        'compositions': (1200, 675), 'groups': (1200, 675), # 16:9
        'graph': (1000, 700), 'shape': (400, 400),
        'connector': (400, 100), 'ambient_graphic': (1920, 1080)
    }

    MIN_CONSTRAINTS = {
        'fontSize': 40,
        'hero_fontSize': 72, # Hero text protection
        'chart_w': 300, 'chart_h': 200,
        'svg_w': 100, 'svg_h': 100,
        'min_spacing': 30
    }

    all_scene_ids = set()
    global_overlay_ids = set()

    print(f"🔍 ANALYZING {len(scenes)} SCENES...")

    for idx, scene in enumerate(scenes):
        scene_id = scene.get('scene_id', f"SCENE_{idx+1}")
        print(f"\n--- {scene_id} ---")

        if scene_id in all_scene_ids:
            issues.append(f"CRITICAL: Duplicate scene_id '{scene_id}' detected.")
        all_scene_ids.add(scene_id)

        duration = scene.get('duration_in_frames', 180)
        overlays = scene.get('overlays', [])

        # 1. Asset Verification
        if scene.get('background_type') == 'video':
            vpath = scene.get('video_path', '')
            if vpath:
                rel_vpath = vpath.replace('renders/', '') if vpath.startswith('renders/') else vpath
                abs_vpath = os.path.join(public_dir, "renders", rel_vpath.lstrip('/'))
                if not os.path.exists(abs_vpath):
                    if not os.path.exists(os.path.join(public_dir, vpath.lstrip('/'))):
                        msg = f"[{scene_id}] Asset Missing: video '{vpath}'"
                        issues.append(msg)
                        print(f"   ❌ ASSETS: {msg}")
                        scores["assets"] -= 20
                else:
                    print(f"   ✅ ASSETS: Video '{vpath}' verified.")

        # 2. Timing Validation
        if duration <= 0:
            msg = f"[{scene_id}] Invalid scene duration: {duration}"
            issues.append(msg)
            print(f"   ❌ TIMING: {msg}")
            scores["timing"] -= 50
        else:
            print(f"   ✅ TIMING: Duration {duration}f valid.")

        # 3. Overlay Validation
        overlay_ids = set()
        placed_geometries = []
        starts = []

        for ov in overlays:
            ov_id = ov.get('id', 'unknown')
            overlay_ids.add(ov_id)
            global_overlay_ids.add(ov_id)

            o_type = str(ov.get('type', 'text')).lower()
            start = ov.get('start', 0)
            starts.append(start)
            ov_dur = ov.get('duration', 0)

            # Timing check
            if start < 0 or start >= duration:
                msg = f"[{scene_id}] '{ov_id}' start time {start} out of bounds."
                issues.append(msg)
                print(f"   ❌ TIMING: {msg}")
                scores["timing"] -= 10

            # Geometry check
            pos = ov.get('position', {})
            x, y = pos.get('x', 960), pos.get('y', 540)

            # Center Stacking Detection
            if (abs(x - 960) < 5 and abs(y - 540) < 5) or (abs(x - 960) < 5 and abs(y - 700) < 5):
                msg = f"[{scene_id}] '{ov_id}' is center-stacked at ({x}, {y}). Avoid generic centering."
                warnings.append(msg)
                print(f"   ⚠️ COMPOSITION: {msg}")
                scores["composition"] -= 15

            # Geometry Prioritization
            base_w, base_h = TYPE_SIZES.get(o_type, (600, 400))
            w = ov.get('width', ov.get('size', base_w))
            h = ov.get('height', ov.get('size', base_h))

            if o_type == 'shape' and ov.get('shape_type') == 'circle':
                radius = ov.get('size', 100)
                w, h = radius * 2, radius * 2

            # Semantic Lifecycle check
            if not ov.get('exitAnimation'):
                msg = f"[{scene_id}] '{ov_id}' missing 'exitAnimation'."
                warnings.append(msg)
                print(f"   ⚠️ PRODUCTION: {msg}")

            if o_type == 'text':
                content = str(ov.get('content', ''))
                fs_match = re.search(r'\d+', str(ov.get('fontSize', '120')))
                fs = int(fs_match.group()) if fs_match else 120

                importance = str(ov.get('importance', '')).lower()
                min_fs = MIN_CONSTRAINTS['hero_fontSize'] if importance == 'hero' else MIN_CONSTRAINTS['fontSize']

                if fs < min_fs:
                    msg = f"[{scene_id}] Text '{ov_id}' ({importance}) fontSize {fs}px is too small (min {min_fs}px)."
                    issues.append(msg)
                    print(f"   ❌ TYPOGRAPHY: {msg}")
                    scores["typography"] -= 20

                max_w = ov.get('maxWidth', 1600)
                w = min(max_w, len(content) * fs * 0.7)
                h = fs * 1.5
                if len(content.split()) > 6:
                    msg = f"[{scene_id}] Text '{ov_id}' is verbose ({len(content.split())} words)."
                    warnings.append(msg)
                    print(f"   ⚠️ TYPOGRAPHY: {msg}")

            l, t = x - w/2, y - h/2
            r, b = x + w/2, y + h/2

            # Offscreen Check
            if l < 0 or r > 1920 or t < 0 or b > 1080:
                msg = f"[{scene_id}] '{ov_id}' is OFFSCREEN (Box: L:{int(l)}, R:{int(r)}, T:{int(t)}, B:{int(b)})"
                issues.append(msg)
                print(f"   ❌ LAYOUT: {msg}")
                scores["layout"] -= 25
            elif l < 150 or r > 1770 or t < 150 or b > 930:
                msg = f"[{scene_id}] '{ov_id}' violates 150px safe margins."
                warnings.append(msg)
                print(f"   ⚠️ COMPOSITION: {msg}")
                scores["composition"] -= 5

            # Collision Detection (Allow Hero/KPI to overlap backgrounds)
            for p_id, p_l, p_t, p_r, p_b, p_s, p_e, p_imp in placed_geometries:
                if max(start, p_s) < min(start + ov_dur, p_e):
                    # Ignore collisions with backgrounds/ambient elements if current is Hero
                    importance = str(ov.get('importance', '')).lower()
                    if (importance == 'hero' or importance == 'secondary') and p_imp in ['background', 'ambient']:
                        continue

                    gap = MIN_CONSTRAINTS['min_spacing']
                    if not (r + gap < p_l or l - gap > p_r or b + gap < p_t or t - gap > p_b):
                        msg = f"[{scene_id}] GEOMETRY COLLISION: '{ov_id}' overlaps with '{p_id}'"
                        issues.append(msg)
                        print(f"   ❌ COLLISION: {msg}")
                        scores["collision"] -= 30

            placed_geometries.append((ov_id, l, t, r, b, start, start + ov_dur, str(ov.get('importance', '')).lower()))


            # Hero Word Timing
            if o_type == 'text':
                hero = ov.get('hero_config', {})
                if hero:
                    h_start = hero.get('start', 0)
                    if h_start < start:
                        msg = f"[{scene_id}] Hero word in '{ov_id}' starts at {h_start}f, before overlay entry at {start}f."
                        issues.append(msg)
                        print(f"   ❌ SYNC: {msg}")
                        scores["timing"] -= 10
                    elif h_start < start + 10:
                        msg = f"[{scene_id}] Hero word in '{ov_id}' starts too early (needs 10f buffer)."
                        warnings.append(msg)
                        print(f"   ⚠️ SYNC: {msg}")

        if not overlays:
            print("   ⚠️ WARNING: Scene has no overlays.")
        else:
            print(f"   ✅ OVERLAYS: {len(overlays)} elements validated.")

    # Final Summary
    overall_score = sum(scores.values()) / len(scores)
    print("\n" + "="*80)
    print(f"📈 FINAL PRODUCTION REPORT: {int(overall_score)}%")
    print("-" * 80)
    for k, v in scores.items():
        status = "✅" if v > 80 else "⚠️" if v > 50 else "❌"
        print(f"   {status} {k.upper():<12} : {max(0, int(v))}/100")
    print("="*80)

    if issues:
        print("\n❌ CRITICAL PRODUCTION ERRORS FOUND:")
        for issue in sorted(issues): print(f"  ● {issue}")
        return False

    print(f"\n✨ PASS: Manifest is Ultra-High End Production ready!")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_manifest_quality.py <path_to_json> [public_dir]")
    else:
        test_manifest_quality(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
