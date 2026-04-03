import pandas as pd
from tqdm import tqdm
from datetime import date
from Levenshtein import ratio
from src.utils.mappings import PLATFORM, GENRE, DEV_PUB, TARGET_SCHEMA
from src.utils.mappings import ENTITY_RESOLUTION
from src.utils.enums import ENTITY_RESOLUTION_TYPES
from src.utils.data_utils import has_value, union_delimited, min_columns, max_columns
from src.utils.data_normalization import (
    normalize_dates,
    normalize_by_mapping,
    normalize_title_numbers,
    normalize_scores,    
    remove_platform_all_and_missing,
    remove_leading_trailing_whitespace)


def pre_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Pre-normalizes datasets for better matching

    Normalization steps:
    - Normalize release dates to datetime.date objects
    - Normalize platform, genre, developer, publisher using predefined mappings
    - Normalize title by removing extra whitespace and standardizing number formats (e.g. "Final Fantasy VII" -> "Final Fantasy 7")
    - Normalize scores to a common scale if needed (e.g. if some datasets have scores out of 10 and others out of 100)
    - Remove records with platform "All" or missing platform, as they are not useful for identity resolution and can introduce noise
    - Remove leading/trailing whitespace from all string fields to avoid false mismatches due to formatting inconsistencies

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: Normalized DataFrame.
    """
    df = df.copy()
    
    df = normalize_dates(df)
    df = normalize_by_mapping(df, PLATFORM, "platform")
    df = normalize_by_mapping(df, GENRE, "genre")
    df = normalize_by_mapping(df, DEV_PUB, "developer")
    df = normalize_by_mapping(df, DEV_PUB, "publisher")
    df = normalize_title_numbers(df)
    df = normalize_scores(df)
    df = remove_platform_all_and_missing(df)
    df = remove_leading_trailing_whitespace(df)
    
    return df

def normalized_levenshtein_similarity(a: str, b: str) -> float:
    """Computes normalized Levenshtein similarity.

    Args:
        a (str): First string.
        b (str): Second string.

    Returns:
        float: Similarity score between 0 and 1.
    """
    if pd.isna(a) or pd.isna(b):
        return 0.0
    return ratio(str(a), str(b))

def normalized_release_date_similarity(release1, release2) -> float:
    """Computes normalized release date similarity based on absolute day difference.

    Rules:
    - 1.0 if same day
    - 0.9 if within 7 days
    - 0.8 if within 15 days
    - ...
    - 0.0 if more than 70 days apart or missing values

    Args:
        release1: First release date.
        release2: Second release date.

    Returns:
        float: Similarity score in [0.0, 1.0].
    """
    if not has_value(release1) or not has_value(release2):
        return 0.0

    if not isinstance(release1, date) or not isinstance(release2, date):
        return 0.0

    delta_days = abs((release1 - release2).days)
    
    return max(0.0, 1 - delta_days / 365) # linear decay over 1 year

def compute_match_score(row1: dict, row2: dict) -> float:
    """Computes weighted match score for two candidate rows.

    Platform mismatch is treated as a hard reject.

    Args:
        row1 (dict): First record.
        row2 (dict): Second record.

    Returns:
        float: Weighted similarity score.
    """
    platform1 = row1.get("platform", pd.NA)
    platform2 = row2.get("platform", pd.NA)

    # Exact platform match required if both have a value
    if has_value(platform1) and has_value(platform2) and platform1 != platform2:
        return 0.0

    title_score = normalized_levenshtein_similarity(
        row1.get("title", pd.NA),
        row2.get("title", pd.NA),
    )
    release_score = normalized_release_date_similarity(
        row1.get("release_date", pd.NA),
        row2.get("release_date", pd.NA),
    )

    NORMALIZED_TITLE_WEIGHT = 0.85
    return NORMALIZED_TITLE_WEIGHT * title_score + (1 - NORMALIZED_TITLE_WEIGHT) * release_score


def reorder_to_target_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Reorders DataFrame columns according to TARGET_SCHEMA.
    Missing columns are ignored, extra columns are appended at the end.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: Reordered DataFrame.
    """
    # Columns that exist in df and are in TARGET_SCHEMA
    ordered_cols = [col for col in TARGET_SCHEMA if col in df.columns]

    # Any additional columns not in TARGET_SCHEMA
    remaining_cols = [col for col in df.columns if col not in TARGET_SCHEMA]

    return df[ordered_cols + remaining_cols]


