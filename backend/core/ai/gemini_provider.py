import os

from google import genai
from core.ai.provider import AIProvider


class GeminiProvider(AIProvider):
    """
    Google Gemini implementation.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found.")

        self.client = genai.Client(api_key=api_key)


    def generate(self, prompt: str) -> str:
        models = [
            os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
        ]

        last_exception = None

        for model in models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=[
                        {
                            "role": "user",
                            "parts": [{"text": prompt}],
                        }
                    ],
                )

                if response.text:
                    return response.text.strip()

            except Exception as error:
                last_exception = error

        raise RuntimeError("All Gemini models failed.") from last_exception
