#!/usr/bin/env python3
"""
WYGWYL Halfworld Agent Office & Kanban Git Worktree Orchestrator
Synthesizes Kohnny + the 10 Open-Source Agent-Office & Worktree Kanban Repositories into:
1. shots/data/terrarium/agent_office_manifest.json (live data for shots/agent_office_kanban.html)
2. CLI Git Worktree + 55-Minute Cache Compaction + Cross-Model Audit helper
3. 3 high-resolution 2400x1350 visual simulation & architecture plates in shots/png_vault/atlas_splats/
"""

import argparse
import json
import math
import os
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch")
SHOTS = ROOT / "shots"
PACKS_DIR = SHOTS / "data" / "terrarium" / "atlas_packs"
VAULT_DIR = SHOTS / "png_vault" / "atlas_splats"
BRAIN_DIR = Path("/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584")
MANIFEST_OUT = SHOTS / "data" / "terrarium" / "agent_office_manifest.json"


def get_font(size=18, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


# ==============================================================================
# 1. DEFINITIVE RANKING & FEATURE SYNTHESIS OF THE 10 OPEN-SOURCE REPOS + KOHNNY
# ==============================================================================
REPOS_RANKED = [
    {
        "rank": 1,
        "tier": "S-TIER · BEST OVERALL 3D MULTIPLAYER + WORKTREES",
        "repo": "AgentSystemLabs/agent-office",
        "url": "https://github.com/AgentSystemLabs/agent-office",
        "category": "3D Office + Worktrees + /lite Mobile + MCP Hiring",
        "score": 98,
        "best_for": "Best all-in-one open-source replacement for Kohnny's 3D multiplayer building + multi-harness desks",
        "superpower": "Maps each repo/stage to a 3D building floor (+ /lite 2D mobile view), puts Claude/Codex/Cursor/OpenCode at desks with live terminals, corkboard issue queues, isolated Git worktrees, and an MCP server so agents can hire/dismiss subagents.",
        "how_used_in_wygwyl": "Powers our 4-Floor 3D Mega-Hub Soundstage Office (Floor 1: Atlantis, Floor 2: Harbor Temple, Floor 3: Mount Vernon, Floor 4: Shore Garden) + /lite 2D Pixel View + MCP Subagent Hiring.",
        "install_cmd": "curl -fsSL https://raw.githubusercontent.com/AgentSystemLabs/agent-office/main/install.sh | bash",
        "accent": "#5ce1e6"
    },
    {
        "rank": 2,
        "tier": "S-TIER · BEST AUTONOMOUS MANAGER (MAESTRO) + KANBAN WORKTREES",
        "repo": "bill10/agent-007",
        "url": "https://github.com/bill10/agent-007",
        "category": "Kanban Worktrees + Pixel Office + Always-On Manager Agent",
        "score": 96,
        "best_for": "Best match for Kohnny's autonomous 'Maestro' agent that plans cards, spawns worktrees, reviews diffs & merges PRs",
        "superpower": "Combines a pixel office, web terminals, a To-Do -> In-Progress -> Review Kanban board with per-card Git worktrees for Claude Code or Codex, Tailscale phone access, and 'Billion' (an always-on orchestrator agent).",
        "how_used_in_wygwyl": "Turns our Halfworld Hound into 'Maestro Hound (Agent-007)' — an always-on director agent that decomposes poem/splat tasks into worktree cards and guards the merge gate.",
        "install_cmd": "git clone https://github.com/bill10/agent-007",
        "accent": "#ffd23f"
    },
    {
        "rank": 3,
        "tier": "S-TIER · BEST SEMANTIC MERGE & CONFLICT-FREE WORKTREE ENGINE",
        "repo": "proactive-agent/workbench",
        "url": "https://github.com/proactive-agent/workbench",
        "category": "Kanban + Worktrees + AI Semantic Merge + Rate-Limit Swap",
        "score": 95,
        "best_for": "Best for Kohnny's single-file FIFO Merge Queue, cross-branch conflict detection & multi-account rate-limit failover",
        "superpower": "Per-task Git worktree isolation with AI-powered semantic merge, conflict awareness across unmerged branches BEFORE merge time, model triage, and automatic multi-account rate-limit swapping.",
        "how_used_in_wygwyl": "Powers our Column 4 FIFO Semantic Merge Queue & Cross-Worktree File-Overlap Matrix (detecting collisions on shots/terrarium.html & png_catalog.json before merging).",
        "install_cmd": "git clone https://github.com/proactive-agent/workbench",
        "accent": "#4ade80"
    },
    {
        "rank": 4,
        "tier": "A+ TIER · BEST MULTI-AGENT KANBAN + INLINE BEFORE/AFTER PREVIEWS",
        "repo": "BloopAI/vibe-kanban",
        "url": "https://github.com/BloopAI/vibe-kanban",
        "category": "10+ Agent Kanban + Worktrees + Dev-Server Previews",
        "score": 93,
        "best_for": "Best zero-install web Kanban (`npx vibe-kanban`) with inline diff comments & dev-server preview links across 10+ CLIs",
        "superpower": "Supports Claude Code, Codex, Gemini CLI, OpenCode & Cursor in isolated per-card worktrees with inline diff comments and embedded localhost dev-server previews.",
        "how_used_in_wygwyl": "Powers our Column 1 (Planning) Before/After Interactive HTML & PNG Mockup Sliders + one-click :8788 live preview buttons inside every Kanban card.",
        "install_cmd": "npx vibe-kanban",
        "accent": "#c4b5fd"
    },
    {
        "rank": 5,
        "tier": "A+ TIER · BEST SPECIALIST ROUTING, PERMISSION CARDS & PAYROLL HUD",
        "repo": "W17ant/Claude-Office",
        "url": "https://github.com/W17ant/Claude-Office",
        "category": "Isometric Office + Specialist Routing + Approval Cards",
        "score": 91,
        "best_for": "Best for specialist roles (Debugger, Reviewer, Frontend), permission-approval cards, token/payroll meters & Slack chat",
        "superpower": "Hook + WebSocket isometric office with live task whiteboard, specialist routing, interactive permission-approval cards, token/payroll/memory meters, and Slack-style office chat.",
        "how_used_in_wygwyl": "Powers our Cross-Model Permission Approval Cards ([Approve Merge] / [Send Back to Doing]), Token/Cache Cost Meters, and the live Halfworld Office Slack Chat.",
        "install_cmd": "git clone https://github.com/W17ant/Claude-Office.git && cd Claude-Office && npm i && npm run install-hooks",
        "accent": "#ff4d6d"
    },
    {
        "rank": 6,
        "tier": "A TIER · BEST CLAUDE + CODEX DUAL-HOOK CHOREOGRAPHY",
        "repo": "KalebKE/PixelOffice",
        "url": "https://github.com/KalebKE/PixelOffice",
        "category": "2D Pixel Office (Claude Code + Codex Hooks)",
        "score": 89,
        "best_for": "Best spatial state machine: agents walk to whiteboards in Plan mode, code at desks, celebrate tests & lounge when idle",
        "superpower": "Event-driven desktop pixel office supporting BOTH Claude Code and Codex hooks; agents physically walk between Whiteboard (Planning), Desk (Coding), QA Bench (Testing), and Coffee Lounge (Idle).",
        "how_used_in_wygwyl": "Drives our 6-Station Agent Choreography: moving a card between columns makes the assigned 2.5D character walk between the Whiteboard, Desk, Library, Audit Bench, Merge Gate & Harbor Cafe.",
        "install_cmd": "git clone https://github.com/KalebKE/PixelOffice && cd PixelOffice && python3 hooks/manage_hooks.py install && ./start.sh",
        "accent": "#fb923c"
    },
    {
        "rank": 7,
        "tier": "A TIER · BEST TMUX + GITHUB PR + MOBILE PUSH NOTIFICATIONS",
        "repo": "langwatch/kanban-code",
        "url": "https://github.com/langwatch/kanban-code",
        "category": "Kanban + Worktrees + tmux + Pushover Mobile Alerts",
        "score": 88,
        "best_for": "Best native tmux session binding + phone push notifications when a card reaches Review",
        "superpower": "Links every Kanban card to a Claude session, Git worktree, persistent tmux terminal pane, and GitHub PR, firing mobile Pushover notifications when human review is needed.",
        "how_used_in_wygwyl": "Generates copyable `tmux new-session` + `git worktree` commands per card and fires Review Notification banners when Cross-Model Audit finishes.",
        "install_cmd": "git clone https://github.com/langwatch/kanban-code",
        "accent": "#38bdf8"
    },
    {
        "rank": 8,
        "tier": "A TIER · BEST CONTEXT WINDOW & PROMPT-CACHE SPEND MONITOR",
        "repo": "NikiforovAll/claude-code-kanban",
        "url": "https://github.com/NikiforovAll/claude-code-kanban",
        "category": "Local Kanban + Context/Token Spend & Plan Preview",
        "score": 87,
        "best_for": "Best lightweight CLI (`claude-code-kanban --open`) for context-window percentage & 55-minute prompt-cache tracking",
        "superpower": "Installs lightweight hooks to track live agent activity, group sessions, preview plan docs, and monitor context window saturation and token spend.",
        "how_used_in_wygwyl": "Paired with Kohnny's 55-Minute Prompt-Cache TTL timer: tracks each agent's elapsed cache age and auto-compacts into a Handoff Soul Note at 55:00 before the 1-hour cache expires.",
        "install_cmd": "npm install -g claude-code-kanban && claude-code-kanban --install && claude-code-kanban --open",
        "accent": "#f472b6"
    },
    {
        "rank": 9,
        "tier": "B+ TIER · BEST ZERO-INVASION TRANSCRIPT WATCHER",
        "repo": "pixel-agents-hq/pixel-agents",
        "url": "https://github.com/pixel-agents-hq/pixel-agents",
        "category": "Zero-Hook Canvas 2D Transcript Watcher",
        "score": 85,
        "best_for": "Best when you want a 2D office watching Claude, Codex, Gemini & Cursor `transcript.jsonl` logs without installing hooks",
        "superpower": "Passively tails JSONL transcripts from Claude Code, Codex, Gemini, and Cursor to drive pathfinding and character state machines with zero CLI modifications.",
        "how_used_in_wygwyl": "Passively tails our `.system_generated/logs/transcript.jsonl` and `png_catalog.json` to animate agent activity in `/lite` 2D mode.",
        "install_cmd": "git clone https://github.com/pixel-agents-hq/pixel-agents",
        "accent": "#a3e635"
    },
    {
        "rank": 10,
        "tier": "B+ TIER · BEST 3D LIBRARY-READ vs. DESK-WRITE VISUALIZATION",
        "repo": "khanh020905/my-office",
        "url": "https://github.com/khanh020905/my-office",
        "category": "3D Claude Code Office (Library vs. Desk)",
        "score": 83,
        "best_for": "Best visual distinction between Reading/Researching (walking to the 3D Library) vs. Coding (typing at the 3D Desk)",
        "superpower": "Spawns a 3D avatar per session that physically walks to the Library bookshelf during file reads/greps and returns to its 3D desk during file edits.",
        "how_used_in_wygwyl": "In our 3D Terrarium Office, agents walk to the 'PNG Vault Library' when reading refs/landpacks and return to their '.GLB Worktree Desk' when writing code.",
        "install_cmd": "git clone https://github.com/khanh020905/my-office",
        "accent": "#60a5fa"
    }
]


# ==============================================================================
# 2. NAMED PERSISTENT-SOUL WYGWYL AGENTS (THE CAST AS LIVE OFFICE WORKERS)
# ==============================================================================
OFFICE_STATIONS = {
    "whiteboard": {"name": "📋 Planning Whiteboard (Before/After Mockups)", "pos3d": [-38.0, 2.5, -24.0], "pos2d": [0.16, 0.26], "color": "#c4b5fd"},
    "desk_splat": {"name": "💻 Desk 1 · .GLB & .SPLAT Infrastructure Rig", "pos3d": [-14.0, 2.5, -6.0], "pos2d": [0.36, 0.48], "color": "#5ce1e6"},
    "desk_tape": {"name": "💻 Desk 2 · 183-Shot Multiplane & Onion Painter", "pos3d": [14.0, 2.5, -6.0], "pos2d": [0.58, 0.48], "color": "#4ade80"},
    "library": {"name": "📚 PNG Vault & Landpack Reference Library (1,349 Plates)", "pos3d": [-42.0, 2.5, 22.0], "pos2d": [0.16, 0.74], "color": "#60a5fa"},
    "audit_bench": {"name": "🔍 Cross-Model Audit Bench (Codex <-> Claude QA)", "pos3d": [36.0, 2.5, -18.0], "pos2d": [0.82, 0.30], "color": "#ff4d6d"},
    "merge_gate": {"name": "🔀 Single-File FIFO Semantic Merge Gate", "pos3d": [38.0, 2.5, 18.0], "pos2d": [0.84, 0.68], "color": "#ffd23f"},
    "coffee_bar": {"name": "☕ Harbor Café Espresso Lounge (Idle & Cache Warmup)", "pos3d": [0.0, 2.5, 32.0], "pos2d": [0.48, 0.82], "color": "#fb923c"},
}

AGENTS = [
    {
        "id": "agent_maestro_hound",
        "name": "Maestro Hound (Billion)",
        "role": "Meta-Orchestrator & FIFO Queue Director",
        "avatar_img": "png_vault/atlas_splats/atlas_hub_03_mount_vernon.png",
        "cutout_type": "hound",
        "harness": "Claude Code (Opus 4.6) + MCP Hiring",
        "auditor_harness": "Codex (o3-pro)",
        "station": "merge_gate",
        "status": "ORCHESTRATING",
        "cache_minutes_elapsed": 42,
        "cache_ttl_minutes": 55,
        "tokens_used": "148.2k / 200k",
        "cost_usd": 1.84,
        "color": "#ffd23f",
        "soul": "Persistent Soul: Halfworld Hound & Showrunner. Speaks with crisp spatial coordinates. Refuses to let two worktrees touch shots/terrarium.html simultaneously without queuing single-file in Column 4.",
        "memory_notes": [
            "Locked 4 Bang-for-Buck Mega-Hubs covering all 14 Poems and 10 City Stages.",
            "Enforced R0/R1 actor inpainting before Marble/Atlas 2560x1280 pano export.",
            "Next priority: Merge Twin-State Harbor Splat shader into main after EX Auditor sign-off."
        ]
    },
    {
        "id": "agent_poet_engineer",
        "name": "The Poet (3D Splat & .GLB Engineer)",
        "role": "3D WebGL, .GLB Collider & Gaussian Splat Architect",
        "avatar_img": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/01_torso_front.png",
        "cutout_type": "poet",
        "harness": "Claude Code (Sonnet 4.5 / Opus 4.6)",
        "auditor_harness": "Codex CLI (Cross-Model Reviewer)",
        "station": "desk_splat",
        "status": "CODING_IN_WORKTREE",
        "cache_minutes_elapsed": 53,
        "cache_ttl_minutes": 55,
        "tokens_used": "176.4k / 200k",
        "cost_usd": 2.31,
        "color": "#5ce1e6",
        "soul": "Persistent Soul: Wears the calibrated black-and-red tracksuit with tucked boot cuffs. Obsessed with OpenCV <-> Three.js datum alignment, 12-bit heightfields, and Z-buffer phantom occlusion.",
        "memory_notes": [
            "Built 14 binary .glb Chisel colliders and 5 32-byte .splat clouds.",
            "Cache at 53/55 mins — ready for auto-compaction handoff note before 60m TTL expiry!"
        ]
    },
    {
        "id": "agent_ex_auditor",
        "name": "The EX (Cross-Model Auditor)",
        "role": "Cross-Model Reviewer (Codex/Gemini Auditing Claude)",
        "avatar_img": "png_vault/atlas_splats/what_happens_01_naive_vs_infrastructure.png",
        "cutout_type": "ex",
        "harness": "OpenAI Codex CLI + Gemini 2.5 Pro",
        "auditor_harness": "Independent Cross-Model Audit",
        "station": "audit_bench",
        "status": "AUDITING_DIFF",
        "cache_minutes_elapsed": 28,
        "cache_ttl_minutes": 55,
        "tokens_used": "92.0k / 200k",
        "cost_usd": 1.12,
        "color": "#ff4d6d",
        "soul": "Persistent Soul: Never rubber-stamps Claude's own code. Runs a separate model family (Codex/Gemini) to catch scale hallucinations (02-04 eyeball), missing file:// links, or Z-fighting.",
        "memory_notes": [
            "Rejected 9 macro close-ups (02-04, 03-01, 04-05, 05-04, 07-00, 12-04..06) and 5 Markov duplicates.",
            "Auditing card WT-104 (Twin-State Harbor Splat Morph) before FIFO Merge."
        ]
    },
    {
        "id": "agent_couple_painters",
        "name": "The Couple (Multiplane & Onion Painters)",
        "role": "Before/After Mockup & 183-Shot Tape Artists",
        "avatar_img": "png_vault/atlas_splats/what_happens_02_4step_glb_splat_pipeline_in_action.png",
        "cutout_type": "couple",
        "harness": "Gemini 2.5 Pro + Image-Gen Subagent",
        "auditor_harness": "Claude Code Visual QA",
        "station": "whiteboard",
        "status": "PLANNING_MOCKUP",
        "cache_minutes_elapsed": 19,
        "cache_ttl_minutes": 55,
        "tokens_used": "64.5k / 200k",
        "cost_usd": 0.78,
        "color": "#c4b5fd",
        "soul": "Persistent Soul: Waltz across R0..R5 concentric onion depth shells. Always generate a side-by-side Before/After visual mockup in Planning before any code is written in Doing.",
        "memory_notes": [
            "Generated 119 360x180 equirectangular spheres and 119 6-shell onion depth peel plates.",
            "Drafting Before/After mockup for WT-101 (WebGL Depth-Sorted Splat Shader)."
        ]
    },
    {
        "id": "agent_child_compactor",
        "name": "Child Traveler (Cache & Library Keeper)",
        "role": "55-Min Prompt-Cache Compactor & Vault Librarian",
        "avatar_img": "png_vault/atlas_splats/what_happens_04_all_4_megahubs_live_3d_views.png",
        "cutout_type": "child",
        "harness": "Claude Code (Haiku / Flash-Lite Daemon)",
        "auditor_harness": "Maestro Hound",
        "station": "library",
        "status": "READING_LIBRARY",
        "cache_minutes_elapsed": 54,
        "cache_ttl_minutes": 55,
        "tokens_used": "188.0k / 200k",
        "cost_usd": 0.42,
        "color": "#4ade80",
        "soul": "Persistent Soul: Watches the 55-minute prompt-cache clock like a hawk. At minute 55, compacts the trajectory into a crisp Handoff Note so the 1-hour cache never cold-starts.",
        "memory_notes": [
            "Indexed 1,349 PNG plates in shots/png_vault/png_catalog.json.",
            "ALERT: 54/55 mins elapsed — ready to trigger 55-Minute Auto-Compaction!"
        ]
    },
    {
        "id": "agent_foundry_architect",
        "name": "Foundry Architect (Inverse Sculptor)",
        "role": "Inverse Topology & Landpack Cartographer",
        "avatar_img": "png_vault/atlas_splats/atlas_district_centro.png",
        "cutout_type": "architect",
        "harness": "OpenCode + Python NumPy/PIL",
        "auditor_harness": "The EX (Codex CLI)",
        "station": "coffee_bar",
        "status": "IDLE_COFFEE",
        "cache_minutes_elapsed": 11,
        "cache_ttl_minutes": 55,
        "tokens_used": "38.1k / 200k",
        "cost_usd": 0.35,
        "color": "#fb923c",
        "soul": "Persistent Soul: Carves 104/104 reference horizons into w1623, w1578, w0746, w1165, w0889, w0980. Grabs espresso at the Harbor Café when all 104 inversions pass.",
        "memory_notes": [
            "Completed 104/104 equirectangular inverse horizon sculptures.",
            "Resting at Harbor Café Lounge waiting for next Foundry landpack card."
        ]
    }
]


# ==============================================================================
# 3. 5-COLUMN KANBAN + GIT WORKTREE PIPELINE CARDS (KOHNNY + 10 REPOS)
# ==============================================================================
KANBAN_CARDS = [
    {
        "id": "WT-101",
        "title": "Hub 01 Atlantis: WebGL Radially-Sorted Ellipsoid Splat Shader",
        "column": "planning",
        "poem": "06",
        "hub": "hub_01_atlantis",
        "worktree_path": ".worktrees/wt-101-atlantis-splat-shader",
        "branch": "feat/wt-101-atlantis-splat-shader",
        "agent_id": "agent_couple_painters",
        "harness": "Claude Code (Opus 4.6)",
        "auditor": "Codex (o3-pro)",
        "files_touched": ["shots/atlas_splat_studio.html", "shots/data/terrarium/atlas_packs/splats/hub_01_atlantis.splat"],
        "conflict_status": "CLEAN (0 overlapping active worktrees)",
        "before_img": "png_vault/atlas_splats/what_happens_01_naive_vs_infrastructure.png",
        "after_img": "png_vault/atlas_splats/atlas_hub_01_atlantis.png",
        "mockup_caption": "Before: Naive unfiltered district splat with frozen R1 ghost blobs -> After: .GLB Z-Phantom + radially sorted 3D Gaussian ellipsoids",
        "tmux_cmd": "git worktree add .worktrees/wt-101-atlantis-splat-shader -b feat/wt-101-atlantis-splat-shader && tmux new -s wt-101 'cd .worktrees/wt-101-atlantis-splat-shader && claude'",
        "audit_notes": "Planning stage: HTML Before/After mockup generated at Whiteboard. Ready to move to Doing.",
        "needs_permission": False
    },
    {
        "id": "WT-102",
        "title": "Hub 03 Mount Vernon: Rooftop Hound to 1920s Ballroom Drop Portal",
        "column": "planning",
        "poem": "01",
        "hub": "hub_03_mount_vernon",
        "worktree_path": ".worktrees/wt-102-mount-vernon-drop",
        "branch": "feat/wt-102-mount-vernon-drop",
        "agent_id": "agent_maestro_hound",
        "harness": "Claude Code + Gemini 2.5 Pro",
        "auditor": "Codex CLI",
        "files_touched": ["shots/data/terrarium/atlas_packs/glb/hub_03_mount_vernon_chisel.glb"],
        "conflict_status": "CLEAN (Isolated .glb asset)",
        "before_img": "png_vault/atlas_splats/atlas_district_mount_vernon.png",
        "after_img": "png_vault/atlas_splats/atlas_hub_03_mount_vernon.png",
        "mockup_caption": "Before: Separate Poem 01, 02, 14 street stages -> After: Unified vertical Mount Vernon .GLB + Ballroom drop aperture",
        "tmux_cmd": "git worktree add .worktrees/wt-102-mount-vernon-drop -b feat/wt-102-mount-vernon-drop && tmux new -s wt-102 'cd .worktrees/wt-102-mount-vernon-drop && claude'",
        "audit_notes": "Before/After vertical drop mockup pinned to Whiteboard.",
        "needs_permission": False
    },
    {
        "id": "WT-103",
        "title": "Depth-Occlusion Phantom Prepass (R3 Archways Occluding R1 Actors)",
        "column": "doing",
        "poem": "06",
        "hub": "hub_01_atlantis",
        "worktree_path": ".worktrees/wt-103-glb-z-phantom",
        "branch": "feat/wt-103-glb-z-phantom",
        "agent_id": "agent_poet_engineer",
        "harness": "Claude Code (Opus 4.6)",
        "auditor": "The EX (Codex o3-pro)",
        "files_touched": ["shots/atlas_splat_studio.html", "shots/data/terrarium/build_atlas_splat_infrastructure.py"],
        "conflict_status": "WATCH: Overlaps shots/atlas_splat_studio.html with WT-101 (WT-101 still in Planning)",
        "before_img": "png_vault/atlas_splats/what_happens_01_naive_vs_infrastructure.png",
        "after_img": "png_vault/atlas_splats/what_happens_02_4step_glb_splat_pipeline_in_action.png",
        "mockup_caption": "4-Stage Cutaway Peel: .GLB renders with colorWrite:false, depthWrite:true at renderOrder -1 so R3 walls occlude R1 puppets",
        "tmux_cmd": "git worktree add .worktrees/wt-103-glb-z-phantom -b feat/wt-103-glb-z-phantom && tmux new -s wt-103 'cd .worktrees/wt-103-glb-z-phantom && claude'",
        "audit_notes": "Coding in isolated worktree. Cache at 53/55m — auto-compaction handoff note armed.",
        "needs_permission": False
    },
    {
        "id": "WT-104",
        "title": "Hub 02 Twin-State Splat Morph (Poem 03 Storm Ruin <-> Poem 11 Temple)",
        "column": "review",
        "poem": "11",
        "hub": "hub_02_harbor_temple",
        "worktree_path": ".worktrees/wt-104-twin-state-harbor-morph",
        "branch": "feat/wt-104-twin-state-harbor-morph",
        "agent_id": "agent_ex_auditor",
        "harness": "Coded by Claude Opus -> Audited by Codex o3-pro",
        "auditor": "The EX (Codex Cross-Model Pass)",
        "files_touched": ["shots/data/terrarium/atlas_packs/splats/hub_02_harbor_storm_ruin.splat", "shots/data/terrarium/atlas_packs/splats/hub_02_harbor_temple.splat"],
        "conflict_status": "CLEAN (Ready for FIFO Merge Queue)",
        "before_img": "png_vault/atlas_splats/atlas_hub_02_harbor_temple.png",
        "after_img": "png_vault/atlas_splats/what_happens_03_twin_state_harbor_morph.png",
        "mockup_caption": "Cross-Model Audit Verified: Both .splat clouds share hub_02_harbor_temple_chisel.glb with zero floor collider drift across 0..100% morph",
        "tmux_cmd": "git worktree add .worktrees/wt-104-twin-state-harbor-morph -b feat/wt-104-twin-state-harbor-morph && tmux new -s wt-104 'codex review --base main'",
        "audit_notes": "CROSS-MODEL AUDIT PASSED: Codex verified 27,818 Gaussians match vertex stride and OpenCV diag(1,-1,-1,1) bridge. Waiting for human/Maestro [Approve] click.",
        "needs_permission": True
    },
    {
        "id": "WT-105",
        "title": "55-Minute Prompt-Cache Compactor & Vault Indexer (1,349 Plates)",
        "column": "review",
        "poem": "01",
        "hub": "hub_04_shore_garden",
        "worktree_path": ".worktrees/wt-105-cache-compactor-vault",
        "branch": "feat/wt-105-cache-compactor-vault",
        "agent_id": "agent_child_compactor",
        "harness": "Coded by Claude Sonnet -> Audited by Gemini 2.5 Pro",
        "auditor": "Gemini 2.5 Pro Cross-Model Pass",
        "files_touched": ["shots/png_vault/png_catalog.json", "shots/png_browser.html"],
        "conflict_status": "SINGLE-FILE QUEUED behind WT-106 on png_catalog.json",
        "before_img": "png_vault/atlas_splats/all_megahubs_atlas_splat_master.png",
        "after_img": "png_vault/atlas_splats/what_happens_04_all_4_megahubs_live_3d_views.png",
        "mockup_caption": "Auto-compacts agent trajectory at 55:00 into Markdown Handoff Note before 1-hour prompt cache expires",
        "tmux_cmd": "git worktree add .worktrees/wt-105-cache-compactor-vault -b feat/wt-105-cache-compactor-vault",
        "audit_notes": "Gemini Auditor confirmed all 1,349 catalog entries return HTTP 200 on :8788.",
        "needs_permission": True
    },
    {
        "id": "WT-106",
        "title": "Terrarium Live .SPLAT Mounter & Hound 'splat' Command Integration",
        "column": "merge_queue",
        "poem": "01",
        "hub": "hub_01_atlantis",
        "worktree_path": ".worktrees/wt-106-terrarium-splat-mounter",
        "branch": "feat/wt-106-terrarium-splat-mounter",
        "agent_id": "agent_maestro_hound",
        "harness": "Claude Opus 4.6 + Codex Audit",
        "auditor": "PASSED (Codex o3-pro)",
        "files_touched": ["shots/data/terrarium/build_terrarium_html.py", "shots/terrarium.html"],
        "conflict_status": "FIFO MERGE SLOT #1 (Head of Queue — Ready to Merge)",
        "before_img": "png_vault/atlas_splats/atlas_district_centro.png",
        "after_img": "png_vault/atlas_splats/what_happens_04_all_4_megahubs_live_3d_views.png",
        "mockup_caption": "Mounts 32-byte .splat clouds directly over the active Terrarium city via #wyg-sel-splat or asking the Hound",
        "tmux_cmd": "git checkout main && git merge --no-ff feat/wt-106-terrarium-splat-mounter",
        "audit_notes": "FIFO Slot #1: Semantic merge pre-check passed with 0 conflicts against origin/main.",
        "needs_permission": False
    },
    {
        "id": "WT-107",
        "title": "6 Concentric Onion Depth Shells (R0..R5) & 360° Equirectangular Outpaints",
        "column": "merged",
        "poem": "01",
        "hub": "hub_01_atlantis",
        "worktree_path": ".worktrees/wt-107-onion-depth-shells",
        "branch": "feat/wt-107-onion-depth-shells",
        "agent_id": "agent_foundry_architect",
        "harness": "Claude Opus 4.6",
        "auditor": "MERGED (Commit bdbe3ca9)",
        "files_touched": ["shots/foundry_inverse.html", "shots/png_vault/onion_depth/"],
        "conflict_status": "MERGED TO MAIN",
        "before_img": "png_vault/atlas_splats/atlas_district_centro.png",
        "after_img": "png_vault/atlas_splats/all_megahubs_atlas_splat_master.png",
        "mockup_caption": "119 Equirectangular spheres + 119 Concentric Onion Depth Peel plates deployed to origin/main",
        "tmux_cmd": "git log -n 1 bdbe3ca9",
        "audit_notes": "Merged cleanly via FIFO queue and pushed to GitHub Pages.",
        "needs_permission": False
    },
    {
        "id": "WT-108",
        "title": "14 Binary .GLB Chisel Colliders & 4 Mega-Hub Actor-Cleaned Upload Packs",
        "column": "merged",
        "poem": "06",
        "hub": "hub_01_atlantis",
        "worktree_path": ".worktrees/wt-108-atlas-glb-packs",
        "branch": "feat/wt-108-atlas-glb-packs",
        "agent_id": "agent_poet_engineer",
        "harness": "Claude Opus 4.6",
        "auditor": "MERGED (Commit 073c89459)",
        "files_touched": ["shots/data/terrarium/build_atlas_splat_infrastructure.py", "shots/data/terrarium/atlas_packs/"],
        "conflict_status": "MERGED TO MAIN",
        "before_img": "png_vault/atlas_splats/what_happens_01_naive_vs_infrastructure.png",
        "after_img": "png_vault/atlas_splats/what_happens_02_4step_glb_splat_pipeline_in_action.png",
        "mockup_caption": "14 .glb colliders + 5 .splat seeds + 19 blueprint & simulation plates deployed to origin/main",
        "tmux_cmd": "git log -n 1 073c89459",
        "audit_notes": "Merged cleanly via FIFO queue and verified HTTP 200.",
        "needs_permission": False
    }
]


def hex_to_rgba(h, alpha=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def draw_badge(draw, x, y, text, bg=(18, 26, 38, 235), fg=(255, 210, 63, 255), border=(255, 210, 63, 180), font_size=14):
    f = get_font(font_size, bold=True)
    tb = draw.textbbox((0, 0), text, font=f)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    pad_x, pad_y = 10, 5
    box = [x, y, x + tw + pad_x * 2, y + th + pad_y * 2]
    draw.rounded_rectangle(box, radius=6, fill=bg, outline=border, width=2)
    draw.text((x + pad_x, y + pad_y - 1), text, font=f, fill=fg)
    return box[2], box[3]


def clean_ascii(s):
    """Strip emoji characters that Helvetica cannot render in PIL."""
    return "".join(ch for ch in str(s) if ord(ch) < 0x2600 or ch in "·—–×✓✗→←↔").strip()


def wrap_line(text, max_chars=96):
    words = clean_ascii(text).split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ==============================================================================
# VISUAL PLATE 1: 10-REPO RANKING & HOW WE SYNTHESIZE ALL 10 INTO WYGWYL
# ==============================================================================
def render_plate_01_10repos_ranking():
    W, H = 2400, 1350
    img = Image.new("RGBA", (W, H), (8, 11, 16, 255))
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, W, 92], fill=(12, 17, 26, 255))
    draw.line([(0, 92), (W, 92)], fill=(60, 80, 115, 255), width=2)
    draw.text((28, 16), "WHICH OPEN-SOURCE 'CLAUDE CODE VIDEO GAME / KOHNNY' REPOS ARE BEST — AND HOW WE USE ALL 10", font=get_font(26, bold=True), fill=(255, 210, 63, 255))
    draw.text((28, 54), "Ranked for our WYGWYL 3D Terrarium + .GLB/.SPLAT + 2.5D Puppet Pipeline — combining 3D Multiplayer Floors, Maestro Orchestration, Git Worktrees, Cross-Model Audit & 55m Cache Compaction", font=get_font(15), fill=(185, 205, 228, 255))

    # 2x5 Grid of the 10 Repositories
    cols = 2
    pad_x, pad_y = 24, 16
    top_y = 110
    card_w = (W - pad_x * 3) // 2
    card_h = 208

    for idx, r in enumerate(REPOS_RANKED):
        c = idx % cols
        row = idx // cols
        x0 = pad_x + c * (card_w + pad_x)
        y0 = top_y + row * (card_h + pad_y)
        x1, y1 = x0 + card_w, y0 + card_h
        acc = hex_to_rgba(r["accent"], 255)

        draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=(14, 20, 30, 255), outline=acc, width=2)
        draw.rounded_rectangle([x0 + 2, y0 + 2, x1 - 2, y0 + 42], radius=8, fill=(20, 29, 44, 255))
        draw.line([(x0, y0 + 42), (x1, y0 + 42)], fill=acc, width=2)
        draw.text((x0 + 16, y0 + 10), f"#{r['rank']} · {r['repo']}  ({r['category']})", font=get_font(18, bold=True), fill=acc)
        draw_badge(draw, x1 - 155, y0 + 6, f"SCORE: {r['score']}/100", bg=(10, 15, 22, 255), fg=acc, border=acc, font_size=13)

        draw.text((x0 + 16, y0 + 50), f"TIER: {r['tier']}", font=get_font(13, bold=True), fill=(255, 210, 63, 255))
        draw.text((x0 + 16, y0 + 72), f"Best For: {r['best_for']}", font=get_font(14, bold=True), fill=(235, 240, 248, 255))
        draw.text((x0 + 16, y0 + 96), f"Mechanism: {r['superpower'][:115]}", font=get_font(13), fill=(180, 196, 218, 255))

        # Highlight Box: How we use it in WYGWYL
        draw.rounded_rectangle([x0 + 14, y0 + 124, x1 - 14, y1 - 10], radius=6, fill=(10, 28, 24, 255), outline=(74, 222, 128, 200), width=1)
        draw.text((x0 + 24, y0 + 132), "BUILT INTO OUR WYGWYL OFFICE STUDIO:", font=get_font(12, bold=True), fill=(74, 222, 128, 255))
        wlines = wrap_line(r["how_used_in_wygwyl"], 108)
        for li, wl in enumerate(wlines[:2]):
            draw.text((x0 + 24, y0 + 152 + li * 19), wl, font=get_font(13), fill=(215, 245, 228, 255))

    # Bottom Verdict Banner
    draw.rounded_rectangle([24, H - 110, W - 24, H - 16], radius=10, fill=(16, 24, 36, 255), outline=(255, 210, 63, 230), width=3)
    draw.text((44, H - 96), "THE VERDICT — THE 3-PILLAR STACK WE BUILT INTO shots/agent_office_kanban.html:", font=get_font(17, bold=True), fill=(255, 210, 63, 255))
    draw.text((44, H - 68), "1. World & Spatial Desks: AgentSystemLabs/agent-office (3D Multi-Floor Building + /lite 2D View) + KalebKE/PixelOffice (Whiteboard/Desk/Lounge Choreography) + khanh020905/my-office (Library vs Desk).", font=get_font(14), fill=(225, 235, 248, 255))
    draw.text((44, H - 44), "2. Autonomous Kanban + Worktree Pipeline: bill10/agent-007 (Maestro Hound Director) + proactive-agent/workbench (FIFO Semantic Merge) + BloopAI/vibe-kanban (Before/After Mockups) + W17ant (Cross-Model Audit) + NikiforovAll (55m Cache Timer).", font=get_font(14), fill=(125, 240, 190, 255))

    out_path = VAULT_DIR / "kohnny_10repos_comparison_and_architecture.png"
    img.convert("RGB").save(out_path, quality=95)
    img.convert("RGB").save(BRAIN_DIR / out_path.name, quality=95)
    print("Saved", out_path)


