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

    # --- ASSET & TYPE REGISTRY (Surgical Validation) ---
    VALID_TYPES = [
        'text', 'ui_panel', 'shape', 'chart', 'indicator', 'data_indicator',
        'graph', 'video', 'image', 'shadcn_chart', 'shadcn_indicator', 'svg'
    ]

    ENGINE_VARIANTS = {
        'shadcn_chart': [
            'glass_area', 'neon_bar', 'stacked_line', 'radial_score', 'radar_web', 'composed_tech',
            'pie_donut_glass', 'scatter_bubble', 'horizontal_pill_bar', 'step_area', 'multi_bar_stack',
            'curved_edge_line', 'double_radar', 'funnel_glass', 'vertical_stepper', 'micro_sparkline',
            'grid_dots', 'smooth_area_dual', 'bar_race_top', 'thick_line_glow', 'layered_pies',
            'range_area', 'pixel_bars', 'curved_scatter', 'staircase_line', 'floating_bars',
            'hollow_pie', 'dual_axis_tech', 'jagged_peak', 'dot_matrix_chart'
        ],
        'shadcn_indicator': [
            'metric_tile', 'tech_badge', 'activity_ring', 'crypto_card', 'server_status',
            'user_profile_stat', 'weather_glass', 'storage_pill', 'upload_cloud', 'score_board',
            'notification_stack', 'data_ticker', 'network_ping', 'step_indicator_glass',
            'battery_pack', 'media_controls', 'social_stats', 'tech_folder', 'system_cpu',
            'location_tag', 'search_bar_glass', 'badge_collection', 'data_download', 'wifi_radar',
            'system_lock', 'clock_modern', 'status_grid', 'floating_icon_text', 'mini_stat_card',
            'activity_dots'
        ],
        'chart': [
            'line', 'area', 'forecast', 'multiLine', 'stackedArea', 'bar', 'horizontalBar',
            'verticalBar', 'groupedBar', 'stackedBar', 'barRace', 'pie', 'donut', 'bump',
            'areaBump', 'heatmap', 'radar', 'radialBar', 'stream', 'swarmplot', 'waffle',
            'funnel', 'marimekko', 'circlePacking', 'calendar', 'parallelCoordinates',
            'voronoi', 'treemap', 'sunburst', 'scatter', 'bubble', 'network', 'chord',
            'sankey', 'boxplot', 'violinPlot'
        ],
        'indicator': [
            'kpi', 'counter', 'kpiNumber', 'percentageCounter', 'comparisonKPI', 'deltaIndicator',
            'timer', 'countdown', 'progressBar', 'circularProgress', 'semiGauge', 'milestoneTracker',
            'dashboardCard', 'timeline', 'milestoneTimeline', 'statGrid', 'techMetric', 'dataWave',
            'scoreCard', 'batteryLevel', 'pulseRadar', 'multiProgress', 'speedometer', 'ringChart',
            'statusBadge', 'metricRing', 'floatingTag', 'stepIndicator'
        ],
        'data_indicator': [
             'kpi', 'counter', 'kpiNumber', 'percentageCounter', 'comparisonKPI', 'deltaIndicator',
            'timer', 'countdown', 'progressBar', 'circularProgress', 'semiGauge', 'milestoneTracker',
            'dashboardCard', 'timeline', 'milestoneTimeline', 'statGrid', 'techMetric', 'dataWave',
            'scoreCard', 'batteryLevel', 'pulseRadar', 'multiProgress', 'speedometer', 'ringChart',
            'statusBadge', 'metricRing', 'floatingTag', 'stepIndicator'
        ],
        'shape': ['circle', 'rect', 'line'],
        'procedural_bg': ['dark_particles', 'liquid_gradient', 'neon_grid']
    }

    VALID_TEXT_HERO_ANIMS = [
        'glow_pulse', 'isolate_zoom', 'bounce_pop', 'neon_flicker', 'shake_alert',
        'rainbow_flow', 'ghost_trail', 'glitch_pop', 'wave_float', 'expand_contract',
        'blur_reveal', 'color_shift', 'rotation_swing', 'shadow_pulse', 'letter_jump',
        'skew_slide', 'tilt_pan', 'bounce_gravity', 'border_glow', 'glass_shimmer',
        'heartbeat', 'strobe_flash', 'threed_flip', 'magnetic_pull', 'fire_glow',
        'pixel_scatter', 'swing_pivot', 'depth_shadow', 'energy_beam', 'spiral_in',
        'fly_in_z', 'typewriter_flicker', 'vibrate_intense', 'float_orbit',
        'mirror_split', 'zoom_blur_pop', 'liquid_waver'
    ]

    # Font Detection
    available_fonts = []
    bangla_fonts = []
    english_fonts = []
    BANGLA_KEYWORDS = ['solaiman', 'kalpurush', 'nikosh', 'hind', 'siliguri', 'adorsho', 'sutonny', 'shonar', 'vrinda', 'bangla', 'liyakats', 'anshu', 'charukola', 'galada', 'mina', 'mukti', 'atreyee', 'benisen', 'bengali', 'shishir', 'shorif', 'maharaj', '_bangla', 'bangla']

    fonts_dir = os.path.join(public_dir, "fonts")
    if os.path.exists(fonts_dir):
        for f in os.listdir(fonts_dir):
            if f.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                name = os.path.splitext(f)[0]
                # Try both original and clean name for availability
                available_fonts.append(name)
                clean_name = re.sub(r'(_english|_bangla)$', '', name, flags=re.IGNORECASE)
                clean_name = re.sub(r'-(Regular|Bold|Italic|Light|Medium|Thin|SemiBold|ExtraBold|Black)$', '', clean_name, flags=re.IGNORECASE)
                available_fonts.append(clean_name)

                if any(kw in name.lower() for kw in BANGLA_KEYWORDS):
                    bangla_fonts.append(name)
                else:
                    english_fonts.append(name)

    available_fonts = list(set(available_fonts))

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
            scores["composition"] -= 20
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
        if scene.get('background_type') == 'procedural':
            bg_var = scene.get('procedural_config', {}).get('variant')
            if bg_var and bg_var not in ENGINE_VARIANTS['procedural_bg']:
                issues.append(f"[{scene_id}] ASSET ERROR: Invalid procedural background variant '{bg_var}'. Valid: {ENGINE_VARIANTS['procedural_bg']}")
                scores["assets"] -= 10

        overlay_ids = set()
        placed_geometries = []
        prev_ov_id = None
        prev_start = -1

        for ov_idx, ov in enumerate(overlays):
            ov_id = ov.get('id', f'overlay_{ov_idx}')
            overlay_ids.add(ov_id)
            o_type = str(ov.get('type', 'text')).lower()
            if o_type not in VALID_TYPES:
                issues.append(f"[{scene_id}] TYPE ERROR: Overlay '{ov_id}' has invalid type '{o_type}'. Valid: {VALID_TYPES}")
                scores["composition"] -= 20

            # Variant Validation
            if o_type in ENGINE_VARIANTS:
                variant_key = 'chart_type' if 'chart' in o_type else 'indicator_type' if 'indicator' in o_type else 'shape_type' if o_type == 'shape' else None
                if variant_key:
                    variant = ov.get(variant_key)
                    if not variant:
                        issues.append(f"[{scene_id}] CONFIG ERROR: Overlay '{ov_id}' of type '{o_type}' is missing '{variant_key}'.")
                        scores["assets"] -= 25 # Severe penalty for missing key config
                    elif variant not in ENGINE_VARIANTS[o_type]:
                        issues.append(f"[{scene_id}] CONFIG ERROR: Overlay '{ov_id}' variant '{variant}' is invalid for type '{o_type}'. Valid: {ENGINE_VARIANTS[o_type]}")
                        scores["assets"] -= 20
                    else:
                        # Deep Validation of specific fields per variant
                        variant_error = False
                        if variant == 'milestoneTracker' and 'milestones' not in ov:
                            issues.append(f"[{scene_id}] DATA ERROR: '{ov_id}' ({variant}) requires 'milestones' array.")
                            variant_error = True
                        elif variant in ['timeline', 'milestoneTimeline'] and 'events' not in ov and 'milestones' not in ov:
                            issues.append(f"[{scene_id}] DATA ERROR: '{ov_id}' ({variant}) requires 'events' or 'milestones' array.")
                            variant_error = True
                        elif variant == 'statGrid' and 'stats' not in ov:
                            issues.append(f"[{scene_id}] DATA ERROR: '{ov_id}' ({variant}) requires 'stats' array.")
                            variant_error = True
                        elif variant in ['multiProgress', 'ringChart'] and 'items' not in ov and 'rings' not in ov:
                            issues.append(f"[{scene_id}] DATA ERROR: '{ov_id}' ({variant}) requires 'items' or 'rings' array.")
                            variant_error = True
                        elif variant in ['stepIndicator', 'step_indicator_glass'] and 'steps' not in ov:
                            issues.append(f"[{scene_id}] DATA ERROR: '{ov_id}' ({variant}) requires 'steps' array.")
                            variant_error = True
                        elif variant in ['kpi', 'metric_tile'] and 'value' not in ov:
                            warnings.append(f"[{scene_id}] DATA WARNING: '{ov_id}' ({variant}) should have a 'value'.")
                            scores["assets"] -= 5

                        if variant_error:
                            scores["assets"] -= 20

            # Typography & Font Validation
            if o_type in ['text', 'shadcn_chart', 'shadcn_indicator', 'chart', 'indicator', 'data_indicator', 'ui_panel']:
                font = ov.get('font')
                content = str(ov.get('content', ov.get('text', ov.get('label', ov.get('title', '')))))
                is_bangla = any('\u0980' <= c <= '\u09FF' for c in content)

                if not font:
                    issues.append(f"[{scene_id}] FONT ERROR: Overlay '{ov_id}' is missing 'font' field.")
                    scores["typography"] -= 10
                elif font not in available_fonts:
                    # Special check for system fallbacks or generic families
                    if font not in ['Inter', 'Arial', 'sans-serif', 'serif', 'monospace']:
                        issues.append(f"[{scene_id}] FONT ERROR: Overlay '{ov_id}' uses font '{font}' which is NOT in /public/fonts. Valid: {available_fonts}")
                        scores["typography"] -= 15
                    else:
                        warnings.append(f"[{scene_id}] FONT WARNING: Overlay '{ov_id}' uses generic font '{font}'. Use local production fonts like {available_fonts[:3]} instead.")
                        scores["typography"] -= 5

                # Language consistency check
                if is_bangla and bangla_fonts and font not in bangla_fonts:
                    warnings.append(f"[{scene_id}] FONT WARNING: Overlay '{ov_id}' has Bangla content but font '{font}' might not support it. Use: {bangla_fonts}")
                    scores["typography"] -= 5
                elif not is_bangla and english_fonts and font in bangla_fonts:
                    warnings.append(f"[{scene_id}] FONT WARNING: Overlay '{ov_id}' has English content but uses Bangla font '{font}'. Use: {english_fonts}")
                    scores["typography"] -= 5

            if o_type == 'text':
                hero = ov.get('hero_config', {})
                h_anim = hero.get('animation')
                if h_anim and h_anim not in VALID_TEXT_HERO_ANIMS:
                    issues.append(f"[{scene_id}] ANIMATION ERROR: Text '{ov_id}' hero animation '{h_anim}' is invalid. Valid: {VALID_TEXT_HERO_ANIMS[:5]}...")
                    scores["typography"] -= 10

                h_word = str(hero.get('word', '')).replace('[.।]', '')
                content = str(ov.get('content', '')).replace('[.।]', '')
                if h_word and h_word not in content:
                    warnings.append(f"[{scene_id}] SYNC WARNING: Hero word '{h_word}' not found in content of '{ov_id}'. Reveal animation might skip.")
                    scores["typography"] -= 5

            start = int(ov.get('start', 0))

            # 2.1 detailed SYNC ORDER Check
            if prev_start != -1 and start < prev_start:
                msg = f"[{scene_id}] SYNC ORDER ERROR: Overlay '{ov_id}' (start={start}) appears AFTER '{prev_ov_id}' (start={prev_start}) in the array. Fx: Increase '{ov_id}.start' to >= {prev_start} or move '{ov_id}' earlier in the array."
                issues.append(msg)
                scores["timing"] -= 15

            prev_start = start
            prev_ov_id = ov_id

            if start < 0 or start >= duration:
                issues.append(f"[{scene_id}] TIMING ERROR: Overlay '{ov_id}' field 'start'={start} is invalid. Scene duration is {duration}. Fix: set 'start' between 0 and {duration-1}.")
                scores["timing"] -= 10

            pos = ov.get('position', {})
            x, y = pos.get('x', 960), pos.get('y', 540)

            # Center Stacking (Bypass for motion tracked elements)
            if not ov.get('tracking', {}).get('enabled'):
                if (abs(x - 960) < 20 and (abs(y - 540) < 20 or abs(y - 700) < 20)):
                    msg = f"[{scene_id}] GEOMETRY ERROR: Overlay '{ov_id}' is generic-centered at ({x}, {y}). Fix: Use Rule of Thirds anchors like (550, 540) or (1370, 540) to avoid center-stacking."
                    issues.append(msg)
                    scores["composition"] -= 15

            base_w, base_h = TYPE_SIZES.get(o_type, (600, 400))
            w, h = ov.get('width', base_w), ov.get('height', base_h)

            if o_type == 'text':
                fs_match = re.search(r'\d+', str(ov.get('fontSize', '120')))
                fs = int(fs_match.group()) if fs_match else 120
                min_fs = MIN_CONSTRAINTS['hero_fontSize'] if str(ov.get('importance','')).lower() == 'hero' else MIN_CONSTRAINTS['fontSize']
                if fs < min_fs:
                    issues.append(f"[{scene_id}] TYPOGRAPHY ERROR: Text '{ov_id}' fontSize {fs}px is too small. Minimum required for {ov.get('importance','primary')} text is {min_fs}px.")
                    scores["typography"] -= 20
                w, h = min(ov.get('maxWidth', 1600), len(str(ov.get('content',''))) * fs * 0.7), fs * 1.5

            l, t, r, b = x - w/2, y - h/2, x + w/2, y + h/2
            if l < 0 or r > 1920 or t < 0 or b > 1080:
                off_desc = []
                if l < 0: off_desc.append(f"left by {abs(l)}px")
                if r > 1920: off_desc.append(f"right by {r-1920}px")
                if t < 0: off_desc.append(f"top by {abs(t)}px")
                if b > 1080: off_desc.append(f"bottom by {b-1080}px")
                issues.append(f"[{scene_id}] OFFSCREEN ERROR: Overlay '{ov_id}' is out of bounds on {' and '.join(off_desc)}. Calculated Box: [L:{int(l)}, T:{int(t)}, R:{int(r)}, B:{int(b)}]. Fix: Move position away from edges.")
                scores["layout"] -= 25
            elif o_type not in ['ambient_graphic', 'background'] and (l < 150 or r > 1770 or t < 150 or b > 930):
                warnings.append(f"[{scene_id}] MARGIN WARNING: Overlay '{ov_id}' violates 150px safety zone. Box: [L:{int(l)}, T:{int(t)}, R:{int(r)}, B:{int(b)}]. Suggest moving towards center.")
                scores["composition"] -= 5

            for p_id, p_l, p_t, p_r, p_b, p_s, p_e, p_imp in placed_geometries:
                # Check for temporal overlap first
                ov_dur = ov.get('duration', duration - start)
                if max(start, p_s) < min(start + ov_dur, p_e):
                    if str(ov.get('importance','')).lower() in ['hero','secondary'] and p_imp in ['background','ambient']: continue
                    gap = MIN_CONSTRAINTS['min_spacing']
                    if not (r + gap < p_l or l - gap > p_r or b + gap < p_t or t - gap > p_b):
                        # Surgical Collision Feedback
                        suggested_anchor = "(550, 320)" if x > 960 else "(1370, 760)"
                        issues.append(f"[{scene_id}] GEOMETRY COLLISION: Overlay '{ov_id}' at ({int(x)}, {int(y)}) overlaps with '{p_id}'. Fix: Move '{ov_id}' to a remote anchor like {suggested_anchor} or adjust timing so they don't appear at once.")
                        scores["collision"] -= 30
            placed_geometries.append((ov_id, l, t, r, b, start, start + ov.get('duration', duration - start), str(ov.get('importance','')).lower()))

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
                scores["composition"] -= 15

    overall_score = sum(scores.values()) / len(scores)
    all_feedback = issues + warnings

    print("\n" + "="*80)
    print(f"📈 FINAL PRODUCTION REPORT: {int(overall_score)}%")
    print("="*80)

    return (len(issues) == 0 and overall_score == 100), int(overall_score), all_feedback

if __name__ == "__main__":
    success, score, feedback = test_manifest_quality(sys.argv[1])
    sys.exit(0 if success else 1)
