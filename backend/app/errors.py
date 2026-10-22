"""Logical API errors (SRS §10). Messages are user-facing (FR-46): reason + how to fix."""
from fastapi import Request
from fastapi.responses import JSONResponse

STATUS = {
    "unauthenticated": 401,
    "forbidden": 403,
    "not_found": 404,
    "conflict": 409,
    "expired": 410,
    "validation_failed": 422,
    "policy_denied": 422,
    "rate_limited": 429,
    "unavailable": 503,
}


class ApiError(Exception):
    def __init__(self, code: str, message: str, details: dict | list | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


def not_found(what: str = "Đối tượng") -> ApiError:
    # Same answer whether the object does not exist or belongs to another org,
    # so the API never reveals other organizations' data (SRS §10).
    return ApiError("not_found", f"{what} không tồn tại hoặc bạn không có quyền truy cập.")


def manager_only(org_name: str) -> ApiError:
    return ApiError("forbidden", f"Chỉ manager của {org_name} mới làm được việc này.")


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    body = {"error": {"code": exc.code, "message": exc.message}}
    if exc.details is not None:
        body["error"]["details"] = exc.details
    return JSONResponse(status_code=STATUS.get(exc.code, 400), content=body)
