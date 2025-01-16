import json
from datetime import datetime, timedelta
from typing import Any

import httpx

from feishu.config import config


class TenantToken:
    """Tenant access token with auto refresh"""

    def __init__(self) -> None:
        self.token = ""
        self.expire_at = datetime.now()

    def __get__(self, instance: "BaseClient", _owner: type["BaseClient"]) -> str:
        if self.token and self.expire_at > datetime.now():
            return self.token

        assert config.app_id and config.app_secret, "Please set APP_ID and APP_SECRET"
        response = instance._client.post(
            url=instance.base_url + "/auth/v3/tenant_access_token/internal",
            json={"app_id": config.app_id, "app_secret": config.app_secret},
        )
        response.raise_for_status()
        data = response.json()

        if data["code"]:
            raise Exception(f"Failed to get tenant token({data['code']}): {data['msg']}")

        self.token = data["tenant_access_token"]
        self.expire_at = timedelta(seconds=data["expire"]) + datetime.now()
        return self.token

    def __set__(self, instance: "BaseClient", value: Any):
        raise AttributeError("TenantToken is read-only")


class BaseClient:
    base_url = config.base_url
    token = TenantToken()  # Shared token for all instances
    _client = httpx.Client()  # Shared client for all instances
    api: dict[str, str]

    def _request(self, method: str, api: str, **kwargs) -> dict:
        url = f"{self.base_url}{api}"
        kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {self.token}"
        res = self._client.request(method, url, **kwargs)

        try:
            data = res.json()
        except json.JSONDecodeError:
            raise Exception(f"Api({api}) request error({res.status_code}): {res.text}")

        if data["code"]:
            raise Exception(
                f"Api({api}) response code error，please check the error code({data['code']}): {data['msg']}"
            )
        return data

    def get(self, api: str, **kwargs) -> dict:
        return self._request("GET", api, **kwargs)

    def post(self, api: str, **kwargs) -> dict:
        return self._request("POST", api, **kwargs)

    def put(self, api: str, **kwargs) -> dict:
        return self._request("PUT", api, **kwargs)
