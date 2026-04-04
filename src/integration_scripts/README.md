# Information Integration

The information integration process consists of the following steps:
1. [Data Collection / Extraction](#1-data-collection--extraction)
2. [Schema Mapping / Data Translation](#2-schema-mapping--data-translation)
3. [Identity Resolution](#3-identity-resolution)
4. [Data Quality Assessment](#4-data-quality-assessment)

Each step besides data quality assessment is implemented in a separate script, which can be executed independently.
The scripts are designed to be modular and are combined in the [main.py](../main.py) script, which executes the entire integration pipeline from data extraction to the final integrated dataset.

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

### Integration Strategy

We perform pairwise integration of the three datasets. First, two datasets are integrated into an intermediate result. This result is then integrated with the remaining dataset in a second step. Consequently, the matching and merging logic is designed to operate on two datasets at a time. The final integrated dataset is obtained after these two integration steps.

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

Using only titles is not sufficient, as many games share nearly identical names across platforms or within a series. For example, "Grand Theft Auto 3" vs. "Grand Theft Auto 4" have a high string similarity but are clearly different games. Including the release date helps distinguish between such cases, as they are released at different times.

However, this comes with its own challenges, as the dates are specified in different formats across datasets and can be missing or inconsistent. 
Release dates can also vary across regions, such as "4x4 Evo 2" on PC, which has two entries with dates for EU and NA.
Furthermore, there can also be different release dates for early access and full release (e.g., two entries for "Mount & Blade 2: Bannerlord" with a 2-year difference in release dates).
To allow for some flexibility, we use a function that calculates a similarity score (between 0.0 and 1.0) based on the difference in release dates, giving higher scores to records with closer release dates. While a missing date results in a score of 0.0, if the title similarity is very high, we can still consider it a match.

The last problem to tackle is the runtime. Comparing each record in one dataset to all records in the other dataset can be very time-consuming. To optimize this we use a greedy matching together with blocking.

**Greedy matching**: We compare each record of the smaller dataset to records from the larger dataset and select the best match if it exceeds the similarity threshold. Once a match is made, the matched record from the larger dataset is removed from consideration for future matches. This prevents multiple records from being matched to the same record in the larger dataset.

**Blocking**: To compare against all records from the larger dataset is inefficient. Therefore we do two blocking steps:
1. We first block records based on their platform, as games on different platforms cannot be the same game according to our definition of identity. This significantly reduces the number of comparisons needed.
2. If the record to be compared has a release date, we further block the records in the platform block to only those that have a release dates within the same year and the year before and after. This allows for some flexibility in release dates (since some release dates vary significantly) while still significantly reducing the number of comparisons.

There are two edge cases to consider in the blocking strategy:
1. If the record to be compared does not have a release date, we cannot apply the second blocking step. In this case, we only block based on platform and compare against all records in the same platform block.
2. If a record in the larger dataset (that we compare against) does not have a release date, we add it to all blocks of the same platform (regardless of the release date of the block). This allows us to still consider records without release dates as potential matches, while ensuring that they are only compared against records of the same platform.

After blocking, we calculate the overall similarity score for each candidate record by combining the title and release date similarity.
- Title similarity: we use normalized Levenshtein distance to calculate a similarity score between 0.0 and 1.0, where 1.0 means an exact match and 0.0 means completely different titles.
- Release date similarity: we use a custom function that calculates a similarity score based on the difference in release dates, giving higher scores to records with closer release dates. A missing date results in a score of 0.0, but if the title similarity is very high, we can still consider it a match.
- Overall similarity: `sim(a,b) = NORMALIZED_TITLE_WEIGHT * title_similarity + (1 - NORMALIZED_TITLE_WEIGHT) * release_date_similarity`.

In our implementation, we set the `NORMALIZED_TITLE_WEIGHT` to 0.85 and the similarity threshold as well to 0.85, meaning that we require a high title similarity and allow for some flexibility in release dates.

The full matching process is as follows:
1. Create blocks of the larger dataset based on platform and release date (if available)
2. For each record in the smaller dataset, identify the platform and release date (if available)
3. Use the platform to select the appropriate block(s) from the larger dataset and further filter by release date if available
4. Calculate the overall similarity score for each candidate record in the block and select the best match that exceeds the similarity threshold
5. If a match is found, merge the records (see [Merging Strategy](#merging-strategy) below) and remove the matched record from the larger dataset to prevent multiple matches
6. If no match is found, add the record from the smaller dataset to the integrated dataset as a new entry
7. For all unmatched records in the larger dataset, add them to the integrated dataset as new entries

### Merging Strategy

To merge two matched records, we have defined a enum with possible merging strategies in [enums.py](../utils/enums.py) and implemented the individual merging cases in [data_utils.py](../utils/data_utils.py). The merging strategy defines how to combine the values of attributes from two matched records. For example, for the `title` we use **max**. That means we use the longer title between the two records, as it is more likely to contain additional information (e.g., "GTA V" vs. "Grand Theft Auto V"). For the `release_date` we use **min**, as it is more likely that one of the records has an incorrect release date that is later than the actual release date.

The attribute `provenance` is used to keep track of the integration process and the source of each piece of information. When merging two records, we combine their provenance information to indicate which datasets contributed to the final merged record. This allows us to trace back the origin of each attribute value in the integrated dataset, which is important for transparency and data quality assessment.

## 4. Data Quality Assessment

The evaluation of the integrated dataset was performed by analyzing the output of the integration process. If unregularities or issues were observed, the provenance information was used to reverse-engineer the integration process and identify the source of the issue. This allowed us to determine whether the issue originated from the input data or from the integration process itself.

### Overall Integration Result

The three input datasets contain a total of **96,872** records, while the final
integrated dataset contains **80,523** records. This indicates that a substantial
number of records were successfully matched and merged.

For games that exist in multiple datasets, the integration process successfully combined information from different sources, resulting in a richer dataset with more attributes per game.

### Data Quality Issues

Issues in the input data and the integration process lead to various data quality problems in the final dataset.

#### Missing and Sparse Attributes

1. Many attributes are only present in one of the datatets, leading to a high number of missing values in the final dataset. For example: 
    - `critic_score`: only in dataset 1 -> missing for all unmatched records from dataset two and three
    - `summary`: only in dataset 2 -> missing for all unmatched records from dataset one and three

2. Some attributes of the same title exist only for a specific platform. Because the entity resolution is only able to match records of the same platform, these attributes cannot be propagated to other platforms. For example:
    - `summary`: different or overall missing for different platforms
      ```
      Grand Theft Auto 5,PlayStation 5,2014-11-18,    [...],
      Grand Theft Auto 5,Xbox Series X / S,2014-11-18,[...],
      Grand Theft Auto 5,PC,2014-11-18,               [...],"Los Santos: a sprawling sun-soaked metropolis..."
      Grand Theft Auto 5,PlayStation 4,2014-11-18,    [...],"The sprawling sun-soaked metropolis of Los Santos..."
      ```
    - `genre`: same game can be listed with different genres on different platforms -> heterogeneous information that is not propagated across platforms

#### Duplicates and Ambiguities

1. Some games have multiple entries in the same input dataset. Because we only match each record to one record in the other dataset, this leads to duplicates in the final dataset. For example:
    - `Dataset 2`: two entries for `4x4 EVO 2,PC` -> duplicate in final dataset
2. The informaion extraction from dataset three assigns the same release date to multiple platforms, which leads to incorrect combinations after splitting into multiple records. For example:
    - `Dataset 3`: The records for `Grand Theft Auto V` have the same release date of `2014-11-18` for all platforms, which is not correct, e.g the PlayStation 5 was released later.

#### Inconsistencies

2. Inconsistent Representations
    - Variations in titles (e.g., *"Grand Theft Auto 5"* vs. *"GTA V"*)
    - Differences in platform naming (e.g., *"PlayStation 4"* vs. *"PS4"*)
    - Different date formats and possible regional release differences

    Some of these inconsistencies were normalized (e.g., platform names), but not all can be resolved without external knowledge.

3. Logical inconsistencies in the input data. For example:
    - `Dataset 2`: *Diablo IV* has a `last_update` of `2023-11-01` which is earlier than its `release_date` of `2023-11-06`, which is not possible. This indicates an error in the input data that cannot be resolved through integration.

### Conclusion and Possible Improvements

The integration successfully combines heterogeneous datasets and increases the
overall information content per entity. However, the final dataset still reflects
limitations of the input data, particularly regarding missing values and
inconsistencies.

Importantly, many observed issues originate from the **source data itself** and
cannot be fully resolved without external validation or enrichment (e.g. the release dates).

**Possible Improvements**

- Use additional attributes (developer, genre) for more robust matching to not only rely on title and release date
- Introduce validation rules (e.g., release date should be before last update or release date should match platform generation)
- Propagate attributes across platforms for the same game to reduce sparsity
- Integrate additional datasets to reduce sparsity
- Flag uncertain matches instead of enforcing merges
- Deduplicate records in input datasets before integration to reduce duplicates in the final dataset or do it as post-processing step after integration