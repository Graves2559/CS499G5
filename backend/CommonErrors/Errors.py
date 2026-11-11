'''
Errors.py

Shared kernel: the errors every layer can raise. They carry a message that is safe to show to the user and know
nothing about HTTP; the interface layer (WI29_Server/interface/ErrorHandlers.py) decides the status code.
'''


class AppError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    pass


class UnauthorizedError(AppError):
    pass


class NotFoundError(AppError):
    pass


class ConflictError(AppError):
    pass


class TooManyRequestsError(AppError):
    pass


class PayloadTooLargeError(AppError):
    pass


class UnsupportedMediaError(AppError):
    pass


class ExternalServiceError(AppError):
    pass
