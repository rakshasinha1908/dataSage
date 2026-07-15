from core.ai.gemini_provider import GeminiProvider


class AIManager:
    """
    Responsible for selecting an AI provider.

    If one provider fails, the next available provider
    is tried automatically.
    """

    def __init__(self):

        self.providers = [
            GeminiProvider(),
        ]

    def generate(
        self,
        prompt: str,
    ) -> str:

        last_exception = None

        for provider in self.providers:

            try:
                return provider.generate(prompt)

            except Exception as error:
                last_exception = error

        raise RuntimeError(
            "All AI providers failed."
        ) from last_exception