## Why

OpenPlan currently generates specs internally but has no way to export them in OpenSpec format for use with the openspec CLI tooling. This limits the ability to leverage OpenSpec's structured change management and tracking capabilities. Adding an OpenSpec adapter enables users to export spec-ready features directly into the OpenSpec workflow.

## What Changes

1. **New OpenSpec Adapter Module** (`openplan/integrations/openspec.py`)
   - `feature_to_openspec_input()` - converts Feature to OpenSpec input format
   - `export_feature()` - exports feature to OpenSpec change directory
   - `ExportError` exception class

2. **New CLI Command** (`openplan export-to-openspec`)
   - `openplan export-to-openspec FEATURE_ID [--openspec-dir PATH] [--arch-context TEXT]`
   - Validates spec_ready before export

3. **New Status Command** (`openplan status`)
   - Shows vision loaded status
   - Roadmap, features, campaigns, ADRs counts
   - Lists spec_ready features
   - Shows locked artifacts

4. **Integration Tests** (`tests/test_integration.py`)
   - Full pipeline tests with mocked LLM
   - Export blocked if not ready test
   - Status command test

5. **README Update**
   - Document all CLI commands with usage examples
   - Include sample vision.yaml

## Capabilities

### New Capabilities

- `openspec-adapter`: Export features to OpenSpec format for integration with openspec CLI tooling
- `status-command`: Display plan state summary with feature readiness information

### Modified Capabilities

<!-- No existing capability requirements are changing -->

## Impact

- New file: `openplan/integrations/openspec.py`
- CLI changes: `openplan/cli/main.py` - add export-to-openspec and status commands
- New test file: `tests/test_integration.py`
- Documentation: `README.md` updates
