import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from feishu.client import ApiError, AuthClient, BaseClient, TenantAccessToken, UserAccessToken


class TestBaseClient(unittest.TestCase):
    """Test base client functionality"""

    def setUp(self):
        self.client = BaseClient()
        self.test_api = "/test/api"

    @patch("httpx.Client.request")
    def test_request_success(self, mock_request):
        """Test successful API request"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": "test"}
        mock_request.return_value = mock_response

        result = self.client._request("GET", self.test_api)
        self.assertEqual(result, {"code": 0, "data": "test"})

    @patch("httpx.Client.request")
    def test_request_error(self, mock_request):
        """Test API request with error response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 99991663, "msg": "error"}
        mock_request.return_value = mock_response

        with self.assertRaises(ApiError) as context:
            self.client._request("GET", self.test_api)
        self.assertEqual(99991663, context.exception.code)
        self.assertEqual("error", context.exception.message)


class TestAuthClient(unittest.TestCase):
    """Test AuthClient with different configurations"""

    def setUp(self):
        # Reset token storage before each test
        TenantAccessToken._tokens = {}
        UserAccessToken._tokens = {}

        # Mock configuration
        self.test_app_id_1 = "test_app_id_1"
        self.test_app_secret_1 = "test_secret_1"
        self.test_app_id_2 = "test_app_id_2"
        self.test_app_secret_2 = "test_secret_2"

        self.client1 = AuthClient(self.test_app_id_1, self.test_app_secret_1)
        self.client2 = AuthClient(self.test_app_id_2, self.test_app_secret_2)

    def mock_token_response(self, token_value):
        return {"code": 0, "expire": 7200, "tenant_access_token": token_value}

    @patch.object(TenantAccessToken, "_auth")
    def test_different_clients_different_tokens(self, mock_auth):
        """Test that different app credentials get different tokens"""
        # Mock different token responses for different credentials
        mock_auth.side_effect = [
            self.mock_token_response("token1"),
            self.mock_token_response("token2"),
        ]

        # Get tokens for both clients
        token1 = self.client1.token
        token2 = self.client2.token

        # Verify different tokens were issued
        self.assertNotEqual(token1, token2)
        self.assertEqual(token1, "token1")
        self.assertEqual(token2, "token2")

    @patch.object(TenantAccessToken, "_auth")
    def test_token_caching(self, mock_auth):
        """Test that tokens are properly cached"""
        mock_auth.return_value = self.mock_token_response("cached_token")

        # Get token multiple times
        token1 = self.client1.token
        token2 = self.client1.token

        # Verify token is cached (auth called only once)
        self.assertEqual(token1, token2)
        mock_auth.assert_called_once()


class TestUserAccessToken(unittest.TestCase):
    """Test UserAccessToken functionality"""

    def setUp(self):
        self.auth_code = "test_auth_code"
        self.redirect_uri = "http://test.com/callback"
        self.app_id = "test_app_id"
        self.app_secret = "test_app_secret"

        # Create a client with UserAccessToken
        self.user_token = UserAccessToken(auth_code=self.auth_code, redirect_uri=self.redirect_uri)
        self.client = AuthClient(self.app_id, self.app_secret)
        self.default_token = AuthClient.__dict__["token"]
        # Replace the default TenantAccessToken with UserAccessToken
        AuthClient.token = self.user_token

    def tearDown(self) -> None:
        AuthClient.token = self.default_token

    @patch.object(UserAccessToken, "_auth")
    def test_user_access_token_auth(self, mock_auth):
        """Test user access token authentication"""
        mock_auth.return_value = {"code": 0, "access_token": "user_token", "expires_in": 7200}

        # Get token
        token = self.client.token

        # Verify correct token is returned
        self.assertEqual(token, "user_token")

        # Verify correct parameters were passed to auth
        mock_auth.assert_called_once_with(
            body={
                "grant_type": "authorization_code",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "code": self.auth_code,
                "redirect_uri": self.redirect_uri,
            }
        )

    def test_user_token_expiration(self):
        """Test that expired user tokens raise exception"""
        # Set an expired token
        UserAccessToken._tokens[(self.app_id, self.app_secret)] = (
            "expired_token",
            datetime.now() - timedelta(hours=1),
        )

        # Attempting to refresh should raise an exception
        with self.assertRaises(Exception) as context:
            self.user_token.refresh_token(self.app_id, self.app_secret)

        self.assertTrue("UserAccessToken is expired" in str(context.exception))

    def test_auth_url_generation(self):
        """Test authentication URL generation"""
        from urllib.parse import quote

        test_redirect = "http://test.com/callback"
        test_scope = "test_scope"

        url = UserAccessToken.auth_url(redirect_uri=test_redirect, scope=test_scope)
        print(url)

        # Verify URL contains required parameters
        self.assertIn(f"redirect_uri={quote(test_redirect, safe='')}", url)
        self.assertIn(f"scope={test_scope}", url)
        self.assertIn("app_id=", url)


if __name__ == "__main__":
    unittest.main()
