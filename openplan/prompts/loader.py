from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class TemplateLoader:
    """Loads and renders Jinja2 templates for prompt generation."""

    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir is None:
            templates_dir = str(Path(__file__).parent / "templates")
        else:
            templates_dir = str(Path(templates_dir))

        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def render(self, template_name: str, context: dict) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file (e.g., 'roadmap.j2')
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template string

        Raises:
            TemplateNotFound: If the template doesn't exist
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise TemplateNotFound(
                f"Template '{template_name}' not found in {self.templates_dir}"
            )
