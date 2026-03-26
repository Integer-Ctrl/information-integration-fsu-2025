# Information Integration

## 1. Data Extraction

In this project, we adopt a Global-as-View (GAV) approach for schema integration.
A unified target schema is defined to represent all relevant attributes of video games. Each source dataset is then mapped into this schema by defining explicit attribute correspondences and applying necessary transformations such as renaming, type conversion, and normalization.
Missing attributes are represented as null values.

Dataset 3 contains a nested attribute Platforms Info with platform-specific metadata.
Since game versions on different platforms are considered separate entities, we apply a denormalization-to-normalization transformation by splitting each record into multiple records, one per platform.
This corresponds to a 1:n mapping with information extraction.

## 2. Data Mapping

## 3. Data Matching

## 4. Data Fusion