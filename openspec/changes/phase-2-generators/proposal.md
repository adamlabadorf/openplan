## Why

OpenPlan currently lacks an automated generation layer to produce planning artifacts (roadmaps, epics, features) from vision statements. Manual creation is time-consuming and error-prone. Building this generation layer enables faster planning cycles and ensures consistent artifact structure.

## What Changes

- ACP client wrapper (`openplan/integrations/acp_client.py`) - thin wrapper around ACPClient
- Jinja2 template loader (`openplan/prompts/loader.py`) - loads and renders prompt templates
- Prompt templates (`openplan/prompts/templates/`) - roadmap, epic, critique, refine templates
- Planning engine (`openplan/core/engine.py`) - event loop driving artifact generation
- CLI additions (`openplan/cli/main.py`) - new generate-roadmap and decompose-epic commands
- Unit tests (`tests/test_engine.py`, `tests/test_prompts.py`)

## Capabilities

### New Capabilities

- `acp-integration`: ACP client wrapper with OpenCodeClient context manager for AI code generation
- `prompt-templates`: Jinja2-based prompt templates for roadmap, epic, critique, and refine operations
- `planning-engine`: Core engine that orchestrates artifact generation with validation and refinement loops
- `generation-cli`: CLI commands for roadmap generation and epic decomposition

### Modified Capabilities

- None - this is a new capability layer

## Impact

- New directory: `openplan/integrations/` for ACP client
- New directory: `openplan/prompts/` for template loading and templates
- New directory: `openplan/prompts/templates/` for Jinja2 templates
- New file: `openplan/core/engine.py` for planning engine
- Modified: `openplan/cli/main.py` for new CLI commands
- New test files: `tests/test_engine.py`, `tests/test_prompts.py`
