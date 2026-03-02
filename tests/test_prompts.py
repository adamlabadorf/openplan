import pytest
from pathlib import Path
import tempfile
import shutil

from jinja2 import TemplateNotFound

from openplan.prompts.loader import TemplateLoader


@pytest.fixture
def temp_template_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


class TestTemplateLoader:
    def test_default_templates_directory(self):
        loader = TemplateLoader()
        assert "templates" in str(loader.templates_dir)

    def test_custom_templates_directory(self, temp_template_dir):
        loader = TemplateLoader(templates_dir=str(temp_template_dir))
        assert loader.templates_dir == str(temp_template_dir)

    def test_render_with_context(self, temp_template_dir):
        template_path = temp_template_dir / "test.j2"
        template_path.write_text("Hello {{ name }}!")

        loader = TemplateLoader(templates_dir=str(temp_template_dir))
        result = loader.render("test.j2", {"name": "World"})

        assert result == "Hello World!"

    def test_render_missing_template_raises_error(self, temp_template_dir):
        loader = TemplateLoader(templates_dir=str(temp_template_dir))

        with pytest.raises(TemplateNotFound):
            loader.render("nonexistent.j2", {})

    def test_render_with_multiple_variables(self, temp_template_dir):
        template_path = temp_template_dir / "multi.j2"
        template_path.write_text(
            "{{ greeting }} {{ name }}, you have {{ count }} items."
        )

        loader = TemplateLoader(templates_dir=str(temp_template_dir))
        result = loader.render(
            "multi.j2",
            {
                "greeting": "Hello",
                "name": "Alice",
                "count": 5,
            },
        )

        assert result == "Hello Alice, you have 5 items."

    def test_render_with_loops(self, temp_template_dir):
        template_path = temp_template_dir / "loop.j2"
        template_path.write_text("{% for item in items %}{{ item }},{% endfor %}")

        loader = TemplateLoader(templates_dir=str(temp_template_dir))
        result = loader.render("loop.j2", {"items": ["a", "b", "c"]})

        assert result == "a,b,c,"

    def test_render_with_conditionals(self, temp_template_dir):
        template_path = temp_template_dir / "conditional.j2"
        template_path.write_text("{% if enabled %}Yes{% else %}No{% endif %}")

        loader = TemplateLoader(templates_dir=str(temp_template_dir))

        result_true = loader.render("conditional.j2", {"enabled": True})
        assert result_true == "Yes"

        result_false = loader.render("conditional.j2", {"enabled": False})
        assert result_false == "No"

    def test_render_empty_context(self, temp_template_dir):
        template_path = temp_template_dir / "empty.j2"
        template_path.write_text("No variables here!")

        loader = TemplateLoader(templates_dir=str(temp_template_dir))
        result = loader.render("empty.j2", {})

        assert result == "No variables here!"
