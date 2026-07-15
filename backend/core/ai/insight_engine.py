from core.ai.manager import AIManager
from core.ai.prompt_builder import PromptBuilder
from models.insight_request import InsightRequest


class InsightEngine:
    """
    Generates AI explanations
    for deterministic analytical results.
    """

    def __init__(self):

        self.ai_manager = AIManager()

    def generate(
        self,
        request: InsightRequest,
    ) -> str:

        prompt = PromptBuilder.build(
            request,
        )

        return self.ai_manager.generate(
            prompt,
        )