# ==============================================================================
# VISUAL PLATE 2: 3D .GLB+.SPLAT MULTIPLAYER AGENT OFFICE + /LITE 2D PIXEL VIEW
# ==============================================================================
def render_plate_02_3d_and_2d_office():
    W, H = 2400, 1350
    img = Image.new("RGBA", (W, H), (8, 11, 16, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 92], fill=(12, 17, 26, 255))
    draw.line([(0, 92), (W, 92)], fill=(60, 80, 115, 255), width=2)
    draw.text((28, 16), "WYGWYL 3D MULTIPLAYER VIRTUAL OFFICE (.GLB + .SPLAT) & /LITE 2D PIXEL OFFICE", font=get_font(26, bold=True), fill=(92, 225, 230, 255))
    draw.text((28, 54), "Left: 3D Soundstage Floor (Club Atlantis .GLB + .SPLAT) with 6 Interactive Agent Stations & 2.5D Cast  |  Right: /lite 2D Pixel Office Floorplan with Pathfinding & 55m Cache Rings", font=get_font(15), fill=(185, 205, 228, 255))

    lw = 1360
    lh = 1120
    lx, ly = 24, 110

    base_3d = Image.open(VAULT_DIR / "what_happens_01_naive_vs_infrastructure.png").convert("RGBA")
    clean_3d_crop = base_3d.crop((1212, 168, 2376, 1244)).resize((lw, lh), Image.Resampling.LANCZOS)
    ld = ImageDraw.Draw(clean_3d_crop)

    ld.rectangle([0, 0, lw, 68], fill=(10, 16, 26, 245))
    ld.text((18, 12), "3D SOUNDSTAGE FLOOR 1 · HUB 01: CLUB ATLANTIS (.GLB COLLIDER + 27,818 SPLAT GAUSSIANS)", font=get_font(19, bold=True), fill=(92, 225, 230, 255))
    ld.text((18, 40), "Inspired by AgentSystemLabs/agent-office + khanh020905/my-office: Each Mega-Hub is a 3D Floor; our 2.5D Cast & Hound walk between 6 Worktree Stations", font=get_font(13), fill=(195, 215, 235, 255))

    stations_3d_ui = [
        (36, 96, "[STATION 1] PLANNING WHITEBOARD", "The Couple (Gemini 2.5 Pro)", "Generating Before/After HTML Mockup for WT-101", "Cache: 19/55m", (196, 181, 253, 255)),
        (36, 250, "[STATION 3] PNG VAULT LIBRARY (1,349 Plates)", "Child Traveler (Cache Keeper)", "Reading png_catalog.json & .landpack.json", "Cache: 54/55m [COMPACTING!]", (74, 222, 128, 255)),
        (465, 860, "[STATION 2] .GLB & .SPLAT WORKTREE DESK", "The Poet (Claude Code Opus 4.6)", "Branch: feat/wt-103-glb-z-phantom (tmux wt-103)", "Cache: 53/55m", (92, 225, 230, 255)),
        (885, 195, "[STATION 4] CROSS-MODEL AUDIT BENCH", "The EX (Codex o3-pro Auditing Claude)", "Reviewing WT-104 Twin-State Morph Diff", "Permission Card Ready", (255, 77, 109, 255)),
        (885, 845, "[STATION 5] SINGLE-FILE FIFO MERGE GATE", "Maestro Hound (Agent-007 Director)", "Slot #1: WT-106 Ready for Conflict-Free Merge", "0 Branch Conflicts", (255, 210, 63, 255)),
    ]

    for sx, sy, stitle, sagent, stask, scache, scol in stations_3d_ui:
        box = [sx, sy, sx + 440, sy + 124]
        ld.rounded_rectangle(box, radius=10, fill=(10, 15, 24, 240), outline=scol, width=3)
        ld.text((sx + 14, sy + 10), stitle, font=get_font(15, bold=True), fill=scol)
        ld.text((sx + 14, sy + 36), f"Agent: {sagent}", font=get_font(14, bold=True), fill=(240, 245, 252, 255))
        ld.text((sx + 14, sy + 60), stask, font=get_font(13), fill=(190, 208, 228, 255))
        draw_badge(ld, sx + 14, sy + 86, scache, bg=(18, 28, 42, 255), fg=scol, border=scol, font_size=12)

    img.alpha_composite(clean_3d_crop, (lx, ly))
    draw.rounded_rectangle([lx, ly, lx + lw, ly + lh], radius=10, outline=(92, 225, 230, 230), width=3)

    # Right Panel: /lite 2D Pixel & Isometric Office View (968 x 1120)
    rw = W - lw - 72
    rh = lh
    rx, ry = lx + lw + 24, ly
    lite_vp = Image.new("RGBA", (rw, rh), (12, 17, 26, 255))
    rdraw = ImageDraw.Draw(lite_vp)

    for gx in range(0, rw, 40):
        rdraw.line([(gx, 68), (gx, rh)], fill=(24, 34, 50, 255), width=1)
    for gy in range(68, rh, 40):
        rdraw.line([(0, gy), (rw, gy)], fill=(24, 34, 50, 255), width=1)

    rdraw.rectangle([0, 0, rw, 68], fill=(20, 15, 34, 255))
    rdraw.text((18, 12), "[/LITE 2D VIEW] PIXEL OFFICE & PATHFINDING FLOORPLAN (PHONE / TABLET)", font=get_font(18, bold=True), fill=(196, 181, 253, 255))
    rdraw.text((18, 40), "Inspired by KalebKE/PixelOffice + W17ant/Claude-Office + pixel-agents: Real-time 2D rooms, pathfinding & Slack feed", font=get_font(13), fill=(200, 190, 230, 255))

    rooms_2d = [
        (28, 92, 456, 360, "ROOM 1 · PLANNING WHITEBOARD", "Before/After HTML & PNG Mockups", (196, 181, 253, 255), "The Couple", "WT-101 Mockup", "png_vault/atlas_splats/atlas_hub_01_atlantis.png"),
        (496, 92, 940, 360, "ROOM 4 · CROSS-MODEL AUDIT BENCH", "Codex / Gemini Auditing Claude Code", (255, 77, 109, 255), "The EX (Auditor)", "WT-104 Diff Audit", "png_vault/atlas_splats/what_happens_03_twin_state_harbor_morph.png"),
        (28, 384, 456, 680, "ROOM 2 · WORKTREE DESK BAY", "Isolated Git Worktrees + tmux Panes", (92, 225, 230, 255), "The Poet (Opus 4.6)", "WT-103 .GLB Z-Phantom", "png_vault/atlas_splats/what_happens_02_4step_glb_splat_pipeline_in_action.png"),
        (496, 384, 940, 680, "ROOM 5 · SINGLE-FILE FIFO MERGE GATE", "Conflict-Free Sequential PR Merger", (255, 210, 63, 255), "Maestro Hound", "WT-106 Slot #1", "png_vault/atlas_splats/atlas_hub_03_mount_vernon.png"),
        (28, 704, 456, 960, "ROOM 3 · PNG VAULT LIBRARY", "Passive Transcript & Catalog Reader", (74, 222, 128, 255), "Child Traveler", "54/55m Auto-Compact!", "png_vault/atlas_splats/all_megahubs_atlas_splat_master.png"),
        (496, 704, 940, 960, "ROOM 6 · HARBOR CAFE LOUNGE", "Idle Agents & Prompt-Cache Warmup", (251, 146, 60, 255), "Foundry Architect", "Sipping Espresso (Idle)", "png_vault/atlas_splats/atlas_district_centro.png"),
    ]

    for x0, y0, x1, y1, rtitle, rsub, rcol, ragent, rbadge, rthumb in rooms_2d:
        rdraw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=(16, 23, 36, 255), outline=rcol, width=2)
        rdraw.rounded_rectangle([x0 + 2, y0 + 2, x1 - 2, y0 + 52], radius=10, fill=(22, 31, 48, 255))
        rdraw.line([(x0, y0 + 52), (x1, y0 + 52)], fill=rcol, width=1)
        rdraw.text((x0 + 14, y0 + 8), rtitle, font=get_font(15, bold=True), fill=rcol)
        rdraw.text((x0 + 14, y0 + 30), rsub, font=get_font(12), fill=(185, 200, 220, 255))

        tpath = SHOTS / rthumb
        if tpath.exists():
            tim = Image.open(tpath).convert("RGBA").resize((240, 122), Image.Resampling.LANCZOS)
            tx, ty = (x0 + x1) // 2 - 120, y0 + 68
            lite_vp.alpha_composite(tim, (tx, ty))
            rdraw = ImageDraw.Draw(lite_vp)
            rdraw.rectangle([tx, ty, tx + 240, ty + 122], outline=rcol, width=2)

        draw_badge(rdraw, x0 + 18, y1 - 44, f"{ragent} · {rbadge}", bg=(10, 15, 24, 255), fg=rcol, border=rcol, font_size=12)

    rdraw.line([(242, 360), (242, 384)], fill=(196, 181, 253, 220), width=3)
    rdraw.line([(456, 530), (496, 226)], fill=(255, 77, 109, 220), width=3)
    rdraw.line([(718, 360), (718, 384)], fill=(255, 210, 63, 220), width=3)

    rdraw.rounded_rectangle([28, 978, 940, rh - 16], radius=10, fill=(10, 14, 22, 255), outline=(75, 95, 130, 220), width=2)
    rdraw.text((44, 990), "LIVE HALFWORLD OFFICE SLACK & HOOK STREAM (W17ant/Claude-Office + Kohnny):", font=get_font(14, bold=True), fill=(255, 210, 63, 255))
    rdraw.text((44, 1018), "[Maestro Hound]: Spawned git worktree .worktrees/wt-103-glb-z-phantom for The Poet. Assigned Desk 1.", font=get_font(13), fill=(92, 225, 230, 255))
    rdraw.text((44, 1042), "[The EX · Codex Auditor]: Cross-model review on WT-104 PASSED (0 scale hallucinations). Permission card raised!", font=get_font(13), fill=(255, 130, 150, 255))
    rdraw.text((44, 1066), "[Child Traveler · 55m Cache Daemon]: Poet session hit 53/55m! Auto-compacting Handoff Soul Note before 1h cache TTL.", font=get_font(13), fill=(74, 222, 128, 255))

    img.alpha_composite(lite_vp, (rx, ry))
    draw.rounded_rectangle([rx, ry, rx + rw, ry + rh], radius=10, outline=(196, 181, 253, 230), width=3)

    draw.rounded_rectangle([24, H - 104, W - 24, H - 16], radius=10, fill=(14, 20, 30, 255), outline=(74, 222, 128, 220), width=2)
    draw.text((44, H - 88), "WHY THIS BEATS A GENERIC CORPORATE OFFICE:", font=get_font(16, bold=True), fill=(74, 222, 128, 255))
    draw.text((485, H - 88), "Instead of generic low-poly office cubicles, our agents work inside the actual 3D WYGWYL Mega-Hubs (.GLB + .SPLAT) they are building!", font=get_font(15), fill=(230, 238, 248, 255))
    draw.text((44, H - 54), "Every Kanban transition physically moves our 2.5D Cast (Poet, EX, Couple, Child, Hound) between the Whiteboard, .GLB Worktree Desk, PNG Vault Library, Cross-Model Audit Bench, and FIFO Merge Gate.", font=get_font(15), fill=(185, 215, 238, 255))

    out_path = VAULT_DIR / "wygwyl_3d_agent_office_and_pixel_lite_simulation.png"
    img.convert("RGB").save(out_path, quality=95)
    img.convert("RGB").save(BRAIN_DIR / out_path.name, quality=95)
    print("Saved", out_path)


