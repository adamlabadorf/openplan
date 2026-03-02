import yaml
from pathlib import Path

from openplan.core.schemas import ADR
from openplan.core.engine import PlanningEngine, PlanningError


class ADRGenerator:
    """Generator for Architecture Decision Records (ADRs)."""

    MAX_REFINEMENTS = 2

    def __init__(self, engine: PlanningEngine):
        self.engine = engine

    def generate(
        self,
        decision_context: str,
        alternatives: str = "",
    ) -> ADR:
        """Generate an ADR for a technical decision.

        Args:
            decision_context: Background and context for the decision
            alternatives: Alternative approaches considered

        Returns:
            Validated ADR object

        Raises:
            PlanningError: If generation fails after max refinements
        """
        context = {
            "decision_context": decision_context,
            "alternatives": alternatives,
        }

        adr_yaml = self._generate_with_validation(
            template_name="adr.j2",
            context=context,
        )

        if isinstance(adr_yaml, dict):
            adr = ADR(**adr_yaml)
            adr.id = self._generate_adr_id()
            self._persist_adr(adr)
            return adr
        else:
            raise PlanningError("Generated ADR is not a valid dictionary")

    def _generate_adr_id(self) -> str:
        """Generate sequential ADR ID."""
        adrs_dir = self.engine.plan_dir / "adrs"
        adrs_dir.mkdir(parents=True, exist_ok=True)

        existing_adrs = list(adrs_dir.glob("adr-*.yaml"))
        if not existing_adrs:
            return "adr-1"

        max_num = 0
        for adr_file in existing_adrs:
            try:
                num = int(adr_file.stem.split("-")[1])
                if num > max_num:
                    max_num = num
            except (IndexError, ValueError):
                continue

        return f"adr-{max_num + 1}"

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
                    "artifact_type": "adr",
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
                        "adr", generated_yaml, [str(e)]
                    )
                    continue
                else:
                    raise PlanningError(
                        f"Failed to parse generated ADR after {self.MAX_REFINEMENTS} refinements",
                        validation_errors=validation_errors,
                    )

            try:
                ADR(**current_yaml)
            except Exception as e:
                validation_errors = [str(e)]
                if iteration < self.MAX_REFINEMENTS:
                    critique_result = self.engine._critique(
                        "adr", generated_yaml, [str(e)]
                    )
                    continue
                else:
                    raise PlanningError(
                        f"Validation failed for ADR after {self.MAX_REFINEMENTS} refinements",
                        validation_errors=validation_errors,
                    )

            return current_yaml

        raise PlanningError(
            f"Failed to generate valid ADR after {self.MAX_REFINEMENTS} refinements"
        )

    def _persist_adr(self, adr: ADR) -> None:
        """Persist ADR to plan directory."""
        adrs_dir = self.engine.plan_dir / "adrs"
        adrs_dir.mkdir(parents=True, exist_ok=True)
        filepath = adrs_dir / f"{adr.id}.yaml"
        with open(filepath, "w") as f:
            yaml.dump(adr.model_dump(by_alias=True), f, default_flow_style=False)
