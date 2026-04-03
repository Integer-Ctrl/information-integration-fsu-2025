## Target Schema

The unified schema after integration:

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


## Attribute Mapping

The mapping from source datasets to the target schema is as follows:

**Dataset 1**

| Source Column   | Target Column |
|-----------------|---------------|
| img             | —             |
| title           | title         |
| console         | platform      |
| genre           | genre         |
| publisher       | publisher     |
| developer       | developer     |
| critic_score    | critic_score  |
| total_sales     | total_sales   |
| na_sales        | —             |
| jp_sales        | —             |
| pal_sales       | —             |
| other_sales     | —             |
| release_date    | release_date  |
| last_update     | —             |

---

**Dataset 2**

| Source Column | Target Column |
|---------------|---------------|
| name          | title         |
| platform      | platform      |
| release_date  | release_date  |
| summary       | summary       |
| user_review   | user_review   |

---

**Dataset 3**

| Source Column         | Target Column                          |
|-----------------------|----------------------------------------|
| Title                 | title                                  |
| Release Date          | release_date                           |
| Developer             | developer                              |
| Publisher             | publisher                              |
| Genres                | genre                                  |
| Product Rating        | product_rating                         |
| User Score            | user_score                             |
| User Ratings Count    | user_ratings_count                     |
| Platforms Info        | 1:n mapping -> platform, metascore     |