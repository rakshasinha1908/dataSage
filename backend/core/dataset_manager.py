from pathlib import Path
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
        "latin1",
    ]

    @staticmethod
    def load_dataset(file, filename: str) -> Dataset:
        extension = Path(filename).suffix.lower()

        if extension == ".csv":
            for encoding in DatasetManager.ENCODINGS:
                try:
                    file.seek(0)
                    dataframe = pd.read_csv(
                        file,
                        encoding=encoding,
                    )
                    return Dataset(
                        dataframe=dataframe,
                        filename=filename,
                    )
                except UnicodeDecodeError:
                    continue

            raise ValueError(
                "Unable to read the uploaded CSV. Unsupported file encoding."
            )

        elif extension in [".xlsx", ".xls"]:
            try:
                file.seek(0)
                dataframe = pd.read_excel(file)
                return Dataset(
                    dataframe=dataframe,
                    filename=filename,
                )
            except Exception as error:
                raise ValueError(
                    "Unable to read the uploaded Excel file."
                ) from error

        raise ValueError(
            "Unsupported file format. Please upload a CSV, XLSX or XLS file."
        )
