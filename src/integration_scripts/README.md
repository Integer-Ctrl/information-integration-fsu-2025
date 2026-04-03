# Information Integration

## 1. Data Collection / Extraction

File: [data_extraction.py](./data_extraction.py)

This step loads three video game datasets from Kaggle using `kagglehub` python package.
Each dataset is downloaded, cached locally, and loaded as a pandas DataFrame.

We use three CSV datasets from Kaggle related to video games.
They share some attributes but also contain dataset-specific information.

- **Dataset 1**
  - Name: Video Games Dataset
  - Url: https://www.kaggle.com/datasets/ujjwalaggarwal402/video-games-dataset/data
  - Format: CSV
  - #entities: 64017
  - #attributes: 14
  - attributes: img,title,console,genre,publisher,developer,critic_score,total_sales,na_sales,jp_sales,pal_sales,other_sales,release_date,last_update
- **Dataset 2**
  - Name: Video Games Data
  - Url: https://www.kaggle.com/datasets/maso0dahmed/video-games-data
  - Format: CSV
  - #entities: 18800
  - #attributes: 5
  - attributes: name,platform,release_date,summary,user_review
- **Dataset 3**
  - Name: 🎮Video Games Dataset
  - Url: https://www.kaggle.com/datasets/beridzeg45/video-games
  - Format: CSV
  - #entities: 14055
  - #attributes: 9
  - attributes: Title,Release Date,Developer,Publisher,Genres,Product Rating,User Score,User Ratings Count,Platforms Info


## 2. Schema Mapping / Data Translation

File: [schema_mapping.py](./schema_mapping.py)

To integrate the three datasets, we first analyzed their schemas and identified
relevant attributes for a unified representation.

A key design decision was how to define entity uniqueness. We consider a game uniquely identified by the combination of **title** and **platform**,
as the same game can exist on multiple platforms.

### Target Schema

First, we define a unified target schema that captures all relevant information across datasets:

| Attribute        |
|------------------|
| title            |
| release_date     |
| developer        |
| publisher        |
| genre            |
| platform         |
| critic_score     |
| user_score       |
| user_review      |
| summary          |
| product_rating   |
| total_sales      |
| source           |
| provenance       |

The attributes `source` and `provenance` are included to ensure traceability of records to generate provenance metadata for the integrated dataset.

### Mapping Strategy

Each dataset is mapped to the target schema using explicit attribute correspondences defined in [`schema.md`](../../schema.md) 
and implemented in [`mappings.py`](../utils/mappings.py).

We distinguish three types of mappings:
- **NULL mapping**  
  Attributes not relevant for the target schema are discarded.
- **1:1 mapping**  
  Attributes are directly mapped (renamed) without transformation.
- **1:n mapping**  
  A single attribute is transformed into multiple attributes.  
  This is required when information is nested or encoded within a single column.

The mapping logic is applied dynamically via the `apply_mapping` function in [`schema_mapping.py`](./schema_mapping.py) which takes a dataset and a mapping definition to produce a transformed DataFrame conforming to the target schema.

## 3. Identity Resolution

File: [identity_resolution.py](./identity_resolution.py)

To identify records that refer to the same video game across two datasets, we combine **title similarity, release date similarity, and exact platform matching**.

### Preprocessing

Before matching records and merging them, we applied a bunch of preprocessing steps to normalize the data and make it more comparable across datasets. The following steps were taken:
- Normalize release dates to `datetime.date` objects to obtain `YYYY-MM-DD` format and allow for date comparisons
- Normalize platform, genre, developer, publisher using predefined mappings (see [mappings.py](../utils/mappings.py))
- Normalize title by removing extra whitespace and standardizing number formats (e.g. "Final Fantasy VII" -> "Final Fantasy 7")
- Normalize scores to a common scale if needed (e.g. if some datasets have scores out of 10 and others out of 100)
- Remove records with platform "All" or missing platform, as they are not useful for identity resolution and can introduce noise
- Remove leading/trailing whitespace from all string fields to avoid false mismatches due to formatting inconsistencies

To obtain the predefined mappings for normalization, we first created (using pandas) a list of all unique values for the relevant attributes across datasets along with their frequencies. Then, we used a LLM (ChatGPT 5.3 Instant) to generate mapping rules for normalization based on the list of unique values. The steps we took are as follows:

