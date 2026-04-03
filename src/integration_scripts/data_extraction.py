import os
import pandas as pd
import kagglehub


def load_dataset(dataset_id: str, target_file: str | None = None) -> pd.DataFrame:
    """Load a dataset from KaggleHub as a pandas DataFrame.

    Downloads and caches the dataset. Loads `target_file` if specified,
    otherwise the first CSV file found.

    Args:
        dataset_id: KaggleHub dataset identifier.
        target_file: Optional CSV filename within the dataset.

    Returns:
        Loaded dataset as a pandas DataFrame.

    Raises:
        ValueError: If `target_file` is specified but not found.
    """
    path = kagglehub.dataset_download(dataset_id)

    files = [f for f in os.listdir(path) if f.endswith(".csv")]

    if target_file:
        if target_file not in files:
            raise ValueError(f"{target_file} not found in {files}")
        file = target_file
    else:
        file = files[0]

    return pd.read_csv(os.path.join(path, file))