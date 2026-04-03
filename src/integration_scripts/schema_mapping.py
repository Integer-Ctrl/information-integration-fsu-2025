import ast
import pandas as pd


def apply_mapping(source: str, df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Apply a schema mapping to a DataFrame.

    The mapping can specify:
    - NULL mapping: target_attr is None -> drop the column
    - 1:1 mapping: target_attr is a string -> rename the column
    - 1:n mapping: target_attr is a dict -> extract information from the original column and create multiple new columns

    Args:
        source: Name of the source dataset for provenance tracking.
        df: Input DataFrame to be transformed.
        mapping: Schema mapping dict where keys are original attribute names and values specify the mapping.

    Returns:
        Transformed DataFrame with the applied schema mapping and added provenance information.
    """
    df = df.copy()

    for orig_attr, target_attr in mapping.items():
        # NULL mapping
        if target_attr is None:
            df.drop(columns=[orig_attr], inplace=True)
        # 1:1 mapping
        elif isinstance(target_attr, str):
            df.rename(columns={orig_attr: target_attr}, inplace=True)
        # 1:n mapping
        elif isinstance(target_attr, dict):
            df = extract_information(df, orig_attr, target_attr)
        else:
            raise ValueError(f"Invalid mapping for attribute '{orig_attr}': {target_attr}")

    # Add source column for provenance tracking
    df["source"] = source
    
    # Add provenance column
    df["provenance"] = f"origin({source})"

    return df


def extract_information(df: pd.DataFrame, orig_attr: str, target_attr: dict) -> pd.DataFrame:
    """Extract information from a column containing string representations of lists of dictionaries and create new columns based on the specified mapping.

    This function assumes that the original column contains string representations of lists of dictionaries (e.g., "[{'key1': 'value1'}, {'key2': 'value2'}]")
    and that the target_attr dict specifies how to map keys from these dictionaries to new column names in the resulting DataFrame.

    E.g.: # "[{'Platform': 'PC', 'Platform Metascore': '72', 'Platform Metascore Count': 'Based on 12 Critic Reviews'},
              {'Platform': 'PlayStation 4', 'Platform Metascore': '69', 'Platform Metascore Count': 'Based on 11 Critic Reviews'}]"

    Args:
        df: Input DataFrame containing the original column.
        orig_attr: Name of the original column to extract information from.
        target_attr: Dict mapping keys from the dictionaries in the original column to new column names in the resulting DataFrame. If a target column name is None, that key will be ignored.

    Returns:
        DataFrame with the original column removed and new columns added based on the extracted information.
    """
    df = df.copy()

    # Convert string representations of lists of dictionaries to actual lists of dictionaries
    df[orig_attr] = df[orig_attr].apply(
        lambda x: ast.literal_eval(x) if pd.notna(x) else []
    )

    # Expand the list of dictionaries into separate rows, then normalize the dictionaries into columns
    df = df.explode(orig_attr)
    extracted = df[orig_attr].apply(lambda x: x if isinstance(x, dict) else {}) # Only keep dicts, replace non-dict values with empty dicts to avoid errors in json_normalize
    extracted_df = pd.json_normalize(extracted)

    # Rename columns based on the target_attr mapping, only keeping those that are actually mapped
    rename_map = {source_key: target_key for source_key, target_key in target_attr.items() if target_key is not None}
    extracted_df = extracted_df.rename(columns=rename_map)

    # Keep only the columns that were mapped to new target column names, ignore the rest
    extracted_df = extracted_df[list(rename_map.values())] if rename_map else pd.DataFrame(index=df.index)

    # Remove the original column and concatenate the extracted columns to the original DataFrame
    df = df.drop(columns=[orig_attr]).reset_index(drop=True)
    extracted_df = extracted_df.reset_index(drop=True)
    df = pd.concat([df, extracted_df], axis=1)
    
    return df