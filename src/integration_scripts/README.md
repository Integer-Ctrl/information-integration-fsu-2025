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

Using only titles is not sufficient, as many games share identical names across platforms or within a series For example, "Grand Theft Auto 3" vs. "Grand Theft Auto 4" have a high string similarity but are clearly different games. Including the release date helps distinguish between such cases, as they are released at different times.

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

First lets have a look at some numerical statistics of the integrated dataset. The sum of records across all three input datasets is **96872**, while the final integrated dataset contains **80523** records. This means that we were able to match and merge a significant number of records across datasets.


<!-- F: ich würde Evaluation in zwei Teilbereiche unterteilen: -->
<!-- F: ## Input data quality -->
<!-- F: ## Integrated (output) data quality -->
<!-- Dadurch kann man besser unterteilen was an uns lag, was an den Quelldaten lag und ob und wenn wir input Probleme addressiert haben -->

After integrating the three datasets, the overall data quality can be considered **mixed**. While the integration process was successful in combining information from multiple sources, several issues remain that affect the usability of the final dataset.

### General Observations

- The integration increases the amount of available information per game.
- However, due to limited overlap between datasets, many attributes are still missing.
- Some inconsistencies from the source data could not be fully resolved.

### Identified Issues

<!-- F: das haben wir doch normalisiert? Die genannten Beispiele haben wir doch perfekt behandelt -->
#### 1. Inconsistent Formats and Naming

- Different date formats (e.g., `2014-11-18`, `18-11-2014`, `November 18, 2014`)
- Variations in titles (e.g., *"Grand Theft Auto 5"* vs. *"GTA V"*)
- Variations in platform names (e.g., *"PlayStation 4"* vs. *"PS4"*)

We addressed this partially (e.g., platform normalization), but not all inconsistencies could be removed.

<!-- F: das ist doch aber nicht unser Problem. Wir können nur auf den gegebenen Daten arbeiten und nicht die Quelldaten ändern um z.B. einen score zu erzeugen-->
#### 2. Missing Values

- Many attributes are only present in one dataset (e.g., scores, reviews)
- This leads to a high number of NULL values in the final dataset
- Dataset 1 also contains many `"Unknown"` entries for developer and publisher

Example:
- *#DRIVE Rally* has no score or rating information after integration

<!-- F: Input data quality -->
#### 3. Temporal Issues

- Some date values are inconsistent or implausible
  - Example: *Diablo IV* has a `last_update` earlier than its `release_date`
- Release dates can differ across datasets (e.g., due to regional releases)

<!-- F: Input data quality -->
#### 4. Ambiguities from Integration

- Dataset 3 assigns one release date to multiple platforms
  - After splitting into multiple records, this can lead to incorrect combinations
  - Example: *GTA V* assigned to PlayStation 5 with a 2014 release date

- User-related attributes are not directly comparable:
  - *user_score* vs. *user_review* (no common scale or definition)

<!-- F: Input data quality -->
### 5. Dublicate in input data
4x4 Evo 2 -> PC


<!-- F: Intgrated data quality -->
- Attribute die nur an einer Kosole hängen werden nicht auf andere Platform propagiert, e.g. Genre, Summary

### Possible Improvements

- Improve normalization of titles and platforms (e.g., more mapping rules)
- Use additional attributes (developer, genre) for better identity resolution
- Apply simple validation rules (e.g., release date should match platform generation)
- Integrate additional datasets to reduce missing values
- Handle ambiguous cases more carefully (e.g., flag instead of duplicating)

### Conclusion

The integrated dataset is usable but still contains **missing values, inconsistencies, and some incorrect mappings**.  
With additional cleaning and validation steps, the data quality could be improved further.