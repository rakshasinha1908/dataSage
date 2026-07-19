import re

from models.ranking import Ranking
from models.ranking_parse_result import RankingParseResult
from utils.text_utils import normalize_text


class RankingParser:
    """
    Extracts ranking instructions from a natural language query.

    This parser is responsible only for determining whether the user
    explicitly requested a subset of rows or all rows.

    Supported examples:

        top 10
        first 5
        last 20
        bottom 15

        show 10 rows
        show 25 records
        display 50 entries

        show all rows
        show every record

    It deliberately ignores unrelated numbers such as years,
    salaries, IDs, ages, etc.
    """

    LIMIT_KEYWORD_PATTERN = re.compile(
        r"\b(top|first|last|bottom)\s+(\d+)\b",
        re.IGNORECASE,
    )

    LIMIT_ROWS_PATTERN = re.compile(
        r"\b(\d+)\s+(?:rows?|records?|entries?)\b",
        re.IGNORECASE,
    )

    ALL_PATTERN = re.compile(
        r"\b(?:all|every)\b",
        re.IGNORECASE,
    )

    @classmethod
    def parse(cls, text: str):

        cleaned_text = normalize_text(text)

        ranking = Ranking()

        # -----------------------------------
        # "show all rows"
        # "show every record"
        # -----------------------------------

        all_match = cls.ALL_PATTERN.search(cleaned_text)

        if all_match:

            ranking.is_explicit = True
            ranking.show_all = True

            cleaned_text = cls.ALL_PATTERN.sub(
                "",
                cleaned_text,
                count=1,
            )

        else:

            # -----------------------------------
            # "top 10"
            # "first 20"
            # "last 5"
            # "bottom 15"
            # -----------------------------------

            keyword_match = cls.LIMIT_KEYWORD_PATTERN.search(
                cleaned_text
            )

            if keyword_match:

                keyword = keyword_match.group(1).lower()

                ranking.limit = int(keyword_match.group(2))
                ranking.is_explicit = True

                if keyword in ("last", "bottom"):
                    ranking.direction = "asc"
                else:
                    ranking.direction = "desc"

                cleaned_text = cls.LIMIT_KEYWORD_PATTERN.sub(
                    "",
                    cleaned_text,
                    count=1,
                )

            else:

                # -----------------------------------
                # "show 25 rows"
                # "display 50 records"
                # "list 100 entries"
                # -----------------------------------

                row_limit_match = cls.LIMIT_ROWS_PATTERN.search(
                    cleaned_text
                )

                if row_limit_match:

                    ranking.limit = int(
                        row_limit_match.group(1)
                    )
                    ranking.is_explicit = True

                    cleaned_text = cls.LIMIT_ROWS_PATTERN.sub(
                        "",
                        cleaned_text,
                        count=1,
                    )

        cleaned_text = " ".join(cleaned_text.split())

        return RankingParseResult(
            cleaned_text=cleaned_text,
            ranking=ranking,
        )