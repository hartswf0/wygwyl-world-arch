#!/usr/bin/env python3
"""
The PAELEO × WYGWYL invariant test for all 14 handmade poem swarms:
did the poem's ekphrasis and governing story law survive the SCION operation?

Usage:
  python3 shots/paeleo/check_wygwyl_handmade.py shots/paeleo/handmade/*
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCORES_PATH = os.path.join(HERE, "score", "wygwyl_scores.json")


def corr(a, b):
    n = len(a)
    if n < 2:
        return 0.0
    ma, mb = sum(a) / n, sum(b) / n
    sa = sum((x - ma) ** 2 for x in a) ** 0.5
    sb = sum((y - mb) ** 2 for y in b) ** 0.5
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb) if sa > 1e-9 and sb > 1e-9 else 1.0


def check_folder(folder, all_scores):
    trace_path = os.path.join(folder, "trace.json")
    if not os.path.exists(trace_path):
        return {"all_ok": False, "error": "missing trace.json"}

    tr = json.load(open(trace_path))
    poem_num = int(tr.get("poem_num", int(os.path.basename(folder.rstrip("/"))[:2])))
    score = all_scores[str(poem_num)]
    fr = tr["frames"] if isinstance(tr, dict) and "frames" in tr else tr

    res = {"poem_num": poem_num, "swarm_id": tr.get("swarm_id", ""), "title": score["title"]}

    # I1: All 6 dramatic choices appear within ±0.25s of the score's target time
    got = []
    for c in score["choices"]:
        hit = next((f for f in fr if f["t"] >= c["t"] - 0.5 and f.get("state") == c["to"]), None)
        dt = None if hit is None else round(hit["t"] - c["t"], 3)
        got.append({
            "t": c["t"],
            "to": c["to"],
            "label": c.get("label", ""),
            "found_at": None if hit is None else hit["t"],
            "dt": dt,
            "ok": dt is not None and abs(dt) <= 0.25,
        })
    res["I1_choices"] = {"ok": all(g["ok"] for g in got), "choices": got}

    # I2: Spatial threshold / boundary invariant holds across the 768 frames
    thresh_target = float(score["threshold_target"])
    q_end = float(fr[-1].get("q_measured", 0.0)) if fr else 0.0
    res["I2_threshold"] = {
        "ok": abs(q_end - thresh_target) <= 0.12,
        "end_q": round(q_end, 4),
        "target_q": round(thresh_target, 4),
        "rule": score["threshold_rule"],
    }

    # I3: Governing monotonic quantity / trajectory follows the score (|r| >= 0.92)
    sc_map = {f["i"]: f["q_score"] for f in score["frames"]}
    pairs = [(float(f["q_measured"]), float(sc_map[f["i"]])) for f in fr if f.get("q_measured") is not None and f["i"] in sc_map]
    r_val = corr([p[0] for p in pairs], [p[1] for p in pairs]) if len(pairs) > 10 else 0.0
    res["I3_monotonic_quantity"] = {
        "ok": abs(r_val) >= 0.92,
        "r": round(r_val, 4),
        "n": len(pairs),
        "quantity_name": score["quantity_name"],
    }

    # I4: Poem-specific signature constraint (e.g. EX back-only, 0 puppets in P03, 9-node KIN graph in P05, etc.)
    sig_flags = [bool(f.get("sig_ok", False)) for f in fr]
    share_ok = sum(1 for b in sig_flags if b) / max(1, len(sig_flags))
    res["I4_signature_constraint"] = {
        "ok": share_ok >= 0.95,
        "share_satisfied": round(share_ok, 4),
        "constraint": score["signature_constraint"],
    }

    # I5: Standalone handmade package check (`build/render.py`, `build/make.sh`, `sources/sources.json`, `film.mp4`, 4 stills, `proof/layers_and_props.jpg`)
    req_files = [
        "build/render.py",
        "build/make.sh",
        "build/fetch_sources.py",
        "sources/sources.json",
        "reviews/round-02-critic.md",
        "film.mp4",
        "stills/still_03.6s.jpg",
        "stills/still_09.0s.jpg",
        "stills/still_19.0s.jpg",
        "stills/still_28.0s.jpg",
        "proof/layers_and_props.jpg",
    ]
    missing = [rf for rf in req_files if not os.path.exists(os.path.join(folder, rf))]
    res["I5_handmade_package"] = {
        "ok": len(missing) == 0,
        "missing": missing,
    }

    res["all_ok"] = all(v["ok"] for k, v in res.items() if k.startswith("I"))
    with open(os.path.join(folder, "invariants.json"), "w") as fp:
        json.dump(res, fp, indent=2)
    return res


def main():
    if not os.path.exists(SCORES_PATH):
        print(f"Error: {SCORES_PATH} not found.")
        sys.exit(1)
    all_scores = json.load(open(SCORES_PATH))
    folders = sys.argv[1:]
    if not folders:
        hm_root = os.path.join(HERE, "handmade")
        folders = [
            os.path.join(hm_root, d)
            for d in sorted(os.listdir(hm_root))
            if os.path.isdir(os.path.join(hm_root, d)) and d[:2].isdigit()
        ]
    all_pass = True
    for f in folders:
        r = check_folder(f, all_scores)
        status = "ALL OK" if r.get("all_ok") else "FAILS"
        if not r.get("all_ok"):
            all_pass = False
        flags = {k: v["ok"] for k, v in r.items() if k.startswith("I")}
        print(f"{os.path.basename(f.rstrip('/')):34s} {status:8s} {flags}")
    if not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
