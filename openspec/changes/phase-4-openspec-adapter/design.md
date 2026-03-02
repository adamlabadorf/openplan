## Context

OpenPlan is a CLI tool for managing project roadmaps, epics, and features. Currently it generates specs internally but lacks integration with OpenSpec CLI tooling. This design outlines how to add OpenSpec adapter functionality to enable exporting spec-ready features to OpenSpec format.

Current constraints:
- Features must be marked `spec_ready=True` before export
- Uses Path-based file I/O for storage
- LLM calls are made via OpenCode adapter (not directly)

## Goals / Non-Goals

**Goals:**
- Create `openspec.py` adapter module with export functionality
- Add `export-to-openspec` CLI command
- Add `status` CLI command to show plan state
- Add integration tests for full pipeline with mocked LLM
- Update README with CLI documentation

**Non-Goals:**
- Do NOT call OpenCode from export_feature - only use openspec CLI
- Do NOT implement real OpenSpec API integration (only CLI subprocess)
- Do NOT add authentication or OAuth flows

## Decisions

1. **Subprocess for openspec CLI** - Using `subprocess.run()` to call `openspec new change` rather than importing openspec as a library. This keeps the adapter simple and decoupled.

2. **ExportError as distinct exception** - Created in `openplan/integrations/openspec.py` to allow callers to distinguish export failures from other errors.

3. **Mocked LLM in integration tests** - Using pytest-mock or unittest.mock to mock LLM responses, enabling fully isolated tests without real API calls.

4. **Status command shows spec_ready count** - Displaying both total features and spec_ready count helps users understand export readiness.

## Risks / Trade-offs

- **Subprocess dependency** → If openspec CLI is not installed, export fails with clear error message. This is intentional - users must have openspec installed.

- **No delta spec support** - Currently only new capability export is supported. Modified capabilities would require additional delta spec logic.

- **Test isolation** → Integration tests use tmp_path fixture to avoid disk side effects. Each test is self-contained.

## Migration Plan

1. Deploy new code to pypi
2. Users run `pip install openplan` to get update
3. Run `openplan status` to verify installation

## Open Questions

- Should we support exporting multiple features at once?
- Should we validate vision.yaml exists before allowing export?
