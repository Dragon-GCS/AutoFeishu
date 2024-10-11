# Author: Dragon
# Python: 3.12
# Created at 2024/10/10 17:12
# Edit with VS Code
# Filename: messages.py
# Description: Feishu bot to send message to user

import json
import os
from io import BufferedReader
from typing import Literal, TypeAlias

from feishu import contact

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None


from feishu.client import BaseClient

TENANT_TOKEN_API = "/auth/v3/tenant_access_token/internal"
MESSAGE_API = "/im/v1/messages"
UPLOAD_IMAGE_API = "/im/v1/images"
UPLOAD_FILE_API = "/im/v1/files"

# if open_id is not set, use phone or email to query open_id, prefer to use phone
FEISHU_PHONE = os.getenv("FEISHU_PHONE", "")
FEISHU_EMAIL = os.getenv("FEISHU_EMAIL", "")
# open_id of user who will receive the message
FEISHU_OPEN_ID = os.getenv("FEISHU_OPEN_ID")


FileStream: TypeAlias = BufferedReader | bytes | bytearray
File: TypeAlias = str | FileStream
FileType: TypeAlias = Literal["opus", "mp4", "pdf", "doc", "xls", "ppt", "stream"]
MsgType: TypeAlias = Literal["text", "image", "audio", "media", "file", "interactive"]


class FeiShuBot(BaseClient):
    """Send message to feishu user or chat.
    When user_id and chat_id are not set, bot will use FEISHU_OPEN_ID to send message.
    If FEISHU_OPEN_ID is not set, bot will use FEISHU_PHONE or FEISHU_EMAIL to query open_id as user_id.
    When user_id and chat_id are set, user_id will be used as at user in message.

    Args:
        user_id(str): open_id of the user who will receive the message
        chat_id(str): chat_id of the chat where the message will be sent
    """

    def __init__(self, user_id: str = "", chat_id: str = ""):
        self.receive_id = user_id or chat_id or FEISHU_OPEN_ID
        if not self.receive_id:
            if not (FEISHU_PHONE or FEISHU_EMAIL):
                raise ValueError(
                    "To query open_id when FEISHU_OPEN_ID isn't set, FEISHU_PHONE "
                    "or FEISHU_EMAIL must be set with your phone or email."
                )
            users = contact.get_open_id(FEISHU_PHONE, FEISHU_EMAIL)
            self.receive_id = users.get(FEISHU_PHONE) or users.get(FEISHU_EMAIL)

            if not self.receive_id:
                raise ValueError(
                    f"User not found with phone {FEISHU_PHONE} or email {FEISHU_EMAIL}"
                )

        if self.receive_id.startswith("ou_"):
            self.receive_id_type = "open_id"
        elif self.receive_id.startswith("oc_"):
            self.receive_id_type = "chat_id"
        else:
            raise Exception(f"Invalid receive_id: {self.receive_id}")

        self.at = user_id if chat_id and user_id else ""

    def _send_message(
        self,
        msg_type: MsgType,
        content: dict,
    ) -> dict:
        return self.post(
            MESSAGE_API,
            params={"receive_id_type": self.receive_id_type},
            json={
                "receive_id": self.receive_id,
                "msg_type": msg_type,
                "content": json.dumps(content),
            },
        )

    def _post_file(
        self, file_type: Literal["image"] | FileType, file: File, filename: str = ""
    ) -> dict:
        if not filename:
            filename = os.path.basename(file.name) if isinstance(file, BufferedReader) else "file"

        if file_type == "image":
            url = UPLOAD_IMAGE_API
            data = {"image_type": "message"}
            files = {"image": (filename, file)}
        else:
            url = UPLOAD_FILE_API
            data = {"file_type": file_type, "file_name": filename}
            files = {"file": (filename, file)}
        return self.post(url, data=data, files=files)["data"]

    def send_text(self, msg: str) -> dict:
        """send text message

        Args:
            msg(str): message to be sent
        """
        if self.at:
            msg = f'<at user_id="{self.at}"></at> {msg}'

        return self._send_message("text", {"text": msg})

    def send_image(self, image: FileStream) -> dict:
        """Send image message

        Args:
            image(FileStream): image to be sent, must be a file opened in binary mode or bytes
        """
        return self._send_message("image", self._post_file("image", image))

    def send_file(self, file: File, file_type: FileType, filename: str = "") -> dict:
        """Send file message

        Args:
            file(File): file to be sent, must be file opened in binary mode, str or bytes
            file_type (str): One of "opus", "mp4", "pdf", "doc", "xls", "ppt", "stream"
            filename (str): filename of the file, default is empty
        """
        return self._send_message("file", self._post_file(file_type, file, filename))

    def send_audio(self, audio: FileStream) -> dict:
        """Send audio message, audio must be opus format. For other audio type,
        refer to the following command to convert:

        `ffmpeg -i SourceFile.mp3 -acodec libopus -ac 1 -ar 16000 TargetFile.opus`

        Args:
            audio(FileStream): audio to be sent, must be opened in binary mode
        """

        return self._send_message("audio", self._post_file("opus", audio))

    def send_media(self, media: FileStream, cover: FileStream | bytes = b"") -> dict:
        """Send media message, media must be mp4 format.

        Args:
            media(FileStream): media to be sent, must be opened in binary mode
            cover(FileStream | bytes): cover for media, default is first frame of media
            filename(str): filename of the audio, default is empty
        """
        if cv2 is None:
            raise Exception("opencv-python is not installed, send_media is unavailable")
        if not cover:
            if not isinstance(media, BufferedReader):
                raise ValueError("Cover must be set when media is not an opened file")
            _, frame = cv2.VideoCapture(media.name).read()
            _, _cover = cv2.imencode(".jpg", frame)
            cover = _cover.tobytes()
        content = self._post_file("mp4", media) | self._post_file("image", cover)
        return self._send_message("media", content)

    def send_card(self, message: str, header: str = "") -> dict:
        """Send feishu card message, only support markdown format now.

        Refer to https://open.feishu.cn/document/ukTMukTMukTM/uADOwUjLwgDM14CM4ATN

        Args:
            message(str): markdown message to be sent
            header(str): card header, default is empty
        """
        content = {
            "config": {"wide_screen_mode": True},
            "elements": [{"tag": "markdown", "content": message}],
        }
        if header:
            content["header"] = {
                "title": {
                    "tag": "plain_text",
                    "content": header,
                },
                "template": "blue",
            }
        return self._send_message("interactive", content)
