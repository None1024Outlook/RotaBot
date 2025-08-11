import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROTAENO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.insert(0, ROTAENO_ROOT)

from database import song_data as song_data_database
from database import player_data as player_data_database
from .taptap import UserAPI

import msgpack
from typing import Tuple, Any
from datetime import datetime
from datetime import timedelta

def calculate_level(xp) -> float:
    xp_ups = [100, 120, 140, 160, 180, 200, 220, 240, 300, 210]
    xp_ups += [220, 230, 240, 250, 260, 270, 280, 290, 300, 250]
    xp_ups += [260, 270, 280, 290, 300, 310, 320, 330, 340, 350]
    xp_ups += [360, 370, 380, 390, 400, 410, 420, 430, 440, 450]
    xp_ups += [460, 470, 480, 490, 500]
    level = 1
    for xp_up in xp_ups:
        xp -= xp_up
        level += 1
        if xp < 1: break
    if xp > 0:
        level += xp / 500
    return level

def calculate_song_rating(song_score, rating_real, song_is_cleared) -> Tuple[float, float]:
    next_rating_point = 0.001

    if song_score >= 1010000:
        song_rating = rating_real + 3.7
        next_point_score = 1010000
    elif 1008000 <= song_score < 1010000:
        song_rating = rating_real + 3.4 + (song_score - 1008000) / 10000
        next_point_score = (song_rating + next_rating_point - rating_real - 3.4) * 10000 + 1008000
    elif 1004000 <= song_score < 1008000:
        song_rating = rating_real + 2.4 + (song_score - 1004000) / 4000
        next_point_score = (song_rating + next_rating_point - rating_real - 2.4) * 4000 + 1004000
    elif 1000000 <= song_score < 1004000:
        song_rating = rating_real + 2.0 + (song_score - 1000000) / 10000
        next_point_score = (song_rating + next_rating_point - rating_real - 2.0) * 10000 + 1000000
    elif 980000 <= song_score < 1000000:
        song_rating = rating_real + 1.0 + (song_score - 980000) / 20000
        next_point_score = (song_rating + next_rating_point - rating_real - 1.0) * 20000 + 980000
    elif 950000 <= song_score < 980000:
        song_rating = rating_real + 0.0 + (song_score - 950000) / 30000
        next_point_score = (song_rating + next_rating_point - rating_real - 0.0) * 30000 + 950000
    elif 900000 <= song_score < 950000:
        song_rating = rating_real - 1.0 + (song_score - 900000) / 50000
        next_point_score = (song_rating + next_rating_point - rating_real + 1.0) * 50000 + 900000
    elif 500000 <= song_score < 900000:
        song_rating = rating_real - 5.0 + (song_score - 500000) / 100000
        next_point_score = (song_rating + next_rating_point - rating_real + 5.0) * 100000 + 500000
    else:
        song_rating = 0
        next_point_score = 500000
        
    if song_rating < 0: song_rating = 0
        
    if not song_is_cleared:
        song_rating = min(6, song_rating)
        
    next_point_score -= song_score
    if next_point_score + song_score > 1010000: next_point_score = 1010000 - song_score
    
    return song_rating, next_point_score


def save_data_to_file(data: dict, save_path: str) -> None:
    if not save_path.endswith(".msgpack"):
        save_path += ".msgpack"
    with open(save_path, "wb") as f:
        msgpack.dump(data, f)

def find_keys_in_any_dict(any_dict: dict, keys: list, default: Any = None) -> Any:
    for key in keys:
        if key in any_dict:
            return any_dict[key]
    if default is not None: return default
    raise KeyError(f"{keys} not in {list(any_dict.keys())}")

