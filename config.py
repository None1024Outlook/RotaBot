import os

DISCORD_BOT_TOKEN = "YOUR DISCORD BOT TOKEN"

VERIFY_USER_DATA_DEFAULT_REQURIED_KEYS = []

DATA_DIR = "./data"

USER_DATA_FILE = os.path.join(DATA_DIR, "users.json")
SONG_ALIAS_DB_FILE = os.path.join(DATA_DIR, "songAlias.db")
SONG_DATA_DB_FILE = os.path.join(DATA_DIR, "songInfo.db")
SONG_CHALLENGE_DB_FILE = os.path.join(DATA_DIR, "songChallenge.json")

ASSETS_DIR = "./assets"

ASSETS_HTML_B40 = os.path.join(ASSETS_DIR, "html", "b40.html")
ASSETS_HTML_B40_CHARACTER = os.path.join(ASSETS_DIR, "html", "b40_character.html")

TEMP_DIR = "./temp"
