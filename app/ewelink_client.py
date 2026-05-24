import time
import hmac
import hashlib
import base64
import requests
import os
from dotenv import load_dotenv

load_dotenv()


class EWeLinkClient:
    def __init__(self):
        self.client_id = os.getenv("EWELINK_CLIENT_ID")
        self.client_secret = os.getenv("EWELINK_CLIENT_SECRET")
        self.region = os.getenv("EWELINK_REGION", "eu")

        if not self.client_id or not self.client_secret:
            raise RuntimeError("Missing eWeLink credentials")

        self.base_url = f"https://{self.region}-apia.coolkit.cc"
        self.access_token = None
        self.token_expiry = 0

    # -------------------------------
    # Authentication
    # -------------------------------
    def _sign(self, payload: str) -> str:
        digest = hmac.new(
            self.client_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(digest).decode()

    def authenticate(self):
        url = f"{self.base_url}/v2/user/login"

        ts = int(time.time() * 1000)
        payload = f"{self.client_id}{ts}"
        sign = self._sign(payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": sign,
            "X-CK-Appid": self.client_id,
            "X-CK-Nonce": str(ts)
        }

        body = {
            "appid": self.client_id,
            "ts": ts
        }

        response = requests.post(url, json=body, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("error") != 0:
            raise RuntimeError(f"Authentication failed: {data}")

        self.access_token = data["data"]["at"]
        self.token_expiry = time.time() + data["data"]["expires_in"] - 60

    def _ensure_token(self):
        if not self.access_token or time.time() >= self.token_expiry:
            self.authenticate()

    # -------------------------------
    # API helpers
    # -------------------------------
    def _headers(self):
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    # -------------------------------
    # Devices
    # -------------------------------
    def get_devices(self):
        url = f"{self.base_url}/v2/device/thing"
        response = requests.get(url, headers=self._headers(), timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get("error") != 0:
            raise RuntimeError(f"Device fetch failed: {data}")

        return data["data"]["thingList"]

    def get_device_status(self, device_id: str):
        url = f"{self.base_url}/v2/device/thing/status"
        params = {"id": device_id}

        response = requests.get(url, headers=self._headers(), params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get("error") != 0:
            raise RuntimeError(f"Status fetch failed: {data}")

        return data["data"]