# ==============================================================================
# VISUAL PLATE 3: 5-COLUMN KANBAN + GIT WORKTREE + CROSS-MODEL AUDIT + 55M CACHE
# ==============================================================================
def render_plate_03_kanban_pipeline():
    W, H = 2400, 1350
    img = Image.new("RGBA", (W, H), (8, 11, 16, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 92], fill=(12, 17, 26, 255))
    draw.line([(0, 92), (W, 92)], fill=(60, 80, 115, 255), width=2)
    draw.text((28, 16), "WYGWYL 5-COLUMN KANBAN + GIT WORKTREE + CROSS-MODEL AUDIT + FIFO MERGE PIPELINE", font=get_font(26, bold=True), fill=(255, 210, 63, 255))
    draw.text((28, 54), "Every card spawns an isolated Git worktree (.worktrees/wt-*), generates Before/After mockups in Planning, runs Cross-Model Audit (Codex auditing Claude), queues single-file in FIFO Merge & auto-compacts at 55m", font=get_font(15), fill=(185, 205, 228, 255))

    columns_meta = [
        ("planning", "1. PLANNING", "Before/After HTML Mockups\n(Whiteboard · vibe-kanban)", "#c4b5fd"),
        ("doing", "2. DOING (WORKTREE)", "Isolated Git Worktree + tmux\n(Desk · agent-office / 007)", "#5ce1e6"),
        ("review", "3. CROSS-MODEL REVIEW", "Codex/Gemini Audits Claude\n(Audit Bench · Claude-Office)", "#ff4d6d"),
        ("merge_queue", "4. FIFO MERGE QUEUE", "Single-File Semantic Merge\n(Merge Gate · workbench)", "#ffd23f"),
        ("merged", "5. MERGED & LIVE", "Pushed to origin/main & :8788\n(PNG Vault · 1,352 Plates)", "#4ade80"),
    ]

    col_w = (W - 24 * 6) // 5
    col_h = 910
    top_y = 110

    for ci, (col_id, ctitle, csub, c_hex) in enumerate(columns_meta):
        cx = 24 + ci * (col_w + 24)
        cy = top_y
        ccol = hex_to_rgba(c_hex, 255)
        draw.rounded_rectangle([cx, cy, cx + col_w, cy + col_h], radius=10, fill=(13, 18, 28, 255), outline=ccol, width=2)
        draw.rounded_rectangle([cx + 2, cy + 2, cx + col_w - 2, cy + 68], radius=8, fill=(20, 28, 44, 255))
        draw.line([(cx, cy + 68), (cx + col_w, cy + 68)], fill=ccol, width=2)
        draw.text((cx + 14, cy + 10), ctitle, font=get_font(17, bold=True), fill=ccol)
        for li, line in enumerate(csub.split("\n")):
            draw.text((cx + 14, cy + 34 + li * 16), line, font=get_font(12), fill=(200, 214, 232, 255))

        col_cards = [c for c in KANBAN_CARDS if c["column"] == col_id]
        ky = cy + 82
        for card in col_cards[:2]:
            ch = 395
            draw.rounded_rectangle([cx + 12, ky, cx + col_w - 12, ky + ch], radius=8, fill=(18, 26, 40, 255), outline=ccol, width=2)
            draw.text((cx + 22, ky + 10), f"{card['id']} · Poem {card['poem']}", font=get_font(14, bold=True), fill=ccol)
            tlines = wrap_line(card["title"], 40)
            for tli, tl in enumerate(tlines[:2]):
                draw.text((cx + 22, ky + 32 + tli * 18), tl, font=get_font(14, bold=True), fill=(240, 245, 252, 255))

            thumb_w = (col_w - 56) // 2
            thumb_h = 110
            ty = ky + 76
            for ti, (tlabel, tpath) in enumerate([("BEFORE", card["before_img"]), ("AFTER", card["after_img"])]):
                tx = cx + 22 + ti * (thumb_w + 12)
                full_p = SHOTS / tpath
                if full_p.exists():
                    tim = Image.open(full_p).convert("RGBA").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                    img.alpha_composite(tim, (tx, ty))
                draw = ImageDraw.Draw(img)
                tcol = (255, 90, 115, 255) if ti == 0 else (74, 222, 128, 255)
                draw.rectangle([tx, ty, tx + thumb_w, ty + thumb_h], outline=tcol, width=2)
                draw.rectangle([tx, ty, tx + 68, ty + 20], fill=(8, 12, 18, 235))
                draw.text((tx + 6, ty + 3), tlabel, font=get_font(11, bold=True), fill=tcol)

            my = ty + thumb_h + 10
            draw.text((cx + 22, my), f"Worktree: {card['worktree_path']}", font=get_font(12, bold=True), fill=(92, 225, 230, 255))
            draw.text((cx + 22, my + 20), f"Coder: {card['harness']}", font=get_font(12), fill=(215, 225, 240, 255))
            draw.text((cx + 22, my + 40), f"Auditor: {card['auditor']}", font=get_font(12, bold=True), fill=(255, 150, 170, 255))
            draw.text((cx + 22, my + 60), f"Status: {card['conflict_status'][:44]}", font=get_font(11), fill=(255, 210, 63, 255))

            if card.get("needs_permission"):
                draw.rounded_rectangle([cx + 22, ky + ch - 42, cx + 195, ky + ch - 12], radius=6, fill=(16, 65, 42, 255), outline=(74, 222, 128, 240), width=2)
                draw.text((cx + 34, ky + ch - 34), "[APPROVE MERGE]", font=get_font(12, bold=True), fill=(110, 250, 175, 255))
                draw.rounded_rectangle([cx + 205, ky + ch - 42, cx + col_w - 22, ky + ch - 12], radius=6, fill=(65, 18, 28, 255), outline=(255, 77, 109, 240), width=2)
                draw.text((cx + 220, ky + ch - 34), "[SEND TO FIX]", font=get_font(12, bold=True), fill=(255, 140, 160, 255))
            else:
                draw_badge(draw, cx + 22, ky + ch - 40, card["audit_notes"][:44] + "...", bg=(12, 18, 28, 255), fg=ccol, border=ccol, font_size=11)

            ky += ch + 14

    by = top_y + col_h + 18
    bh = H - by - 16
    draw.rounded_rectangle([24, by, W - 24, by + bh], radius=10, fill=(14, 20, 32, 255), outline=(255, 210, 63, 230), width=3)
    draw.text((44, by + 16), "[55:00 CACHE DAEMON] KOHNNY + NIKIFOROVALL 55-MINUTE PROMPT-CACHE AUTO-COMPACTION & HANDOFF ENGINE:", font=get_font(18, bold=True), fill=(255, 210, 63, 255))
    draw.text((44, by + 48), "Anthropic's 1-hour prompt cache expires at 60:00. At 55:00, our daemon automatically compacts the agent's context into a persistent Markdown Soul & Handoff Note", font=get_font(15), fill=(225, 235, 248, 255))
    draw.text((44, by + 74), "(.worktrees/<id>/HANDOFF_55M.md) and respawns a warm session — avoiding 10x cold-cache token spikes while preserving every .GLB/.SPLAT coordinate!", font=get_font(15), fill=(120, 240, 190, 255))

    gx = 1360
    for ai, ag in enumerate(AGENTS[:4]):
        bx0 = gx + ai * 250
        by0 = by + 18
        pct = ag["cache_minutes_elapsed"] / ag["cache_ttl_minutes"]
        gcol = (255, 77, 109, 255) if pct >= 0.92 else (74, 222, 128, 255)
        draw.rounded_rectangle([bx0, by0, bx0 + 236, by0 + bh - 36], radius=8, fill=(10, 15, 24, 255), outline=gcol, width=2)
        draw.text((bx0 + 12, by0 + 10), ag["name"][:24], font=get_font(13, bold=True), fill=gcol)
        draw.text((bx0 + 12, by0 + 32), f"Cache Clock: {ag['cache_minutes_elapsed']}:00 / 55:00", font=get_font(13, bold=True), fill=(240, 245, 252, 255))
        draw.rectangle([bx0 + 12, by0 + 58, bx0 + 224, by0 + 72], fill=(28, 38, 54, 255))
        draw.rectangle([bx0 + 12, by0 + 58, bx0 + 12 + int(212 * min(1.0, pct)), by0 + 72], fill=gcol)
        status_txt = "AUTO-COMPACT READY!" if pct >= 0.92 else f"Tokens: {ag['tokens_used']}"
        draw.text((bx0 + 12, by0 + 82), status_txt, font=get_font(12, bold=True), fill=gcol)

    out_path = VAULT_DIR / "wygwyl_kanban_worktree_crossmodel_pipeline.png"
    img.convert("RGB").save(out_path, quality=95)
    img.convert("RGB").save(BRAIN_DIR / out_path.name, quality=95)
    print("Saved", out_path)


