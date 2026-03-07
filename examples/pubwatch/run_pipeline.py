#!/usr/bin/env python3
"""
Full OpenPlan → OpenSpec → OpenCode pipeline for pubwatch.

Runs autonomously:
  1. Decompose all epics into features (epic-scoped IDs)
  2. Stabilize each feature (expand criteria, set spec_ready=True)
  3. Export spec-ready features to OpenSpec
  4. Run /opsx-ff + /opsx-apply for each OpenSpec change via ACP

Writes a log to pipeline.log and a summary to pipeline_result.md.
"""

import sys, os, json, time, traceback, yaml, shutil
from pathlib import Path

PUBWATCH_DIR = Path(__file__).parent
OPENPLAN_PKG = Path(__file__).parent.parent.parent
sys.path.insert(0, str(OPENPLAN_PKG))
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/opencode/tools"))

from openplan.core.engine import PlanningEngine, PlanningError
from openplan.core.schemas import Epic, Feature, Roadmap
from openplan.core.stabilizer import FeatureStabilizer
from openplan.integrations.openspec import export_feature, ExportError
from acp_client import ACPClient

LOG = open(PUBWATCH_DIR / "pipeline.log", "w", buffering=1)
RESULT = []

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.write(line + "\n")

def section(title):
    log(f"\n{'='*60}")
    log(f"  {title}")
    log(f"{'='*60}")


# ── Setup ─────────────────────────────────────────────────────────────────────
section("SETUP")

# Clean stale feature files from prior runs to avoid ID collisions on disk
features_dir = PUBWATCH_DIR / "openplan" / "features"
if features_dir.exists():
    stale = list(features_dir.glob("*.yaml"))
    for f in stale:
        f.unlink()
    if stale:
        log(f"Cleaned {len(stale)} stale feature files")

engine = PlanningEngine(
    plan_dir=str(PUBWATCH_DIR / "openplan"),
    project_dir=str(PUBWATCH_DIR),
    model="ollama/qwen3-coder:30b",
)
stabilizer = FeatureStabilizer(engine)

# Load roadmap
roadmap_dir = PUBWATCH_DIR / "openplan" / "roadmaps"
roadmap_files = list(roadmap_dir.glob("*.yaml"))
if not roadmap_files:
    log("ERROR: No roadmap found. Run openplan generate-roadmap first.")
    sys.exit(1)

with open(roadmap_files[0]) as f:
    roadmap_data = yaml.safe_load(f)

roadmap = Roadmap(**roadmap_data)
log(f"Loaded roadmap: {roadmap.id} — {roadmap.title}")
log(f"Epics: {[e.id for e in roadmap.epics]}")


# ── Phase 1: Decompose Epics ──────────────────────────────────────────────────
section("PHASE 1: EPIC DECOMPOSITION")

all_features: list[Feature] = []

for epic in roadmap.epics:
    log(f"Decomposing: {epic.id} — {epic.title}")
    try:
        features = engine.decompose_epic(epic)
        log(f"  → {len(features)} features: {[f.id for f in features]}")
        all_features.extend(features)
        RESULT.append({"epic": epic.id, "features": [f.id for f in features], "status": "decomposed"})
    except Exception as e:
        log(f"  ERROR: {e}")
        RESULT.append({"epic": epic.id, "status": f"decompose_failed: {e}"})
        traceback.print_exc(file=LOG)

log(f"\nTotal features: {len(all_features)}")


# ── Phase 2: Stabilize Features ───────────────────────────────────────────────
section("PHASE 2: FEATURE STABILIZATION")

stabilized: list[Feature] = []

for feature in all_features:
    log(f"Stabilizing: {feature.id}")
    try:
        stable = stabilizer.stabilize(feature)
        log(f"  → spec_ready={stable.spec_ready}, criteria={len(stable.acceptance_criteria)}")
        stabilized.append(stable)
    except Exception as e:
        log(f"  ERROR: {e}")
        traceback.print_exc(file=LOG)

log(f"\nStabilized: {len(stabilized)}/{len(all_features)}")


# ── Phase 3: Export to OpenSpec ───────────────────────────────────────────────
section("PHASE 3: OPENSPEC EXPORT")

openspec_dir = PUBWATCH_DIR
exported: list[Feature] = []

for feature in stabilized:
    if not feature.spec_ready:
        log(f"  SKIP {feature.id} — not spec_ready")
        continue
    log(f"Exporting: {feature.id}")
    try:
        change_path = export_feature(feature=feature, openspec_dir=openspec_dir)
        log(f"  → {change_path}")
        exported.append(feature)
    except Exception as e:
        log(f"  ERROR: {e}")
        traceback.print_exc(file=LOG)

log(f"\nExported {len(exported)} features")


# ── Phase 4: Implement via OpenCode ──────────────────────────────────────────
section("PHASE 4: IMPLEMENTATION VIA OPENCODE")

impl_results: list[dict] = []

for feature in exported:
    change_id = feature.id
    log(f"\nImplementing: {change_id} — {feature.title}")
    try:
        with ACPClient(cwd=str(PUBWATCH_DIR), permission="allow", agent="build") as client:
            client.initialize()
            client.new_session()
            chunks = []
            def on_update(t, u):
                if t == "agent_message_chunk":
                    txt = u.get("content", {}).get("text", "")
                    if txt:
                        chunks.append(txt)
            # Fast-forward spec then apply
            ff_prompt = f"/opsx-ff {change_id}\n\n{feature.title}\n\nGoal: {feature.description}\n\nAcceptance criteria:\n" + "\n".join(f"- {c}" for c in feature.acceptance_criteria)
            ff_result = client.prompt(ff_prompt, on_update=on_update)
            log(f"  ff done: {ff_result['stop_reason']}")

            client.new_session()
            chunks2 = []
            def on_update2(t, u):
                if t == "agent_message_chunk":
                    txt = u.get("content", {}).get("text", "")
                    if txt:
                        chunks2.append(txt)
            apply_result = client.prompt(f"/opsx-apply {change_id}", on_update=on_update2)
            log(f"  apply done: {apply_result['stop_reason']}")
            log(f"  preview: {''.join(chunks2)[:200]}")
            impl_results.append({"feature": change_id, "status": "done"})
    except Exception as e:
        log(f"  ERROR: {e}")
        impl_results.append({"feature": change_id, "status": f"failed: {e}"})
        traceback.print_exc(file=LOG)

    time.sleep(3)


# ── Summary ───────────────────────────────────────────────────────────────────
section("PIPELINE COMPLETE")

done_count = len([r for r in impl_results if r["status"] == "done"])
summary = f"""# OpenPlan Pubwatch Pipeline — Results

**Roadmap:** {roadmap.id} — {roadmap.title}
**Epics:** {len(roadmap.epics)}
**Features generated:** {len(all_features)}
**Features stabilized:** {len(stabilized)}
**Features exported to OpenSpec:** {len(exported)}
**Features implemented:** {done_count}

## Epic Breakdown
""" + "\n".join(
    f"- **{r['epic']}** ({r['status']}): {', '.join(r.get('features', []))}"
    for r in RESULT
) + "\n\n## Implementation Results\n" + "\n".join(
    f"- **{r['feature']}**: {r['status']}" for r in impl_results
)

with open(PUBWATCH_DIR / "pipeline_result.md", "w") as f:
    f.write(summary)

log("\n" + summary)
LOG.close()
print("\nDone. See pipeline_result.md")
