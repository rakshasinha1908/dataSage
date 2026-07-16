from models.insight_request import InsightRequest


class PromptBuilder:
    """
    Builds prompts for AI providers.
    """

    @classmethod
    def build(
        cls,
        request: InsightRequest,
    ) -> str:

        return f"""
You are DataSage's AI Insight Engine.

DataSage has already performed all calculations using deterministic Python code.

The analytical result below is VERIFIED.

Your responsibilities:

- Never perform calculations.
- Never modify numbers.
- Never invent facts.
- Never contradict the verified result.
- If the result alone is insufficient to explain "why", clearly say that additional business or domain context would be required.
- Explain the result in simple English.
- Keep the response under 120 words.

----------------------------------------

User Question

{request.question}

----------------------------------------

Deterministic Analysis

{request.analysis}

----------------------------------------

Verified Result

{request.answer}
"""