def merge_records(row1: dict, row2: dict) -> dict:
    """Merges two records (rows) into one, resolving conflicts based on predefined rules and tracking provenance of each field.
    
    Conflict resolution rules are specified in the ENTITY_RESOLUTION mapping, which defines how to resolve conflicts for specific columns.
    For example:
    - If resolution type is MIN, take the minimum of the two values (for numeric or date fields).
    - If resolution type is MAX, take the maximum of the two values (for numeric or date fields).
    - If resolution type is UNION, combine the values into a delimited string (genre).
    - If resolution type is LONGEST, take the longest value (title).
    - If resolution type is NOTHING or not specified, prefer value from row1 if present, otherwise take value from row2.
    
    Args:
        row1 (dict): First record.
        row2 (dict): Second record.

    Returns:
        dict: Merged record with provenance.
    """
    
    merged = {"provenance": ""}  # track which columns came from which source for transparency
    
    all_cols = set(row1.keys()).union(set(row2.keys()))
    all_cols.discard("provenance")  # handle provenance separately
    
    src1 = row1.get("source", "")
    src2 = row2.get("source", "")

    for col in all_cols:
        v1 = row1.get(col, pd.NA)
        v2 = row2.get(col, pd.NA)

        if has_value(v1) and has_value(v2):
            if v1 == v2:
                merged[col] = v1
                merged["provenance"] = union_delimited(merged["provenance"], f"{col}=eq({src1},{src2})", delimiter=",")
            else:
                resolution_type = ENTITY_RESOLUTION.get(col, ENTITY_RESOLUTION_TYPES.NOTHING)
                if resolution_type == ENTITY_RESOLUTION_TYPES.MIN:
                    merged[col] = min_columns(v1, v2)
                    merged["provenance"] = union_delimited(merged["provenance"], f"{col}=min({src1},{src2})", delimiter=",")
                elif resolution_type == ENTITY_RESOLUTION_TYPES.MAX:
                    merged[col] = max_columns(v1, v2)
                    merged["provenance"] = union_delimited(merged["provenance"], f"{col}=max({src1},{src2})", delimiter=",")
                elif resolution_type == ENTITY_RESOLUTION_TYPES.UNION:
                    merged[col] = union_delimited(v1, v2, delimiter=",")
                    merged["provenance"] = union_delimited(merged["provenance"], f"{col}=union({src1},{src2})", delimiter=",")
                else:
                    # NOTHING or unspecified -> prefer value from row1 if present, otherwise take value from row2
                    # We do not write any provenance here, since it is used for the provenance column itself
                    merged[col] = v1
        elif has_value(v1):
            merged[col] = v1
            merged["provenance"] = union_delimited(merged["provenance"], f"{col}=single({src1})", delimiter=",")
        elif has_value(v2):
            merged[col] = v2
            merged["provenance"] = union_delimited(merged["provenance"], f"{col}=single({src2})", delimiter=",")
        else:
            merged[col] = pd.NA # both values missing, keep as NA and no provenance needed

    return merged