def update_catalog_and_manifest():
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)

    # Save agent_office_manifest.json
    manifest = {
        "version": "1.0.0",
        "title": "WYGWYL Halfworld 3D/2D Agent Office & Kanban Git Worktree Studio",
        "repos_ranked": REPOS_RANKED,
        "stations": OFFICE_STATIONS,
        "agents": AGENTS,
        "kanban_cards": KANBAN_CARDS,
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2))
    print("Saved", MANIFEST_OUT)

    # Update png_catalog.json
    cat_path = SHOTS / "png_vault" / "png_catalog.json"
    if not cat_path.exists():
        return
    cat = json.loads(cat_path.read_text())
    new_files = {
        "kohnny_10repos_comparison_and_architecture.png",
        "wygwyl_3d_agent_office_and_pixel_lite_simulation.png",
        "wygwyl_kanban_worktree_crossmodel_pipeline.png",
    }
    items = [it for it in cat.get("items", []) if it.get("filename") not in new_files]
    new_entries = [
        {
            "id": "agent_office_10repos_ranking",
            "title": "Kohnny & 10 Open-Source Agent-Office / Worktree Kanban Repos: Ranked & Synthesized",
            "filename": "kohnny_10repos_comparison_and_architecture.png",
            "file": "png_vault/atlas_splats/kohnny_10repos_comparison_and_architecture.png",
            "category": "atlas_splats",
            "subcategory": "master_atlas_splat_sheet",
            "poem": "01",
            "width": 2400,
            "height": 1350,
            "desc": "Definitive ranking of all 10 open-source Kohnny alternatives (agent-office, agent-007, workbench, vibe-kanban, Claude-Office, PixelOffice, kanban-code, claude-code-kanban, pixel-agents, my-office) and how each is built into our WYGWYL studio.",
        },
        {
            "id": "agent_office_3d_and_2d_simulation",
            "title": "WYGWYL 3D Multiplayer Virtual Office (.GLB + .SPLAT) & /lite 2D Pixel Office Simulation",
            "filename": "wygwyl_3d_agent_office_and_pixel_lite_simulation.png",
            "file": "png_vault/atlas_splats/wygwyl_3d_agent_office_and_pixel_lite_simulation.png",
            "category": "atlas_splats",
            "subcategory": "megahub_splat_pack",
            "poem": "06",
            "width": 2400,
            "height": 1350,
            "desc": "Side-by-side simulation of our 3D Soundstage Floor (Club Atlantis .GLB + .SPLAT) with 6 interactive agent stations & 2.5D Cast alongside the /lite 2D Pixel Office view.",
        },
        {
            "id": "agent_office_kanban_worktree_pipeline",
            "title": "WYGWYL 5-Column Kanban + Git Worktree + Cross-Model Audit + 55m Cache Compaction Pipeline",
            "filename": "wygwyl_kanban_worktree_crossmodel_pipeline.png",
            "file": "png_vault/atlas_splats/wygwyl_kanban_worktree_crossmodel_pipeline.png",
            "category": "atlas_splats",
            "subcategory": "master_atlas_splat_sheet",
            "poem": "11",
            "width": 2400,
            "height": 1350,
            "desc": "5-Column Kanban board where every card spawns an isolated Git worktree, renders Before/After mockups in Planning, runs Cross-Model Audit (Codex auditing Claude), queues single-file in FIFO Merge, and auto-compacts at 55 minutes.",
        },
    ]
    cat["items"] = new_entries + items
    cat["total_count"] = len(cat["items"])
    cat["atlas_splats_count"] = sum(1 for x in cat["items"] if x.get("category") == "atlas_splats")
    if isinstance(cat.get("categories"), dict):
        cat["categories"]["atlas_splats"] = cat["atlas_splats_count"]
    cat_path.write_text(json.dumps(cat, indent=2))
    print("Updated png_catalog.json -> total:", cat["total_count"], "atlas_splats:", cat["atlas_splats_count"])


