#!/usr/bin/env python3
"""Standalone handmade builder for PAE-W10 · Poem 10 (Magic Ride) · SCION-009 × SCION-026 · IGARASHI ARAP MESH ON MULTIPLANE SCROLLING STRIP."""
import os, sys
sys.path.insert(0, "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots/data/terrarium")
import run_wygwyl_paeleo_swarms as R

if __name__ == "__main__":
    R.build_scores_json()
    spec = [s for s in R.POEM_SWARM_SPECS if s["num"] == 10][0]
    R.build_single_poem_swarm(spec)
