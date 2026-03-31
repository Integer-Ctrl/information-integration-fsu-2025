# Information Integration

## 1. Data Collection / Extraction

## 2. Schema Mapping / Data Translation

In this project, we adopt a Global-as-View (GAV) approach for schema integration.
A unified target schema is defined to represent all relevant attributes of video games. Each source dataset is then mapped into this schema by defining explicit attribute correspondences and applying necessary transformations such as renaming, type conversion, and normalization.
Missing attributes are represented as null values.

Dataset 3 contains a nested attribute Platforms Info with platform-specific metadata.
Since game versions on different platforms are considered separate entities, we apply a denormalization-to-normalization transformation by splitting each record into multiple records, one per platform.
This corresponds to a 1:n mapping with information extraction.

### TODO
- [ ]

## 3. Identity Resolution

- Differences in naming:
    - PS4 vs PlayStation 4

Console Mapping:
1. Created a list of all unique console/platform values across datasets along with their frequencies
2. Used a LLM based on the list to create mapping rules for normalization
3. Applied the mapping rules to standardize console/platform names across datasets

### TODO

Matching: 
- title -> levenshtein/jaro, high similarity
- release date -> exact match
- platform -> exact match

## 4. Data Quality Assessment / Data Fusion

dataset1: last update is sometimes newer than release_date
    - Diablo IV,All,Role-Playing,Blizzard Entertainment,Blizzard Entertainment,,,,,,,01-12-2022,29-10-2020