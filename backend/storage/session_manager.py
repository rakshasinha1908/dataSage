import uuid

from models.dataset import Dataset
from models.session import Session


class SessionManager:
    """
    Stores uploaded datasets in memory.
    """

    _sessions = {}

    @classmethod
    def save(cls, dataset: Dataset) -> str:
        session_id = str(uuid.uuid4())
        dataset.session_id = session_id

        session = Session(
            dataset=dataset,
        )

        cls._sessions[session_id] = session
        return session_id

    @classmethod
    def get(cls, session_id: str) -> Dataset | None:
        session = cls._sessions.get(session_id)
        if session is None:
            return None
        return session.dataset

    @classmethod
    def save_query_context(cls, session_id: str, query_context):
        session = cls._sessions.get(session_id)
        if session is None:
            return
        session.latest_query = query_context

    @classmethod
    def get_query_context(cls, session_id: str):
        session = cls._sessions.get(session_id)
        if session is None:
            return None
        return session.latest_query
