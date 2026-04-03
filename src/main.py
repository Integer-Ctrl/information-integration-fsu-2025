import os
from pathlib import Path
from src.integration_scripts.data_extraction import load_dataset
from src.integration_scripts.schema_mapping import apply_mapping
from src.integration_scripts.identity_resolution import merge_identities
import src.utils.mappings as mappings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)
os.makedirs(PROCESSED_OUTPUT_DIR, exist_ok=True)

DATASETS = [
    ("games_dataset_1", "ujjwalaggarwal402/video-games-dataset", "Video Games Data.csv"),
    ("games_dataset_2", "maso0dahmed/video-games-data", None),
    ("games_dataset_3", "beridzeg45/video-games", None),
]

MAPPINGS = {
    "games_dataset_1": mappings.DATASET1,
    "games_dataset_2": mappings.DATASET2,
    "games_dataset_3": mappings.DATASET3
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

        mapped_df = apply_mapping(name, df, MAPPINGS[name])
        MAPPED_DATA.append((name, mapped_df))

        # (Optional) Save mapped datasets for reference
        # mapped_df.to_csv(f"{PROCESSED_OUTPUT_DIR}/{name}_mapped.csv", index=False)

    # Step 3: Identity resolution (normalize and merge records referring to the same game across datasets)
    df_intermediate_merge = merge_identities(MAPPED_DATA[0][1], MAPPED_DATA[1][1])
    final_merged_df = merge_identities(df_intermediate_merge, MAPPED_DATA[2][1])

    # Final cleanup: sort by title and save final integrated dataset
    final_merged_df = final_merged_df.sort_values(by="title")
    final_merged_df.to_csv(f"{PROCESSED_OUTPUT_DIR}/games_integrated_dataset.csv", index=False)

    size_raw = sum(len(df) for _, df in RAW_DATA)
    size_final = len(final_merged_df)
    print(f"Size of raw datasets combined: {size_raw}")
    print(f"Size of final merged dataset: {size_final}")
    

if __name__ == "__main__":
    main()
