from . import api
from . import utils
from . import database

import os
import time
import json
import string

class SafeTemplate(string.Template):
    delimiter = "$$"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(CURRENT_DIR, "assets")
SAVES_DIR = os.path.join(CURRENT_DIR, "saves")
CLOUD_SAVES_DIR = os.path.join(SAVES_DIR, "cloud_saves")
USER_DATAS_DIR = os.path.join(SAVES_DIR, "user_datas")
FOLLOW_DATAS_DIR = os.path.join(SAVES_DIR, "follow_datas")

LOCALES_DIR = os.path.join(ASSETS_DIR, "i18n")
LOCALES = {}
for locale_file in os.listdir(LOCALES_DIR):
    with open(os.path.join(LOCALES_DIR, locale_file), "r", encoding="utf-8") as f:
        LOCALES[locale_file.split(".")[0]] = json.load(f)

def t(locale="zh-CN"):
    return LOCALES.get(str(locale), LOCALES.get("zh-CN", {}))

def get_best40(user_profile: dict, just_data: bool = False, just_html: bool = False) -> str | dict:
    if user_profile["serverCode"] == "cn": region = api.taptap.ServerRegion.CN
    elif user_profile["serverCode"] == "global": region = api.taptap.ServerRegion.GLOBAL
    user_data = api.taptap_processor.TapTapAPI(region=region, user_profile=user_profile).get_cloud_save(save_path=os.path.join(CLOUD_SAVES_DIR, f"{user_profile.get('objectID', 'EMPTY')}-{time.time()}.msgpack"), add_to_database=True)
    user_data["songDatas"] = sorted(user_data["songDatas"], key=lambda x: x["ratingMix"], reverse=True)[:40]
    
    if just_data: return user_data["songDatas"]
    
    with open(f"{ASSETS_DIR}/html/b40.html", "r", encoding="utf-8") as f:
        html = SafeTemplate(f.read()).safe_substitute({
            "data": json.dumps(user_data, indent=4, ensure_ascii=False),
            **t(user_profile.get("locale", "zh-CN"))
        })
    
    if just_html: return html
    
    return utils.render_html_to_jpg(window_size=(1600, 1350), html=html)

def get_song(user_profile: dict, song_id: str, just_data: bool = False, just_html: bool = False) -> str | dict:
    if user_profile["serverCode"] == "cn": region = api.taptap.ServerRegion.CN
    elif user_profile["serverCode"] == "global": region = api.taptap.ServerRegion.GLOBAL
    user_data = api.taptap_processor.TapTapAPI(region=region, user_profile=user_profile).get_cloud_save(save_path=os.path.join(CLOUD_SAVES_DIR, f"{user_profile.get('objectID', 'EMPTY')}-{time.time()}.msgpack"), add_to_database=True)
    song_artist = database.song_data.song_data.get_song(song_id=song_id)["artist"]
    song_data = {}
    for song_level_data in user_data["songDatas"]:
        if song_level_data["id"] == song_id:
            song_level_data.update({"artist": song_artist})
            song_data[song_level_data["level"]] = song_level_data
    user_data["songData"] = song_data
    del user_data["songDatas"]
    
    if just_data: return user_data["songData"]
    
    with open(f"{ASSETS_DIR}/html/song.html", "r", encoding="utf-8") as f:
        html = SafeTemplate(f.read()).safe_substitute({
            "data": json.dumps(user_data, indent=4, ensure_ascii=False),
            **t(user_profile.get("locale", "zh-CN"))
        })
    
    if just_html: return html
    
    return utils.render_html_to_jpg(window_size=(1360, 900), html=html)

def get_song_status(user_profile: dict, song_status: str, just_data: bool = False, just_html: bool = False) -> str | dict:
    if user_profile["serverCode"] == "cn": region = api.taptap.ServerRegion.CN
    elif user_profile["serverCode"] == "global": region = api.taptap.ServerRegion.GLOBAL
    user_data = api.taptap_processor.TapTapAPI(region=region, user_profile=user_profile).get_cloud_save(save_path=os.path.join(CLOUD_SAVES_DIR, f"{user_profile.get('objectID', 'EMPTY')}-{time.time()}.msgpack"), add_to_database=True)
    
    song_datas = []
    for song_data in user_data["songDatas"]:
        if song_status == "CLEAR" and song_data["isCleared"]: song_datas.append(song_data)
        elif song_status == "NOTCLEAR" and not song_data["isCleared"]: song_datas.append(song_data)
        elif song_status == "FAVORITE" and song_data["isFavorite"]: song_datas.append(song_data)
        elif song_status == "NOTFAVORITE" and not song_data["isFavorite"]: song_datas.append(song_data)
        elif song_status == song_data["status"]: song_datas.append(song_data)
    user_data["songDatas"] = song_datas
    user_data["songStatus"] = song_status
    
    if just_data: return user_data["songDatas"]
    
    with open(f"{ASSETS_DIR}/html/song_status.html", "r", encoding="utf-8") as f:
        html = SafeTemplate(f.read()).safe_substitute({
            "data": json.dumps(user_data, indent=4, ensure_ascii=False),
            **t(user_profile.get("locale", "zh-CN"))
        })
    
    if just_html: return html
    
    return utils.render_html_to_jpg(window_size=(1600, 1310), html=html)

def get_song_rtr(user_profile: dict, song_level_num_range: tuple = (12.5, 1145), song_sort_type: str = "rating", just_data: bool = False, just_html: bool = False) -> str | dict:
    if user_profile["serverCode"] == "cn": region = api.taptap.ServerRegion.CN
    elif user_profile["serverCode"] == "global": region = api.taptap.ServerRegion.GLOBAL
    user_data = api.taptap_processor.TapTapAPI(region=region, user_profile=user_profile).get_cloud_save(save_path=os.path.join(CLOUD_SAVES_DIR, f"{user_profile.get('objectID', 'EMPTY')}-{time.time()}.msgpack"), add_to_database=True)
    
    song_datas = []
    for song_data in user_data["songDatas"]:
        if song_level_num_range[0] <= song_data["diff"] <= song_level_num_range[1]:
            song_datas.append(song_data)
    
    if song_sort_type == "rating":
        song_datas = sorted(song_datas, key=lambda x: x["ratingMix"], reverse=True)
    elif song_sort_type == "score":
        song_datas = sorted(song_datas, key=lambda x: x["score"], reverse=True)
    elif song_sort_type == "level":
        song_datas = sorted(song_datas, key=lambda x: x["diff"], reverse=True)
    
    user_data["songDatas"] = song_datas
    user_data["songLevelNumRange"] = song_level_num_range
    user_data["songSortType"] = song_sort_type.capitalize()
    
    if just_data: return user_data["songDatas"]
    
    with open(f"{ASSETS_DIR}/html/song_rtr.html", "r", encoding="utf-8") as f:
        html = SafeTemplate(f.read()).safe_substitute({
            "data": json.dumps(user_data, indent=4, ensure_ascii=False),
            **t(user_profile.get("locale", "zh-CN"))
        })
    
    if just_html: return html
    
    return utils.render_html_to_jpg(window_size=(1600, 1310), html=html)
