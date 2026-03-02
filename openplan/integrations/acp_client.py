"""
acp_client.py — OpenCode ACP integration for OpenPlan.

Wraps the ACPClient from the opencode skill to provide a clean
generate() interface for the PlanningEngine.
"""
import sys
import os
from typing import Optional

# ---------------------------------------------------------------------------
# Inline the real ACPClient from the opencode skill
# ---------------------------------------------------------------------------
_SKILL_TOOLS = os.path.expanduser(
    "~/.openclaw/workspace/skills/opencode/tools"
)
if _SKILL_TOOLS not in sys.path:
    sys.path.insert(0, _SKILL_TOOLS)

from acp_client import ACPClient  # noqa: E402  (the real one)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class GenerationError(Exception):
    """Raised when AI generation fails."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.details = details


# ---------------------------------------------------------------------------
# OpenCodeClient wrapper
# ---------------------------------------------------------------------------

class OpenCodeClient:
    """Context manager that drives OpenCode via ACP and returns reply text."""

    def __init__(
        self,
        project_dir: str,
        model: Optional[str] = None,
        agent: str = "build",
    ):
        self.project_dir = project_dir
        self.model = model
        self.agent = agent
        self._client: Optional[ACPClient] = None
        self._ctx = None

    def __enter__(self) -> "OpenCodeClient":
        self._client = ACPClient(
            cwd=self.project_dir,
            permission="allow",
            agent=self.agent,
        )
        self._ctx = self._client.__enter__()
        self._ctx.initialize()
        self._ctx.new_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            self._client.__exit__(exc_type, exc_val, exc_tb)

    def generate(self, prompt: str) -> str:
        """Send a prompt to OpenCode and return the full reply text."""
        if not self._ctx:
            raise GenerationError("OpenCodeClient must be used as a context manager")

        chunks: list[str] = []

        def on_update(update_type: str, update: dict) -> None:
            if update_type == "agent_message_chunk":
                text = update.get("content", {}).get("text", "")
                if text:
                    chunks.append(text)

        try:
            self._ctx.prompt(prompt, on_update=on_update)
        except Exception as e:
            raise GenerationError(f"ACP generation failed: {e}", details=str(e)) from e

        return "".join(chunks)
