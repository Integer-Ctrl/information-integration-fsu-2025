import pandas as pd
import roman
import re
from difflib import SequenceMatcher
from tqdm import tqdm
from src.utils.mappings import PLATFORM, GENRE, DEV_PUB
from src.utils.mappings import ENTITY_RESOLUTION
from src.utils.enums import ENTITY_RESOLUTION_TYPES
from datetime import date, datetime

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

def levenshtein_similarity(a: str, b: str) -> float:
    if pd.isna(a) or pd.isna(b):
        return 0.0
    return SequenceMatcher(None, str(a), str(b)).ratio()


def compute_match_score_from_values(title1, title2, release1, release2, platform1, platform2) -> float:
    # exact platform match required
    if has_value(platform1) and has_value(platform2) and platform1 != platform2:
        return 0.0

    # exact release_date match if both exist
    # if has_value(release1) and has_value(release2) and release1 != release2:
    #     return 0.0

    # release_date within 7 days is acceptable
    # if has_value(release1) and has_value(release2):
    #     if abs((release1 - release2).days) > 7:
    #         return 0.0

    # fuzzy title match
    return levenshtein_similarity(title1, title2)


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


def merge_identities_v2(df1: pd.DataFrame, df2: pd.DataFrame, threshold: float = 0.85) -> pd.DataFrame:
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

    def dates_within_x_days(d1, d2, x) -> bool:
        if not has_value(d1) or not has_value(d2):
            return False
        if not isinstance(d1, date) or not isinstance(d2, date):
            return False
        return abs((d1 - d2).days) <= x
    
    # Faster access to rows as dicts
    df1_records = df1.to_dict(orient="records")
    df2_records = df2.to_dict(orient="records")

    # Block larger dataset by platform and cache frequently used fields
    platform_blocks = {}
    for idx, row in enumerate(df2_records):
        platform_key = row.get("platform")
        block = platform_blocks.setdefault(platform_key, {
            "indices": [],
            "release_dates": [],
            "titles": [],
        })
        block["indices"].append(idx)
        block["release_dates"].append(row.get("release_date", pd.NA))
        block["titles"].append(row.get("title", pd.NA))

    merged_rows = []
    matched_df2_indices = set()

    for row1 in tqdm(df1_records, total=len(df1_records), desc="Merging identities"):
        platform1 = row1.get("platform", pd.NA)
        release1 = row1.get("release_date", pd.NA)
        title1 = row1.get("title", pd.NA)

        block = platform_blocks.get(platform1)

        if block is None:
            row1_dict = dict(row1)
            row1_dict.setdefault("provenance", "")
            merged_rows.append(row1_dict)
            continue

        candidate_indices = block["indices"]
        candidate_release_dates = block["release_dates"]
        candidate_titles = block["titles"]

        # Date filteringinside platform block
        if has_value(release1) and isinstance(release1, date):
            filtered = [
                (idx2, title2, release2)
                for idx2, title2, release2 in zip(candidate_indices, candidate_titles, candidate_release_dates)
                if dates_within_x_days(release1, release2, 60)
            ]
            
            if filtered:
                candidates = filtered
            else:
                candidates = list(zip(candidate_indices, candidate_titles, candidate_release_dates))
        else:
            candidates = list(zip(candidate_indices, candidate_titles, candidate_release_dates))

        best_match_idx = None
        best_score = 0.0

        # print(f"Candidates for '{title1}' on platform '{platform1}' with release date '{release1}': {len(candidates)}")
        for idx2, title2, release2 in candidates:
            if idx2 in matched_df2_indices:
                continue

            row2 = df2_records[idx2]

            # score = compute_match_score_from_values(
            #     title1=title1,
            #     title2=title2,
            #     release1=release1,
            #     release2=release2,
            #     platform1=platform1,
            #     platform2=row2.get("platform", pd.NA),
            # )
            score = levenshtein_similarity(title1, title2)

            if score > best_score:
                best_score = score
                best_match_idx = idx2

        if best_match_idx is not None and best_score >= threshold:
            merged_row = merge_records(row1, df2_records[best_match_idx])
            merged_rows.append(merged_row)
            matched_df2_indices.add(best_match_idx)
        else:
            row1_dict = dict(row1)
            row1_dict.setdefault("provenance", "")
            merged_rows.append(row1_dict)

    for idx2, row2 in enumerate(df2_records):
        if idx2 not in matched_df2_indices:
            row2_dict = dict(row2)
            row2_dict.setdefault("provenance", "")
            merged_rows.append(row2_dict)

    return pd.DataFrame(merged_rows)


