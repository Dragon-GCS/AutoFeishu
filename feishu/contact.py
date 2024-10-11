from functools import cache
from typing import Union

from feishu.client import BaseClient

USER_ID_API = "/contact/v3/users/batch_get_id"


@cache
def get_open_id(
    phones: Union[str, list[str]] = "", emails: Union[str, list[str]] = ""
) -> dict[str, str]:
    assert phones or emails, "User phone or user email must be set to query open_id"

    if isinstance(phones, str):
        phones = [phones]
    if isinstance(emails, str):
        emails = [emails]

    body = {"emails": emails, "mobiles": list(filter(bool, phones))}

    resp = BaseClient().post(
        USER_ID_API,
        params={"user_id_type": "open_id"},
        json=body,
    )

    return {
        user.get("email") or user.get("mobile"): user["user_id"]
        for user in resp["data"]["user_list"]
        if "user_id" in user
    }
