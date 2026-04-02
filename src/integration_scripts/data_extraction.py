import os
import pandas as pd
import kagglehub


def load_dataset(dataset_id: str, target_file: str | None = None) -> pd.DataFrame:
    path = kagglehub.dataset_download(dataset_id)

    files = [f for f in os.listdir(path) if f.endswith(".csv")]

    if target_file:
        if target_file not in files:
            raise ValueError(f"{target_file} not found in {files}")
        file = target_file
    else:
        file = files[0]

    return pd.read_csv(os.path.join(path, file))