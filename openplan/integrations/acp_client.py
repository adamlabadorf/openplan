from typing import Optional


class GenerationError(Exception):
    """Raised when AI generation fails."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.details = details


class OpenCodeClient:
    """Context manager wrapper for AI code generation via ACP."""

    def __init__(
        self,
        project_dir: str,
        model: Optional[str] = None,
        agent: str = "build",
    ):
        self.project_dir = project_dir
        self.model = model
        self.agent = agent
        self._client = None

    def __enter__(self) -> "OpenCodeClient":
        try:
            from acp import ACPClient
        except ImportError:
            raise GenerationError(
                "ACPClient not found. Please install the acp package.",
                details="Run: pip install acp-client",
            )

        self._client = ACPClient(
            project_dir=self.project_dir,
            permission="allow",
            agent=self.agent,
        )
        if self.model:
            self._client.model = self.model
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            self._client.close()

    def generate(self, prompt: str) -> str:
        """Send a prompt and return the reply text."""
        if not self._client:
            raise GenerationError(
                "OpenCodeClient must be used as a context manager",
                details="Use: with OpenCodeClient(...) as client:",
            )

        try:
            response = self._client.generate(prompt)
            return response.text
        except Exception as e:
            raise GenerationError(f"Generation failed: {str(e)}", details=str(e)) from e
