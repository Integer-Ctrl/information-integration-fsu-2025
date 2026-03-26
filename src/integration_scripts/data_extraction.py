import os
import pandas as pd
import kagglehub

OUTPUT_DIR = "../../data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)


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


def main():
    datasets = [
        ("dataset1", "ujjwalaggarwal402/video-games-dataset", "Video Games Data.csv"),
        ("dataset2", "maso0dahmed/video-games-data", None),
        ("dataset3", "beridzeg45/video-games", None),
    ]

    for name, dataset_id, file in datasets:
        df = load_dataset(dataset_id, file)
        df.to_csv(f"{OUTPUT_DIR}/{name}.csv", index=False)

        print(f"{name}: {len(df)} rows")


if __name__ == "__main__":
    main()