#!/usr/bin/env python3
"""Standalone handmade builder for PAE-W03 · Poem 03 (How to Break Off an Engagement) · SCION-049 · OPEN-CONTENT ATELIER & RELIC STAGE."""
import os, sys
sys.path.insert(0, "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots/data/terrarium")
import run_wygwyl_paeleo_swarms as R

if __name__ == "__main__":
    R.build_scores_json()
    spec = [s for s in R.POEM_SWARM_SPECS if s["num"] == 3][0]
    R.build_single_poem_swarm(spec)
