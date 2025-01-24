from pydantic import BaseModel
from typing import Literal, Optional


class GroupInfo(BaseModel):
    name: str = ""
    description: str = ""
    owner_id: str = ""  # 群主为机器人时无返回值
    owner_id_type: str = ""  # 群主为机器人时无返回值
    tenant_key: str = ""
    external: Optional[bool] = None
    chat_status: Optional[Literal["normal", "dissolved", "dissolved_save"]] = None
