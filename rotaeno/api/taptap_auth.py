import requests
import json
import io
import tempfile
from uuid import uuid4
from time import time
from hashlib import md5
from time import sleep
from qrcode import make

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TapTapLogin:
    def __init__(
        self,
        server: str,
        device_id=None
    ):
        app_key = ["FT9iFE4DBdWG5je8bP7ieBcC", "0zRcDIygHhqGH3FAinANy0zC"]
        app_id = ["OLNEwJ5x64vEP7QNw2yt8heM-gzGzoHsz", "wsNh5k0vbzxei1fsF0KC6dCG-MdYXbMMI"]
        client_id = ["FTGgtd8jIDSwEbUyEf", "D36LuUfKQMlgPeYWv9"]
        cloud_server_address = ["https://rotaeno.leancloud.indie.xd.com", "https://leanapi.rotaeno.com"]
        code_url = ["https://accounts.tapapis.cn/oauth2/v1/device/code", "https://accounts.tapapis.com/oauth2/v1/device/code"]
        token_url = ["https://accounts.tapapis.cn/oauth2/v1/token", "https://accounts.tapapis.com/oauth2/v1/token"]
        profile_url = ["https://open.tapapis.cn/account/profile/v1", "https://open.tapapis.com/account/profile/v1"]
        profile_host = ["open.tapapis.cn", "open.tapapis.com"]
        union_token_url = ["https://xdsdk-cn-prod-gateway.xd.cn/api/login/v1/union", "https://xdsdk-os-prod-gateway.xd.com/api/login/v1/union"]
        app_version_id = ["2076001", "2023001"]
        tap_sdk_version = ["2.1", "2.1"]
        
        self.DeviceID = device_id
        if server == "cn":
            self.AppKey = app_key[0]
            self.AppID = app_id[0]
            self.ClientId = client_id[0]
            self.CloudServerAddress = cloud_server_address[0]
            self.TapTapCodeUrl = code_url[0]
            self.TapTapTokenUrl = token_url[0]
            self.TapTapProfileUrl = profile_url[0]
            self.TapTapProfileHost = profile_host[0]
            self.TapTapPUnionTokenUrl = union_token_url[0]
            self.AppIDVersionID = app_version_id[0]
            self.TapSDKVersion = tap_sdk_version[0]
        elif server == "global":
            self.AppKey = app_key[1]
            self.AppID = app_id[1]
            self.ClientId = client_id[1]
            self.CloudServerAddress = cloud_server_address[1]
            self.TapTapCodeUrl = code_url[1]
            self.TapTapTokenUrl = token_url[1]
            self.TapTapProfileUrl = profile_url[1]
            self.TapTapProfileHost = profile_host[1]
            self.TapTapPUnionTokenUrl = union_token_url[1]
            self.AppIDVersionID = app_version_id[1]
            self.TapSDKVersion = tap_sdk_version[1]

    def md5hash(self, text: str):
        return md5(text.encode()).hexdigest()

    def sign_headers(self, headers: dict, add_app_key=False):
        ts = int(time() * 1000)
        raw = f"{ts}{self.AppKey}" if add_app_key else str(ts)
        headers["X-LC-Sign"] = f"{self.md5hash(raw)},{ts}"

    def request(self, url, method="POST", headers=None, data=None, add_app_key=False, needError=False):
        headers = headers or {}
        self.sign_headers(headers, add_app_key)
        try:
            if method == "POST":
                if headers.get("Content-Type") == "application/json":
                    data = json.dumps(data)
                response = requests.post(url, headers=headers, data=data, verify=False)
            else:
                response = requests.get(url, headers=headers, verify=False)
                response.raise_for_status()
        except requests.exceptions.SSLError:
            if needError: raise requests.exceptions.SSLError
            sleep(0.1)
            return self.request(url, method=method, headers=headers, data=data, add_app_key=add_app_key)
        return response.json()

    def get_qrcode(self, needImage=False):
        device_id = self.DeviceID
        if self.DeviceID is None:
            device_id = uuid4().hex
        payload = {
            "client_id": self.ClientId,
            "response_type": "device_code",
            "scope": "public_profile",
            "version": self.TapSDKVersion,
            "platform": "unity",
            "info": {"device_id": device_id}
        }
        data = self.request(self.TapTapCodeUrl, data=payload)
        with tempfile.NamedTemporaryFile(mode='w+t', delete=False, suffix=".png") as tmp:
            if needImage is not None:
                make(data["data"]["qrcode_url"]).save(tmp.name, format="PNG")
            return {**data["data"], "device_id": device_id, "image": tmp.name}

    def check_login(self, qrcode_data):
        payload = {
            "grant_type": "device_token",
            "client_id": self.ClientId,
            "secret_type": "hmac-sha-1",
            "code": qrcode_data["device_code"],
            "version": "1.0",
            "platform": "unity",
            "info": json.dumps({"device_id": qrcode_data["device_id"]})
        }
        try:
            return self.request(self.TapTapTokenUrl, data=payload)
        except Exception as e:
            return {"error": str(e)}

    def get_union_token(self, login_data, device_id):
        params = {
            "pt": "Android",
            "sdkVer": "6.21.1",
            "did": device_id,
            "sdkLang": "zh_CN",
            "appId": self.AppIDVersionID
        }
        
        payload = {
            "code": "",
            "grantType": "",
            "origDid": "",
            "scope": "compliance,public_profile",
            "subType": "",
            "token": login_data["kid"],
            "type": "5",
            "secret": login_data["mac_key"]
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(self.TapTapPUnionTokenUrl, params=params, data=json.dumps(payload), headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    def get_objectid_and_sessiontoken(self, qrcode_data=None, show_qrcode=True):
        if qrcode_data is None:
            qrcode_data = self.get_qrcode()
        
        if show_qrcode:
            make(qrcode_data["qrcode_url"]).show()

        _wait_time = 0
        wait_time = qrcode_data["interval"]
        while True:
            time1 = time()
            login_info = self.check_login(qrcode_data)
            if login_info.get("data") is not None:
                if login_info["data"].get("kid") is not None:
                    break
            sleep(wait_time)
            _wait_time += time() - time1
            if _wait_time > 60:
                raise TimeoutError("二维码已过期")
        
        union_response = self.get_union_token(login_info["data"], qrcode_data["device_id"])
        access_token = f"{union_response['data']['kid']} {union_response['data']['macKey']}"
        
        payload = {
            "authData": {
                "xdg": {
                    "access_token": access_token,
                    "uid": "should_be_replaced_after_validation",
                    "device_id": qrcode_data["device_id"]
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-LC-Id": self.AppID,
            "X-LC-Key": self.AppKey
        }
        
        response = requests.post(
            f"{self.CloudServerAddress}/1.1/users",
            headers=headers,
            data=json.dumps(payload),
            verify=False,
            timeout=10
        )
        
        userdata = response.json()
        userdata["sessionToken"]
        userdata["objectId"]
        return {"sessionToken": userdata["sessionToken"], "objectID": userdata["objectId"]}
