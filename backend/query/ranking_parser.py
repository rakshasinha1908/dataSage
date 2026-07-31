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

    DEFAULT_LIMIT_KEYWORD_PATTERN = re.compile(
        r"\b("
        r"top|bottom|"
        r"highest|lowest|"
        r"largest|smallest|"
        r"biggest|least|"
        r"best|worst"
        r")\b",
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

        ranking = None

        # -----------------------------------
        # "show all rows"
        # "show every record"
        # -----------------------------------

        all_match = cls.ALL_PATTERN.search(cleaned_text)

        if all_match:

            ranking = Ranking(
                is_explicit=True,
                show_all=True,
            )

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

                ranking = Ranking(
                    limit=int(keyword_match.group(2)),
                    direction=(
                        "asc"
                        if keyword in ("last", "bottom")
                        else "desc"
                    ),
                    is_explicit=True,
                )

                cleaned_text = cls.LIMIT_KEYWORD_PATTERN.sub(
                    "",
                    cleaned_text,
                    count=1,
                )

            else:

                # -----------------------------------
                # "top"
                # "bottom"
                # "highest"
                # "lowest"
                # -----------------------------------

                default_keyword_match = cls.DEFAULT_LIMIT_KEYWORD_PATTERN.search(
                    cleaned_text
                )

                if default_keyword_match:

                    keyword = default_keyword_match.group(1).lower()

                    ranking = Ranking(
                        limit=10,
                        direction=(
                            "asc"
                            if keyword in (
                                "bottom",
                                "lowest",
                                "smallest",
                                "least",
                                "worst",
                            )
                            else "desc"
                        ),
                        is_explicit=False,
                    )

                    cleaned_text = cls.DEFAULT_LIMIT_KEYWORD_PATTERN.sub(
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

                        ranking = Ranking(
                            limit=int(row_limit_match.group(1)),
                            is_explicit=True,
                        )

                        cleaned_text = cls.LIMIT_ROWS_PATTERN.sub(
                            "",
                            cleaned_text,
                            count=1,
                        )

        cleaned_text = " ".join(cleaned_text.split())

        print("\n" + "=" * 60)
        print("🔥 RANKING PARSER")
        print("Input         :", repr(text))
        print("Cleaned Text  :", repr(cleaned_text))
        print("Ranking       :", ranking)
        print("=" * 60)

        return RankingParseResult(
            cleaned_text=cleaned_text,
            ranking=ranking,
        )
