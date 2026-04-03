# Information Integration

## 1. Data Collection / Extraction

File: [data_extraction.py](./data_extraction.py)

We use three CSV datasets from Kaggle related to video games.
They share some attributes but also contain dataset-specific information.

- **Dataset 1**
  - Name: 
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

Warum vergleichen wir nicht nur die Titel?
-> Grand Theft Auto 3 vs Grand Theft Auto 4 -> zwei verschiedene Spiele, aber ähnliche Titel (Levenshtein würde hier zu einem False Positive führen)
-> Betrachtung der Release Dates um zwischen verschiedenen Spielen mit ähnlichen Titeln zu unterscheiden

Warum kann man sich nicht auf eine exakte Übereinstimmung der Release Dates verlassen?
-> Uncertainty, verschiedene Quellen
-> Release Dates können für dasselbe Spiel und für die selbe Plattform trotzdem unterschiedlich sein, da
- sie an verschiedenen Tagen in verschiedenen Regionen veröffentlicht werden können (4x4 Evo 2)
- Early Access und Full Release unterschiedliche Daten haben können (Mount & Blade 2: Bannerlord)


## 4. Data Quality Assessment / Data Fusion

dataset1: last update is sometimes newer than release_date
    - Diablo IV,All,Role-Playing,Blizzard Entertainment,Blizzard Entertainment,,,,,,,01-12-2022,29-10-2020

Grand Theft Auto 5,PlayStation 5,2014-11-18,Rockstar North,Rockstar Games,Action,,8.4,81,Rated M For Mature,,ds3,,,16392.0
Grand Theft Auto 5,PlayStation 5,2021-12-01,Rockstar Games,Rockstar Games,Action,,,,,,ds1,,,18962.0