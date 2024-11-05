import json
from datetime import datetime
from typing import Literal, Optional, Union

from feishu.client import BaseClient
from feishu.models.approval import ApprovalDefine, ApprovalDetail


class Approval(BaseClient):
    api = {
        "instance": "/approval/v4/instances",
        "approval": "/approval/v4/approvals",
        "approve_task": "/approval/v4/tasks/approve",
        "reject_task": "/approval/v4/tasks/reject",
    }

    def __init__(self, approval_code: str, instance_code: str):
        self.approval_code = approval_code
        self.instance_code = instance_code

    @classmethod
    def create(
        cls,
        approval_code: str,
        open_id: str,
        form: list[dict],
        department_id: Optional[str] = None,
        approvers: dict[str, list[str]] = {},
        cc_list: dict[str, list[str]] = {},
        uuid: Optional[str] = None,
        allow_resubmit: Optional[bool] = None,
        allow_submit_again: Optional[bool] = None,
        cancel_bot_notification: Literal[None, "1", "2", "4"] = None,
        forbid_revoke: Optional[bool] = None,
        title: Optional[str] = None,
        title_display_method: int = 0,
        auto_approvals: list[dict[Literal["CUSTOM", "NON_CUSTOM"], str]] = [],
    ) -> "Approval":
        """创建审批实例 https://open.feishu.cn/document/server-docs/approval-v4/instance/create

        Args:
            approval_code (str): 审批定义的唯一标识
            open_id (str): 发起审批用户的`open_id`。
            department_id (str): 发起审批用户部门id，如果用户只属于一个部门，可以不填。如果属于多个部门，默认会选择部门列表第一个部门。
            approvers (dict[str, str]):
                如果有发起人自选节点，则需要填写对应节点的审批人。key为节点id，value为审批人open_id列表。
            cc_list (dict[str, str]):
                如果有发起人自选节点，则可填写对应节点的抄送人。key为节点id，value为抄送人open_id列表。
            uuid (str):  审批实例 uuid，用于幂等操作, 每个租户下面的唯一key，同一个 uuid 只能用于创建一个审批实例，
                如果冲突，返回错误码 60012 ，格式建议为 XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX，不区分大小写。
            allow_resubmit (bool | None): 可配置“提交”按钮，该操作适用于审批人退回场景，提单人在同一实例提交单据
            allow_submit_again (bool | None): 可配置是否可以再次提交，适用于周期性提单场景，按照当前表单内容再次发起一个新实例
            cancel_bot_notification (str | None): 取消指定的 bot 推送通知。可选值:
                1：取消通过推送。
                2：取消拒绝推送。
                4：取消实例取消推送。
                支持同时取消多个 bot 推送通知。位运算，即如需取消 1 和 2 两种通知，则需要传入加和值 3。
            forbid_revoke (bool | None): 是否禁止撤回。
            title (str | None): 审批展示名称，如果填写了该字段，则审批列表中的审批名称使用该字段，如果不填该字段，则审批名称使用审批定义的名称。
            title_display_method (int): 详情页title展示模式，默认为0。可选值:
                0: 如果都有title，展示approval 和instance的title，竖线分割。
                1: 如果都有title，只展示instance的title
            auto_approvals (list[dict[str, str]]): 自动通过节点。Key为节点类型(CUSTOM|NON_CUSTOM)，value为节点id。
        """
        body: dict[str, Union[str, int, list]] = {
            "approval_code": approval_code,
            "open_id": open_id,
            "form": json.dumps(form),
            "title_display_method": title_display_method,
        }
        if department_id is not None:
            body["department_id"] = department_id
        if approvers:
            body["node_approver_open_id_list"] = [
                {"key": k, "value": v} for k, v in approvers.items()
            ]
        if cc_list:
            body["node_cc_open_id_list"] = [{"key": k, "value": v} for k, v in cc_list.items()]
        if uuid is not None:
            body["uuid"] = uuid
        if allow_resubmit is not None:
            body["allow_resubmit"] = allow_resubmit
        if allow_submit_again is not None:
            body["allow_submit_again"] = allow_submit_again
        if cancel_bot_notification is not None:
            body["cancel_bot_notification"] = cancel_bot_notification
        if forbid_revoke is not None:
            body["forbid_revoke"] = forbid_revoke
        if title is not None:
            body["title"] = title
        if auto_approvals:
            body["node_auto_approval_list"] = [
                {"key": k, "value": v}
                for auto_approval in auto_approvals
                for k, v in auto_approval.items()
            ]

        res = BaseClient().post(cls.api["instance"], json=body)
        instance_code = res["data"]["instance_code"]
        return cls(approval_code, instance_code)

    @classmethod
    def list_instances(
        cls,
        approval_code: str,
        start_time: Union[int, datetime],
        end_time: Union[int, datetime],
        num: int = 0,
        page_size: int = 100,
    ):
        """批量查询审批实例 https://open.feishu.cn/document/server-docs/approval-v4/instance/list

        Args:
            approval_code (str): 审批定义的唯一标识
            start_time (Union[int, datetime]): 开始时间, 整数毫秒或者 datetime 对象
            end_time (Union[int, datetime]): 结束时间, 整数毫秒或者 datetime 对象
            num (int, optional): 查询数量。 默认为 0, 表示查询全部.
            page_size (int, optional): 分页大小。默认为 100，最大100。
        """
        if isinstance(start_time, datetime):
            start_time = int(start_time.timestamp() * 1000)
        if isinstance(end_time, datetime):
            end_time = int(end_time.timestamp() * 1000)
        params = {
            "page_size": min(page_size, 100),
            "approval_code": approval_code,
            "start_time": start_time,
            "end_time": end_time,
        }
        _client = BaseClient()
        data = _client.get(cls.api["instance"], params=params)["data"]
        instance = [cls(approval_code, code) for code in data["instance_code_list"]]

        while (not num or len(instance) < num) and data["has_more"]:
            params["page_token"] = data["page_token"]
            data = _client.get(cls.api["instance"], params=params)["data"]
            instance.extend([cls(approval_code, code) for code in data["instance_code_list"]])

        if num:
            instance = instance[:num]
        return instance

    @classmethod
    def get_define(cls, approval_code: str) -> ApprovalDefine:
        """获取审批定义详情 https://open.feishu.cn/document/server-docs/approval-v4/approval/get"""
        res = BaseClient().get(f"{cls.api['approval']}/{approval_code}")
        return ApprovalDefine(**res["data"])

    def detail(self, open_id: str = ""):
        """获取审批实例详情 https://open.feishu.cn/document/server-docs/approval-v4/instance/get

        Args:
            open_id (str): 可选，发起审批的用户id
        """
        res = self.get(
            f"{self.api['instance']}/{self.instance_code}",
            params={"user_id": open_id, "user_id_type": "open_id"},
        )
        return ApprovalDetail(**res["data"])

    def approve(self, open_id: str, task_id: str, comment: str = "", form: Optional[dict] = None):
        """同意审批任务 https://open.feishu.cn/document/server-docs/approval-v4/task/approve

        Args:
            open_id (str): 审批人的`open_id`
            task_id (str): 任务id
            comment (str, optional): 审批意见, 默认为空
            form (dict, optional): 表单数据
        """
        self.post(
            self.api["approve_task"],
            json={
                "approval_code": self.approval_code,
                "instance_code": self.instance_code,
                "user_id": open_id,
                "task_id": task_id,
                "comment": comment,
                "form": form,
            },
        )

    def reject(self, open_id: str, task_id: str, comment: str = "", form: Optional[dict] = None):
        """拒绝审批任务 https://open.feishu.cn/document/server-docs/approval-v4/task/reject

        Args:
            open_id (str): 审批人的`open_id`
            task_id (str): 任务id
            comment (str, optional): 审批意见, 默认为空
            form (dict, optional): 表单数据
        """
        self.post(
            self.api["reject_task"],
            json={
                "approval_code": self.approval_code,
                "instance_code": self.instance_code,
                "user_id": open_id,
                "task_id": task_id,
                "comment": comment,
                "form": form,
            },
        )
