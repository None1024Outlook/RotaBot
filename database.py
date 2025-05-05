import config
import sqlite3
from thefuzz import fuzz
import random
from typing import List
import json

class songAlias:
    def __init__(self, database_path):
        self.database_path = database_path
        self.initDatabase()
    
    def initDatabase(self):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS song_alias (
                    alias TEXT PRIMARY KEY,
                    id TEXT
                )
            """)
            conn.commit()
    
    def getSongID(self, songAlias, fit=80):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT alias, id FROM song_alias")
            records = cursor.fetchall()
            
            res = {}
            if records:
                aliases = [record[0] for record in records]
                match = []
                for alias in aliases:
                    match.append((alias, fuzz.token_set_ratio(songAlias, alias)))
                if match:
                    for i in match:
                        if i[1] >= fit:
                            cursor.execute("SELECT id FROM song_alias WHERE alias = ?", (i[0],))
                            result = cursor.fetchone()
                            if result is None: continue
                            if i[0].lower() == songAlias.lower(): return {i[0]: result[0]} # 如果别名小写一样则直接返回
                            res[i[0]] = result[0]
                    if len(res) > 1:
                        for i in res:
                            if i.lower() == songAlias.lower(): return {i: res[i]}
            return res
    
    def addSongAlias(self, songAlias, songID):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO song_alias (alias, id) VALUES (?, ?)", (songAlias, songID))
                conn.commit()
        except sqlite3.IntegrityError:
            print(f"Error: The alias '{songAlias}' already exists.")
    
    def delSongAlias(self, songAlias):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM song_alias WHERE alias = ?", (songAlias,))
            conn.commit()

class songData:
    def __init__(self, database_path):
        self.database_path = database_path
        self.initDatabase()
    
    def initDatabase(self) -> None:
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS songs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS song_levels (
                    id TEXT PRIMARY KEY,
                    I FLOAT NOT NULL,
                    II FLOAT NOT NULL,
                    III FLOAT NOT NULL,
                    IV FLOAT NOT NULL,
                    IV_Alpha FLOAT NOT NULL
                )
            """)
            conn.commit()
    
    def addSong(self, songID, songTitle, songArtist, songLevels) -> None:
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO songs (id, title, artist) VALUES (?, ?, ?)", 
                             (songID, songTitle, songArtist))
                cursor.execute("""
                    INSERT INTO song_levels (id, I, II, III, IV, IV_Alpha) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (songID, songLevels["I"], songLevels["II"], songLevels["III"], 
                     songLevels["IV"], songLevels.get("IV_Alpha", 0)))
                conn.commit()
        except sqlite3.IntegrityError:
            print(f"Error: The song '{songID}' already exists.")
    
    def delSong(self, songID) -> None:
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM songs WHERE id = ?", (songID,))
            conn.commit()
    
    def getSong(self, songID)-> dict:
        res = {}
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title, artist FROM songs WHERE id = ?", (songID,))
            result = cursor.fetchone()
            if result is None: return res
            res["id"] = songID
            res["title"] = result[0]
            res["artist"] = result[1]
            
            cursor.execute("SELECT I, II, III, IV, IV_Alpha FROM song_levels WHERE id = ?", (songID,))
            result = cursor.fetchone()
            if result is None: return res
            
            res["levels"] = [
                result[0],  # I
                result[1],  # II
                result[2],  # III
                result[3],  # IV
                result[4]   # IV_Alpha
            ]
            res["__levels"] = {
                "I": result[0],
                "II": result[1],
                "III": result[2],
                "IV": result[3],
                "IV_Alpha": result[4]
            }
        return res
    
    def getSongsRatingRealRange(self, songRatingReal1, songRatingReal2) -> List[dict]:
        res = []
        level_map = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "IV_Alpha"}
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, I, II, III, IV, IV_Alpha
                FROM song_levels
                WHERE (I BETWEEN ? AND ?)
                OR (II BETWEEN ? AND ?)
                OR (III BETWEEN ? AND ?)
                OR (IV BETWEEN ? AND ?)
                OR (IV_Alpha BETWEEN ? AND ?)
            """, (songRatingReal1, songRatingReal2, songRatingReal1, songRatingReal2, 
                 songRatingReal1, songRatingReal2, songRatingReal1, songRatingReal2,
                 songRatingReal1, songRatingReal2))
            
            for row in cursor.fetchall():
                tmp = {}
                for level in level_map:
                    if row[level] >= songRatingReal1 and row[level] <= songRatingReal2 and row[level] != 0:
                        tmp["id"] = row[0]
                        try:
                            tmp["levels"].append(level_map[level])
                        except:
                            tmp["levels"] = [level_map[level]]
                if tmp != {}: 
                    res.append(tmp)
        return res

class songChallenge:
    def __init__(self, database_path):
        self.database_path = database_path
    
    def addSongChallenge(self, challenge):
        with open(self.database_path, "r", encoding="utf-8") as f:
            challenges = json.load(f)
        challenges.append(challenge)
        with open(self.database_path, "w", encoding="utf-8") as f:
            json.dump(challenges, f, indent=4, ensure_ascii=False)
    
    def delSongChallenge(self, challenge):
        with open(self.database_path, "r", encoding="utf-8") as f:
            challenges = json.load(f)
        with open(self.database_path, "w", encoding="utf-8") as f:
            json.dump([c for c in challenges if c != challenge], f, indent=4, ensure_ascii=False)
    
    def getSongChallenge(self):
        with open(self.database_path, "r", encoding="utf-8") as f:
            challenges = json.load(f)
        return challenges
    
    def randomSongChallenge(self, count=1):
        challenges = self.getSongChallenge()
        return random.sample(challenges, min(count, len(challenges)))

songAlias = songAlias(config.SONG_ALIAS_DB_FILE)
songData = songData(config.SONG_DATA_DB_FILE)
songChallenge = songChallenge(config.SONG_CHALLENGE_DB_FILE)
