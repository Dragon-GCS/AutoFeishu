from datetime import datetime
from typing import Any, Literal, Optional

from typing_extensions import Self

from feishu.client import AuthClient
from feishu.models import GroupInfo, Message


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
        """获取当前app或用户可见群组
        https://open.feishu.cn/document/server-docs/group/chat/search

        Args:
            query (str): 群组名称关键词。
            num (int): 获取群组数量，默认获取全部群组
        Returns:
            groups (list[Group]): 群组列表。
        """
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
        """将当前app或用户加入群组
        https://open.feishu.cn/document/server-docs/group/chat-member/me_join
        """
        self.patch(self.api["join"])

    def invite(
        self,
        user_ids: list[str] = [],
        member_id_type: Literal["app_id", "open_id", "user_id", "union_id"] = "open_id",
        succeed_type: Literal[0, 1, 2] = 0,
    ) -> dict:
        """以当前身份邀请指定用户加入群组
        https://open.feishu.cn/document/server-docs/group/chat-member/create

        Args:
            user_ids (list[str]): 用户id列表
            member_id_type (Literal["app_id", "open_id", "user_id", "union_id"]): 用户id类型
            succeed_type (Literal[0, 1, 2]): 成功类型
                0：不存在/不可见的 ID 会拉群失败，并返回错误响应。存在已离职 ID 时，会将其他可用 ID 拉入群聊，返回拉群成功的响应。
                1：将参数中可用的 ID 全部拉入群聊，返回拉群成功的响应，并展示剩余不可用的 ID 及原因。
                2：参数中只要存在任一不可用的 ID ，就会拉群失败，返回错误响应，并展示出不可用的 ID。
        Returns:
            response (dict): 响应数据

        """
        return self.post(
            self.api["members"],
            params={"member_id_type": member_id_type, "succeed_type": succeed_type},
            json={"id_list": user_ids},
        )["data"]

    def remove(
        self,
        user_ids: list[str] = [],
        member_id_type: Literal["app_id", "open_id", "user_id", "union_id"] = "open_id",
    ):
        """以当前身份将指定用户移除群组
        https://open.feishu.cn/document/server-docs/group/chat-member/delete
        """
        self.delete(
            self.api["members"],
            params={"member_id_type": member_id_type},
            json={"id_list": user_ids},
        )

    def members(
        self, member_id_type: Literal["app_id", "open_id", "user_id", "union_id"] = "open_id"
    ) -> dict[str, str]:
        """
        获取群成员列表
        https://open.feishu.cn/document/server-docs/group/chat-member/get

        Args:
            member_id_type (Literal["app_id", "open_id", "user_id", "union_id"]): 用户ID类型，默认open_id
        Return:
            members (dict): member_id -> member_name
        """
        params = {
            "member_id_type": member_id_type,
            "page_size": 100,
        }
        data = self.get(self.api["members"], params=params)["data"]
        members = data["items"]
        while data["has_more"]:
            params["page_token"] = data["page_token"]
            data = self.get(self.api["message"], params=params)["data"]
            members.extend(data["items"])
        return {member["member_id"]: member["name"] for member in members}

    def history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        ascending: bool = True,
        thread_id: str = "",
        num: int = 0,
    ) -> list[Message]:
        """获取群聊历史记录
        https://open.feishu.cn/document/server-docs/im-v1/message/list

        Args:
            start_time (Optional[datetime]): 开始时间.
            end_time (Optional[datetime]): 结束时间.
            ascending (bool): 是否按时间升序排列.
            thread_id (str): 话题ID.
            num (int): 获取消息数量，默认全部
        Returns:
            messages (list[Message]): 消息列表
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
