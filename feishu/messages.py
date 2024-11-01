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

from feishu.contact import Contact

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None


from feishu.client import BaseClient

FileStream: TypeAlias = BufferedReader | bytes | bytearray
File: TypeAlias = str | FileStream
FileType: TypeAlias = Literal["opus", "mp4", "pdf", "doc", "xls", "ppt", "stream"]
MsgType: TypeAlias = Literal["text", "image", "audio", "media", "file", "interactive"]


class FeiShuBot(BaseClient):
    """发送消息给指定用户或聊天群组。
    当 user_id 和 chat_id 未设置时，机器人将使用Contact().default_open_id作为默认收件人。
    当 user_id 和 chat_id 都设置时，将会在群消息中@指定用户。

    Args:
        user_id (str): 将接收消息的用户的 open_id
        chat_id (str): 将发送消息的聊天的 chat_id
    """

    api = {"message": "/im/v1/messages", "images": "/im/v1/images", "files": "/im/v1/files"}

    def __init__(self, user_id: str = "", chat_id: str = ""):
        self.receive_id = user_id or chat_id
        if not self.receive_id:
            self.receive_id = Contact().default_open_id

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
            self.api["message"],
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
            url = self.api["images"]
            data = {"image_type": "message"}
            files = {"image": (filename, file)}
        else:
            url = self.api["files"]
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
