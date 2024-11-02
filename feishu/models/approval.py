import json
from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, BeforeValidator

JsonConvert = BeforeValidator(lambda s: json.loads(s) if isinstance(s, str) else s)


class ApprovalViewer(BaseModel):
    # 租户内可见, 指定部门, 指定用户, 指定角色, 指定用户组, 任何人都不可见
    type: Literal["TENANT", "DEPARTMENT", "USER", "ROLE", "USER_GROUP", "NONE"]
    id: str
    user_id: str


class ApprovalRange(BaseModel):
    approver_range_type: Literal[0, 1, 2]
    approver_range_ids: list[str]


class ApprovalNode(BaseModel):
    name: str
    need_approver: bool
    node_id: str
    custom_node_id: str
    # AND: 会签节点, OR: 或签节点, SEQUENCE: 顺序节点, CC_NODE: 抄送节点
    node_type: Literal["AND", "OR", "SEQUENCE", "CC_NODE"]
    approver_chosen_multi: bool  # 是否支持多选
    approver_chosen_range: list[ApprovalRange] = []
    require_signature: bool  # 是否需要签字


class ApprovalForm(BaseModel):
    custom_id: str = ""
    default_value_type: str = ""
    display_condition: Annotated[Optional[dict], JsonConvert] = None
    enable_default_value: bool
    id: str
    name: str
    required: bool
    type: str
    widget_default_value: str


class ApprovalDefine(BaseModel):
    """Ref: https://open.feishu.cn/document/server-docs/approval-v4/approval/get?appId=cli_a32100b4bf38500d"""

    approval_name: str
    status: Literal["ACTIVE", "INACTIVE", "DELETED", "UNKNOWN"]
    form: Annotated[list[ApprovalForm], JsonConvert]
    node_list: list[dict]
    viewers: list[ApprovalViewer] = []
    approval_admin_ids: list[str] = []


class ApprovalTask(BaseModel):
    end_time: datetime
    id: str
    node_id: str
    node_name: str
    open_id: str
    start_time: datetime
    # 任务状态: 待审批, 已审批, 已拒绝, 已转交, 已完成
    status: Literal["PENDING", "APPROVED", "REJECTED", "TRANSFERRED", "DONE"]
    # 审批方式: 会签，或签，自动通过，自动拒绝，按顺序
    type: Literal["AND", "OR", "AUTO_PASS", "AUTO_REJECT", "SEQUENTIAL"]


class ApprovalAttachment(BaseModel):
    url: str
    file_size: int
    title: str
    type: str


class ApprovalTimeline(BaseModel):
    create_time: datetime
    user_id: str = ""
    open_id: str = ""
    node_key: str
    # 动态其他信息，json格式，目前包括 user_id_list, user_id，open_id_list，open_id
    ext: Annotated[dict, JsonConvert]
    # 动态类型，不同ext内的user_id_list含义不一样
    # 审批开始，通过，拒绝，自动通过，自动拒绝，去重，转交，前加签，并加签，后加签，减签，指定回退，全部回退，撤回，删除，抄送
    type: Literal[
        "START",
        "PASS",
        "REJECT",
        "AUTO_PASS",
        "AUTO_REJECT",
        "REMOVE_REPEAT",
        "TRANSFER",
        "ADD_APPROVER_BEFORE",
        "ADD_APPROVER",
        "ADD_APPROVER_AFTER",
        "DELETE_APPROVER",
        "ROLLBACK_SELECTED",
        "ROLLBACK",
        "CANCEL",
        "DELETE",
        "CC",
    ]
    user_id_list: Annotated[list[str], JsonConvert] = []
    cc_user_list: Annotated[list[str], JsonConvert] = []
    files: list[ApprovalAttachment] = []


class ApprovalDetailCCUser(BaseModel):
    user_id: str = ""
    cc_id: str
    open_id: str = ""


class ApprovalDetail(BaseModel):
    """Ref: https://open.feishu.cn/document/server-docs/approval-v4/instance/get"""

    approval_code: str
    approval_name: str
    department_id: str
    end_time: datetime
    form: Annotated[list[dict], JsonConvert]
    instance_code: str
    reverted: bool
    serial_number: str  # 审批编号
    start_time: datetime
    # 审批状态: 审批中, 通过, 拒绝, 撤回, 删除
    status: Literal["PENDING", "APPROVED", "REJECTED", "CANCELED", "DELETED"]
    cc_user_list: list[ApprovalDetailCCUser] = []
    task_list: list[ApprovalTask] = []
    timeline: list[ApprovalTimeline] = []
    open_id: str = ""
    user_id: str = ""
    uuid: str
