import pandas as pd
import re
import roman

def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes release_date column to datetime.date, handling various formats and edge cases.

    Converts existing release_date values into datetime.date yyyy-mm-dd format.
    On missing or invalid release_date values, sets them to pd.NA. Handles 'tbd' as a special case and converts it to pd.NA.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with normalized release_date column.
    """
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
    """Normalizes score columns by replacing 'tbd' with pd.NA.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with normalized score columns.
    """
    df = df.copy()

    if "metascore" in df.columns:
        df["metascore"] = df["metascore"].replace(r"(?i)^\s*tbd\s*$", pd.NA, regex=True)
    if "user_score" in df.columns:
        df["user_score"] = df["user_score"].replace(r"(?i)^\s*tbd\s*$", pd.NA, regex=True)
    if "critic_score" in df.columns:
        df["critic_score"] = df["critic_score"].replace(r"(?i)^\s*tbd\s*$", pd.NA, regex=True)

    return df


def normalize_by_mapping(df: pd.DataFrame, mapping: dict, column: str) -> pd.DataFrame:
    """Normalizes values in a column based on a provided mapping.

    Args:
        df (pd.DataFrame): Input DataFrame.
        mapping (dict): Mapping dictionary.
        column (str): Column name to normalize.

    Returns:
        pd.DataFrame: DataFrame with normalized column.
    """
    df = df.copy()
    if column in df.columns: # the column might not exist in all datasets
        df[column] = df[column].str.lower().map(mapping).fillna(df[column])
    return df


def normalize_title_numbers(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes roman numerals in title column to Arabic numerals.

    For example: "Final Fantasy VII" -> "Final Fantasy 7", "Resident Evil III" -> "Resident Evil 3"

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with normalized title column.
    """
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
    """Remove records with platform 'all' or missing values.

    Such records cannot be reliably matched across datasets, as platform is
    required to uniquely identify a game (together with its title).

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    df = df.copy()
    df = df[df["platform"].str.lower() != "all"]
    df = df[df["platform"].notnull()]

    return df

def remove_leading_trailing_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Removes leading and trailing whitespace from all string columns.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: Cleaned DataFrame.
    """
    df = df.copy()
    for col in df.select_dtypes(include=["object", "string"]):
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    return df