def spawn_real_worktree_handoff(card_id="WT-103"):
    """Create a real non-destructive .worktrees/<card-id>/HANDOFF_55M.md soul & handoff state note."""
    wt_root = ROOT / ".worktrees"
    wt_root.mkdir(parents=True, exist_ok=True)
    card = next((c for c in KANBAN_CARDS if c["id"] == card_id), KANBAN_CARDS[2])
    agent = next((a for a in AGENTS if a["id"] == card["agent_id"]), AGENTS[1])
    cdir = wt_root / card["id"].lower()
    cdir.mkdir(parents=True, exist_ok=True)
    handoff_md = cdir / "HANDOFF_55M.md"
    handoff_md.write_text(
        f"# ⏱️ 55-Minute Prompt-Cache Auto-Compaction Handoff Note (`{card['id']}`)\n\n"
        f"- **Card Title**: {card['title']}\n"
        f"- **Worktree Path**: `{card['worktree_path']}` (`{card['branch']}`)\n"
        f"- **Assigned Agent**: **{agent['name']}** (`{agent['harness']}`)\n"
        f"- **Cross-Model Auditor**: **{card['auditor']}**\n"
        f"- **Cache Elapsed at Compaction**: `{agent['cache_minutes_elapsed']}:00 / 55:00` (Saved before 60:00 TTL expiry)\n\n"
        f"## Persistent Soul\n> {agent['soul']}\n\n"
        f"## Memory & State Handoff\n"
        + "\n".join(f"- {m}" for m in agent["memory_notes"])
        + f"\n\n## Files Touched (FIFO Conflict Guard)\n"
        + "\n".join(f"- `{f}`" for f in card["files_touched"])
        + f"\n\n## Resume Command\n```bash\n{card['tmux_cmd']}\n```\n"
    )
    print("Wrote 55-minute handoff note:", handoff_md)


def main():
    parser = argparse.ArgumentParser(description="WYGWYL Agent Office & Worktree Kanban Orchestrator")
    parser.add_argument("--compact", type=str, default="WT-103", help="Generate 55-minute handoff note for card")
    args = parser.parse_args()

    render_plate_01_10repos_ranking()
    render_plate_02_3d_and_2d_office()
    render_plate_03_kanban_pipeline()
    update_catalog_and_manifest()
    spawn_real_worktree_handoff(args.compact)


if __name__ == "__main__":
    main()
