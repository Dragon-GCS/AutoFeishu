class ApiError(Exception):
    def __init__(self, api: str, code: int, message: str):
        self.api = api
        self.code = code
        self.message = message
        super().__init__(f"Api({api}) response code error({code}): {message}")
