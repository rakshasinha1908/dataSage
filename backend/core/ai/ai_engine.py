from core.ai.manager import AIManager


class AIEngine:
    """
    Thin wrapper around the AI provider.

    Given a prompt, returns the model's response.
    """

    def __init__(self):
        self.ai_manager = AIManager()

    def generate(
        self,
        prompt: str,
    ) -> str:

        return self.ai_manager.generate(
            prompt,
        )