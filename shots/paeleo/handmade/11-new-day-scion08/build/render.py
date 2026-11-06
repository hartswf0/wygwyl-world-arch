#!/usr/bin/env python3
"""Standalone handmade builder for PAE-W11 · Poem 11 (New Day) · SCION-008 × SCION-039 · SUTHERLAND SKETCHPAD + TURN LAB MULTIVIEW."""
import os, sys
sys.path.insert(0, "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots/data/terrarium")
import run_wygwyl_paeleo_swarms as R

if __name__ == "__main__":
    R.build_scores_json()
    spec = [s for s in R.POEM_SWARM_SPECS if s["num"] == 11][0]
    R.build_single_poem_swarm(spec)
