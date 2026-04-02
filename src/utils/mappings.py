"""
Schema mappings (Correspondences) for Global-as-View (GAV) integration.

- Keys: source attributes
- Values: target attributes
- None: attribute is ignored (not part of target schema)
"""

from src.utils.enums import ENTITY_RESOLUTION_TYPES


# ============================================================
# Global Target Schema
# ============================================================

TARGET_SCHEMA = [
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
    "provenance",
]

ENTITY_RESOLUTION = {
    "title": ENTITY_RESOLUTION_TYPES.LONGEST,
    "release_date": ENTITY_RESOLUTION_TYPES.MIN,
    "developer": ENTITY_RESOLUTION_TYPES.LONGEST,
    "publisher": ENTITY_RESOLUTION_TYPES.LONGEST,
    "genre": ENTITY_RESOLUTION_TYPES.UNION,
    "platform": ENTITY_RESOLUTION_TYPES.NOTHING, # Entity resolution is based on exact match of platform -> no resolution required
    "critic_score": ENTITY_RESOLUTION_TYPES.MAX,
    "user_score": ENTITY_RESOLUTION_TYPES.MAX,
    "metascore": ENTITY_RESOLUTION_TYPES.MAX,
    "summary": ENTITY_RESOLUTION_TYPES.UNION,
    "product_rating": ENTITY_RESOLUTION_TYPES.MAX,
    "total_sales": ENTITY_RESOLUTION_TYPES.MAX,
    "source": ENTITY_RESOLUTION_TYPES.UNION,
    "provenance": ENTITY_RESOLUTION_TYPES.NOTHING,
}


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
    "xbox live": "Xbox Network",
    "xbox network": "Xbox Network",

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
    "playstation network": "PlayStation Network",
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
    # Canonical top-level genres
    "misc": "Miscellaneous",
    "miscellaneous": "Miscellaneous",
    "action": "Action",
    "adventure": "Adventure",
    "role-playing": "RPG",
    "rpg": "RPG",
    "sports": "Sports",
    "shooter": "Shooter",
    "platform": "Platform",
    "strategy": "Strategy",
    "racing": "Racing",
    "puzzle": "Puzzle",
    "simulation": "Simulation",
    "fighting": "Fighting",

    # Action / Adventure variants
    "action adventure": "Action",
    "action-adventure": "Action",
    "open-world action": "Action",
    "linear action adventure": "Action",
    "first-person adventure": "Adventure",
    "third-person adventure": "Adventure",
    "point-and-click": "Point-and-Click",
    "text adventure": "Adventure",
    "visual novel": "Adventure",
    "survival": "Survival",
    "sandbox": "Sandbox",

    # RPG variants
    "action rpg": "RPG",
    "jrpg": "RPG",
    "rpg": "RPG",
    "western rpg": "RPG",
    "trainer rpg": "RPG",
    "mmorpg": "RPG",
    "mmo": "RPG",

    # Shooter variants
    "fps": "FPS,Shooter",
    "third person shooter": "Shooter",
    "tactical third person shooter": "Shooter",
    "tactical fps": "FPS,Shooter",
    "rail shooter": "Shooter",
    "light gun": "Shooter",
    "top-down shoot-'em-up": "Top-Down,Shooter",
    "vertical shoot-'em-up": "Vertical,Shooter",
    "horizontal shoot-'em-up": "Horizontal,Shooter",

    # Platform / Fighting variants
    "2d platformer": "Platform",
    "3d platformer": "Platform",
    "metroidvania": "Platform",
    "2d fighting": "Fighting",
    "3d fighting": "Fighting",
    "2d beat-'em-up": "Fighting",
    "3d beat-'em-up": "Fighting",
    "wrestling": "Fighting",
    "combat sport": "Sports",

    # Strategy variants
    "turn-based tactics": "Strategy",
    "real-time strategy": "Strategy",
    "command rts": "Strategy",
    "turn-based strategy": "Strategy",
    "real-time tactics": "Strategy",
    "4x strategy": "Strategy",
    "defense": "Strategy",
    "artillery": "Strategy",
    "moba": "Strategy",

    # Racing variants
    "auto racing": "Racing",
    "auto racing sim": "Racing",
    "arcade racing": "Racing",
    "future racing": "Racing",
    "racing sim": "Racing",
    "horse racing": "Horse Racing",

    # Puzzle / Board variants
    "action puzzle": "Puzzle",
    "matching puzzle": "Puzzle",
    "logic puzzle": "Puzzle",
    "stacking puzzle": "Puzzle",
    "board": "Puzzle",
    "board game": "Puzzle",
    "card battle": "Puzzle",
    "hidden object": "Puzzle",
    "trivia": "Puzzle",

    # Simulation variants
    "tycoon": "Simulation",
    "management": "Simulation",
    "virtual life": "Simulation",
    "virtual career": "Simulation",
    "virtual pet": "Simulation",
    "vehicle sim": "Simulation",
    "aircraft combat sim": "Aircraft Simulation",
    "vehicle combat sim": "Simulation",
    "space combat sim": "Aircraft Simulation",
    "marine combat sim": "Marine Simulation",
    "aircraft sim": "Aircraft Simulation",
    "space sim": "Aircraft Simulation",
    "marine sim": "Marine Simulation",
    "train sim": "Train Simulation",
    "application": "Application",

    # Sports variants
    "soccer sim": "Football,Sports",
    "football sim": "Football,Sports",
    "basketball sim": "Basketball,Sports",
    "baseball sim": "Baseball,Sports",
    "golf sim": "Golf,Sports",
    "soccer": "Football,Sports",
    "football": "Football,Sports",
    "basketball": "Basketball,Sports",
    "baseball": "Baseball,Sports",
    "golf": "Golf,Sports",
    "hockey": "Hockey,Sports",
    "tennis": "Tennis,Sports",
    "skiing": "Skiing,Sports",
    "athletics": "Sports",
    "biking": "Biking,Sports",
    "fishing": "Fishing,Sports",
    "hunting": "Hunting,Sports",
    "surfing": "Surfing,Sports",
    "rugby": "Rugby,Sports",
    "cricket": "Cricket,Sports",
    "bowling": "Bowling,Sports",
    "volleyball": "Volleyball,Sports",
    "skating": "Skating,Sports",
    "soccer management": "Football,Sports",
    "individual sports": "Sports",
    "team sports": "Sports",

    # Misc/arcade/music/other variants
    "arcade": "Arcade",
    "party": "Party Game",
    "compilation": "Miscellaneous",
    "music": "Music",
    "rhythm": "Music",
    "dancing": "Dancing",
    "pinball": "Pinball",
    "gambling": "Gambling",
    "future sport": "Sports",
    "exercise": "Sports",
    "edutainment": "Educational",
    "education": "Educational",
    "roguelike": "Roguelike",
}

DEV_PUB = {
    "namco bandai games": "Bandai Namco Entertainment",
    "bandai namco games": "Bandai Namco Entertainment",
    "electronic arts": "Electronic Arts",
    "ea": "Electronic Arts",
    "ea sports": "Electronic Arts",
    "warner bros. interactive": "Warner Bros. Interactive Entertainment",
    "mojang ab": "Mojang",
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