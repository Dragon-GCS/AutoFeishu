from datetime import datetime
from unittest import TestCase

from feishu import Approval
from feishu.contact import Contact
from feishu.models.approval import ApprovalDefine

# 测试用审批流
APPROVAL_CODE = "17BC676C-1A4F-4409-A592-22C1F196E29A"


class TestApproval(TestCase):
    api = {"instance": "/approval/v4/instances"}

    def test_get_approval_define(self):
        approval_define = Approval.get_define(APPROVAL_CODE)
        expected_define = ApprovalDefine.model_validate(
            {
                "approval_name": "Test",
                "form": [
                    {
                        "default_value_type": "",
                        "display_condition": None,
                        "enable_default_value": False,
                        "id": "widget17304709164440001",
                        "name": "Text",
                        "printable": True,
                        "required": True,
                        "type": "input",
                        "visible": True,
                        "widget_default_value": "",
                    },
                    {
                        "default_value_type": "",
                        "display_condition": None,
                        "enable_default_value": False,
                        "id": "widget17304709185330001",
                        "name": "MultiText",
                        "printable": True,
                        "required": True,
                        "type": "textarea",
                        "visible": True,
                        "widget_default_value": "",
                    },
                ],
                "node_list": [
                    {
                        "approver_chosen_multi": True,
                        "approver_chosen_range": [
                            {"approver_range_ids": [], "approver_range_type": 0}
                        ],
                        "name": "审批",
                        "need_approver": True,
                        "node_id": "270179659ee85e4d188ebd5f16088a77",
                        "node_type": "AND",
                        "require_signature": False,
                    },
                    {
                        "approver_chosen_multi": False,
                        "name": "结束",
                        "need_approver": False,
                        "node_id": "b1a326c06d88bf042f73d70f50197905",
                        "node_type": "AND",
                        "require_signature": False,
                    },
                    {
                        "approver_chosen_multi": True,
                        "name": "提交",
                        "need_approver": False,
                        "node_id": "b078ffd28db767c502ac367053f6e0ac",
                        "node_type": "AND",
                        "require_signature": False,
                    },
                ],
                "status": "ACTIVE",
                "viewers": [{"id": "", "type": "TENANT", "user_id": ""}],
            }
        )
        for key in expected_define.model_fields:
            with self.subTest(key=key):
                self.assertEqual(getattr(approval_define, key), getattr(expected_define, key))

    def test_approval(self):
        open_id = Contact().default_open_id
        # 提交任务
        task_param = {
            "approval_code": APPROVAL_CODE,
            "open_id": open_id,
            "form": [
                {"id": "widget17304709164440001", "type": "input", "value": "11111"},
                {
                    "id": "widget17304709185330001",
                    "required": True,
                    "type": "textarea",
                    "value": "11111",
                },
            ],
            "approvers": {"270179659ee85e4d188ebd5f16088a77": [open_id]},
        }
        approval = Approval.create(**task_param)
        self.assertEqual(approval.approval_code, APPROVAL_CODE)

        # 任务详情
        detail = approval.detail(open_id)
        self.assertEqual(detail.approval_code, APPROVAL_CODE)
        self.assertEqual(detail.instance_code, approval.instance_code)
        self.assertEqual(detail.status, "PENDING")
        # 审批任务
        with self.subTest(test="审批通过"):
            task_id = detail.task_list[0].id
            approval.approve(open_id, task_id=task_id, comment="同意")
            detail = approval.detail(open_id)
            self.assertEqual(detail.status, "APPROVED")
        with self.subTest(test="审批拒绝"):
            approval = Approval.create(**task_param)
            detail = approval.detail(open_id)
            task_id = detail.task_list[0].id
            approval.reject(open_id, task_id=task_id, comment="拒绝")
            detail = approval.detail(open_id)
            self.assertEqual(detail.status, "REJECTED")

    def test_approval_instances(self):
        approvals = Approval.list_instances(
            APPROVAL_CODE, start_time=datetime(2024, 11, 1), end_time=datetime(2024, 11, 30)
        )
        self.assertTrue(all(ins.approval_code == APPROVAL_CODE for ins in approvals))
