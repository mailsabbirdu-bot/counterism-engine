import json
import sys
import os
import re

def test_manifest_quality(filepath, public_dir=None):
    """
    Hardened Geometry-Aware QA suite for Studio V4 manifests.
    Returns: (success, score, issues)
    """
    print(f"\n" + "="*80)
    print(f"🎬 STUDIO V4 PRODUCTION QA: {os.path.basename(filepath)}")
    print("="*80)

    if not os.path.exists(filepath):
        msg = f"QA Error: File {filepath} not found."
        print(f"❌ {msg}")
        return False, 0, [msg]

    if public_dir is None:
        public_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(filepath)), "public"))

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        msg = f"QA Error: Failed to parse JSON: {e}"
        print(f"❌ {msg}")
        return False, 0, [msg]

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
        msg = "CRITICAL: No scenes found in manifest."
        print(f"❌ {msg}")
        return False, 0, [msg]

    TYPE_SIZES = {
        'text': (800, 200),
        'chart': (1000, 562), 'shadcn_chart': (1000, 562),
        'ui_panel': (800, 600),
        'data_indicator': (500, 375), 'shadcn_indicator': (500, 375),
        'svg': (400, 400), 'kpi': (450, 400), 'kpi_card': (450, 400),
        'timeline': (1200, 300),
        'hub_network': (800, 800), 'flow_diagram': (1000, 562), 'process': (1000, 562),
        'media': (960, 540), 'image': (960, 540), 'video': (960, 540),
        'label': (300, 100), 'callout': (400, 200),
        'compositions': (1200, 675), 'groups': (1200, 675),
        'graph': (1000, 700), 'shape': (400, 400),
        'connector': (400, 100), 'ambient_graphic': (1920, 1080)
    }

    MIN_CONSTRAINTS = {
        'fontSize': 40,
        'hero_fontSize': 100,
        'chart_w': 300, 'chart_h': 200,
        'svg_w': 100, 'svg_h': 100,
        'min_spacing': 30
    }

    all_scene_ids = set()
    print(f"🔍 ANALYZING {len(scenes)} SCENES...")

    for idx, scene in enumerate(scenes):
        scene_id = scene.get('scene_id', f"SCENE_{idx+1}")
        print(f"\n--- {scene_id} ---")

        if scene_id in all_scene_ids:
            issues.append(f"[{scene_id}] CRITICAL: Duplicate scene_id detected.")
        all_scene_ids.add(scene_id)

        # Reading Order & Sequencing
        beats = scene.get('beats', [])
        if not beats:
            warnings.append(f"[{scene_id}] Missing 'beats' array for visual sequencing.")
            scores["timing"] -= 5

        if not scene.get('transition'):
            warnings.append(f"[{scene_id}] Missing 'transition' object for story flow.")
            scores["composition"] -= 5

        duration = scene.get('duration_in_frames', 180)
        overlays = scene.get('overlays', [])

        # 1. Asset Verification
        if scene.get('background_type') == 'video':
            vpath = scene.get('video_path', '')
            if vpath:
                rel_vpath = vpath.replace('renders/', '') if vpath.startswith('renders/') else vpath
                abs_vpath = os.path.join(public_dir, "renders", rel_vpath.lstrip('/'))
                if not os.path.exists(abs_vpath):
                    msg = f"[{scene_id}] Asset Missing: video '{vpath}'"
                    issues.append(msg)
                    scores["assets"] -= 20
                else:
                    print(f"   ✅ ASSETS: Video verified.")

        # 2. Timing
        if duration <= 0:
            msg = f"[{scene_id}] Invalid scene duration: {duration}"
            issues.append(msg)
            scores["timing"] -= 50

        # 3. Overlay Validation
        overlay_ids = set()
        placed_geometries = []
        sorted_ovs = sorted(overlays, key=lambda x: x.get('start', 0))
        prev_start = -1
        sequential = True

        for ov in overlays:
            ov_id = ov.get('id', 'unknown')
            overlay_ids.add(ov_id)
            o_type = str(ov.get('type', 'text')).lower()
            start = ov.get('start', 0)
            if start < prev_start: sequential = False
            prev_start = start

            if start < 0 or start >= duration:
                issues.append(f"[{scene_id}] '{ov_id}' start time {start} out of bounds.")
                scores["timing"] -= 10

            pos = ov.get('position', {})
            x, y = pos.get('x', 960), pos.get('y', 540)

            # Center Stacking
            if (abs(x - 960) < 5 and (abs(y - 540) < 5 or abs(y - 700) < 5)):
                msg = f"[{scene_id}] '{ov_id}' is center-stacked at ({x}, {y})."
                warnings.append(msg)
                scores["composition"] -= 15

            base_w, base_h = TYPE_SIZES.get(o_type, (600, 400))
            w, h = ov.get('width', base_w), ov.get('height', base_h)

            if o_type == 'text':
                fs_match = re.search(r'\d+', str(ov.get('fontSize', '120')))
                fs = int(fs_match.group()) if fs_match else 120
                min_fs = MIN_CONSTRAINTS['hero_fontSize'] if str(ov.get('importance','')).lower() == 'hero' else MIN_CONSTRAINTS['fontSize']
                if fs < min_fs:
                    issues.append(f"[{scene_id}] Text '{ov_id}' fontSize {fs}px is too small (min {min_fs}px).")
                    scores["typography"] -= 20
                w, h = min(ov.get('maxWidth', 1600), len(str(ov.get('content',''))) * fs * 0.7), fs * 1.5

            l, t, r, b = x - w/2, y - h/2, x + w/2, y + h/2
            if l < 0 or r > 1920 or t < 0 or b > 1080:
                issues.append(f"[{scene_id}] '{ov_id}' is OFFSCREEN.")
                scores["layout"] -= 25
            elif l < 150 or r > 1770 or t < 150 or b > 930:
                warnings.append(f"[{scene_id}] '{ov_id}' violates 150px safe margins.")
                scores["composition"] -= 5

            for p_id, p_l, p_t, p_r, p_b, p_s, p_e, p_imp in placed_geometries:
                if max(start, p_s) < min(start + ov.get('duration',0), p_e):
                    if str(ov.get('importance','')).lower() in ['hero','secondary'] and p_imp in ['background','ambient']: continue
                    gap = MIN_CONSTRAINTS['min_spacing']
                    if not (r + gap < p_l or l - gap > p_r or b + gap < p_t or t - gap > p_b):
                        issues.append(f"[{scene_id}] GEOMETRY COLLISION: '{ov_id}' overlaps with '{p_id}'")
                        scores["collision"] -= 30
            placed_geometries.append((ov_id, l, t, r, b, start, start + ov.get('duration',0), str(ov.get('importance','')).lower()))

        if overlays and not sequential:
            warnings.append(f"[{scene_id}] Overlays revealed out of sequence.")
            scores["timing"] -= 10

        # 4. Camera & Lines
        camera = scene.get('camera', {})
        shots = camera.get('shots', [])
        if not shots:
            warnings.append(f"[{scene_id}] No camera shots defined.")
            scores["camera"] -= 10
        else:
            for s_idx, shot in enumerate(shots):
                target = shot.get('targetId')
                if target and target not in overlay_ids:
                    issues.append(f"[{scene_id}] Camera shot {s_idx} targets non-existent overlay '{target}'.")
                    scores["camera"] -= 20

        for line in scene.get('infographic_lines', []):
            if line.get('from_id') not in overlay_ids or line.get('to_id') not in overlay_ids:
                issues.append(f"[{scene_id}] Infographic line references missing ID.")

    overall_score = sum(scores.values()) / len(scores)
    all_feedback = issues + warnings

    print("\n" + "="*80)
    print(f"📈 FINAL PRODUCTION REPORT: {int(overall_score)}%")
    print("="*80)

    return (len(issues) == 0 and overall_score == 100), int(overall_score), all_feedback

if __name__ == "__main__":
    success, score, feedback = test_manifest_quality(sys.argv[1])
    sys.exit(0 if success else 1)
