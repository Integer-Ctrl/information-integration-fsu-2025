import os
from pathlib import Path
import pandas as pd
from src.integration_scripts.data_extraction import load_dataset
from src.integration_scripts.schema_mapping import apply_mapping
import src.utils.mappings as mappings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)
os.makedirs(PROCESSED_OUTPUT_DIR, exist_ok=True)

DATASETS = [
    ("dataset1", "ujjwalaggarwal402/video-games-dataset", "Video Games Data.csv"),
    ("dataset2", "maso0dahmed/video-games-data", None),
    ("dataset3", "beridzeg45/video-games", None),
]

MAPPINGS = {
    "dataset1": mappings.DATASET1,
    "dataset2": mappings.DATASET2,
    "dataset3": mappings.DATASET3
}

def main():

    print(RAW_OUTPUT_DIR)
    print(PROCESSED_OUTPUT_DIR)

    RAW_DATA = []
    MAPPED_DATA = []

    # Step 1: Load dataset
    for name, dataset_id, file in DATASETS:

        df = load_dataset(dataset_id, file)
        RAW_DATA.append((name, df))
        
        # (Optional) Save raw datasets for reference
        df.to_csv(f"{RAW_OUTPUT_DIR}/{name}.csv", index=False)

    # Step 2: Apply schema mapping
    for name, df in RAW_DATA:

        mapped_df = apply_mapping(df, MAPPINGS[name])
        MAPPED_DATA.append((name, mapped_df))

        # (Optional) Save mapped datasets for reference
        mapped_df.to_csv(f"{PROCESSED_OUTPUT_DIR}/{name}_mapped.csv", index=False)


    # Intermediate output for verification
    # First: Concatenate all mapped datasets into one DataFrame, Second: Sort by title, Third: Save to CSV
    final_df = pd.concat([df for _, df in MAPPED_DATA], ignore_index=True)
    final_df = final_df.sort_values(by="title")
    print(final_df)
    final_df.to_csv(f"{PROCESSED_OUTPUT_DIR}/mapped_data.csv", index=False)

if __name__ == "__main__":
    main()
