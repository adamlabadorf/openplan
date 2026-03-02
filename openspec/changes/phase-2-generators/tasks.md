## 1. ACP Integration

- [x] 1.1 Copy acp_client.py from skills/opencode/tools/ to openplan/integrations/acp_client.py
- [x] 1.2 Create OpenCodeClient context manager class in openplan/integrations/acp_client.py
- [x] 1.3 Implement generate() method that sends prompt and returns reply text
- [x] 1.4 Add GenerationError exception class
- [x] 1.5 Ensure all requests use permission="allow"
- [x] 1.6 Set default agent="build" in OpenCodeClient

## 2. Jinja2 Template Loader

- [x] 2.1 Create openplan/prompts/ directory structure
- [x] 2.2 Create openplan/prompts/templates/ directory
- [x] 2.3 Implement TemplateLoader class in openplan/prompts/loader.py
- [x] 2.4 Implement render() method with template_name and context parameters
- [x] 2.5 Add error handling for missing templates
- [x] 2.6 Set default templates directory to openplan/prompts/templates/

## 3. Prompt Templates

- [x] 3.1 Create roadmap.j2 template for roadmap generation
- [x] 3.2 Create epic.j2 template for epic decomposition
- [x] 3.3 Create critique.j2 template for artifact critique
- [x] 3.4 Create refine.j2 template for artifact refinement
- [x] 3.5 Add "Respond with ONLY valid YAML" instruction to all templates

## 4. Planning Engine

- [x] 4.1 Create openplan/core/ directory if needed
- [x] 4.2 Implement PlanningEngine class in openplan/core/engine.py
- [x] 4.3 Implement generate_roadmap() method with template rendering
- [x] 4.4 Implement YAML parsing and Pydantic validation in generate_roadmap()
- [x] 4.5 Add critique/refine loop (max 2 iterations) to generate_roadmap()
- [x] 4.6 Persist roadmap.yaml to openplan/ directory
- [x] 4.7 Implement decompose_epic() method
- [x] 4.8 Add critique/refine loop to decompose_epic()
- [x] 4.9 Persist feature YAMLs to openplan/features/ directory
- [x] 4.10 Raise PlanningError on validation failure after 2 refinements

## 5. CLI Commands

- [x] 5.1 Add generate-roadmap command to openplan/cli/main.py
- [x] 5.2 Add --vision-file option to generate-roadmap
- [x] 5.3 Add --model option to generate-roadmap
- [x] 5.4 Add --time-horizon option to generate-roadmap
- [x] 5.5 Add decompose-epic command to openplan/cli/main.py
- [x] 5.6 Add --model option to decompose-epic

## 6. Unit Tests

- [x] 6.1 Create tests/test_engine.py
- [x] 6.2 Create tests/test_prompts.py
- [x] 6.3 Write unit tests for TemplateLoader render()
- [x] 6.4 Write unit tests for missing template error
- [x] 6.5 Mock OpenCodeClient in engine tests
- [x] 6.6 Test happy path for generate_roadmap()
- [x] 6.7 Test refinement loop behavior
- [x] 6.8 Test failure after 2 refinement attempts
- [x] 6.9 Test happy path for decompose_epic()
