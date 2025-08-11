import time
import json
import hashlib
import requests
from enum import Enum

class ServerRegion(Enum):
    CN = "cn"
    GLOBAL = "global"

class ServerURL:
    CN = "https://rotaeno.leancloud.indie.xd.com"
    GLOBAL = "https://leanapi.rotaeno.com"

class ServerSecret:
    CN = {
        "id": "OLNEwJ5x64vEP7QNw2yt8heM-gzGzoHsz",
        "key": "FT9iFE4DBdWG5je8bP7ieBcC"
    }
    GLOBAL = {
        "id": "wsNh5k0vbzxei1fsF0KC6dCG-MdYXbMMI",
        "key": "0zRcDIygHhqGH3FAinANy0zC"
    }

class BaseAPI:
    def __init__(self, region: ServerRegion, user_profile: dict, proxies: dict = None) -> None:
        self.region = region
        self.user_profile = user_profile
        self.proxies = proxies

        if region == ServerRegion.CN:
            self.base_url = ServerURL.CN
            self.secret = ServerSecret.CN
        elif region == ServerRegion.GLOBAL:
            self.base_url = ServerURL.GLOBAL
            self.secret = ServerSecret.GLOBAL
        else:
            raise ValueError("Invalid region")

    def _build_headers(self) -> dict:
        timestamp = str(int(time.time()))
        sign_raw = f"{timestamp}{self.secret['key']}".encode("utf-8")
        sign = hashlib.md5(sign_raw).hexdigest()

        return {
            "X-LC-Sign": f"{sign},{timestamp}",
            "X-LC-Session": self.user_profile.get("sessionToken", ""),
            "X-LC-Id": self.secret["id"],
            "Content-Type": "application/json"
        }

    def get(self, endpoint: str, params: dict = None) -> dict:
        return requests.get(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            params=params,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

    def post(self, endpoint: str, data: dict = None) -> dict:
        return requests.post(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            json=data,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

    def put(self, endpoint: str, data: dict = None) -> dict:
        return requests.put(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            json=data,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

class UserAPI(BaseAPI):
    def get_cloud_save(self, get_object_id: bool = False) -> dict:
        if not get_object_id:
            object_id = self.user_profile.get("objectID", "")
        else:
            object_id = self.get_user_data()["objectId"]
        params = {
            "where": json.dumps({
                "user": {
                    "__type": "Pointer",
                    "className": "_User",
                    "objectId": object_id
                }
            })
        }
        return self.get("/1.1/classes/CloudSave", params=params)
    
    def get_user_data(self) -> dict:
        return self.get(f"/1.1/users/me")

    def get_follow_data(self) -> dict:
        return self.get("/1.1/call/GetAllFolloweeSocialData", params={})
    
    def follow_user(self, shortID: str) -> dict:
        return self.post("/1.1/call/FollowPlayer", data={"ShortId": shortID.upper()})
    
    def unfollow_user(self, shortID: str) -> dict:
        return self.post("/1.1/call/UnfollowPlayer", data={"ShortId": shortID.upper()})
