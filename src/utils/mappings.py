"""
Schema mappings (Correspondences) for Global-as-View (GAV) integration.

- Keys: source attributes
- Values: target attributes
- None: attribute is ignored (not part of target schema)
"""


# ============================================================
# Global Target Schema
# ============================================================

TARGET_SCHEMA = [
    "game_id",
    "title",
    "release_date",
    "developer",
    "publisher",
    "genre",
    "platform",
    "critic_score",
    "user_score",
    "metascore",
    "summary",
    "product_rating",
    "total_sales",
    "source",
]


# ============================================================
# Dataset 1 Mapping
# ============================================================

DATASET1 = {
    "img": None,
    "title": "title",
    "console": "platform",
    "genre": "genre",
    "publisher": "publisher",
    "developer": "developer",
    "critic_score": "critic_score",
    "total_sales": "total_sales",
    "na_sales": None,
    "jp_sales": None,
    "pal_sales": None,
    "other_sales": None,
    "release_date": "release_date",
    "last_update": None,  # not part of target schema
}


# ============================================================
# Dataset 2 Mapping
# ============================================================

DATASET2 = {
    "name": "title",
    "platform": "platform",
    "release_date": "release_date",
    "summary": "summary",
    "user_review": "user_score",
}


# ============================================================
# Dataset 3 Mapping
# ============================================================

DATASET3 = {
    "Title": "title",
    "Release Date": "release_date",
    "Developer": "developer",
    "Publisher": "publisher",
    "Genres": "genre",
    "Product Rating": "product_rating",
    "User Score": "user_score",
    "User Ratings Count": None,
    "Platforms Info": {"Platform": "platform", "Platform Metascore": "metascore", "Platform Metascore Count": None}, # information extraction required
}


# ============================================================
# Notes for implementation
# ============================================================

"""
Special handling required:

- "Platforms Info" (Dataset 3):
  -> contains multiple values (platform, metascore, review count)
  -> requires parsing / information extraction
  -> only 'platform' is mapped to target schema

- All attributes mapped to None:
  -> should be ignored during transformation

- Missing target attributes:
  -> must be filled with NULL / NaN

- This file defines ONLY correspondences
  -> actual transformations are implemented in schema_mapping.py
"""