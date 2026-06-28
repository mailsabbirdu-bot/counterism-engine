import json
import sys
import os
import re

def test_manifest_quality(filepath, public_dir=None):
    """
    Hardened Geometry-Aware QA suite for Studio V4 manifests.
    Validates assets, geometry, collisions, timing, typography, and data integrity.
    """
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
        "assets": 100
    }

    scenes = data.get('scenes', [])
    if not scenes:
        issues.append("CRITICAL: No scenes found in manifest.")
        return False

    TYPE_SIZES = {
        'text': (800, 200), 'chart': (1000, 600), 'shadcn_chart': (1000, 600),
        'ui_panel': (700, 500), 'data_indicator': (450, 400), 'shadcn_indicator': (450, 400),
        'svg': (400, 400), 'kpi': (450, 400), 'timeline': (1200, 300),
        'hub_network': (900, 900), 'flow_diagram': (1000, 450), 'process': (1000, 450),
        'media': (900, 700), 'image': (900, 700), 'video': (900, 700),
        'label': (300, 100), 'callout': (400, 200), 'composition': (1200, 800), 'groups': (1200, 800)
    }

    # Minimum production constraints
    MIN_CONSTRAINTS = {
        'fontSize': 40,
        'chart_w': 300, 'chart_h': 200,
        'svg_w': 100, 'svg_h': 100,
        'min_spacing': 30
    }

    all_scene_ids = set()
    global_overlay_ids = set()

    for idx, scene in enumerate(scenes):
        scene_id = scene.get('scene_id', f"SCENE_{idx+1}")
        if scene_id in all_scene_ids:
            issues.append(f"CRITICAL: Duplicate scene_id '{scene_id}' detected.")
        all_scene_ids.add(scene_id)

        duration = scene.get('duration_in_frames', 180)
        overlays = scene.get('overlays', [])

        # 1. Asset Verification
        if scene.get('background_type') == 'video':
            vpath = scene.get('video_path', '')
            if vpath:
                # Video paths in manifest are usually relative to 'public/'
                rel_vpath = vpath.replace('renders/', '') if vpath.startswith('renders/') else vpath
                abs_vpath = os.path.join(public_dir, "renders", rel_vpath.lstrip('/'))
                if not os.path.exists(abs_vpath):
                    # Try direct join if not in renders/
                    if not os.path.exists(os.path.join(public_dir, vpath.lstrip('/'))):
                        issues.append(f"[{scene_id}] Asset Missing: video '{vpath}'")
                        scores["assets"] -= 20

        # 2. Timing Validation
        if duration <= 0:
            issues.append(f"[{scene_id}] Invalid scene duration: {duration}")
            scores["timing"] -= 50

        # 3. Overlay Validation
        overlay_ids = set()
        placed_geometries = []
        scene_colors = set()
        starts = []

        for ov in overlays:
            ov_id = ov.get('id', 'unknown')
            if not ov.get('id'):
                issues.append(f"[{scene_id}] Overlay missing ID.")
            if ov_id in overlay_ids:
                issues.append(f"[{scene_id}] Duplicate overlay ID: {ov_id}")
            overlay_ids.add(ov_id)
            global_overlay_ids.add(ov_id)

            o_type = str(ov.get('type', 'text')).lower()
            start = ov.get('start', 0)
            starts.append(start)
            ov_dur = ov.get('duration', 0)

            # Timing
            if start < 0 or start >= duration:
                issues.append(f"[{scene_id}] '{ov_id}' start time {start} out of bounds.")
                scores["timing"] -= 10
            if ov_dur <= 0:
                issues.append(f"[{scene_id}] '{ov_id}' has invalid duration.")
            if start + ov_dur > duration + 5:
                warnings.append(f"[{scene_id}] '{ov_id}' ends after scene ({start+ov_dur} > {duration}).")
                scores["timing"] -= 5

            # Geometry
            pos = ov.get('position', {})
            x, y = pos.get('x', 960), pos.get('y', 540)

            # Center Stacking Detection
            if (abs(x - 960) < 5 and abs(y - 540) < 5) or (abs(x - 960) < 5 and abs(y - 700) < 5):
                warnings.append(f"[{scene_id}] '{ov_id}' is center-stacked at ({x}, {y}). Avoid generic centering.")
                scores["composition"] -= 15

            # 1. Prioritize manifest width/height
            # 2. Fallback to TYPE_SIZES
            base_w, base_h = TYPE_SIZES.get(o_type, (600, 400))
            w = ov.get('width', base_w)
            h = ov.get('height', base_h)

            if o_type == 'text':
                content = str(ov.get('content', ''))
                fs_match = re.search(r'\d+', str(ov.get('fontSize', '120')))
                fs = int(fs_match.group()) if fs_match else 120

                # Check min fontSize constraint
                if fs < MIN_CONSTRAINTS['fontSize']:
                    issues.append(f"[{scene_id}] Text '{ov_id}' fontSize {fs}px is below production minimum (40px).")
                    scores["typography"] -= 20

                # Compute effective visual box for text
                w = min(1600, len(content) * fs * 0.7)
                h = fs * 1.5
                if len(content.split()) > 6:
                    warnings.append(f"[{scene_id}] Text '{ov_id}' is verbose ({len(content.split())} words).")

            # Check other min constraints
            elif 'chart' in o_type:
                if w < MIN_CONSTRAINTS['chart_w'] or h < MIN_CONSTRAINTS['chart_h']:
                    issues.append(f"[{scene_id}] Chart '{ov_id}' size {w}x{h} is below production minimum.")
                    scores["layout"] -= 20
            elif o_type == 'svg':
                if w < MIN_CONSTRAINTS['svg_w'] or h < MIN_CONSTRAINTS['svg_h']:
                    issues.append(f"[{scene_id}] SVG '{ov_id}' size {w}x{h} is below production minimum.")
                    scores["layout"] -= 20

            l, t = x - w/2, y - h/2
            r, b = x + w/2, y + h/2

            # Offscreen Check
            if l < -50 or r > 1970 or t < -50 or b > 1130:
                issues.append(f"[{scene_id}] '{ov_id}' is OFFSCREEN (Box: L:{int(l)}, R:{int(r)}, T:{int(t)}, B:{int(b)})")
                scores["layout"] -= 25
            elif l < 80 or r > 1840 or t < 60 or b > 1020:
                warnings.append(f"[{scene_id}] '{ov_id}' violates safe margins.")
                scores["composition"] -= 5

            # Collision Detection (AABB)
            for p_id, p_l, p_t, p_r, p_b, p_start, p_end in placed_geometries:
                if max(start, p_start) < min(start + ov_dur, p_end):
                    gap = MIN_CONSTRAINTS['min_spacing']
                    if not (r + gap < p_l or l - gap > p_r or b + gap < p_t or t - gap > p_b):
                        issues.append(f"[{scene_id}] GEOMETRY COLLISION: '{ov_id}' overlaps with '{p_id}'")
                        scores["collision"] -= 30

            placed_geometries.append((ov_id, l, t, r, b, start, start + ov_dur))

            # Hero Word
            if o_type == 'text':
                hero = ov.get('hero_config', {})
                h_word = hero.get('word', '')
                if h_word:
                    if h_word not in str(ov.get('content', '')):
                        issues.append(f"[{scene_id}] Hero word '{h_word}' not found in content of '{ov_id}'.")
                    if hero.get('start', 0) < start:
                        warnings.append(f"[{scene_id}] Hero word in '{ov_id}' starts before overlay.")

            if ov.get('color'): scene_colors.add(ov['color'].upper())

        # Staging check
        if len(set(starts)) == 1 and len(starts) > 1:
            warnings.append(f"[{scene_id}] Elements lack progressive staging (all start at frame {starts[0]}).")
            scores["timing"] -= 10

        # 4. Camera Shot Validation
        shots = scene.get('camera', {}).get('shots', [])
        last_shot_end = 0
        camera_targets = []
        for s_idx, shot in enumerate(shots):
            target = shot.get('targetId')
            camera_targets.append(target)
            if target and target not in overlay_ids:
                issues.append(f"[{scene_id}] Camera shot {s_idx} targets missing ID: {target}")
                scores["camera"] -= 20

            s_start = shot.get('startFrame', 0)
            s_dur = shot.get('duration', 0)
            if s_start < last_shot_end - 1:
                warnings.append(f"[{scene_id}] Camera shot {s_idx} overlaps with previous.")
            if s_start + s_dur > duration + 1:
                issues.append(f"[{scene_id}] Camera shot {s_idx} exceeds scene duration.")
                scores["camera"] -= 10
            last_shot_end = s_start + s_dur

        if len(camera_targets) > 1 and len(set(camera_targets)) == 1:
            warnings.append(f"[{scene_id}] Camera repeatedly targets the same element '{camera_targets[0]}'.")
            scores["camera"] -= 15

        # 5. Infographic Line Validation
        for line in scene.get('infographic_lines', []):
            f, t = line.get('from'), line.get('to')
            if f not in overlay_ids: issues.append(f"[{scene_id}] Line 'from' missing: {f}")
            if t not in overlay_ids: issues.append(f"[{scene_id}] Line 'to' missing: {t}")

    # Final Report
    overall_score = sum(scores.values()) / len(scores)

    print("\n" + "="*65)
    print(f"🎬 STUDIO V4 PRODUCTION QA: {os.path.basename(filepath)}")
    print(f"   Scenes: {len(scenes)} | Overall Health: {int(overall_score)}%")
    print("-" * 65)
    for k, v in scores.items():
        status = "✅" if v > 80 else "⚠️" if v > 50 else "❌"
        print(f"   {status} {k.upper():<12} : {max(0, int(v))}/100")
    print("="*65)

    if issues:
        print("\n❌ CRITICAL PRODUCTION ERRORS:")
        for issue in sorted(issues)[:15]: print(f"  ● {issue}")
        if len(issues) > 15: print(f"  ... and {len(issues)-15} more.")

    if warnings:
        print("\n⚠️ AESTHETIC WARNINGS:")
        for warn in sorted(warnings)[:10]: print(f"  ○ {warn}")

    if not issues:
        print(f"\n✅ PASS: Manifest is ready for rendering (Score: {int(overall_score)}%)")
        return True
    else:
        print(f"\n🛑 FAIL: {len(issues)} critical errors must be resolved.")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_manifest_quality.py <path_to_json> [public_dir]")
    else:
        test_manifest_quality(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
