import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from feishu.api.group import Group
from feishu.models.group import GroupInfo
from feishu.models.message import Message


class TestGroup(unittest.TestCase):
    def setUp(self):
        self.chat_id = "test_chat_id"
        self.group = Group(chat_id=self.chat_id)

    def test_init(self):
        """Test Group initialization"""
        self.assertEqual(self.group.chat_id, self.chat_id)
        self.assertIsInstance(self.group.info, GroupInfo)

        # Test API endpoints formatting
        expected_api = {
            "join": f"/im/v1/chats/{self.chat_id}/members/me_join",
            "members": f"/im/v1/chats/{self.chat_id}/members",
            "chats": "/im/v1/chats",
            "message": "/im/v1/messages",
        }
        self.assertEqual(self.group.api, expected_api)

    @patch.object(Group.default_client, "get")
    def test_get_groups(self, mock_get: MagicMock):
        """Test get_groups method"""
        # Mock API response
        mock_response = {
            "data": {
                "items": [
                    {"chat_id": "chat1", "name": "Group 1"},
                    {"chat_id": "chat2", "name": "Group 2"},
                ],
                "has_more": False,
                "page_token": "token123",
            }
        }
        mock_get.return_value = mock_response

        # Test without query and num
        groups = Group.get_groups()
        self.assertEqual(len(groups), 2)
        self.assertIsInstance(groups[0], Group)
        mock_get.assert_called_with(
            "/im/v1/chats", params={"user_id_type": "open_id", "page_size": 100}
        )

        # Test with query
        groups = Group.get_groups(query="test")
        mock_get.assert_called_with(
            "/im/v1/chats/search",
            params={"user_id_type": "open_id", "page_size": 100, "query": "test"},
        )

    @patch.object(Group, "patch")
    def test_join(self, mock_patch: MagicMock):
        """Test join method"""
        mock_patch.return_value = {"success": True}
        result = self.group.join()
        mock_patch.assert_called_with(f"/im/v1/chats/{self.chat_id}/members/me_join")
        self.assertEqual(result, {"success": True})

    @patch.object(Group, "post")
    def test_invite(self, mock_post: MagicMock):
        """Test invite method"""
        mock_post.return_value = {"success": True}
        user_ids = ["user1", "user2"]
        result = self.group.invite(user_ids=user_ids)

        mock_post.assert_called_with(
            f"/im/v1/chats/{self.chat_id}/members",
            params={"member_id_type": "open_id", "succeed_type": 0},
            json={"id_list": user_ids},
        )
        self.assertEqual(result, {"success": True})

    @patch.object(Group, "delete")
    def test_remove(self, mock_delete: MagicMock):
        """Test remove method"""
        mock_delete.return_value = {"success": True}
        user_ids = ["user1", "user2"]
        result = self.group.remove(user_ids=user_ids)

        mock_delete.assert_called_with(
            f"/im/v1/chats/{self.chat_id}/members",
            params={"member_id_type": "open_id"},
            json={"id_list": user_ids},
        )
        self.assertEqual(result, {"success": True})

    @patch.object(Group, "get")
    def test_history(self, mock_get: MagicMock):
        """Test history method"""
        mock_response = {
            "data": {
                "has_more": False,
                "items": [
                    {
                        "message_id": "msg1",
                        "root_id": "root1",
                        "parent_id": "parent1",
                        "thread_id": "thread1",
                        "msg_type": "text",
                        "create_time": "1672574400000",
                        "update_time": "1672574400000",
                        "deleted": False,
                        "chat_id": "chat1",
                        "sender": {
                            "id": "sender1",
                            "id_type": "open_id",
                            "sender_type": "user",
                            "tenant_key": "key1",
                        },
                        "body": {"content": '{"text": "Hello World"}'},
                        "mentions": [
                            {
                                "key": "key1",
                                "id": "user1",
                                "id_type": "open_id",
                                "name": "User 1",
                                "tenant_key": "tenant1",
                            }
                        ],
                        "upper_message_id": "upper1",
                    },
                    {
                        "message_id": "msg2",
                        "root_id": "root2",
                        "parent_id": "parent2",
                        "thread_id": "thread2",
                        "msg_type": "text",
                        "create_time": "1672578000000",
                        "update_time": "1672578000000",
                        "deleted": False,
                        "chat_id": "chat2",
                        "sender": {
                            "id": "sender2",
                            "id_type": "open_id",
                            "sender_type": "user",
                            "tenant_key": "key2",
                        },
                        "body": {"content": '{"text": "Hello Again"}'},
                        "mentions": [],
                        "upper_message_id": "upper2",
                    },
                ],
                "page_token": "token123",
            },
        }
        mock_get.return_value = mock_response

        # Test basic history
        messages = self.group.history()
        self.assertEqual(len(messages), 2)
        self.assertIsInstance(messages[0], Message)
        self.assertEqual(messages[0].message_id, "msg1")
        self.assertEqual(messages[0].body["text"], "Hello World")
        self.assertEqual(len(messages[0].mentions), 1)
        self.assertEqual(messages[0].mentions[0].id, "user1")

        mock_get.assert_called_with(
            "/im/v1/messages",
            params={
                "container_id_type": "chat",
                "container_id": self.chat_id,
                "sort_type": "ByCreateTimeAsc",
                "page_size": 50,
            },
        )

        # Test history with parameters
        start_time = datetime(2023, 1, 1)
        end_time = datetime(2023, 12, 31)
        messages = self.group.history(
            start_time=start_time, end_time=end_time, ascending=False, thread_id="thread1", num=10
        )

        self.assertIsInstance(messages[0], Message)
        self.assertEqual(messages[1].message_id, "msg2")
        self.assertEqual(messages[1].body["text"], "Hello Again")
        self.assertEqual(len(messages[1].mentions), 0)

        mock_get.assert_called_with(
            "/im/v1/messages",
            params={
                "container_id_type": "thread",
                "container_id": "thread1",
                "sort_type": "ByCreateTimeDesc",
                "page_size": 10,
                "start_time": int(start_time.timestamp()),
                "end_time": int(end_time.timestamp()),
            },
        )

    def test_repr(self):
        """Test __repr__ method"""
        group = Group(chat_id=self.chat_id, name="Test Group")
        expected_repr = (
            f"<Group chat_id='{self.chat_id}' name='Test Group' description='' "
            "owner_id='' owner_id_type='' tenant_key='' external=None chat_status=None>"
        )
        self.assertEqual(repr(group), expected_repr)


if __name__ == "__main__":
    unittest.main()
