#!/usr/bin/env python3
"""
Full OpenPlan → OpenSpec → OpenCode pipeline for pubwatch.

Runs autonomously:
  1. Decompose all 3 epics into features
  2. Stabilize each feature (expand criteria, set spec_ready=True)
  3. Export spec-ready features to OpenSpec
  4. Run /opsx-apply for each OpenSpec change via ACP

Writes a log to pipeline.log and a summary to pipeline_result.md.
"""

import sys, os, json, time, traceback, yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "openplan"))
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/opencode/tools"))

PUBWATCH_DIR = Path(__file__).parent
OPENPLAN_PKG = Path(__file__).parent.parent.parent
sys.path.insert(0, str(OPENPLAN_PKG))

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
log(f"Loaded roadmap: {roadmap.id} with {len(roadmap.epics)} epics")


# ── Phase 1: Decompose Epics ──────────────────────────────────────────────────
section("PHASE 1: EPIC DECOMPOSITION")

all_features: list[Feature] = []

for epic in roadmap.epics:
    log(f"Decomposing epic: {epic.id} — {epic.title}")
    try:
        features = engine.decompose_epic(epic)
        log(f"  → {len(features)} features generated")
        for f in features:
            log(f"    - {f.id}: {f.description[:60]}")
        all_features.extend(features)
        RESULT.append({"epic": epic.id, "features": [f.id for f in features], "status": "decomposed"})
    except Exception as e:
        log(f"  ERROR decomposing {epic.id}: {e}")
        RESULT.append({"epic": epic.id, "status": f"decompose_failed: {e}"})
        traceback.print_exc(file=LOG)

log(f"\nTotal features generated: {len(all_features)}")


# ── Phase 2: Stabilize Features ───────────────────────────────────────────────
section("PHASE 2: FEATURE STABILIZATION")

stabilized: list[Feature] = []

for feature in all_features:
    log(f"Stabilizing: {feature.id} — {feature.description[:50]}")
    try:
        stable = stabilizer.stabilize(feature)
        log(f"  → spec_ready={stable.spec_ready}, criteria={len(stable.acceptance_criteria)}")
        stabilized.append(stable)
    except Exception as e:
        log(f"  ERROR stabilizing {feature.id}: {e}")
        traceback.print_exc(file=LOG)

log(f"\nStabilized: {len(stabilized)}/{len(all_features)} features spec_ready")


# ── Phase 3: Export to OpenSpec ───────────────────────────────────────────────
section("PHASE 3: OPENSPEC EXPORT")

openspec_dir = PUBWATCH_DIR
exported_changes: list[str] = []

for feature in stabilized:
    if not feature.spec_ready:
        log(f"  SKIP {feature.id} — not spec_ready")
        continue
    log(f"Exporting: {feature.id}")
    try:
        change_path = export_feature(
            feature=feature,
            openspec_dir=openspec_dir,
        )
        log(f"  → OpenSpec change created: {change_path}")
        exported_changes.append(feature.id)
    except ExportError as e:
        log(f"  ERROR exporting {feature.id}: {e}")
    except Exception as e:
        log(f"  ERROR exporting {feature.id}: {e}")
        traceback.print_exc(file=LOG)

log(f"\nExported {len(exported_changes)} features to OpenSpec")


# ── Phase 4: Implement via OpenCode /opsx-apply ───────────────────────────────
section("PHASE 4: IMPLEMENTATION VIA OPENCODE")

impl_results: list[dict] = []

for change_id in exported_changes:
    log(f"Implementing: {change_id}")
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
            result = client.prompt(f"/opsx-apply {change_id}", on_update=on_update)
            reply = "".join(chunks)
            log(f"  → stop_reason={result['stop_reason']}")
            log(f"  → reply preview: {reply[:200]}")
            impl_results.append({"feature": change_id, "status": "done", "stop_reason": result["stop_reason"]})
    except Exception as e:
        log(f"  ERROR implementing {change_id}: {e}")
        impl_results.append({"feature": change_id, "status": f"failed: {e}"})
        traceback.print_exc(file=LOG)

    # Brief pause between sessions to avoid resource contention
    time.sleep(5)


# ── Summary ───────────────────────────────────────────────────────────────────
section("PIPELINE COMPLETE")

summary_lines = [
    "# OpenPlan Pubwatch Pipeline — Results\n",
    f"**Roadmap:** {roadmap.id} — {roadmap.title}",
    f"**Epics:** {len(roadmap.epics)}",
    f"**Features generated:** {len(all_features)}",
    f"**Features stabilized:** {len(stabilized)}",
    f"**Features exported to OpenSpec:** {len(exported_changes)}",
    f"**Features implemented:** {len([r for r in impl_results if r['status'] == 'done'])}",
    "",
    "## Epic Breakdown",
]
for r in RESULT:
    feats = r.get("features", [])
    summary_lines.append(f"- **{r['epic']}** ({r['status']}): {', '.join(feats) if feats else 'none'}")

summary_lines += ["", "## Implementation Results"]
for r in impl_results:
    summary_lines.append(f"- **{r['feature']}**: {r['status']}")

summary = "\n".join(summary_lines)

with open(PUBWATCH_DIR / "pipeline_result.md", "w") as f:
    f.write(summary)

log("\n" + summary)
LOG.close()
print("\nDone. See pipeline_result.md for full summary.")
