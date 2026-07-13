from dataclasses import dataclass

from models.ranking import Ranking


@dataclass
class RankingParseResult:
    """
    Stores the parsed ranking information along with
    the remaining text.
    """

    cleaned_text: str

    ranking: Ranking | None