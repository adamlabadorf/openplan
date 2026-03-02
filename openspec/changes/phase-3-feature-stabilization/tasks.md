## 1. Prompt Templates

- [x] 1.1 Create stabilize_feature.j2 template in openplan/prompts/templates/
- [x] 1.2 Create campaign.j2 template in openplan/prompts/templates/
- [x] 1.3 Create adr.j2 template in openplan/prompts/templates/

## 2. FeatureStabilizer Implementation

- [x] 2.1 Create openplan/core/stabilizer.py with FeatureStabilizer class
- [x] 2.2 Implement stabilize() method with generate→validate→critique→refine loop
- [x] 2.3 Add min 3 testable criteria enforcement
- [x] 2.4 Add spec_ready=True after successful validation

## 3. CampaignGenerator Implementation

- [x] 3.1 Create openplan/core/campaign_generator.py with CampaignGenerator class 3.2
- [x] Implement generate() method with subsystem and technical_debt params
- [x] 3.3 Add validation for non-empty rollback_strategy
- [x] 3.4 Add max 2 refinement iterations
- [x] 3.5 Add persistence to openplan/campaigns/<id>.yaml

## 4. ADRGenerator Implementation

- [x] 4.1 Create openplan/core/adr_generator.py with ADRGenerator class
- [x] 4.2 Implement generate() method with decision_context and alternatives
- [x] 4.3 Add sequential ID generation (adr-<N>)
- [x] 4.4 Add max 2 refinement iterations
- [x] 4.5 Add persistence to openplan/adrs/<id>.yaml

## 5. CLI Commands

- [x] 5.1 Add stabilize-feature command to openplan/cli/main.py
- [x] 5.2 Add generate-campaign command to openplan/cli/main.py
- [x] 5.3 Add generate-adr command to openplan/cli/main.py
- [x] 5.4 Add --model flag support to all commands
- [x] 5.5 Add --debt flag to generate-campaign
- [x] 5.6 Add --context flag to generate-adr

## 6. Unit Tests

- [x] 6.1 Write unit tests for FeatureStabilizer (mock engine, happy path)
- [x] 6.2 Test spec_ready=True after stabilization
- [x] 6.3 Write unit tests for CampaignGenerator (mock engine)
- [x] 6.4 Test validation fails for empty rollback_strategy
- [x] 6.5 Write unit tests for ADRGenerator (mock engine)
- [x] 6.6 Test sequential ID generation
- [x] 6.7 Write unit tests for CLI commands using Typer test client
