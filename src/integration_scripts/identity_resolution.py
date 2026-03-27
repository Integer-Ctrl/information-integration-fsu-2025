import pandas as pd
import roman
import re
from difflib import SequenceMatcher
from tqdm import tqdm
from src.utils.mappings import PLATFORM as platform_mappings

def pre_normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    df = normalize_dates(df)
    df = normalize_platforms(df)
    df = normalize_title_numbers(df)
    df = remove_platform_all(df)
    df = remove_leading_trailing_whitespace(df)
    
    df["summary"] = ""
    
    return df

def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Convert release_date to datetime, handling errors and ensuring UTC timezone
    df["release_date"] = pd.to_datetime(
        df["release_date"],
        errors="coerce",
        utc=True
    )

    # Convert to date only (remove time component)
    df["release_date"] = df["release_date"].dt.date

    return df

def normalize_platforms(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Normalize platform names using the mapping
    df["platform"] = df["platform"].str.lower().map(platform_mappings).fillna(df["platform"])
    
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


def remove_platform_all(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df[df["platform"].str.lower() != "all"]
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
    # if platform1 != platform2:
    #     return 0.0

    # exact release_date match if both exist
    # if pd.notna(release1) and pd.notna(release2) and release1 != release2:
    #     return 0.0

    # release_date within 7 days is acceptable
    if pd.notna(release1) and pd.notna(release2):
        if abs((release1 - release2).days) > 7:
            return 0.0

    # fuzzy title match
    return levenshtein_similarity(title1, title2)


def merge_records(row1: dict, row2: dict) -> dict:
    merged = {}
    all_cols = set(row1.keys()).union(set(row2.keys()))
    sources = set()

    for col in all_cols:
        v1 = row1.get(col, pd.NA)
        v2 = row2.get(col, pd.NA)

        # TODO: could implement more sophisticated conflict resolution here (e.g. prefer non-null, or use match score as weight for numeric fields), but for simplicity we just prefer values from row1 if present
        # TODO: define wether to UNION or use value from one dataset in case of non-null conflict (e.g. summary could be concatenated, while title should be chosen from one)
        if pd.notna(v1) and v1 != "":
            merged[col] = v1
            sources.add(row1.get("source", pd.NA)) # NA shoud not occur, but just in case
        elif pd.notna(v2) and v2 != "":
            merged[col] = v2
            sources.add(row2.get("source", pd.NA))
        else:
            merged[col] = pd.NA

    merged["source"] = "|".join(sorted(sources)) if sources else pd.NA

    return merged


def merge_identities(df1: pd.DataFrame, df2: pd.DataFrame, threshold: float = 0.85) -> pd.DataFrame:
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
            merged_record = merge_records(row1_dict, df2_records[best_match])
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

