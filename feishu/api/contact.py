from typing import Literal, Union

from feishu.client import AuthClient, Cache
from feishu.config import config
from feishu.models.user import User


class Contact(AuthClient):
    api = {
        "batch_user_id": "/contact/v3/users/batch_get_id",
        "user_info": "/contact/v3/users/{user_id}",
        "batch_user_info": "/contact/v3/users/batch",
    }
    # 缓存不同app的联系人
    _cache: Cache[dict[str, str]] = Cache(dict)

    def __init__(self, app_id: str = "", app_secret: str = ""):
        super().__init__(app_id, app_secret)

    @property
    def default_open_id(self) -> str:
        """通过环境变量获取默认的 open_id。如果设置了`FEISHU_OPEN_ID`，则返回该值。否则，使用`FEISHU_PHONE`或`FEISHU_EMAIL`查询。"""

        if config.open_id and (self.app_id, self.app_secret) == (config.app_id, config.app_secret):
            return config.open_id

        if not config.phone and not config.email:
            raise ValueError(
                "To query open_id when FEISHU_OPEN_ID isn't set, FEISHU_PHONE "
                "or FEISHU_EMAIL must be set with your phone or email."
            )
        users = self.get_open_id(config.phone, config.email)
        open_id = users.get(config.phone) or users.get(config.email)

        if not open_id:
            raise ValueError(f"User not found with phone {config.phone} or email {config.email}")
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
            self.api["batch_user_id"],
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

    def get_user_info(
        self,
        user_id: str,
        user_id_type: Literal["open_id", "union_id", "user_id"] = "open_id",
        department_id_type: Literal["department_id", "open_department_id"] = "open_department_id",
    ) -> User:
        """获取用户信息
        https://open.feishu.cn/document/server-docs/contact-v3/user/get

        Args:
            user_id (str): 用户ID
            user_id_type (Literal["open_id", "union_id", "user_id"]): 用户ID类型，默认"open_id"。
            department_id_type (Literal["department_id", "open_department_id"]):
                部门ID类型，默认"open_department_id"。
        Returns:
            user (User): 用户信息
        """
        data = self.get(
            self.api["user_info"].format(user_id=user_id),
            params={"user_id_type": user_id_type, "department_id_type": department_id_type},
        )["data"]
        return User.model_validate(data["user"])

    def batch_user_info(
        self,
        user_ids: list[str],
        user_id_type: Literal["open_id", "union_id", "user_id"] = "open_id",
        department_id_type: Literal["department_id", "open_department_id"] = "open_department_id",
    ) -> list[User]:
        """批量获取用户信息
        https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/contact-v3/user/batch

        Args:
            user_ids (list[str]): 用户ID列表
            user_id_type (Literal["open_id", "union_id", "user_id"]): 用户ID类型，默认"open_id"。
            department_id_type (Literal["department_id", "open_department_id"]):
                部门ID类型，默认"open_department_id"。
        Returns:
            users (list[User]): 用户信息列表
        """
        data = self.get(
            self.api["batch_user_info"],
            params={
                "user_ids": user_ids,
                "user_id_type": user_id_type,
                "department_id_type": department_id_type,
            },
        )["data"]
        return [User.model_validate(user) for user in data["items"]]
