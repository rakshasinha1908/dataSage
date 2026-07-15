from abc import ABC, abstractmethod


class AIProvider(ABC):
    """
    Base interface for all AI providers.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generates a response for the given prompt.
        """
        pass