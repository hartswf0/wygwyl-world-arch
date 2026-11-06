#!/usr/bin/env python3
"""Standalone handmade builder for PAE-W05 · Poem 05 (Bloodlines) · SCION-018 · CARTOON SALOON PAINTERLY GOUACHE & SACRED LINE."""
import os, sys
sys.path.insert(0, "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots/data/terrarium")
import run_wygwyl_paeleo_swarms as R

if __name__ == "__main__":
    R.build_scores_json()
    spec = [s for s in R.POEM_SWARM_SPECS if s["num"] == 5][0]
    R.build_single_poem_swarm(spec)