class TapTapAPI(UserAPI):
    def get_cloud_save(self, get_object_id: bool = False, raw_data: dict = None, save_path: str = None, add_to_database: bool = False) -> dict:
        def format_duration_en(td: timedelta):
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            parts = []
            if hours >= 0:
                parts.append(f"{hours} hour{'s' if hours not in [0, 1] else ''}")
            if minutes >= 0:
                parts.append(f"{minutes} minute{'s' if minutes not in [0, 1] else ''}")
            if seconds >= 0 or not parts:
                parts.append(f"{seconds} second{'s' if seconds not in [0, 1] else ''}")
            return " ".join(parts)
        
        if raw_data:
            cloud_save = raw_data["results"][0]["cloudSave"]
        else:
            cloud_save = super().get_cloud_save(get_object_id=get_object_id)["results"][0]["cloudSave"]
        if save_path is not None:
            save_data_to_file(cloud_save, save_path)
        
        user_data = cloud_save["data"]["data"]
        favorite_song_ids = user_data.get("FavoriteSong", {"songIds": []})["songIds"]
        song_records = user_data["songs"]["songs"]
        display_name = user_data["profile"]["DisplayName"]
        avatar = user_data["badges"]["EquippedBadgeId"] if "boss" not in user_data["badges"]["EquippedBadgeId"] else user_data["badges"]["EquippedBadgeId"] + "-4"
        background = user_data["collectable-background"]["EquippedBackgroundId"].replace("background_", "")
        character = user_data["collectable-character"]["EquippedCharacterId"].replace("character_", "")
        total_play_time = [float(time) for time in cloud_save["TotalPlayTime"].replace("-", "").split(":")]
        total_play_time_delta = timedelta(hours=total_play_time[0], minutes=total_play_time[1], seconds=total_play_time[2])
        total_play_time = format_duration_en(total_play_time_delta)
        play_records = user_data["playRecords"]
        exp = user_data["PlayerLevel"]["AccumXp"]
        level = calculate_level(exp)
        try: 
            collectible_avatars = {i.replace("badge_", ""): user_data["missions"]["missions"]["data"][i]["completed"] for i in user_data["missions"]["missions"]["data"] if "badge_" in i}
            collectible_characters = {i.replace("character_", ""): user_data["missions"]["missions"]["data"][i]["completed"] for i in user_data["missions"]["missions"]["data"] if "character_" in i}
            collectible_backgrounds = {i.replace("background_", ""): user_data["collectables"]["Saves"][i]["Amount"] != 0 for i in user_data["collectables"]["Saves"] if "background_" in i and "background_cg" not in i}
            collectible_cgs = {i.replace("background_cg-", ""): user_data["collectables"]["Saves"][i]["Amount"] != 0 for i in user_data["collectables"]["Saves"] if "background_" in i and "background_cg" in i}
        except KeyError:
            collectible_avatars = {}
            collectible_characters = {}
            collectible_backgrounds = {}
            collectible_cgs = {}
        collectibles = {
            "avatar": collectible_avatars,
            "character": collectible_characters,
            "background": collectible_backgrounds,
            "cg": collectible_cgs
        }
        
        song_ratings = {}
        for song_id, song_levels in song_records.items():
            song_info = song_data_database.song_data.get_song(song_id=song_id)
            song_levels = song_levels.get("levels", {})
            if song_info == {}:
                print(f"Song ID `{song_id}` not found in song data")
                continue
            for song_level, song_data in song_levels.items():
                if song_level not in song_info["levels"]:
                    print(f"Song level `{song_level}` not found in song data for song ID `{song_id}`")
                    continue
                song_diff = song_info["levels"][song_level]["num"]
                song_score = song_data["Score"]
                song_is_cleared = song_data["IsCleared"]
                song_rating, next_point_score = calculate_song_rating(song_score, song_diff, song_is_cleared)
                # print(song_rating, next_point_score)
                
                if song_ratings.get(song_id) is None: song_ratings[song_id] = {}
                song_ratings[song_id][song_level] = {
                    "title": song_info["title"],
                    "diff": song_diff,
                    "rating": song_rating,
                    "ratingMix": song_rating,
                    "score": song_score,
                    "status": song_data["Flag"].upper(),
                    "isCleared": song_is_cleared,
                    "nextPointScore": next_point_score,
                    "isFavorite": song_id in favorite_song_ids
                }
        
        for songID, levels in song_ratings.items():
            if "IV_Alpha" in levels and "IV" in levels:
                if levels["IV_Alpha"]["ratingMix"] >= levels["IV"]["ratingMix"]:
                    levels["IV"]["ratingMix"] = 0
                else:
                    levels["IV_Alpha"]["ratingMix"] = 0
                song_ratings[songID] = levels

        all_ratings = []
        for levels in song_ratings.values():
            for data in levels.values():
                all_ratings.append(data["ratingMix"])
        all_ratings.sort(reverse=True)
        
        rating = (sum(all_ratings[:10]) * 0.6 / 10) + (sum(all_ratings[10:20]) * 0.2 / 10) + (sum(all_ratings[20:40]) * 0.2 / 20)
        
        player_info = {
            "displayName": display_name,
            "rating": rating,
            "exp": exp,
            "level": level,
            "avatar": avatar,
            "background": background,
            "character": character,
            "totalPlayTime": total_play_time,
            "favoriteSongIDs": favorite_song_ids,
            "collectibles": collectibles,
            "playRecords": play_records
        }

        song_datas = []
        for song_id, song_levels in song_ratings.items():
            for song_level, song_data in song_levels.items():
                song_data["id"] = song_id
                song_data["level"] = song_level
                song_datas.append(song_data)
        
        if add_to_database:
            object_id = self.user_profile.get("objectID", "")
            if object_id == "":
                print("Why the objectID is empty, this data will not be added to the player data")
            else:
                timestamp = datetime.now()
                
                player = player_data_database.Player(
                    object_id=object_id,
                    rating=player_info["rating"],
                    exp=player_info["exp"],
                    level=player_info["level"],
                    all_perfect_plus=player_info["playRecords"]["TotalApp"],
                    all_perfect=player_info["playRecords"]["TotalAp"],
                    full_combo=player_info["playRecords"]["TotalFc"],
                    miss=player_info["playRecords"]["Miss"],
                    good=player_info["playRecords"]["Good"],
                    perfect=player_info["playRecords"]["Perfect"],
                    perfect_plus=player_info["playRecords"]["PerfectPlus"],
                    play_record=player_info["playRecords"]
                )
                player_data_database.player_data.add_player(player=player, timestamp=timestamp)
        
        return {
            "playerInfo": player_info,
            "songDatas": song_datas
        }
    
    def get_user_data(self, raw_data: dict = None, save_path: str = None) -> dict:
        if raw_data:
            user_data = raw_data
        else:
            user_data = super().get_user_data()
        if save_path is not None:
            save_data_to_file(user_data, save_path)
        
        i = 0
        ii = 0
        iii = 0
        iv = 0
        iv_alpha = 0
        playStats = {"i": {}, "ii": {}, "iii": {}, "iv": {}, "iv_alpha": {}, "all": {}}
        for x in user_data["privateSocialData"]["user_data"]["SongRecords"]:
            i += find_keys_in_any_dict(user_data["privateSocialData"]["user_data"]["SongRecords"][x]["Levels"], ["I", "I"])["Score"]
            ii += find_keys_in_any_dict(user_data["privateSocialData"]["user_data"]["SongRecords"][x]["Levels"], ["Ii", "II"])["Score"]
            iii += find_keys_in_any_dict(user_data["privateSocialData"]["user_data"]["SongRecords"][x]["Levels"], ["Iii", "III"])["Score"]
            iv += find_keys_in_any_dict(user_data["privateSocialData"]["user_data"]["SongRecords"][x]["Levels"], ["Iv", "IV"])["Score"]
            iv_alpha += find_keys_in_any_dict(user_data["privateSocialData"]["user_data"]["SongRecords"][x]["Levels"], ["IV_Alpha"], default={"Score": 0})["Score"]
        playStats["i"]["scores"] = i
        playStats["ii"]["scores"] = ii
        playStats["iii"]["scores"] = iii
        playStats["iv"]["scores"] = iv
        playStats["iv_alpha"]["scores"] = iv_alpha
        playStats["all"]["scores"] = i + ii + iii + iv + iv_alpha
        
        return {
            "updateAt": user_data["updatedAt"],
            "FriendCap": user_data["privateSocialData"]["FriendCap"],
            "playerAvatar": user_data["badges"]["EquippedBadgeId"] if "boss" not in user_data["badges"]["EquippedBadgeId"] else user_data["badges"]["EquippedBadgeId"] + "-4",
            "playerBackground": user_data["privateSocialData"]["user_data"]["BackgroundId"].replace("background_", ""),
            "playerCharacter": user_data["privateSocialData"]["user_data"]["CharacterId"].replace("character_", ""),
            "ShowRating": user_data["privateSocialData"]["user_data"]["ShowRating"],
            "playerExp": user_data["privateSocialData"]["user_data"]["Exp"],
            "playerLevel": calculate_level(user_data["privateSocialData"]["user_data"]["Exp"]),
            "playerDisplayName": user_data["privateSocialData"]["user_data"]["DisplayName"],
            "playerRating": user_data["privateSocialData"]["user_data"]["Rating"],
            "createdAt": user_data["createdAt"].split("T")[0],
            "emailVerified": user_data["emailVerified"],
            "mobilePhoneVerified": user_data["mobilePhoneVerified"],
            "playerPlayStats": playStats,
            "playerFriendCode": user_data["shortId"].upper(),
            "playerUserID": user_data["authData"]["xdg"]["detail"]["userId"]
        }
    
    def get_follow_data(self, raw_data: dict = None, save_path: str = None) -> dict:
        def processingFollowData(user_data):
            i = 0
            ii = 0
            iii = 0
            iv = 0
            iv_alpha = 0
                
            scoresKey = "scores" if "scores" in user_data else "songScores"
            for x in user_data[scoresKey]:
                    i += find_keys_in_any_dict(user_data[scoresKey][x], ["i", "I"], default=0)
                    ii += find_keys_in_any_dict(user_data[scoresKey][x], ["ii", "II"], default=0)
                    iii += find_keys_in_any_dict(user_data[scoresKey][x], ["iii", "III"], default=0)
                    iv += find_keys_in_any_dict(user_data[scoresKey][x], ["iv", "IV"], default=0)
                    iv_alpha += find_keys_in_any_dict(user_data[scoresKey][x], ["iv_alpha", "IV_Alpha"], default=0)
            user_data["playStats"]["i"] = user_data["playStats"].get("i", {})
            user_data["playStats"]["ii"] = user_data["playStats"].get("ii", {})
            user_data["playStats"]["iii"] = user_data["playStats"].get("iii", {})
            user_data["playStats"]["iv"] = user_data["playStats"].get("iv", {})
            user_data["playStats"]["iv_alpha"] = user_data["playStats"].get("iv_alpha", {})
            user_data["playStats"]["i"]["scores"] = i
            user_data["playStats"]["ii"]["scores"] = ii
            user_data["playStats"]["iii"]["scores"] = iii
            user_data["playStats"]["iv"]["scores"] = iv
            user_data["playStats"]["iv_alpha"]["scores"] = iv_alpha
            user_data["playStats"]["all"]["scores"] = i + ii + iii + iv + iv_alpha
            
            score_datas = user_data[scoresKey]
            for song_id, song_data in score_datas.items():
                score_datas[song_id] = {
                    "I": find_keys_in_any_dict(song_data, ["i", "I"], default=0),
                    "II": find_keys_in_any_dict(song_data, ["ii", "II"], default=0),
                    "III": find_keys_in_any_dict(song_data, ["iii", "III"], default=0),
                    "IV": find_keys_in_any_dict(song_data, ["iv", "IV"], default=0),
                    "IV_Alpha": find_keys_in_any_dict(song_data, ["iv_alpha", "IV_Alpha"], default=0)
                }
                    
            return {
                "shortID": user_data["shortId"].upper(),
                "playerRating": user_data["rating"],
                "playerDisplayName": user_data["displayName"],
                "playerPlayStats": user_data["playStats"],
                "isFriend": user_data["isTwoWayFriend"],
                "playerBackground": user_data["backgroundId"],
                "playerCharacter": user_data["characterId"],
                "playerAvatar": user_data["badgeId"],
                "playerExp": user_data["exp"],
                "playerLevel": calculate_level(user_data["exp"]),
                "songScores": score_datas
            }
        
        if raw_data:
            follow_data = raw_data["result"]["socialDatas"]
        else:
            follow_data = super().get_follow_data()["result"]["socialDatas"]
        if save_path is not None:
            save_data_to_file(follow_data, save_path)

        return [processingFollowData(user_data) for user_data in follow_data]

    def follow_user(self) -> dict:
        raw_data = {
            "result": {
                "socialDatas": [super().follow_user()]
            }
        }
        return self.get_follow_data(raw_data=raw_data)
    
    def unfollow_user(self) -> dict:
        return super().unfollow_user()
