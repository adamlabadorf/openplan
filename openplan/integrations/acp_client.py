"""
acp_client.py — OpenCode ACP integration for OpenPlan.

Wraps the real ACPClient from the opencode skill. Key design:
- One `opencode acp` subprocess per OpenCodeClient context manager lifetime.
- Each `generate()` call internally calls `new_session()` first, giving every
  generation task a completely clean context with no prior conversation history.
"""
import sys
import os
from typing import Optional

# ---------------------------------------------------------------------------
# Pull in the real ACPClient from the opencode skill
# ---------------------------------------------------------------------------
_SKILL_TOOLS = os.path.expanduser(
    "~/.openclaw/workspace/skills/opencode/tools"
)
if _SKILL_TOOLS not in sys.path:
    sys.path.insert(0, _SKILL_TOOLS)

from acp_client import ACPClient as _RealACPClient  # noqa: E402


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class GenerationError(Exception):
    """Raised when AI generation fails."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.details = details


# ---------------------------------------------------------------------------
# OpenCodeClient
# ---------------------------------------------------------------------------

class OpenCodeClient:
    """
    Context manager wrapping a single `opencode acp` subprocess.

    Usage::

        with OpenCodeClient(project_dir="/path/to/project") as client:
            result1 = client.generate("first task")   # isolated session
            result2 = client.generate("second task")  # isolated session

    Each call to :meth:`generate` creates a fresh ACP session (blank context)
    before sending the prompt, so there is no conversation bleed between calls.
    """

    def __init__(
        self,
        project_dir: str,
        model: Optional[str] = None,
        agent: str = "build",
    ):
        self.project_dir = project_dir
        self.model = model
        self.agent = agent
        self._client: Optional[_RealACPClient] = None

    def __enter__(self) -> "OpenCodeClient":
        self._client = _RealACPClient(
            cwd=self.project_dir,
            permission="allow",
            agent=self.agent,
        )
        self._client.__enter__()
        self._client.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client is not None:
            self._client.__exit__(exc_type, exc_val, exc_tb)
            self._client = None

    def generate(self, prompt: str) -> str:
        """
        Send *prompt* to OpenCode and return the full reply text.

        Internally calls ``new_session()`` before each prompt so that every
        generation task starts with a completely clean conversation context.
        """
        if self._client is None:
            raise GenerationError(
                "OpenCodeClient must be used as a context manager"
            )

        chunks: list[str] = []

        def on_update(update_type: str, update: dict) -> None:
            if update_type == "agent_message_chunk":
                text = update.get("content", {}).get("text", "")
                if text:
                    chunks.append(text)

        try:
            # Fresh session = blank context for every generation call
            self._client.new_session()
            self._client.prompt(prompt, on_update=on_update)
        except Exception as e:
            raise GenerationError(
                f"ACP generation failed: {e}", details=str(e)
            ) from e

        return "".join(chunks)
