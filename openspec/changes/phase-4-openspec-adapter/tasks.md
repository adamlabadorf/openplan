## 1. OpenSpec Adapter Module

- [x] 1.1 Create `openplan/integrations/openspec.py` file
- [x] 1.2 Define `ExportError` exception class
- [x] 1.3 Implement `feature_to_openspec_input(feature, arch_context)` function
- [x] 1.4 Implement `export_feature(feature, openspec_dir, arch_context)` function
- [x] 1.5 Add spec_ready validation in export_feature
- [x] 1.6 Add openspec CLI validation in export_feature
- [x] 1.7 Add subprocess call to create openspec change
- [x] 1.8 Add file write for change proposal

## 2. CLI Commands

- [ ] 2.1 Add `export-to-openspec` command to CLI
- [ ] 2.2 Add `--openspec-dir` option to export command
- [ ] 2.3 Add `--arch-context` option to export command
- [ ] 2.4 Add `status` command to CLI
- [ ] 2.5 Implement vision loaded status check
- [ ] 2.6 Implement roadmap epics count
- [ ] 2.7 Implement features total and spec_ready count
- [ ] 2.8 Implement campaigns count
- [ ] 2.9 Implement adrs count
- [ ] 2.10 Implement locked artifacts listing

## 3. Integration Tests

- [ ] 3.1 Create `tests/test_integration.py` file
- [ ] 3.2 Implement `test_full_roadmap_pipeline` with mocked LLM
- [ ] 3.3 Implement `test_full_epic_decomposition` with mocked LLM
- [ ] 3.4 Implement `test_feature_stabilization_pipeline` with mocked LLM
- [ ] 3.5 Implement `test_openspec_export_blocked_if_not_ready`
- [ ] 3.6 Implement `test_status_command`
- [ ] 3.7 Use tmp_path fixture for isolation
- [ ] 3.8 Mock all LLM calls in tests

## 4. Documentation

- [x] 4.1 Update README.md with CLI commands documentation
- [x] 4.2 Add usage examples for all commands
- [x] 4.3 Include sample vision.yaml example
- [x] 4.4 Validate vision.yaml against Vision Pydantic schema
