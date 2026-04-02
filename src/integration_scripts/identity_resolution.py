import pandas as pd
import roman
import re
from Levenshtein import ratio
from tqdm import tqdm
from src.utils.mappings import PLATFORM, GENRE, DEV_PUB, TARGET_SCHEMA
from src.utils.mappings import ENTITY_RESOLUTION
from src.utils.enums import ENTITY_RESOLUTION_TYPES
from datetime import date


def pre_normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    df = normalize_dates(df)
    df = normalize_by_mapping(df, PLATFORM, "platform")
    df = normalize_by_mapping(df, GENRE, "genre")
    df = normalize_by_mapping(df, DEV_PUB, "developer")
    df = normalize_by_mapping(df, DEV_PUB, "publisher")
    df = normalize_title_numbers(df)
    df = normalize_scores(df)
    df = remove_platform_all_and_missing(df) # remove records with platform all or missing platform
    df = remove_leading_trailing_whitespace(df)
    
    return df


def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "release_date" in df.columns:
        df["release_date"] = df["release_date"].replace(r"(?i)^\s*tbd\s*$", pd.NA, regex=True)
    
    # Convert release_date to datetime, handling errors and ensuring UTC timezone
    df["release_date"] = pd.to_datetime(
        df["release_date"],
        errors="coerce",
        utc=True,
    )

    # Convert to date only (remove time component)
    df["release_date"] = df["release_date"].dt.date

    return df


def normalize_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "metascore" in df.columns:
        df["metascore"] = df["metascore"].replace(r"(?i)^\s*tbd\s*$", pd.NA, regex=True)
    if "user_score" in df.columns:
        df["user_score"] = df["user_score"].replace(r"(?i)^\s*tbd\s*$", pd.NA, regex=True)
    if "critic_score" in df.columns:
        df["critic_score"] = df["critic_score"].replace(r"(?i)^\s*tbd\s*$", pd.NA, regex=True)

    return df


def normalize_by_mapping(df: pd.DataFrame, mapping: dict, column: str) -> pd.DataFrame:
    df = df.copy()
    if column in df.columns: # the column might not exist in all datasets
        df[column] = df[column].str.lower().map(mapping).fillna(df[column])
    return df


def normalize_title_numbers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    ROMAN_PATTERN = re.compile(r"\b[IVXLCDM]+\b")
    # Edge cases in datasets
    SPECIAL_ROMAN_CASES = {
        "IIII": "4",
    }

    def replace_roman(text: str) -> str:
        if not isinstance(text, str):
            return text

        def repl(match: re.Match) -> str:
            token = match.group(0)

            special = SPECIAL_ROMAN_CASES.get(token)
            if special is not None:
                return special

            try:
                return str(roman.fromRoman(token))
            except roman.InvalidRomanNumeralError:
                return token

        return ROMAN_PATTERN.sub(repl, text)

    df["title"] = df["title"].apply(replace_roman)
    return df


def remove_platform_all_and_missing(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df[df["platform"].str.lower() != "all"]
    df = df[df["platform"].notnull()]

    return df

def remove_leading_trailing_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include=["object", "string"]):
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    return df

def normalized_levenshtein_similarity(a: str, b: str) -> float:
    if pd.isna(a) or pd.isna(b):
        return 0.0
    return ratio(str(a), str(b))


def has_value(value) -> bool:
    return pd.notna(value) and value != ""


def min_columns(v1, v2):
    if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
        return min(v1, v2)
    elif isinstance(v1, date) and isinstance(v2, date):
        return min(v1, v2)
    else:
        return pd.NA


def union_delimited(v1, v2, delimiter=","):
    """Combine two delimited values, deduplicating and preserving order."""
    if has_value(v1) and has_value(v2):
        return f"{v1}{delimiter}{v2}"
    elif has_value(v1):
        return v1
    elif has_value(v2):
        return v2
    else:
        return ""


