"""Python twin of scale.js (same names, same numbers). See scale.js for the rule.

    from scale import px_per_cm_at, foot_y_for_depth, place, part_scale
"""

CORRECTIONS = dict(collar_tuck_cm=0.8, head_brad_up_tab=0.04, knee_above_hem_cm=4.0, wing_to_torso=1.35,
                   reach_top_arm_frac=0.92, far_limb_shade=0.72)


def k_of(ch):
    return ch['height_cm'] / ch['build_height_cm']


def camera_height_cm(st):
    g, s = st['ground'], st['scale']
    return (g['y_px'] - g['horizon_y_px']) / s['px_per_cm_at_ground_line']


def px_per_cm_at(st, y):
    g, s = st['ground'], st['scale']
    return s['px_per_cm_at_ground_line'] * (y - g['horizon_y_px']) / (g['y_px'] - g['horizon_y_px'])


def foot_y_for_depth(st, depth_m):
    g = st['ground']
    return g['horizon_y_px'] + (g['y_px'] - g['horizon_y_px']) * st['scale']['camera_distance_m'] / depth_m


def depth_for_foot_y(st, y):
    g = st['ground']
    return st['scale']['camera_distance_m'] * (g['y_px'] - g['horizon_y_px']) / (y - g['horizon_y_px'])


def place(ch, st, x, y_foot):
    ppc = px_per_cm_at(st, y_foot)
    if not ppc > 0:
        raise ValueError('foot line at or above the horizon: nothing can stand there')
    return dict(x=x, y=y_foot, px_per_cm=ppc, height_px=ch['height_cm'] * ppc, head_top_y=y_foot - ch['height_cm'] * ppc,
                depth_m=depth_for_foot_y(st, y_foot) if st['scale'].get('camera_distance_m') else None, z=y_foot)


def part_scale(part, ch, ppc):
    return ppc * k_of(ch) / part['px_per_cm']


def reach_top_cm(ch):
    p = ch['proportions']
    return p['shoulder_height_cm'] + CORRECTIONS['reach_top_arm_frac'] * (p['upper_arm_cm'] + p['forearm_cm'])


def prop_scale(ch, owner, ref_leg_cm=88.4):
    return 1.0 if owner == 'set' else ch['proportions']['leg_cm'] / ref_leg_cm


def height_ratio(a, b):
    return a['height_cm'] / b['height_cm']


def check_placed(ch, st, y_foot, measured_height_px, tol_pct=3.0):
    want = ch['height_cm'] * px_per_cm_at(st, y_foot)
    err = 100 * (measured_height_px / want - 1)
    return dict(want_px=want, err_pct=err, ok=abs(err) <= tol_pct)
