# Author: Dragon
# Python: 3.12
# Created at 2024/10/10 17:12
# Edit with VS Code
# Filename: spread_sheet.py

from __future__ import annotations

from pydantic import BaseModel

from feishu.client import BaseClient


class WriteResult(BaseModel):
    spreadsheetToken: str
    updatedCells: int
    updatedColumns: int
    updatedRange: str
    updatedRows: int


class SpreadSheet(BaseClient):
    """Operate Feishu SpreadSheet

    Args:
        doc_id(str): The document ID of the spreadsheet
    """

    def __init__(self, doc_id: str):
        self.doc_id = doc_id

    def _request(self, method: str, api: str, **kwargs):
        version = "v3" if api.startswith("/sheets/") else "v2"
        api = f"/sheets/{version}/spreadsheets/{self.doc_id}{api}"
        data = super()._request(method, api, **kwargs)
        return data["data"]

    def list_sheets(self) -> list[Sheet]:
        """List all sheets in the spreadsheet

        Returns:
            list[Sheet]: List of sheet objects
        """

        data = self.get("/sheets/query")
        return [
            Sheet(owner=self, sheet_id=sheet["sheet_id"], title=sheet["title"])
            for sheet in data["sheets"]
        ]

    def get_sheet(self, sheet_id_or_title: str) -> Sheet:
        """Get sheet by sheet_id or title

        Args:
            sheet_id_or_title(str): The sheet_id or title of the sheet

        Returns:
            Sheet: The sheet object
        """

        sheets = self.list_sheets()
        for sheet in sheets:
            if sheet_id_or_title in (sheet.sheet_id, sheet.title):
                return sheet
        raise ValueError(f"Sheet {sheet_id_or_title} not found")

    def add_sheet(self, title: str) -> "Sheet":
        """Add a new sheet to the spreadsheet

        Args:
            title(str): The title of the new sheet
        Returns:
            Sheet: The new sheet object
        """

        data = self.post(
            "/sheets_batch_update",
            json={"requests": {"addSheet": {"properties": {"title": title}}}},
        )
        sheet_id = data["replies"][0]["addSheet"]["properties"]["sheetId"]
        return Sheet(owner=self, sheet_id=sheet_id, title=title)

    def delete_sheet(self, sheet_id: str) -> bool:
        """Delete a sheet from the spreadsheet

        Args:
            sheet_id(str): The sheet_id of the sheet to delete
        """
        data = self.post(
            "/sheets_batch_update", json={"requests": {"deleteSheet": {"sheetId": sheet_id}}}
        )
        return data["replies"][0]["deleteSheet"]["result"]


class Sheet:
    """Operate a sheet in a Feishu SpreadSheet, suggest to get the sheet object by
    SpreadSheet.list_sheets() or SpreadSheet.get_sheet().

    Args:
        owner(SpreadSheet | str): The SpreadSheet object or doc_id of the sheet
        sheet_id(str): The sheet_id of the sheet
        title(str): The title of the sheet, default is ""
    """

    def __init__(self, owner: SpreadSheet | str, sheet_id: str, title: str = ""):
        self.owner = owner if isinstance(owner, SpreadSheet) else SpreadSheet(owner)
        self.sheet_id = sheet_id
        self.title = title

    def read(self, start: str = "", end: str = "") -> list[list]:
        """Read data from the sheet

        Args:
            start(str): The start cell of the range, e.g. "A1"
            end(str): The end cell of the range, e.g. "C3"
        """
        if (start or end) and not (start and end):
            raise ValueError("Both start and end should be provided")
        _range = f"{self.sheet_id}!{start}:{end}".strip("!:")
        data = self.owner.get(f"/values/{_range}", params={"valueRenderOption": "FormattedValue"})
        return data["valueRange"]["values"]

    def write(self, start: str, end: str, values: list[list]) -> WriteResult:
        """Write data to the sheet

        Args:
            start(str): The start cell of the range, e.g. "A1"
            end(str): The end cell of the range, e.g. "C3"
            values(list[list]): The data to write, e.g. [["A", "B", "C"], [1, 2, 3]]

        Returns:
            WriteResult: The result of the write operation
        """
        assert all(len(row) == len(values[0]) for row in values[1:]), "Data中的行长度不一致"
        range_col = ord(end[0]) - ord(start[0]) + 1
        range_row = int(end[1:]) - int(start[1:]) + 1
        assert range_col >= len(values[0]) and range_row >= len(values), "数据超出范围"

        data = self.owner.put(
            "/values",
            json={"valueRange": {"range": f"{self.sheet_id}!{start}:{end}", "values": values}},
        )
        return WriteResult(**data)

    try:
        import pandas as pd

        def read_df(self, start: str = "", end: str = "") -> pd.DataFrame:
            values = self.read(start, end)
            return pd.DataFrame(values[1:], columns=values[0])  # noqa:F821 # type: ignore

        def write_df(self, df: pd.DataFrame, start: str = "A1") -> WriteResult:
            values = [df.columns.tolist()] + df.values.tolist()
            end = f"{chr(ord(start[0]) + len(df.columns) - 1)}{len(df) + 1}"
            return self.write(start, end, values)
    except ImportError:
        pass
