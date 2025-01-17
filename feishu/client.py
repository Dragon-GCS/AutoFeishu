import atexit
import json
from datetime import datetime, timedelta
from typing import Any, Literal, Optional

import httpx

from feishu.config import config


class BaseClient:
    """BaseClient for FeiShu API, handle each request."""

    base_url = config.base_url
    _client = httpx.Client()  # Shared client for all instances

    atexit.register(_client.close)

    @classmethod
    def _request(cls, method: str, api: str, **kwargs) -> dict:
        url = cls.base_url + api
        res = cls._client.request(method, url, **kwargs)

        try:
            data = res.json()
        except json.JSONDecodeError:
            raise Exception(f"Api({api}) request error({res.status_code}): {res.text}")

        if data["code"]:
            raise Exception(
                f"Api({api}) response code error，please check the error code({data['code']}): "
                f"{data.get('msg') or data['error']}"
            )
        return data

    @classmethod
    def get(cls, api: str, **kwargs) -> dict:
        return cls._request("GET", api, **kwargs)

    @classmethod
    def post(cls, api: str, **kwargs) -> dict:
        return cls._request("POST", api, **kwargs)

    @classmethod
    def put(cls, api: str, **kwargs) -> dict:
        return cls._request("PUT", api, **kwargs)

    @classmethod
    def delete(cls, api: str, **kwargs) -> dict:
        return cls._request("DELETE", api, **kwargs)

    @classmethod
    def patch(cls, api: str, **kwargs) -> dict:
        return cls._request("PATCH", api, **kwargs)

    @classmethod
    def head(cls, api: str, **kwargs) -> dict:
        return cls._request("HEAD", api, **kwargs)

    @classmethod
    def options(cls, api: str, **kwargs) -> dict:
        return cls._request("OPTIONS", api, **kwargs)


class Token(BaseClient):
    """Base class for token management"""

    auth_api: str

    def _auth(self, body: dict) -> dict:
        return self.post(self.auth_api, json=body)

    def __set__(self, instance: Optional["AuthClient"], value: Any):
        if not isinstance(value, Token):
            raise AttributeError(f"{self.__class__.__name__} is read-only")
        if instance is not None:
            # attribute name should be "token"
            instance.__dict__["token"] = value


class TenantAccessToken(Token):
    """Tenant access token with auto refresh

    Get tenant access token:
    https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
    """

    auth_api = "/auth/v3/tenant_access_token/internal"

    def __init__(self) -> None:
        self.token = ""
        self.expire_at = datetime.now()

    def __get__(self, instance: "AuthClient", owner: type["AuthClient"]) -> str:
        if self.token and self.expire_at > datetime.now():
            return self.token

        assert config.app_id and config.app_secret, "Please set APP_ID and APP_SECRET"
        auth_data = self._auth({"app_id": config.app_id, "app_secret": config.app_secret})
        self.token = auth_data["tenant_access_token"]
        self.expire_at = timedelta(seconds=auth_data["expire"]) + datetime.now()
        return self.token


class UserAccessToken(Token):
    """
    Get user authorization code:
    https://open.feishu.cn/document/common-capabilities/sso/api/obtain-oauth-code

    Get user access token:
    https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/authentication-management/access-token/get-user-access-token
    """

    auth_api = "/authen/v2/oauth/token"

    @classmethod
    def auth_url(
        cls,
        redirect_uri: str,
        scope: str = "",
        state: str = "",
        code_challenge: str = "",
        code_challenge_method: Literal["S256", "plain"] = "plain",
    ):
        from urllib.parse import urlencode

        params = {
            "app_id": config.app_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
        }
        return f"{config.base_url}/authen/v1/authorize?{urlencode(params)}"

    def __init__(self, auth_code: str, redirect_uri: str, code_verify: str = "", scope: str = ""):
        self.auth_code = auth_code
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.code_verify = code_verify
        self.token = ""
        self.expire_at = None

    def __get__(self, instance: "AuthClient", owner: type["AuthClient"]) -> str:
        if self.expire_at is not None and self.expire_at < datetime.now():
            raise Exception("UserAccessToken is expired")
        if self.token:
            return self.token

        assert config.app_id and config.app_secret, "Please set APP_ID and APP_SECRET"
        body = {
            "grant_type": "authorization_code",
            "client_id": config.app_id,
            "client_secret": config.app_secret,
            "code": self.auth_code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": self.code_verify,
        }
        if self.scope:
            body["scope"] = self.scope
        if self.code_verify:
            body["code_verifier"] = self.code_verify

        auth_data = self._auth(body=body)
        self.token = auth_data["access_token"]
        self.expire_at = timedelta(seconds=auth_data["expires_in"]) + datetime.now()
        return self.token


class AuthClient(BaseClient):
    """Client with automatic token management."""

    token: Token = TenantAccessToken()  # Shared token for all instances
    api: dict[str, str]

    @classmethod
    def _request(cls, method: str, api: str, **kwargs) -> dict:
        kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {cls.token}"
        return super()._request(method, api, **kwargs)
