import os
from functools import cached_property
from typing import Union

from feishu.client import BaseClient


class Contact(BaseClient):
    api = {"user_id": "/contact/v3/users/batch_get_id"}
    _instance = None
    _cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @cached_property
    def default_open_id(self) -> str:
        """通过环境变量获取默认的 open_id。如果设置了`FEISHU_OPEN_ID`，则返回该值。否则，使用`FEISHU_PHONE`或`FEISHU_EMAIL`查询。"""

        if open_id := os.getenv("FEISHU_OPEN_ID", ""):
            return open_id
        phone = os.getenv("FEISHU_PHONE", "")
        email = os.getenv("FEISHU_EMAIL", "")

        if not (phone or email):
            raise ValueError(
                "To query open_id when FEISHU_OPEN_ID isn't set, FEISHU_PHONE "
                "or FEISHU_EMAIL must be set with your phone or email."
            )
        users = self.get_open_id(phone, email)
        open_id = users.get(phone) or users.get(email)

        if not open_id:
            raise ValueError(f"User not found with phone {phone} or email {email}")
        return open_id

    def get_open_id(
        self,
        phones: Union[str, list[str]] = "",
        emails: Union[str, list[str]] = "",
        cache: bool = True,
    ) -> dict[str, str]:
        """根据给定的手机号或电话号码或电子邮件地址获取用户的 open ID。

        Args:
            phones (str | list[str]): 单个手机号或手机号列表。默认为 ""。
            emails (str | list[str]): 单个电子邮件地址或电子邮件地址列表。默认为 ""。
            cache (bool): 是否缓存查询结果。默认为 True。
        Returns:
            dict[str, str]: 将每个提供的手机号或电子邮件地址到其对应的OpenID的映射。
        Exceptions:
            AssertionError: 如果未提供电话号码或电子邮件地址。
        """

        assert phones or emails, "User phone or user email must be set to query open_id"

        if isinstance(phones, str):
            phones = [phones]
        if isinstance(emails, str):
            emails = [emails]

        body = {"emails": [e for e in emails if e], "mobiles": [p for p in phones if p]}

        if cache and all(contact in self._cache for contact in body["emails"] + body["mobiles"]):
            return {contact: self._cache[contact] for contact in body["emails"] + body["mobiles"]}

        resp = self.post(
            self.api["user_id"],
            params={"user_id_type": "open_id"},
            json=body,
        )
        users = {
            user.get("email") or user.get("mobile"): user["user_id"]
            for user in resp["data"]["user_list"]
            if "user_id" in user
        }
        if cache:
            self._cache.update(users)
        return users
