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
    "game_id", # unique identifier, generated as hash of title + platform at the end of transformation
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
    "source", # provenance information: which dataset(s) contributed to this record
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
# Platform Mapping
# ============================================================

PLATFORM = {
    # --- PC / Desktop ---
    "pc": "PC",
    "winp": "PC",
    "windows": "PC",
    "osx": "MacOS",
    "mac": "MacOS",
    "linux": "Linux",

    # --- PlayStation ---
    "playstation": "PlayStation",
    "ps": "PlayStation",
    "ps1": "PlayStation",

    "playstation 2": "PlayStation 2",
    "ps2": "PlayStation 2",

    "playstation 3": "PlayStation 3",
    "ps3": "PlayStation 3",

    "playstation 4": "PlayStation 4",
    "ps4": "PlayStation 4",

    "playstation 5": "PlayStation 5",
    "ps5": "PlayStation 5",

    # --- PlayStation Handheld ---
    "psp": "PSP",
    "psv": "PlayStation Vita",
    "ps vita": "PlayStation Vita",
    "playstation vita": "PlayStation Vita",

    # --- Xbox ---
    "xbox": "Xbox",
    "xb": "Xbox",

    "xbox 360": "Xbox 360",
    "x360": "Xbox 360",

    "xbox one": "Xbox One",
    "xone": "Xbox One",

    "xs": "Xbox Series X / S",
    "series": "Xbox Series X / S",
    "xbox series": "Xbox Series X / S",
    "xbox series x": "Xbox Series X / S",
    "xbox series s": "Xbox Series X / S",

    # --- Nintendo ---
    "ns": "Nintendo Switch",
    "switch": "Nintendo Switch",
    "nintendo switch": "Nintendo Switch",

    "wii": "Wii",
    "wiiu": "Wii U",
    "wii u": "Wii U",

    "gamecube": "GameCube",
    "gc": "GameCube",

    "n64": "Nintendo 64",
    "nintendo 64": "Nintendo 64",

    "nes": "NES",
    "snes": "SNES",

    "gb": "Game Boy",
    "gbc": "Game Boy Color",
    "gba": "Game Boy Advance",
    "game boy advance": "Game Boy Advance",

    "ds": "Nintendo DS",
    "dsi": "Nintendo DSi",
    "dsiw": "Nintendo DSi",
    "3ds": "Nintendo 3DS",

    # --- Mobile ---
    "android": "Android",
    "and": "Android",
    "ios": "iOS",
    "ios (iphone/ipad)": "iOS",
    "mob": "Mobile",

    # --- Digital Platforms ---
    "psn": "PlayStation Network",
    "xbl": "Xbox Live",
    "vc": "Virtual Console",

    # --- Sega ---
    "dc": "Dreamcast",
    "dreamcast": "Dreamcast",
    "sat": "Sega Saturn",
    "gen": "Sega Genesis",
    "smd": "Sega Mega Drive",
    "gg": "Game Gear",
    "scd": "Sega CD",
    "32x": "Sega 32X",
    "s32x": "Sega 32X",

    # --- Other Consoles ---
    "3do": "3DO",
    "cdi": "Philips CD-i",
    "int": "Intellivision",
    "colecovision": "ColecoVision",
    "cv": "ColecoVision",
    "5200": "Atari 5200",
    "7800": "Atari 7800",
    "2600": "Atari 2600",
    "lynx": "Atari Lynx",
    "jaguar": "Atari Jaguar",
    "aj": "Atari Jaguar",

    # --- Computer Systems ---
    "c64": "Commodore 64",
    "amig": "Amiga",
    "msx": "MSX",
    "zxs": "ZX Spectrum",
    "bbc": "BBC Micro",
    "bbcm": "BBC Micro",

    # --- Misc / Modern ---
    "meta quest": "Meta Quest",
    "quest": "Meta Quest",
    "stadia": "Stadia",
    "ouya": "Ouya",

    # --- Arcade ---
    "arc": "Arcade",
    "arcade": "Arcade",

    # --- Browser ---
    "brw": "Browser",
    "browser": "Browser",

    # --- Rare / Edge ---
    "ng": "Neo Geo",
    "neogeo": "Neo Geo",
    "ngage": "N-Gage",
    "giz": "Gizmondo",
    "vb": "Virtual Boy",
}

GENRE = {
  "misc": "Miscellaneous",
  "auto racing sim": "Racing",
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