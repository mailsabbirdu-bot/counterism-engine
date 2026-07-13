import json
import sys
import os
import re

def test_manifest_quality(filepath, public_dir=None):
    """
    v3.0 Machine-Actionable QA suite for Studio V4 manifests.
    Provides structured feedback, severity levels, and explicit repair values.
    Returns: (success, score, issues)
    """
    print(f"\n" + "="*80)
    print(f"🎬 STUDIO V4 PRODUCTION QA (v3.0): {os.path.basename(filepath)}")
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

    all_feedback = [] # List of structured finding dicts

    # Severity Definitions
    S_CRITICAL = "CRITICAL" # Structural failure, data corruption
    S_ERROR = "ERROR"       # Rule violation, invalid variant
    S_WARNING = "WARNING"   # Aesthetic issue, margin violation
    S_INFO = "INFO"         # Minor optimization

    # Rule of Thirds Anchors (Synced with logic)
    ANCHORS = {
        "L_TOP": (550, 320), "C_TOP": (960, 320), "R_TOP": (1370, 320),
        "L_MID": (550, 540), "C_MID": (960, 540), "R_MID": (1370, 540),
        "L_BOT": (550, 760), "C_BOT": (960, 760), "R_BOT": (1370, 760)
    }

    # --- ASSET & TYPE REGISTRY (Surgical Validation) ---
    VALID_TYPES = [
        'text', 'ui_panel', 'shape', 'chart', 'indicator', 'data_indicator',
        'graph', 'video', 'image', 'shadcn_chart', 'shadcn_indicator', 'svg', 'connector',
        'hub_network', 'flow_diagram', 'process', 'kpi_card', 'timeline', 'compositions', 'groups',
        'ambient_graphic', 'callout', 'label', 'crve'
    ]

    ENGINE_VARIANTS = {
        'connector': [
            'smooth_curve', 'soft_arc', 'straight_flow', 'energy_flow', 'signal_beam',
            'data_stream', 's_curve', 'zigzag_soft', 'multi_branch', 'network_web',
            'callout_line', 'camera_focus', 'timeline_path', 'route_path', 'curved_route',
            'neon_connector', 'blueprint_connector', 'organic_connector'
        ],
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
        'mirror_split', 'zoom_blur_pop', 'liquid_waver', 'wordReveal', 'glassReveal'
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
        "typography": 100,
        "structure": 100
    }

    # --- ROOT STRUCTURE VALIDATION ---
    if 'global_settings' not in data:
        all_feedback.append({"severity": S_CRITICAL, "msg": "Missing 'global_settings' at root.", "category": "structure"})
        scores["structure"] -= 50
    else:
        gs = data['global_settings']
        for field in ['width', 'height', 'fps']:
            if field not in gs:
                all_feedback.append({"severity": S_CRITICAL, "msg": f"'global_settings' missing required field '{field}'.", "category": "structure"})
                scores["structure"] -= 20

    if 'project_id' not in data and 'project_name' not in data:
        all_feedback.append({"severity": S_WARNING, "msg": "Missing 'project_id' at root.", "category": "structure"})
        scores["structure"] -= 5

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
            all_feedback.append({"scene": scene_id, "severity": S_CRITICAL, "msg": "Duplicate scene_id detected.", "category": "logic"})
            scores["composition"] -= 20
        all_scene_ids.add(scene_id)

        # Reading Order & Sequencing
        beats = scene.get('beats', [])
        if not beats:
            all_feedback.append({"scene": scene_id, "severity": S_WARNING, "msg": "Missing 'beats' array for visual sequencing.", "category": "timing"})
            scores["timing"] -= 5

        if not scene.get('transition'):
            all_feedback.append({"scene": scene_id, "severity": S_WARNING, "msg": "Missing 'transition' object.", "category": "composition"})
            scores["composition"] -= 5

        duration = scene.get('duration_in_frames', 180)
        if 'duration' in scene:
            all_feedback.append({
                "scene": scene_id, "severity": S_ERROR,
                "msg": "Redundant 'duration' key found. Use 'duration_in_frames'.",
                "patch": {"_delete": ["duration"]},
                "category": "schema"
            })
            scores["timing"] -= 5

        overlays = scene.get('overlays', [])
        connections = scene.get('connections', [])
        has_connector = any(str(o.get('type', '')).lower() == 'connector' for o in overlays)
        if has_connector and not connections:
            all_feedback.append({"scene": scene_id, "severity": S_WARNING, "msg": "Scene has connectors but empty 'connections' array.", "category": "logic"})
            scores["composition"] -= 10

        # 1. Asset Verification
        if scene.get('background_type') == 'video':
            vpath = scene.get('video_path', '')
            if vpath:
                rel_vpath = vpath.replace('renders/', '') if vpath.startswith('renders/') else vpath
                abs_vpath = os.path.join(public_dir, "renders", rel_vpath.lstrip('/'))
                if not os.path.exists(abs_vpath):
                    all_feedback.append({"scene": scene_id, "severity": S_CRITICAL, "msg": f"Video asset missing: '{vpath}'", "category": "assets"})
                    scores["assets"] -= 20
                else:
                    print(f"   ✅ ASSETS: Video verified.")

        # 2. Timing
        if duration <= 0:
            all_feedback.append({"scene": scene_id, "severity": S_CRITICAL, "msg": f"Invalid scene duration: {duration}", "category": "timing"})
            scores["timing"] -= 50

        # 3. Overlay Validation
        if scene.get('background_type') == 'procedural':
            bg_var = scene.get('procedural_config', {}).get('variant')
            if bg_var and bg_var not in ENGINE_VARIANTS['procedural_bg']:
                all_feedback.append({"scene": scene_id, "severity": S_ERROR, "msg": f"Invalid procedural bg variant '{bg_var}'.", "category": "assets"})
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
                all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_ERROR, "msg": f"Invalid type '{o_type}'.", "category": "schema"})
                scores["composition"] -= 20

            # Redundant Typography/Z-index check
            if 'size' in ov:
                all_feedback.append({
                    "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                    "msg": "Redundant 'size' key found. Use 'fontSize'.",
                    "patch": {"_delete": ["size"]},
                    "category": "schema"
                })
                scores["typography"] -= 5
            if 'z_index' in ov:
                all_feedback.append({
                    "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                    "msg": "Redundant 'z_index' key found. Use 'zIndex'.",
                    "patch": {"_delete": ["z_index"]},
                    "category": "composition"
                })
                scores["composition"] -= 5
            if 'variant' in ov:
                all_feedback.append({
                    "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                    "msg": "Redundant 'variant' key found. Use specific variant keys (e.g. 'chart_type').",
                    "patch": {"_delete": ["variant"]},
                    "category": "schema"
                })
                scores["assets"] -= 5

            # Media Asset Verification
            if o_type in ['video', 'image']:
                src = ov.get('src')
                if not src:
                    all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_ERROR, "msg": "Missing 'src' path.", "category": "assets"})
                    scores["assets"] -= 20
                else:
                    rel_src = src.replace('renders/', '') if src.startswith('renders/') else src
                    abs_src = os.path.join(public_dir, "renders", rel_src.lstrip('/'))
                    if not os.path.exists(abs_src):
                        all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_WARNING, "msg": f"Asset missing: '{src}'", "category": "assets"})
                        scores["assets"] -= 10

            # Variant Validation
            if o_type in ENGINE_VARIANTS:
                variant_key = 'chart_type' if 'chart' in o_type else 'indicator_type' if 'indicator' in o_type else 'shape_type' if o_type == 'shape' else None
                if variant_key:
                    variant = ov.get(variant_key)
                    if not variant:
                        # Patch: Assign default variant
                        default_v = ENGINE_VARIANTS[o_type][0]
                        all_feedback.append({
                            "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                            "msg": f"Missing '{variant_key}'.",
                            "patch": {variant_key: default_v},
                            "category": "schema"
                        })
                        scores["assets"] -= 25
                    elif variant not in ENGINE_VARIANTS[o_type]:
                        # Patch: Map to nearest or first valid variant
                        suggested_v = ENGINE_VARIANTS[o_type][0]
                        for v in ENGINE_VARIANTS[o_type]:
                            if v in variant or variant in v: suggested_v = v; break

                        all_feedback.append({
                            "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                            "msg": f"Invalid variant '{variant}' for type '{o_type}'. Valid: {ENGINE_VARIANTS[o_type]}",
                            "patch": {variant_key: suggested_v},
                            "category": "schema"
                        })
                        scores["assets"] -= 20
                    else:
                        # Deep Validation with Patches
                        if variant == 'milestoneTracker' and 'milestones' not in ov:
                            all_feedback.append({
                                "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                                "msg": f"Variant '{variant}' requires 'milestones' array.",
                                "patch": {"milestones": [{"label": "Initiated", "date": "Start"}]},
                                "category": "data"
                            })
                            scores["assets"] -= 20
                        elif variant in ['timeline', 'milestoneTimeline'] and 'events' not in ov and 'milestones' not in ov:
                            all_feedback.append({
                                "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                                "msg": f"Variant '{variant}' requires 'events' array.",
                                "patch": {"events": [{"title": "Initial Event", "date": "T-0", "description": "Sequence started"}]},
                                "category": "data"
                            })
                            scores["assets"] -= 20
                        elif variant == 'statGrid' and 'stats' not in ov:
                            all_feedback.append({
                                "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                                "msg": f"Variant '{variant}' requires 'stats' array.",
                                "patch": {"stats": [{"label": "Metric", "value": 100, "suffix": "%"}]},
                                "category": "data"
                            })
                            scores["assets"] -= 20
                        elif variant in ['multiProgress', 'ringChart'] and 'items' not in ov and 'rings' not in ov:
                            all_feedback.append({
                                "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                                "msg": f"Variant '{variant}' requires 'items' array.",
                                "patch": {"items": [{"label": "Primary", "value": 85, "color": "#00F5FF"}]},
                                "category": "data"
                            })
                            scores["assets"] -= 20
                        elif variant in ['stepIndicator', 'step_indicator_glass'] and 'steps' not in ov:
                            all_feedback.append({
                                "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                                "msg": f"Variant '{variant}' requires 'steps' array.",
                                "patch": {"steps": ["Step 1", "Step 2", "Step 3"]},
                                "category": "data"
                            })
                            scores["assets"] -= 20

            # Typography & Font Validation
            if o_type in ['text', 'shadcn_chart', 'shadcn_indicator', 'chart', 'indicator', 'data_indicator', 'ui_panel']:
                # Import here to avoid dependency issues for standalone script
                try:
                    from remotion_jsonMaker.perception_logic import VisionConstants
                    is_bangla_func = VisionConstants.is_bangla
                except:
                    is_bangla_func = lambda t: any('\u0980' <= c <= '\u09FF' for c in str(t))

                font = ov.get('font')
                content = str(ov.get('content', ov.get('text', ov.get('label', ov.get('title', '')))))
                is_bangla = is_bangla_func(content)

                if not font:
                    all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_ERROR, "msg": "Missing 'font' field.", "category": "typography"})
                    scores["typography"] -= 10
                elif font not in available_fonts:
                    if font not in ['Inter', 'Arial', 'sans-serif', 'serif', 'monospace']:
                        # PRODUCTION: Fallback to logic defaults if fonts are missing in public/fonts
                        suggested = bangla_fonts[0] if (is_bangla and bangla_fonts) else (english_fonts[0] if (not is_bangla and english_fonts) else None)
                        if not suggested:
                            suggested = "Sohid_bangla" if is_bangla else "Audiowide-Regular_english"

                        all_feedback.append({
                            "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                            "msg": f"Font '{font}' is NOT in /public/fonts.",
                            "patch": {"font": suggested},
                            "category": "typography"
                        })
                        scores["typography"] -= 15
                    else:
                        suggested = bangla_fonts[0] if (is_bangla and bangla_fonts) else (english_fonts[0] if (not is_bangla and english_fonts) else None)
                        if not suggested:
                            suggested = "Sohid_bangla" if is_bangla else "Audiowide-Regular_english"

                        all_feedback.append({
                            "scene": scene_id, "id": ov_id, "severity": S_WARNING,
                            "msg": f"Uses generic font '{font}'.",
                            "patch": {"font": suggested},
                            "category": "typography"
                        })
                        scores["typography"] -= 5

                # Language consistency
                if is_bangla and bangla_fonts and font not in bangla_fonts:
                    all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_INFO, "msg": f"Font '{font}' sub-optimal for Bangla. Suggested: '{bangla_fonts[0]}'.", "category": "typography"})
                    scores["typography"] -= 2
                elif not is_bangla and english_fonts and font in bangla_fonts:
                    all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_INFO, "msg": f"Font '{font}' sub-optimal for English. Suggested: '{english_fonts[0]}'.", "category": "typography"})
                    scores["typography"] -= 2

            if o_type == 'text':
                hero = ov.get('hero_config', {})
                h_anim = hero.get('animation')
                if h_anim and h_anim not in VALID_TEXT_HERO_ANIMS:
                    all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_ERROR, "msg": f"Invalid hero animation '{h_anim}'. Valid: {VALID_TEXT_HERO_ANIMS[:5]}...", "category": "motion"})
                    scores["typography"] -= 10

                h_word = str(hero.get('word', '')).replace('[.।]', '')
                content = str(ov.get('content', '')).replace('[.।]', '')
                if h_word and h_word not in content:
                    all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_WARNING, "msg": f"Hero word '{h_word}' not in content. Sugggested: Update 'word' to one of: {content.split()[:5]}", "category": "logic"})
                    scores["typography"] -= 5

            start = int(ov.get('start', 0))

            # 2.1 detailed SYNC ORDER Check (Strict Chronological Enforcement)
            if prev_start != -1 and start < prev_start:
                all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_ERROR, "msg": f"Incorrect array order (start={start}) vs prev {prev_ov_id} (start={prev_start}). Fix: Sort overlays array by 'start' time.", "category": "timing"})
                scores["timing"] -= 25

            prev_start = start
            prev_ov_id = ov_id

            if start < 0 or start >= duration:
                all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_ERROR, "msg": f"Invalid 'start'={start} (Scene dur: {duration}). Fix: Set start between 0 and {duration-1}.", "category": "timing"})
                scores["timing"] -= 10

            pos = ov.get('position', {})
            x, y = pos.get('x', 960), pos.get('y', 540)

            # Center Stacking (Bypass for motion tracked elements)
            if not ov.get('tracking', {}).get('enabled'):
                if (abs(x - 960) < 20 and (abs(y - 540) < 20 or abs(y - 700) < 20)):
                    all_feedback.append({
                        "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                        "msg": f"Generic center detected at ({x}, {y}).",
                        "patch": {"position": {"x": 1370, "y": 540}},
                        "category": "composition"
                    })
                    scores["composition"] -= 15

            base_w, base_h = TYPE_SIZES.get(o_type, (600, 400))
            w, h = ov.get('width', base_w), ov.get('height', base_h)

            if o_type == 'text':
                fs_match = re.search(r'\d+', str(ov.get('fontSize', '120')))
                fs = int(fs_match.group()) if fs_match else 120
                min_fs = MIN_CONSTRAINTS['hero_fontSize'] if str(ov.get('importance','')).lower() == 'hero' else MIN_CONSTRAINTS['fontSize']
                if fs < min_fs:
                    all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_ERROR, "msg": f"fontSize {fs}px too small (min {min_fs}px).", "patch": {"fontSize": f"{min_fs}px"}, "category": "typography"})
                    scores["typography"] -= 20
                w, h = min(ov.get('maxWidth', 1600), len(str(ov.get('content',''))) * fs * 0.7), fs * 1.5

            l, t, r, b = x - w/2, y - h/2, x + w/2, y + h/2
            if l < 0 or r > 1920 or t < 0 or b > 1080:
                all_feedback.append({"scene": scene_id, "id": ov_id, "severity": S_CRITICAL, "msg": f"Offscreen! Box: [L:{int(l)}, T:{int(t)}, R:{int(r)}, B:{int(b)}]. Move to Rule of Thirds anchor.", "patch": {"position": {"x": 960, "y": 540}}, "category": "layout"})
                scores["layout"] -= 25
            elif o_type not in ['ambient_graphic', 'background'] and (l < 150 or r > 1770 or t < 150 or b > 930):
                # Deterministic patch for safety margin: move to nearest Rule of Thirds anchor
                target_x = 550 if x < 960 else 1370
                target_y = 540 if abs(y-540) < abs(y-320) and abs(y-540) < abs(y-760) else (320 if y < 540 else 760)

                all_feedback.append({
                    "scene": scene_id, "id": ov_id, "severity": S_WARNING,
                    "msg": f"Safety margin violation. Box: [L:{int(l)}, T:{int(t)}, R:{int(r)}, B:{int(b)}]. Move to ({target_x}, {target_y}).",
                    "patch": {"position": {"x": target_x, "y": target_y}},
                    "category": "composition"
                })
                scores["composition"] -= 5

            for p_id, p_l, p_t, p_r, p_b, p_s, p_e, p_imp in placed_geometries:
                # Check for temporal overlap first
                ov_dur = ov.get('duration', duration - start)
                if max(start, p_s) < min(start + ov_dur, p_e):
                    if str(ov.get('importance','')).lower() in ['hero','secondary'] and p_imp in ['background','ambient']: continue
                    gap = MIN_CONSTRAINTS['min_spacing']
                    if not (r + gap < p_l or l - gap > p_r or b + gap < p_t or t - gap > p_b):
                        # Surgical Collision Feedback
                        suggested_x = 550 if x > 960 else 1370
                        all_feedback.append({
                            "scene": scene_id, "id": ov_id, "severity": S_ERROR,
                            "msg": f"Collision with '{p_id}'.",
                            "patch": {"position": {"x": suggested_x, "y": y}},
                            "category": "layout"
                        })
                        scores["collision"] -= 30
            placed_geometries.append((ov_id, l, t, r, b, start, start + ov.get('duration', duration - start), str(ov.get('importance','')).lower()))

        # 4. Camera & Lines
        camera = scene.get('camera', {})
        shots = camera.get('shots', [])
        if not shots:
            all_feedback.append({"scene": scene_id, "severity": S_WARNING, "msg": "No camera shots defined.", "category": "camera"})
            scores["camera"] -= 10
        else:
            for s_idx, shot in enumerate(shots):
                target = shot.get('targetId')
                if target and target not in overlay_ids:
                    all_feedback.append({"scene": scene_id, "severity": S_ERROR, "msg": f"Camera shot {s_idx} targets missing ID '{target}'.", "category": "camera"})
                    scores["camera"] -= 20

        for line in scene.get('infographic_lines', []):
            if line.get('from_id') not in overlay_ids or line.get('to_id') not in overlay_ids:
                all_feedback.append({"scene": scene_id, "severity": S_ERROR, "msg": "Infographic line targets missing ID.", "category": "logic"})
                scores["composition"] -= 15

    overall_score = sum(scores.values()) / len(scores)

    # RUTHLESS ACCURACY ENFORCEMENT
    fatal_feedback = [f for f in all_feedback if f['severity'] in [S_CRITICAL, S_ERROR]]
    num_fatal = len(fatal_feedback)
    has_structural = any(f['severity'] == S_CRITICAL or f['category'] == 'data' for f in fatal_feedback)

    if num_fatal > 0:
        overall_score = min(overall_score, 100 - (num_fatal * 10))
        if has_structural: overall_score = min(overall_score, 45)
        else: overall_score = min(overall_score, 75)

    overall_score = max(0, int(overall_score))

    # Structured printing for Gemini parsing (Deduplicated)
    if all_feedback:
        print("\n--- STRUCTURED QA FEEDBACK ---")
        scenes_affected = sorted(list(set(f.get('scene','GLOBAL') for f in all_feedback)))
        for s in scenes_affected:
            s_f = [f for f in all_feedback if f.get('scene') == s]

            # Deduplicate messages in the same scene
            seen_msgs = set()
            unique_f = []
            for f in s_f:
                msg_key = f"{f['severity']}:{f['msg']}"
                if msg_key not in seen_msgs:
                    unique_f.append(f)
                    seen_msgs.add(msg_key)

            print(f"\n[{s}]")
            for f in unique_f:
                prefix = f"[{f['severity']}]"
                target = f" ({f['id']})" if f.get('id') else ""
                patch = f" -> REQUIRED PATCH: {json.dumps(f['patch'])}" if f.get('patch') else ""
                print(f"  {prefix}{target} {f['msg']}{patch}")

    print("\n" + "="*80)
    print(f"📈 FINAL PRODUCTION REPORT: {overall_score}%")
    print("="*80)

    # Return as flat strings for backward compat with generator.py feedback loops
    # Includes machine-actionable patches if available
    str_feedback = []
    for f in all_feedback:
        scene = f.get('scene','GLOBAL')
        target = f" ({f['id']})" if f.get('id') else ""
        fb = f"[{scene}] {f['severity']}:{target} {f['msg']}"
        if f.get('patch'):
            fb += f" -> REQUIRED PATCH: {json.dumps(f['patch'])}"
        str_feedback.append(fb)

    return (num_fatal == 0 and overall_score == 100), overall_score, str_feedback

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/test_manifest_quality.py <manifest_path> [public_dir]")
        sys.exit(1)
    # Add project root to path for internal imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    success, score, feedback = test_manifest_quality(sys.argv[1])
    sys.exit(0 if success else 1)
