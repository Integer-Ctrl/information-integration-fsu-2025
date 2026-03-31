import os
from pathlib import Path
import pandas as pd
from src.integration_scripts.data_extraction import load_dataset
from src.integration_scripts.schema_mapping import apply_mapping
from src.integration_scripts.identity_resolution import pre_normalize, merge_identities
import src.utils.mappings as mappings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)
os.makedirs(PROCESSED_OUTPUT_DIR, exist_ok=True)

DATASETS = [
    ("ds1", "ujjwalaggarwal402/video-games-dataset", "Video Games Data.csv"),
    ("ds2", "maso0dahmed/video-games-data", None),
    ("ds3", "beridzeg45/video-games", None),
]

MAPPINGS = {
    "ds1": mappings.DATASET1,
    "ds2": mappings.DATASET2,
    "ds3": mappings.DATASET3
}

def main():

    print(RAW_OUTPUT_DIR)
    print(PROCESSED_OUTPUT_DIR)

    RAW_DATA = []
    MAPPED_DATA = []
    NORMALIZED_DATA = []

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
        mapped_df.to_csv(f"{PROCESSED_OUTPUT_DIR}/{name}_mapped.csv", index=False)


    # Intermediate output for verification
    # First: Concatenate all mapped datasets into one DataFrame, Second: Sort by title, Third: Save to CSV
    # final_df = pd.concat([df for _, df in MAPPED_DATA], ignore_index=True)
    # final_df = final_df.sort_values(by="title")
    # print(final_df)
    # final_df.to_csv(f"{PROCESSED_OUTPUT_DIR}/mapped_data.csv", index=False)

    # Step 3: Identity resolution (normalize and merge records referring to the same game across datasets)
    for name, df in MAPPED_DATA:
        normalized_df = pre_normalize(df)
        NORMALIZED_DATA.append((name, normalized_df))

        # (Optional) Save normalized datasets for reference
        normalized_df.to_csv(f"{PROCESSED_OUTPUT_DIR}/{name}_normalized.csv", index=False)

    # Merge datasets pairwise
    df_intermediate_merge = merge_identities(NORMALIZED_DATA[0][1], NORMALIZED_DATA[1][1])
    df_intermediate_merge.to_csv(f"{PROCESSED_OUTPUT_DIR}/intermediate_merge.csv", index=False)
    final_merged_df = merge_identities(df_intermediate_merge, NORMALIZED_DATA[2][1])
    final_merged_df.to_csv(f"{PROCESSED_OUTPUT_DIR}/final_merged.csv", index=False)

    counts = final_merged_df["platform"].value_counts()
    counts.to_csv(f"{PROCESSED_OUTPUT_DIR}/platform_counts.csv")

    size_raw = sum(len(df) for _, df in RAW_DATA)
    size_final = len(final_merged_df)
    print(f"Size of raw datasets combined: {size_raw}")
    print(f"Size of final merged dataset: {size_final}")
    

if __name__ == "__main__":
    main()