1. Created a list of all unique console/platform values across datasets along with their frequencies
2. Used a LLM based on the list to create mapping rules for normalization
3. Applied the mapping rules to standardize console/platform names across datasets
4. Manually reviewed the mapping results to ensure accuracy and consistency across specific cases

### Matching Logic

Using only titles is not sufficient, as many games share identical names across platforms or within a series For example, "Grand Theft Auto 3" vs. "Grand Theft Auto 4" have a high string similarity but are clearly different games. Including the release date helps distinguish between such cases, as they are released at different times.

### Merging Strategy



---

A combination of title similarity and exact platform matching might sound promising, but it is not sufficient for correct identity resolution. 
In many cases, it can lead to false positives, especially for games that are part of a series or have similar titles (e.g., "Grand Theft Auto 3" and "Grand Theft Auto 4").
When comparing these records, the title similarity might be high, but they are clearly different games.

To address this, we also consider the release dates of the games.
However, this comes with its own challenges, as the dates are specified in different formats across datasets and can be missing or inconsistent. 
Release dates can also vary across regions, such as "4x4 Evo 2" on PC, which has two entries with dates for EU and NA.
Furthermore, there can also be different release dates for early access and full release (e.g., two entries for "Mount & Blade 2: Bannerlord" with a 2-year difference in release dates).
To allow for some flexibility, we use a function that calculates a similarity score (between 0.0 and 1.0) based on the difference in release dates, giving higher scores to records with closer release dates. While a missing date results in a score of 0.0, if the title similarity is very high, we can still consider it a match.

The full identity resolution process is as follows:
1. Block records based on their platform (for higher efficiency)
2. Only look for matches within the same platform block (forces exact platform matches)
3. Calculate title similarity using Levenshtein distance and normalize it to a score between 0.0 and 1.0
4. Calculate release date similarity using a custom function that considers the difference in release dates
5. Combine the title similarity and release date similarity scores using a weighted average
6. Only consider records over a certain threshold and choose the best match for merging
7. Remove the merged record from the pool to prevent multiple matches to the same record

## 4. Data Quality Assessment

After integrating the three datasets, the overall data quality can be considered **mixed**. While the integration process was successful in combining information from multiple sources, several issues remain that affect the usability of the final dataset.

### General Observations

- The integration increases the amount of available information per game.
- However, due to limited overlap between datasets, many attributes are still missing.
- Some inconsistencies from the source data could not be fully resolved.

### Identified Issues

#### 1. Inconsistent Formats and Naming

- Different date formats (e.g., `2014-11-18`, `18-11-2014`, `November 18, 2014`)
- Variations in titles (e.g., *"Grand Theft Auto 5"* vs. *"GTA V"*)
- Variations in platform names (e.g., *"PlayStation 4"* vs. *"PS4"*)

We addressed this partially (e.g., platform normalization), but not all inconsistencies could be removed.

#### 2. Missing Values

- Many attributes are only present in one dataset (e.g., scores, reviews)
- This leads to a high number of NULL values in the final dataset
- Dataset 1 also contains many `"Unknown"` entries for developer and publisher

Example:
- *#DRIVE Rally* has no score or rating information after integration

#### 3. Temporal Issues

- Some date values are inconsistent or implausible
  - Example: *Diablo IV* has a `last_update` earlier than its `release_date`
- Release dates can differ across datasets (e.g., due to regional releases)

#### 4. Ambiguities from Integration

- Dataset 3 assigns one release date to multiple platforms
  - After splitting into multiple records, this can lead to incorrect combinations
  - Example: *GTA V* assigned to PlayStation 5 with a 2014 release date

- User-related attributes are not directly comparable:
  - *user_score* vs. *user_review* (no common scale or definition)

### Possible Improvements

- Improve normalization of titles and platforms (e.g., more mapping rules)
- Use additional attributes (developer, genre) for better identity resolution
- Apply simple validation rules (e.g., release date should match platform generation)
- Integrate additional datasets to reduce missing values
- Handle ambiguous cases more carefully (e.g., flag instead of duplicating)

### Conclusion

The integrated dataset is usable but still contains **missing values, inconsistencies, and some incorrect mappings**.  
With additional cleaning and validation steps, the data quality could be improved further.