def merge_records(row1: dict, row2: dict) -> dict:
    merged = {"provenance": ""}  # track which columns came from which source for transparency
    
    all_cols = set(row1.keys()).union(set(row2.keys()))
    all_cols.discard("provenance")  # handle provenance separately
    
    src1 = row1.get("source", "")
    src2 = row2.get("source", "")

    for col in all_cols:
        v1 = row1.get(col, pd.NA)
        v2 = row2.get(col, pd.NA)

        # TODO: could implement more sophisticated conflict resolution here (e.g. prefer non-null, or use match score as weight for numeric fields), but for simplicity we just prefer values from row1 if present
        # TODO: define wether to UNION or use value from one dataset in case of non-null conflict (e.g. summary could be concatenated, while title should be chosen from one)
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
                    merged[col] = max(float(v1), float(v2))
                    merged["provenance"] = union_delimited(merged["provenance"], f"{col}=max({src1},{src2})", delimiter=",")
                elif resolution_type == ENTITY_RESOLUTION_TYPES.UNION:
                    merged[col] = union_delimited(v1, v2, delimiter=",")
                    merged["provenance"] = union_delimited(merged["provenance"], f"{col}=union({src1},{src2})", delimiter=",")
                elif resolution_type == ENTITY_RESOLUTION_TYPES.LONGEST:
                    if len(str(v1)) == len(str(v2)): # tie, prefer value from row1 arbitrarily
                        merged[col] = v1
                        merged["provenance"] = union_delimited(merged["provenance"], f"{col}=longest(tie:{src1},{src2})", delimiter=",")
                    else: # prefer longest value
                        merged[col] = v1 if len(str(v1)) > len(str(v2)) else v2
                        merged["provenance"] = union_delimited(merged["provenance"], f"{col}=longest({src1},{src2})", delimiter=",")
                else:
                    merged[col] = v1  # prefer value from row1 arbitrarily
        elif has_value(v1):
            merged[col] = v1
            merged["provenance"] = union_delimited(merged["provenance"], f"{col}=single({src1})", delimiter=",")
        elif has_value(v2):
            merged[col] = v2
            merged["provenance"] = union_delimited(merged["provenance"], f"{col}=single({src2})", delimiter=",")
        else:
            merged[col] = pd.NA

    return merged


