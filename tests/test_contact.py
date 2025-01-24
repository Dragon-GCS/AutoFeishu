import unittest
from unittest.mock import MagicMock, patch

from feishu import Contact
from feishu.models import User


class TestContact(unittest.TestCase):
    def setUp(self):
        self.contact = Contact(app_id="test_app_id", app_secret="test_app_secret")

    @patch("feishu.api.contact.config")
    def test_default_open_id_with_config(self, mock_config):
        # Test when config.open_id is set
        mock_config.open_id = "test_open_id"
        mock_config.app_id = "test_app_id"
        mock_config.app_secret = "test_app_secret"

        result = self.contact.default_open_id
        self.assertEqual(result, "test_open_id")

    @patch("feishu.api.contact.config")
    def test_default_open_id_with_phone(self, mock_config):
        # Test when using phone to get open_id
        mock_config.open_id = None
        mock_config.phone = "1234567890"
        mock_config.email = None

        self.contact.get_open_id = MagicMock(return_value={"1234567890": "test_open_id"})
        result = self.contact.default_open_id
        self.assertEqual(result, "test_open_id")

    @patch("feishu.api.contact.config")
    def test_default_open_id_raises_error(self, mock_config):
        # Test when no identification is provided
        mock_config.open_id = None
        mock_config.phone = None
        mock_config.email = None

        with self.assertRaises(ValueError):
            _ = self.contact.default_open_id

    @patch.object(Contact, "post")
    def test_get_open_id(self, mock_post):
        mock_post.return_value = {
            "data": {
                "user_list": [
                    {"mobile": "1234567890", "user_id": "ou_123"},
                    {"email": "test@example.com", "user_id": "ou_456"},
                ]
            }
        }

        result = self.contact.get_open_id(
            phones="1234567890", emails="test@example.com", cache=True
        )

        expected = {"1234567890": "ou_123", "test@example.com": "ou_456"}
        self.assertEqual(result, expected)

        # Test cache functionality
        result_cached = self.contact.get_open_id(
            phones="1234567890", emails="test@example.com", cache=True
        )
        self.assertEqual(result_cached, expected)
        # Verify post was only called once due to caching
        mock_post.assert_called_once()

    @patch.object(Contact, "get")
    def test_get_user_info(self, mock_get):
        mock_get.return_value = {
            "data": {
                "user": {
                    "description": "Test description",
                    "en_name": "Test En Name",
                    "mobile_visible": True,
                    "name": "Test User",
                    "nickname": "Tester",
                    "open_id": "ou_123",
                    "union_id": "on_456",
                    "avatar": {
                        "avatar_72": "http://example.com/72.jpg",
                        "avatar_240": "http://example.com/240.jpg",
                        "avatar_640": "http://example.com/640.jpg",
                        "avatar_origin": "http://example.com/origin.jpg",
                    },
                }
            }
        }

        result = self.contact.get_user_info(
            user_id="ou_123", user_id_type="open_id", department_id_type="open_department_id"
        )

        self.assertIsInstance(result, User)
        # Test required fields
        self.assertEqual(result.description, "Test description")
        self.assertEqual(result.en_name, "Test En Name")
        self.assertEqual(result.mobile_visible, True)
        self.assertEqual(result.name, "Test User")
        self.assertEqual(result.nickname, "Tester")
        self.assertEqual(result.open_id, "ou_123")
        self.assertEqual(result.union_id, "on_456")
        # Test avatar fields
        self.assertEqual(result.avatar.avatar_72, "http://example.com/72.jpg")
        self.assertEqual(result.avatar.avatar_240, "http://example.com/240.jpg")
        self.assertEqual(result.avatar.avatar_640, "http://example.com/640.jpg")
        self.assertEqual(result.avatar.avatar_origin, "http://example.com/origin.jpg")

        mock_get.assert_called_once_with(
            self.contact.api["user_info"].format(user_id="ou_123"),
            params={"user_id_type": "open_id", "department_id_type": "open_department_id"},
        )

    @patch.object(Contact, "get")
    def test_batch_user_info(self, mock_get):
        mock_get.return_value = {
            "data": {
                "items": [
                    {
                        "description": "Description 1",
                        "en_name": "User One",
                        "mobile_visible": True,
                        "name": "User 1",
                        "nickname": "U1",
                        "open_id": "ou_123",
                        "union_id": "on_123",
                        "email": "user1@example.com",
                        "avatar": {
                            "avatar_72": "http://example.com/1_72.jpg",
                            "avatar_240": "http://example.com/1_240.jpg",
                            "avatar_640": "http://example.com/1_640.jpg",
                            "avatar_origin": "http://example.com/1_origin.jpg",
                        },
                    },
                    {
                        "description": "Description 2",
                        "en_name": "User Two",
                        "mobile_visible": True,
                        "name": "User 2",
                        "nickname": "U2",
                        "open_id": "ou_456",
                        "union_id": "on_456",
                        "email": "user2@example.com",
                        "avatar": {
                            "avatar_72": "http://example.com/2_72.jpg",
                            "avatar_240": "http://example.com/2_240.jpg",
                            "avatar_640": "http://example.com/2_640.jpg",
                            "avatar_origin": "http://example.com/2_origin.jpg",
                        },
                    },
                ]
            }
        }

        user_ids = ["ou_123", "ou_456"]
        result = self.contact.batch_user_info(
            user_ids=user_ids, user_id_type="open_id", department_id_type="open_department_id"
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], User)

        # Test required fields
        self.assertEqual(result[0].description, "Description 1")
        self.assertEqual(result[0].en_name, "User One")
        self.assertEqual(result[0].mobile_visible, True)
        self.assertEqual(result[0].name, "User 1")
        self.assertEqual(result[0].nickname, "U1")
        self.assertEqual(result[0].open_id, "ou_123")
        self.assertEqual(result[0].union_id, "on_123")
        self.assertEqual(result[0].email, "user1@example.com")

        # Test avatar fields
        self.assertEqual(result[0].avatar.avatar_72, "http://example.com/1_72.jpg")
        self.assertEqual(result[0].avatar.avatar_240, "http://example.com/1_240.jpg")

        mock_get.assert_called_once_with(
            self.contact.api["batch_user_info"],
            params={
                "user_ids": user_ids,
                "user_id_type": "open_id",
                "department_id_type": "open_department_id",
            },
        )


if __name__ == "__main__":
    unittest.main()
