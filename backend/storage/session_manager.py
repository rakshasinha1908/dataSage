import uuid

from models.dataset import Dataset


class SessionManager:
    """
    Stores uploaded datasets in memory.
    """

    _sessions = {}

    @classmethod
    def save(cls, dataset: Dataset) -> str:
        session_id = str(uuid.uuid4())

        cls._sessions[session_id] = dataset

        return session_id

    @classmethod
    def get(cls, session_id: str) -> Dataset | None:
        return cls._sessions.get(session_id)