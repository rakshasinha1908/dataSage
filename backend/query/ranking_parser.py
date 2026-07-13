import re

from models.ranking import Ranking
from models.ranking_parse_result import RankingParseResult
from utils.text_utils import normalize_text


class RankingParser:
    """
    Extracts ranking instructions from the user's question.
    """

    @classmethod
    def parse(cls, text: str):

        cleaned_text = normalize_text(text)

        ranking = None

        # -------------------------------
        # Top N
        # -------------------------------

        match = re.search(r"top\s+(\d+)", cleaned_text)

        if match:

            ranking = Ranking(
                direction="desc",
                limit=int(match.group(1)),
            )

            cleaned_text = cleaned_text.replace(
                match.group(0),
                "",
            )

        # -------------------------------
        # Bottom N
        # -------------------------------

        else:

            match = re.search(r"bottom\s+(\d+)", cleaned_text)

            if match:

                ranking = Ranking(
                    direction="asc",
                    limit=int(match.group(1)),
                )

                cleaned_text = cleaned_text.replace(
                    match.group(0),
                    "",
                )

        cleaned_text = " ".join(cleaned_text.split())

        return RankingParseResult(
            cleaned_text=cleaned_text,
            ranking=ranking,
        )