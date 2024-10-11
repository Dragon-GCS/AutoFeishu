import os
import unittest

import httpx

from feishu.messages import FeiShuBot


class TestFeishu(unittest.TestCase):
    bot = FeiShuBot()

    def test_send_text(self):
        self.bot.send_text("This is a test message.")

    def test_send_file(self):
        with open(__file__, "rb") as f:
            self.bot.send_file(f, "stream")

    def test_send_image(self):
        self.bot.send_image(
            httpx.get("https://random.imagecdn.app/500/150", follow_redirects=True).content
        )

    @unittest.skipUnless(os.path.exists("test.mp4"), "test.mp4 not found")
    def test_send_media(self):
        with open("test.mp4", "rb") as f:
            self.bot.send_media(f)

    @unittest.skipUnless(os.path.exists("test.opus"), "test.opus not found")
    def test_send_audio(self):
        with open("test.opus", "rb") as f:
            self.bot.send_audio(f)

    def test_send_card(self):
        self.bot.send_card("This is a test **message**.", "Test card")
