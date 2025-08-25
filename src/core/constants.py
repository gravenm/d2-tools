from streamlit import secrets

# -- API Constants --
API_ROOT_PATH = "https://www.bungie.net/Platform"
AUTH_URL = "https://www.bungie.net/en/OAuth/Authorize"
TOKEN_URL = f"{API_ROOT_PATH}/App/OAuth/token/"
MANIFEST_URL = f"{API_ROOT_PATH}/Destiny2/Manifest/"
MANIFEST_FILE_NAME = "world_sql_content.db"
API_KEY = secrets.get("API_KEY", "7172d986158b459e82a8b6a66f4bd077")
CLIENT_ID = secrets.get("CLIENT_ID", "50537")
HEADERS = {"X-API-Key": API_KEY}

# -- Game Data Constants --
ARMOR_TYPE_HASHES = [45, 46, 47, 48, 49]
STAT_HASH_TO_NAME = {
    2996146975: "Weapons", 392767087: "Health", 1943323491: "Class",
    1735777505: "Grenade", 144602215: "Super", 4244567218: "Melee",
}
ARTIFICE_SOCKET_TYPE_HASH = 1433225414
MASTERWORK_ENERGY_PLUG_CATEGORY_HASH = 2325141259
GENERAL_ARMOR_MOD_SOCKET_CATEGORY_HASH = 590099826
EXOTIC_TIER_TYPE = 6
ARMOR_SLOT_HASHES = {
    45: "Helmet",
    46: "Gauntlets",
    47: "Chest Armor",
    48: "Leg Armor",
    49: "Class Item",
}
# -- Weighting Constants --
DEFAULT_WEIGHTS = {"BST": 1.0, "Artifice": 1.0}
ARCHETYPE_WEIGHTS = {
    "Bulwark": 0.7, "Brawler": 1.6, "Gunner": 1.1, "Specialist": 1.6,
    "Grenadier": 1.8, "Paragon": 1.6,
}
TIER_WEIGHTS = {
    "Tier 1": {"low": 1.0, "high": 1.05}, "Tier 2": {"low": 1.1, "high": 1.15},
    "Tier 3": {"low": 1.2, "high": 1.25}, "Tier 4": {"low": 1.3, "high": 1.35},
    "Tier 5": {"low": 1.5, "high": 1.55},
}
ILLEGAL_COMBO_WEIGHTS = {
    ("Grenade", "Health"): 5.0, ("Health", "Super"): 5.0,
    ("Health", "Weapons"): 5.0, ("Grenade", "Melee"): 10.0,
    ("Melee", "Weapons"): 10.0, ("Class", "Melee"): 10.0,
    ("Class", "Grenade"): 9.3, ("Class", "Super"): 8.2,
    ("Super", "Weapons"): 10.0,
}
ARCHETYPES = {
    "Brawler": {"Primary": "Melee", "Secondary": "Health"},
    "Gunner": {"Primary": "Weapons", "Secondary": "Grenade"},
    "Specialist": {"Primary": "Class", "Secondary": "Weapons"},
    "Grenadier": {"Primary": "Grenade", "Secondary": "Super"},
    "Paragon": {"Primary": "Super", "Secondary": "Melee"},
    "Bulwark": {"Primary": "Health", "Secondary": "Class"}
}
TIERS = {
    "Tier 1": [52, 57], "Tier 2": [58, 63], "Tier 3": [64, 69],
    "Tier 4": [70, 75], "Tier 5": [75, 81],
}