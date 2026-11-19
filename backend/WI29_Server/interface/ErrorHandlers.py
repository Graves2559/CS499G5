'''
ErrorHandlers.py

The one place that turns the application's errors (CommonErrors/Errors.py) into HTTP responses.
Routes never build error responses themselves; they let the error propagate.
'''
from fastapi import Request
from fastapi.responses import JSONResponse

from CommonErrors.Errors import (
    AppError, ConflictError, ExternalServiceError, NotFoundError, PayloadTooLargeError, TooManyRequestsError,
    UnauthorizedError, UnsupportedMediaError, ValidationError,
)

STATUS_BY_ERROR = {
    ValidationError: 400,
    UnauthorizedError: 401,
    NotFoundError: 404,
    ConflictError: 409,
    PayloadTooLargeError: 413,
    UnsupportedMediaError: 415,
    TooManyRequestsError: 429,
    ExternalServiceError: 502,
}


def statusFor(error: AppError) -> int:
    for errorType in type(error).__mro__:
        if errorType in STATUS_BY_ERROR:
            return STATUS_BY_ERROR[errorType]
    return 500


def registerErrorHandlers(app):
    @app.exception_handler(AppError)
    async def handleAppError(request: Request, error: AppError):
        return JSONResponse({"detail": error.message}, status_code=statusFor(error))