def merge_identities(df1: pd.DataFrame, df2: pd.DataFrame, threshold: float = 0.85) -> pd.DataFrame:

    # Goal:
    # 1. Block by platform and release year +/- 1 year to reduce candidate pairs (with edge case handling for missing release dates)
    # 2. Compute match score for candidates using title similarity and release date proximity: score = 0.8 * title_similarity + 0.2 * release_date_similarity, where title_similarity is normalized Levenshtein similarity and release_date_similarity is 1 if release dates equal, 0.9 if within 3 days, 0.8 if within 6 days, ... >30 days is 0

    # 1. Pre-normalize datasets for better matching (e.g. unify platform names, normalize dates, etc.)
    df1 = pre_normalize(df1.copy())
    df2 = pre_normalize(df2.copy())

    # 2. Ensure we always match smaller dataset against larger for efficiency
    if len(df1) > len(df2):
        df1, df2 = df2, df1
        print(f"Swapped datasets for matching (smaller -> larger): {len(df1)} vs {len(df2)}")

    # Stable indices so we can track matched rows from the larger dataset
    df1 = df1.reset_index(drop=True)
    df2 = df2.reset_index(drop=True)

    # Tage seit Epoch (1970-01-01) als numerischer Wert für release_date, damit wir schneller nach ähnlichen release_dates filtern können (z.B. innerhalb von 30 Tagen)
    df1_dt_temp = pd.to_datetime(df1['release_date'], errors='coerce')
    df1['days_since_release'] = (df1_dt_temp - pd.Timestamp("1970-01-01")).dt.days
    df2_dt_temp = pd.to_datetime(df2['release_date'], errors='coerce')
    df2['days_since_release'] = (df2_dt_temp - pd.Timestamp("1970-01-01")).dt.days

    # Replace invalid datetime with pd.NA
    df1.loc[df1_dt_temp.isna(), 'days_since_epoch'] = pd.NA
    df2.loc[df2_dt_temp.isna(), 'days_since_epoch'] = pd.NA

    # Faster access to rows as dicts
    df1_records = df1.to_dict(orient="records")
    df2_records = df2.to_dict(orient="records")

    def normalized_release_date_similarity(release1, release2) -> float:
        """
        Compute normalized release date similarity based on absolute day difference.

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
        """
        Compute weighted match score for two candidate rows.

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

        NORMELIZED_TITLE_WEIGHT = 0.85
        return NORMELIZED_TITLE_WEIGHT * title_score + (1 - NORMELIZED_TITLE_WEIGHT) * release_score

    # Block larger dataset by platform and year of release
    #
    # Block contains indices of release date one year before and after to allow
    # edge cases (e.g. 2002-12-30 vs 2003-01-02) to still match.
    #
    # Example block key:
    #   ("pc", 2003)
    #
    # Edge case 1:
    #   entity from smaller dataset has no release date
    #   -> match against all entities on same platform in larger dataset
    #
    # Edge case 2:
    #   entity from larger dataset has no release date
    #   -> include in platform-wide fallback block so it can still be matched
    blocks = {}
    platform_only_blocks = {}

    for idx, row in enumerate(df2_records):
        platform_key = row.get("platform")
        release_date = row.get("release_date", pd.NA)

        # Platform-wide fallback block
        platform_block = platform_only_blocks.setdefault(platform_key, {
            "indices": [],
            "release_dates": [],
            "titles": [],
        })
        platform_block["indices"].append(idx)
        platform_block["release_dates"].append(release_date)
        platform_block["titles"].append(row.get("title", pd.NA))

        # TODO: ensure all entries without release date are included in all platform-year blocks for that platform
        # Year-based blocks
        if has_value(release_date) and isinstance(release_date, date):
            year_key = release_date.year

            # Add row to blocks for year-1, year, year+1
            # so querying only the exact year of the smaller row is enough
            for y in (year_key - 1, year_key, year_key + 1):
                block_key = (platform_key, y)
                block = blocks.setdefault(block_key, {
                    "indices": [],
                    "release_dates": [],
                    "titles": [],
                })
                block["indices"].append(idx)
                block["release_dates"].append(release_date)
                block["titles"].append(row.get("title", pd.NA))

    merged_rows = []
    matched_df2_indices = set()

    # Iterate over smaller dataset and compare only against relevant blocks
    for row1 in tqdm(df1_records, total=len(df1_records), desc="Merging identities v3"):
        platform1 = row1.get("platform", pd.NA)
        release1 = row1.get("release_date", pd.NA)

        # Determine candidate block:
        # - if release_date exists -> platform + exact year block
        # - otherwise -> full platform block
        if has_value(release1) and isinstance(release1, date):
            candidate_block = blocks.get((platform1, release1.year))
        else:
            candidate_block = platform_only_blocks.get(platform1)

        # Fallback to platform-only block if year block does not exist
        if candidate_block is None:
            candidate_block = platform_only_blocks.get(platform1)

        # No candidates on this platform -> keep row unchanged
        if candidate_block is None:
            row1_dict = dict(row1)
            row1_dict.setdefault("provenance", "")
            merged_rows.append(row1_dict)
            continue

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

    result = pd.DataFrame(merged_rows)

    # Remove helper column from final output
    if "days_since_epoch" in result.columns:
        result = result.drop(columns=["days_since_epoch"])

    result = reorder_to_target_schema(result)

    return result


def reorder_to_target_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reorder DataFrame columns according to TARGET_SCHEMA.
    Missing columns are ignored, extra columns are appended at the end.
    """
    # Columns that exist in df and are in TARGET_SCHEMA
    ordered_cols = [col for col in TARGET_SCHEMA if col in df.columns]

    # Any additional columns not in TARGET_SCHEMA
    remaining_cols = [col for col in df.columns if col not in TARGET_SCHEMA]

    return df[ordered_cols + remaining_cols]