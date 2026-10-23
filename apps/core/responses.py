from http import HTTPStatus
from typing import Any

from rest_framework.response import Response


class SuccessResponse(Response):
    def __init__(
        self,
        data: Any = None,
        message: str = '',
        status: int = HTTPStatus.OK,
        **kwargs: Any,
    ) -> None:
        super().__init__(data=data, status=status, **kwargs)
        self.message = message