def merge_identities(df1: pd.DataFrame, df2: pd.DataFrame, threshold: float = 0.85) -> pd.DataFrame:
    """Normalizes and merges two datasets using fuzzy matching and blocking.

    Goal:
    1.    Block by platform and release year +/- 1 year to reduce candidate pairs 
          (with edge case handling for missing release dates)
    2.    Compute match score for candidates using title similarity and release date proximity:
          score = 0.85 * title_similarity + 0.15 * release_date_similarity, where title_similarity 
          is normalized Levenshtein similarity and release_date_similarity is 1 if release dates equal, 
          0.9 if within 7 days, 0.8 if within 15 days, ... >365 days is 0

    Blocking strategy:
    - Block larger dataset by platform and year of release
    - Block contains indices of release date one year before and after to allow edge cases (e.g. 2002-12-30 vs 2003-01-02) to still match.
    - Edge case 1: entity from smaller dataset has no release date -> match against all entities on same platform in larger dataset
    - Edge case 2: entity from larger dataset has no release date -> include in all platform-year blocks for that platform so it can still be matched

    Args:
        df1 (pd.DataFrame): First dataset.
        df2 (pd.DataFrame): Second dataset.
        threshold (float): Matching threshold.

    Returns:
        pd.DataFrame: Merged dataset.
    """

    # Pre-normalize datasets for better matching (e.g. unify platform names, normalize dates, etc.)
    df1 = pre_normalize(df1.copy())
    df2 = pre_normalize(df2.copy())

    # Ensure we always match smaller dataset against larger for efficiency
    if len(df1) > len(df2):
        df1, df2 = df2, df1
        print(f"Swapped datasets for matching (smaller -> larger): {len(df1)} vs {len(df2)}")
    
    # Reset indices to ensure they are sequential and start from 0
    df1 = df1.reset_index(drop=True)
    df2 = df2.reset_index(drop=True)

    # Faster access to rows as dicts
    df1_records = df1.to_dict(orient="records")
    df2_records = df2.to_dict(orient="records")

    # Blocking strategy as described above
    platform_year_blocks = {} # key: (platform, year) -> value: list of indices in df2_records with that platform and release year +/- 1 year
    platform_only_blocks = {} # key: platform -> value: list of indices in df2_records with that platform (for edge case of missing release date)
    missing_date_indices_by_platform = {} # separate tracking of indices with missing release date by platform to include in all blocks of that platform later

    # Build blocks for rows in df2 with release date
    for idx, row in enumerate(df2_records):
        platform_key = row.get("platform")
        release_date = row.get("release_date", pd.NA)

        # Platform-wide fallback block
        platform_block = platform_only_blocks.setdefault(platform_key, {"indices": []})
        platform_block["indices"].append(idx)

        # Year-based blocks
        if has_value(release_date) and isinstance(release_date, date):
            year_key = release_date.year

            # Add row to blocks for year-1, year, year+1
            # so querying only the exact year of the smaller row is enough
            for y in (year_key - 1, year_key, year_key + 1):
                block_key = (platform_key, y)
                block = platform_year_blocks.setdefault(block_key, {"indices": []})
                block["indices"].append(idx)

        # Edge case: missing release date -> add to separate missing block to include later in all (platform, year) blocks
        else:
            missing_date_indices_by_platform.setdefault(platform_key, []).append(idx)
            
    # Add rows with missing release_date to all year blocks of that platform
    for platform, indices in missing_date_indices_by_platform.items():
        for block_key, block in platform_year_blocks.items():
            if block_key[0] == platform:
                for idx in indices:
                    block["indices"].append(idx)

    merged_rows = []
    matched_df2_indices = set()

    # Iterate over smaller dataset and compare only against relevant blocks
    for row1 in tqdm(df1_records, total=len(df1_records), desc="Merging identities v3"):
        platform1 = row1.get("platform", pd.NA)
        release1 = row1.get("release_date", pd.NA)

        # Determine candidate block:
        # - if release_date exists -> platform + exact year block
        # - otherwise -> full platform block
        candidate_block = None
        if has_value(release1) and isinstance(release1, date):
            candidate_block = platform_year_blocks.get((platform1, release1.year))

        if candidate_block is None:
            candidate_block = platform_only_blocks.get(platform1)

        # No candidates on this platform -> keep row unchanged
        if candidate_block is None:
            row1_dict = dict(row1)
            row1_dict.setdefault("provenance", "")
            merged_rows.append(row1_dict)
            continue # Skip to next row1

        candidate_indices = candidate_block["indices"]

        best_match_idx = None
        best_score = 0.0

        # Evaluate all unmatched candidates in the selected block
        for idx2 in candidate_indices:
            if idx2 in matched_df2_indices:
                continue

            row2 = df2_records[idx2]
            score = compute_match_score(row1, row2)

            if score > best_score:
                best_score = score
                best_match_idx = idx2

        # Merge best candidate if above threshold
        if best_match_idx is not None and best_score >= threshold:
            merged_row = merge_records(row1, df2_records[best_match_idx])
            merged_rows.append(merged_row)
            matched_df2_indices.add(best_match_idx)
        else:
            row1_dict = dict(row1)
            row1_dict.setdefault("provenance", "")
            merged_rows.append(row1_dict)

    # Add remaining unmatched rows from the larger dataset
    for idx2, row2 in enumerate(df2_records):
        if idx2 not in matched_df2_indices:
            row2_dict = dict(row2)
            row2_dict.setdefault("provenance", "")
            merged_rows.append(row2_dict)

    return reorder_to_target_schema(pd.DataFrame(merged_rows))