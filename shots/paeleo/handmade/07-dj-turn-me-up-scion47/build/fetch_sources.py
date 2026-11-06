#!/usr/bin/env python3
"""Fetches and verifies existing WYGWYL multiplane plates, cut props, and 4-angle character cuts in sources/ for Poem 07."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
PAELEO = os.path.abspath(os.path.join(FOLDER, "..", ".."))
if PAELEO not in sys.path:
    sys.path.insert(0, PAELEO)
from lib_handmade_round2_assets import populate_poem_sources

if __name__ == "__main__":
    populate_poem_sources(7, FOLDER)
    print("Populated sources/ for Poem 07")
