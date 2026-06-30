import pandas as pd

from models.dataset import Dataset


class DatasetManager:
    """
    Responsible for loading datasets into memory.
    """

    ENCODINGS = [
        "utf-8",
        "utf-8-sig",
        "cp1252",
        "latin1"
    ]

    @staticmethod
    def load_dataset(file, filename: str) -> Dataset:

        for encoding in DatasetManager.ENCODINGS:
            try:
                file.seek(0)

                dataframe = pd.read_csv(
                    file,
                    encoding=encoding
                )

                return Dataset(
                    dataframe=dataframe,
                    filename=filename
                )

            except UnicodeDecodeError:
                continue

        raise ValueError(
            "Unable to read the uploaded CSV. Unsupported file encoding."
        )