def merge_identities_v1(df1: pd.DataFrame, df2: pd.DataFrame, threshold: float = 0.85) -> pd.DataFrame:
    df1 = pre_normalize(df1.copy())
    df2 = pre_normalize(df2.copy())

    # smaller -> larger
    if len(df1) > len(df2):
        df1, df2 = df2, df1
        print(f"Swapped datasets for matching (smaller -> larger): {len(df1)} vs {len(df2)}")

    # helper columns prepared once
    df1["_platform_key"] = df1["platform"].astype(str).str.strip().str.lower()
    df2["_platform_key"] = df2["platform"].astype(str).str.strip().str.lower()

    df1["_title_key"] = df1["title"].astype(str).str.strip().str.lower()
    df2["_title_key"] = df2["title"].astype(str).str.strip().str.lower()

    df1["_release_key"] = df1["release_date"]
    df2["_release_key"] = df2["release_date"]

    # turn df2 into dict records once
    df2_records = df2.to_dict(orient="index")

    # build blocking index for df2:
    # first by (platform, release_date), fallback later by platform only
    block_exact = {}
    block_platform = {}

    for idx, row in df2.iterrows():
        p = row["_platform_key"]
        r = row["_release_key"]

        block_platform.setdefault(p, []).append(idx)
        block_exact.setdefault((p, r), []).append(idx)

    result_rows = []
    matched_df2 = set()

    cols = list(df1.columns)
    idx_platform = cols.index("_platform_key")
    idx_title = cols.index("_title_key")
    idx_release = cols.index("_release_key")

    for row1 in tqdm(df1.itertuples(index=True, name=None), total=len(df1), desc="Matching df1 vs df2"):
        idx1 = row1[0]  # Index ist erstes Element

        platform1 = row1[idx_platform + 1]
        title1 = row1[idx_title + 1]
        release1 = row1[idx_release + 1]

        row1_dict = df1.loc[idx1].to_dict()

        # blocking:
        # if release exists -> use exact (platform, release_date)
        # else -> use platform only
        if pd.notna(release1):
            candidate_indices = block_exact.get((platform1, release1), [])
        else:
            candidate_indices = block_platform.get(platform1, [])

        if not candidate_indices:
            single_record = row1_dict
            single_record["match_score"] = pd.NA
            result_rows.append(single_record)
            continue

        best_match = None
        best_score = 0.0

        for idx2 in candidate_indices:
            if idx2 in matched_df2:
                continue

            row2 = df2_records[idx2]

            score = compute_match_score_from_values(
                title1=title1,
                title2=row2["_title_key"],
                release1=release1,
                release2=row2["_release_key"],
                platform1=platform1,
                platform2=row2["_platform_key"],
            )

            if score > best_score:
                best_score = score
                best_match = idx2

                # early stop on perfect title match
                if best_score == 1.0:
                    break
                
        if best_match is not None and best_score >= threshold:
            for helper_key in ("_platform_key", "_title_key", "_release_key"):
                row1_dict.pop(helper_key, None)

            row2_dict = dict(df2_records[best_match])
            for helper_key in ("_platform_key", "_title_key", "_release_key"):
                row2_dict.pop(helper_key, None)

            merged_record = merge_records(row1_dict, row2_dict)
            merged_record["match_score"] = best_score
            result_rows.append(merged_record)
            matched_df2.add(best_match)
        else:
            single_record = row1_dict
            single_record["match_score"] = pd.NA
            result_rows.append(single_record)

    # add unmatched rows from df2
    for idx2, row2_dict in df2_records.items():
        if idx2 not in matched_df2:
            single_record = dict(row2_dict)
            single_record["match_score"] = pd.NA
            result_rows.append(single_record)

    result = pd.DataFrame(result_rows)

    # helper columns entfernen
    helper_cols = ["_platform_key", "_title_key", "_release_key"]
    result = result.drop(columns=[c for c in helper_cols if c in result.columns], errors="ignore")

    return result
        

if __name__ == "__main__":
    df1 = pd.read_csv("data/processed/dataset1_mapped.csv")
    df2 = pd.read_csv("data/processed/dataset2_mapped.csv")
    df3 = pd.read_csv("data/processed/dataset3_mapped.csv")

    df1 = normalize_dates(df1)
    df2 = normalize_dates(df2)
    df3 = normalize_dates(df3)

    print(df3) # 2013-09-17 00:00:00+00:00

