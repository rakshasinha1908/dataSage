import re

from models.ranking import Ranking
from models.ranking_parse_result import RankingParseResult
from utils.text_utils import normalize_text


class RankingParser:
    """
    Extracts only the ranking limit from the remaining query text.

    OperationParser is responsible for determining whether the
    operation is HEAD or TAIL.
    """

    @classmethod
    def parse(cls, text: str):

        cleaned_text = normalize_text(text)

        ranking = None

        # Find the first integer anywhere in the text
        match = re.search(r"\b(\d+)\b", cleaned_text)

        if match:

            ranking = Ranking(
                direction=None,
                limit=int(match.group(1)),
            )

            cleaned_text = cleaned_text.replace(
                match.group(1),
                "",
                1,
            )

        cleaned_text = " ".join(cleaned_text.split())

        return RankingParseResult(
            cleaned_text=cleaned_text,
            ranking=ranking,
        )