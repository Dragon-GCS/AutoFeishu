from typing import Literal

from pydantic import BaseModel, Field


class UserAvatar(BaseModel):
    avatar_72: str
    avatar_240: str
    avatar_640: str
    avatar_origin: str


class User(BaseModel):
    description: str
    en_name: str
    mobile_visible: bool
    name: str
    nickname: str
    open_id: str
    union_id: str

    user_id: str = ""
    email: str = ""
    mobile: str = ""
    gender: Literal[0, 1, 2, 4] = 0
    avatar: UserAvatar
    status: dict = Field(default_factory=dict)
    department_ids: list[str] = Field(default_factory=list)
    leader_user_id: str = ""
    city: str = ""
    country: str = ""
    work_station: str = ""
    join_time: int = 0
    is_tenant_manager: bool = False
    employee_no: str = ""
    employee_type: Literal[None, 1, 2, 3, 4, 5] = None
    orders: list[dict] = Field(default_factory=list)
    custom_attrs: list[dict] = Field(default_factory=list)
    enterprise_email: str = ""
    job_title: str = ""
    geo: str = ""
    job_level_id: str = ""
    job_family_id: str = ""
    assign_info: list[dict] = Field(default_factory=list)
    department_path: list[dict] = Field(default_factory=list)
    dotted_line_leader_user_ids: list[str] = Field(default_factory=list)
