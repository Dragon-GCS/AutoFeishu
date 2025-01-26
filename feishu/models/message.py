import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class MessageSender(BaseModel):
    id: str
    id_type: Literal["open_id", "app_id", ""]
    sender_type: Literal["user", "system", "app", "anonymous", "unknown", ""]
    tenant_key: str = ""


class MessageMention(BaseModel):
    key: str
    id: str
    id_type: Literal["open_id"]
    name: str
    tenant_key: str = ""


class MessageBody(BaseModel):
    content: dict

    @field_validator("content", mode="before")
    @classmethod
    def parse_body(cls, v: str, info: ValidationInfo) -> dict:
        if isinstance(v, dict):
            return v
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return {info.data["msg_type"]: v}


class Message(BaseModel):
    """
    Model for feishu messages
    https://open.feishu.cn/document/server-docs/im-v1/message/list
    """

    message_id: str
    root_id: str = ""
    parent_id: str = ""
    thread_id: str = ""
    msg_type: str
    create_time: datetime
    update_time: datetime
    deleted: bool
    chat_id: str
    sender: MessageSender
    body: MessageBody
    mentions: list[MessageMention] = Field(default_factory=list)
    upper_message_id: str = ""
