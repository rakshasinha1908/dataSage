import re


class QueryNormalizer:
    """
    Normalizes natural language queries into a consistent form before parsing.

    Responsibilities:
    - Lowercase the query
    - Remove unnecessary punctuation
    - Normalize common English phrases
    - Collapse extra whitespace

    It should NOT:
    - Detect operations
    - Match columns
    - Understand the dataset
    """

    PHRASE_NORMALIZATIONS = {
        # -------------------------------
        # Counting
        # -------------------------------
        "how many": "count",
        "number of": "count",
        "no of": "count",

        # -------------------------------
        # Average
        # -------------------------------
        "avg": "average",
        "mean": "average",

        # -------------------------------
        # Sum
        # -------------------------------
        "total": "sum",
        "overall": "sum",

        # -------------------------------
        # Maximum
        # -------------------------------
        "max": "maximum",

        # -------------------------------
        # Minimum
        # -------------------------------
        "min": "minimum",

        # -------------------------------
        # Preview
        # -------------------------------
        "first": "top",
        "last": "bottom",

        # -------------------------------
        # Dataset
        # -------------------------------
        "records": "rows",
        "record": "row",
        "entries": "rows",
        "entry": "row",
        "observations": "rows",
        "observation": "row",

        # -------------------------------
        # Misc
        # -------------------------------
        "dataset size": "count rows",
        "table size": "count rows",
    }

    @classmethod
    def normalize(cls, question: str) -> str:
        """
        Returns a normalized version of the user's question.
        """

        question = question.lower().strip()

        # Remove punctuation except underscores
        question = re.sub(r"[^\w\s]", " ", question)

        # Replace longest phrases first
        replacements = sorted(
            cls.PHRASE_NORMALIZATIONS.items(),
            key=lambda x: len(x[0]),
            reverse=True,
        )

        for phrase, replacement in replacements:

            pattern = r"\b" + re.escape(phrase) + r"\b"

            question = re.sub(
                pattern,
                replacement,
                question,
            )

        # Collapse whitespace
        question = re.sub(r"\s+", " ", question)

        return question.strip()