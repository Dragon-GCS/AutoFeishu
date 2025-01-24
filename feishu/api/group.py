from datetime import datetime
from typing import Any, Literal, Optional

from typing_extensions import Self

from feishu.client import AuthClient
from feishu.models.group import GroupInfo
from feishu.models.message import Message


class Group(AuthClient):
    api = {
        "join": "/im/v1/chats/{chat_id}/members/me_join",
        "members": "/im/v1/chats/{chat_id}/members",
        "chats": "/im/v1/chats",
        "message": "/im/v1/messages",
    }

    def __init__(self, chat_id: str, app_id: str = "", app_secret: str = "", **kwargs):
        super().__init__(app_id, app_secret)
        self.chat_id = chat_id
        self.api = {name: api.format(chat_id=chat_id) for name, api in self.api.items()}
        self.info = GroupInfo(**kwargs)

    @classmethod
    def get_groups(cls, query: str = "", num: int = 0) -> list[Self]:
        api = cls.api["chats"]
        params: dict[str, Any] = {"user_id_type": "open_id"}
        params["page_size"] = min(num, 100) if num > 0 else 100
        if query:
            params["query"] = query
            api += "/search"
        data = cls.default_client.get(api, params=params)["data"]
        groups = [cls(**group) for group in data["items"]]
        while data["has_more"] and (num <= 0 or len(groups) < num):
            data = cls.default_client.get(
                api,
                params=params | {"page_token": data["page_token"]},
            )["data"]
            groups.extend([cls(**group) for group in data["items"]])
        return groups[:num] if num > 0 else groups

    def join(self):
        """
        https://open.feishu.cn/document/server-docs/group/chat-member/me_join
        """
        return self.patch(self.api["join"])

    def invite(
        self,
        user_ids: list[str] = [],
        member_id_type: Literal["app_id", "open_id", "user_id", "union_id"] = "open_id",
        succeed_type: Literal[0, 1, 2] = 0,
    ):
        """
        https://open.feishu.cn/document/server-docs/group/chat-member/create
        """
        return self.post(
            self.api["members"],
            params={"member_id_type": member_id_type, "succeed_type": succeed_type},
            json={"id_list": user_ids},
        )

    def remove(
        self,
        user_ids: list[str] = [],
        member_id_type: Literal["app_id", "open_id", "user_id", "union_id"] = "open_id",
    ):
        """
        https://open.feishu.cn/document/server-docs/group/chat-member/delete
        """
        return self.delete(
            self.api["members"],
            params={"member_id_type": member_id_type},
            json={"id_list": user_ids},
        )

    def history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        ascending: bool = True,
        thread_id: str = "",
        num: int = 0,
    ) -> list[Message]:
        """
        https://open.feishu.cn/document/server-docs/im-v1/message/list
        """
        params = {
            "container_id_type": "thread" if thread_id else "chat",
            "container_id": thread_id or self.chat_id,
            "sort_type": "ByCreateTimeAsc" if ascending else "ByCreateTimeDesc",
            "page_size": min(num, 50) if num > 0 else 50,
        }
        if start_time is not None:
            params["start_time"] = int(start_time.timestamp())
        if end_time is not None:
            params["end_time"] = int(end_time.timestamp())
        data = self.get(self.api["message"], params=params)["data"]
        messages = [Message(**item) for item in data["items"]]
        while data["has_more"] and (num <= 0 or len(messages) < num):
            params["page_token"] = data["page_token"]
            data = self.get(self.api["message"], params=params)["data"]
            messages.extend(Message(**item) for item in data["items"])
        return messages[:num] if num > 0 else messages

    def __repr__(self) -> str:
        return f"<Group chat_id='{self.chat_id}' {self.info}>"
