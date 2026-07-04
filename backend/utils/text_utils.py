import re


def normalize_text(text: str) -> str:
    """
    Normalize text for deterministic comparison.
    """

    text = text.lower()

    text = text.replace("_", " ")

    text = text.replace("-", " ")

    text = re.sub(r"[^\w\s]", "", text)

    text = " ".join(text.split())

    return text