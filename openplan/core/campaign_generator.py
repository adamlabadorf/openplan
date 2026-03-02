import yaml
from pathlib import Path

from openplan.core.schemas import Campaign
from openplan.core.engine import PlanningEngine, PlanningError


class CampaignGenerator:
    """Generator for campaign YAMLs for technical debt remediation."""

    MAX_REFINEMENTS = 2

    def __init__(self, engine: PlanningEngine):
        self.engine = engine

    def generate(
        self,
        subsystem: str,
        technical_debt: str = "",
    ) -> Campaign:
        """Generate a campaign for a subsystem.

        Args:
            subsystem: The subsystem to generate a campaign for
            technical_debt: Description of technical debt to address

        Returns:
            Validated Campaign object

        Raises:
            PlanningError: If generation fails after max refinements
        """
        context = {
            "subsystem": subsystem,
            "technical_debt": technical_debt,
        }

        with self.engine.client_context():
            campaign_yaml = self._generate_with_validation(
                template_name="campaign.j2",
                context=context,
            )

        if isinstance(campaign_yaml, dict):
            campaign = Campaign(**campaign_yaml)
            self._persist_campaign(campaign)
            return campaign
        else:
            raise PlanningError("Generated campaign is not a valid dictionary")

    def _generate_with_validation(
        self,
        template_name: str,
        context: dict,
    ) -> dict:
        """Generate content with validation and max refinement iterations.

        Args:
            template_name: Name of the template to use
            context: Template context

        Returns:
            Parsed and validated YAML data

        Raises:
            PlanningError: If validation fails after max refinements
        """
        import json

        validation_errors = None
        current_yaml = {}
        critique_result = {}

        for iteration in range(self.MAX_REFINEMENTS + 1):
            if iteration == 0:
                prompt = self.engine.template_loader.render(template_name, context)
            else:
                refine_context = {
                    "artifact_type": "campaign",
                    "artifact_yaml": yaml.dump(current_yaml),
                    "critique_json": json.dumps(critique_result),
                }
                prompt = self.engine.template_loader.render("refine.j2", refine_context)

            generated_yaml = self.engine._generate(prompt)

            try:
                parsed = yaml.safe_load(generated_yaml)
                if parsed is None:
                    parsed = {}
                current_yaml = parsed
            except yaml.YAMLError as e:
                validation_errors = [str(e)]
                if iteration < self.MAX_REFINEMENTS:
                    critique_result = self.engine._critique(
                        "campaign", generated_yaml, [str(e)]
                    )
                    continue
                else:
                    raise PlanningError(
                        f"Failed to parse generated campaign after {self.MAX_REFINEMENTS} refinements",
                        validation_errors=validation_errors,
                    )

            try:
                campaign = Campaign(**current_yaml)
                if (
                    not campaign.rollback_strategy
                    or not campaign.rollback_strategy.strip()
                ):
                    raise ValueError("Campaign must have a non-empty rollback_strategy")
            except Exception as e:
                validation_errors = [str(e)]
                if iteration < self.MAX_REFINEMENTS:
                    critique_result = self.engine._critique(
                        "campaign", generated_yaml, [str(e)]
                    )
                    continue
                else:
                    raise PlanningError(
                        f"Validation failed for campaign after {self.MAX_REFINEMENTS} refinements",
                        validation_errors=validation_errors,
                    )

            return current_yaml

        raise PlanningError(
            f"Failed to generate valid campaign after {self.MAX_REFINEMENTS} refinements"
        )

    def _persist_campaign(self, campaign: Campaign) -> None:
        """Persist campaign to plan directory."""
        campaigns_dir = self.engine.plan_dir / "campaigns"
        campaigns_dir.mkdir(parents=True, exist_ok=True)
        filepath = campaigns_dir / f"{campaign.id}.yaml"
        with open(filepath, "w") as f:
            yaml.dump(campaign.model_dump(by_alias=True), f, default_flow_style=False)
