import ast
import pandas as pd


def apply_mapping(source: str, df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
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
            # "[{'Platform': 'PC', 'Platform Metascore': '72', 'Platform Metascore Count': 'Based on 12 Critic Reviews'}, {'Platform': 'PlayStation 4', 'Platform Metascore': '69', 'Platform Metascore Count': 'Based on 11 Critic Reviews'}]"
            df = extract_information(df, orig_attr, target_attr)
        else:
            raise ValueError(f"Invalid mapping for attribute '{orig_attr}': {target_attr}")

    # Add source column for provenance tracking
    df["source"] = source
    
    # Add provenance column
    df["provenance"] = pd.NA

    return df


def extract_information(df: pd.DataFrame, orig_attr: str, target_attr: dict) -> pd.DataFrame:
    df = df.copy()

    # String -> Python list
    df[orig_attr] = df[orig_attr].apply(
        lambda x: ast.literal_eval(x) if pd.notna(x) else []
    )

    # List -> multiple rows
    df = df.explode(orig_attr)
    # Nur echte dicts behalten, sonst json_normalize kaputt
    extracted = df[orig_attr].apply(lambda x: x if isinstance(x, dict) else {})
    extracted_df = pd.json_normalize(extracted)

    # Nur gewünschte Felder übernehmen / umbenennen
    rename_map = {source_key: target_key for source_key, target_key in target_attr.items() if target_key is not None}
    extracted_df = extracted_df.rename(columns=rename_map)

    # Nur Zielspalten behalten, die wirklich gemappt werden
    extracted_df = extracted_df[list(rename_map.values())] if rename_map else pd.DataFrame(index=df.index)

    # Originalspalte entfernen und neue Spalten anhängen
    df = df.drop(columns=[orig_attr]).reset_index(drop=True)
    extracted_df = extracted_df.reset_index(drop=True)

    df = pd.concat([df, extracted_df], axis=1)
    return df