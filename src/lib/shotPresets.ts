import { Easing } from 'remotion';

export interface ShotPreset {
    startZoom?: number;
    endZoomOffset?: number;
    rotationX?: number;
    rotationY?: number;
    rotationZ?: number;
    zOffset?: number;
    easing?: string | { type: 'bezier'; bezier: [number, number, number, number] };
}

export const SHOT_PRESETS: Record<string, ShotPreset> = {
    push_in: { startZoom: 0.85 },
    slow_push: { startZoom: 0.85 },
    pull_out: { startZoom: 1.15 },
    slow_pull: { startZoom: 1.15 },
    whip_pan: { easing: { type: 'bezier', bezier: [1, 0, 0, 1] } },
    dramatic_reveal: {
        startZoom: 1.5,
        easing: { type: 'bezier', bezier: [0.16, 1, 0.3, 1] },
        rotationX: 25,
        rotationY: -15,
        zOffset: -200,
    },
    cinematic_drift: { rotationZ: 2, rotationX: 3 },
    dynamic_orbit: { rotationY: 15, rotationX: 5 },
    vertical_sweep: { rotationX: -20 },
    spiral_vortex: { rotationZ: 45, startZoom: 0.5 },
    glitch_snap: {
        easing: { type: 'bezier', bezier: [0.1, 0.9, 0.2, 1] },
        rotationZ: -5,
    },
    low_angle_hero: { rotationX: -35, zOffset: 100 },
    side_strafe_left: { rotationY: -20 },
    side_strafe_right: { rotationY: 20 },
    aerial_top_down: { rotationX: 70, startZoom: 0.7 },
    shaky_handheld: { rotationZ: 3, rotationX: 2, rotationY: 2 },
    zoom_blur_reveal: {
        startZoom: 0.1,
        easing: { type: 'bezier', bezier: [0.4, 0, 0.2, 1] },
    },
    tilt_shift_focus: { rotationX: 15, rotationY: 15 },
    power_zoom: {
        startZoom: 0.4,
        easing: { type: 'bezier', bezier: [0.85, 0, 0.15, 1] },
    },
    smooth_glide: { rotationZ: -1, rotationY: -5 },
    epic_scaling: { startZoom: 0.5, endZoomOffset: 1.2 },
    warp_speed: { zOffset: -1000, startZoom: 0.5 },
    rolling_horizon: {
        rotationZ: -90,
        easing: { type: 'bezier', bezier: [0.6, -0.28, 0.735, 0.045] },
    },
    fisheye_distort: { startZoom: 1.8, rotationX: 10 },
    dolly_zoom: { startZoom: 2, zOffset: 500 },
    parallax_slide: { rotationY: 40, zOffset: -300 },
    staccato_jump: { easing: { type: 'bezier', bezier: [0, 1, 0, 1] } },
    oblique_view: { rotationX: 20, rotationY: 20, rotationZ: 10 },
    macro_focus: { startZoom: 1.4 },
    uprising_reveal: { rotationX: -60, zOffset: -500 },
    descending_gaze: { rotationX: 60, zOffset: 500 },
    infinity_loop: { rotationZ: 360, rotationY: 30 },
    kaleidoscope: { rotationZ: 180, rotationX: 20, rotationY: 20 },
    cyber_scan: { rotationY: -45, rotationX: 10 },
    extreme_closeup: { startZoom: 3 },
    wide_panorama: { startZoom: 0.3 },
    pendulum_swing: { rotationZ: -30, rotationY: 15 },
    drunken_stumble: { rotationZ: 10, rotationX: 10, rotationY: 10 },
    floating_weightless: { rotationX: 5, rotationY: 5, rotationZ: 5 },
    rapid_fire: { easing: 'bounce' },
    gentle_breeze: { rotationZ: 0.5, rotationY: 1 },
    the_matrix: { rotationY: 90, startZoom: 0.5 },
    heartbeat_zoom: { easing: 'elastic' },
};
