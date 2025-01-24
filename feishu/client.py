import atexit
from datetime import datetime, timedelta
from typing import Any, Callable, ClassVar, Generic, Literal, Optional, TypeVar

import httpx

from feishu.config import config
from feishu.errors import ApiError


class BaseClient:
    """BaseClient for FeiShu API, handle each request."""

    _client = httpx.Client(timeout=config.http_timeout)  # Shared client for all instances

    atexit.register(_client.close)

    def _request(self, method: str, api: str, **kwargs) -> dict:
        url = config.base_url + api
        res = self._client.request(method, url, **kwargs)
        data = res.json()
        if code := data["code"]:
            raise ApiError(api, code, data.get("msg") or data["error"])
        return data

    def get(self, api: str, **kwargs) -> dict:
        return self._request("GET", api, **kwargs)

    def post(self, api: str, **kwargs) -> dict:
        return self._request("POST", api, **kwargs)

    def put(self, api: str, **kwargs) -> dict:
        return self._request("PUT", api, **kwargs)

    def delete(self, api: str, **kwargs) -> dict:
        return self._request("DELETE", api, **kwargs)

    def patch(self, api: str, **kwargs) -> dict:
        return self._request("PATCH", api, **kwargs)

    def head(self, api: str, **kwargs) -> dict:
        return self._request("HEAD", api, **kwargs)

    def options(self, api: str, **kwargs) -> dict:
        return self._request("OPTIONS", api, **kwargs)


T = TypeVar("T")


class Cache(Generic[T]):
    def __init__(self, default_factory: Callable[[], T] = dict):
        self._cache: dict[tuple[str, str], T] = {}
        self._default_factory = default_factory

    def __set__(self, instance: "AuthClient", value: T):
        app_id = instance.app_id
        app_secret = instance.app_secret
        assert app_id and app_secret, "Please set FEISHU_APP_ID and FEISHU_APP_SECRET"
        self._cache[(app_id, app_secret)] = value

    def __get__(self, instance: "AuthClient", owner: type["AuthClient"]):
        app_id = instance.app_id
        app_secret = instance.app_secret
        assert app_id and app_secret, "Please set FEISHU_APP_ID and FEISHU_APP_SECRET"
        key = (app_id, app_secret)
        return self._cache.setdefault(key, self._default_factory())


class Token(BaseClient):
    """Base class for token management"""

    auth_api: ClassVar[str]
    # Store tokens for different apps
    _tokens: ClassVar[dict[tuple[str, str], tuple[str, datetime]]]

    def _auth(self, body: dict) -> dict:
        return self.post(self.auth_api, json=body)

    def __set__(self, instance: Optional["AuthClient"], value: Any):
        if not isinstance(value, Token):
            raise AttributeError(f"{self.__class__.__name__} is read-only")
        if instance is not None:
            raise AttributeError("Only support assign new token on class level")

    def __get__(self, instance: "AuthClient", owner: type["AuthClient"]) -> str:
        app_id = instance.app_id
        app_secret = instance.app_secret
        assert app_id and app_secret, "Please set FEISHU_APP_ID and FEISHU_APP_SECRET"
        key = (app_id, app_secret)
        token, expire_at = self._tokens.get(key, (None, None))
        if not (token and expire_at and expire_at > datetime.now()):
            self.refresh_token(app_id, app_secret)
        return self._tokens[key][0]

    def _update_token(self, app_id: str, app_secret: str, token: str, expires_in: int) -> None:
        """Update token and expire time"""
        self._tokens[(app_id, app_secret)] = (
            token,
            datetime.now() + timedelta(seconds=expires_in),
        )

    def refresh_token(self, app_id: str, app_secret: str) -> None:
        """Refresh token, should be implemented by subclass"""
        raise NotImplementedError


class TenantAccessToken(Token):
    """Tenant access token with auto refresh

    Get tenant access token:
    https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
    """

    auth_api = "/auth/v3/tenant_access_token/internal"
    _tokens = {}

    def refresh_token(self, app_id: str, app_secret: str) -> None:
        auth_data = self._auth({"app_id": app_id, "app_secret": app_secret})
        self._update_token(
            app_id, app_secret, auth_data["tenant_access_token"], auth_data["expire"]
        )


class UserAccessToken(Token):
    """
    Get user authorization code:
    https://open.feishu.cn/document/common-capabilities/sso/api/obtain-oauth-code

    Get user access token:
    https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/authentication-management/access-token/get-user-access-token
    """

    auth_api = "/authen/v2/oauth/token"
    _tokens = {}

    @classmethod
    def auth_url(
        cls,
        redirect_uri: str,
        scope: str = "",
        state: str = "",
        code_challenge: str = "",
        code_challenge_method: Literal["S256", "plain"] = "plain",
    ):
        """
        https://open.feishu.cn/document/common-capabilities/sso/api/obtain-oauth-code
        """
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

    def refresh_token(self, app_id: str, app_secret: str) -> None:
        """
        https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/authentication-management/access-token/get-user-access-token
        """
        # Execute only on first refresh or when token expired(raise exception if token exists)
        if self._tokens.get((app_id, app_secret)):
            raise Exception("UserAccessToken is expired")

        body = {
            "grant_type": "authorization_code",
            "client_id": app_id,
            "client_secret": app_secret,
            "code": self.auth_code,
            "redirect_uri": self.redirect_uri,
        }
        if self.scope:
            body["scope"] = self.scope
        if self.code_verify:
            body["code_verifier"] = self.code_verify

        auth_data = self._auth(body=body)
        self._update_token(app_id, app_secret, auth_data["access_token"], auth_data["expires_in"])


class AuthClient(BaseClient):
    """Client with automatic token management."""

    token = TenantAccessToken()
    api: dict[str, str]
    default_client: ClassVar["BaseClient"]  # default client with default app_id and app_secret

    def __init__(self, app_id: str = "", app_secret: str = ""):
        self.app_id = app_id or config.app_id
        self.app_secret = app_secret or config.app_secret

    def _request(self, method: str, api: str, **kwargs) -> dict:
        kwargs.setdefault("headers", {})["Authorization"] = f"Bearer {self.token}"
        return super()._request(method, api, **kwargs)


AuthClient.default_client = AuthClient()
