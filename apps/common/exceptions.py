"""Contract-shaped errors: {"error": {"code", "message", "fields"?}}."""
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class ContractError(APIException):
    """Raise with a stable machine code + message to match API_CONTRACT.md."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "error"
    default_message = "Something went wrong."

    def __init__(self, code=None, message=None, status_code=None, fields=None):
        self.code = code or self.default_code
        self.message = message or self.default_message
        self.fields = fields
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=self.message)


# Convenience constructors for the documented error codes.
def invalid_credentials():
    return ContractError("invalid_credentials", "Invalid credentials.", 401)


def not_verified():
    return ContractError("not_verified", "Account not fully verified.", 403)


def code_invalid():
    return ContractError("code_invalid", "That code is not correct.", 400)


def code_expired():
    return ContractError("code_expired", "That code has expired.", 400)


def code_max_attempts():
    return ContractError("code_max_attempts", "Too many attempts; request a new code.", 429)


def already_exists(message="That account already exists."):
    return ContractError("already_exists", message, 409)


def not_found(message="Not found."):
    return ContractError("not_found", message, 404)


def forbidden(message="You do not have permission."):
    return ContractError("forbidden", message, 403)


def rate_limited(message="Too many requests; slow down."):
    return ContractError("rate_limited", message, 429)


def contract_exception_handler(exc, context):
    """Wrap every error in the contract envelope."""
    if isinstance(exc, ContractError):
        body = {"error": {"code": exc.code, "message": exc.message}}
        if exc.fields:
            body["error"]["fields"] = exc.fields
        return Response(body, status=exc.status_code)

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    code = "error"
    fields = None
    message = "Request failed."

    if response.status_code == 401:
        code, message = "unauthenticated", "Authentication required."
    elif response.status_code == 403:
        code, message = "forbidden", "You do not have permission."
    elif response.status_code == 404:
        code, message = "not_found", "Not found."
    elif response.status_code in (400, 422):
        code, message = "validation_error", "Validation failed."
        if isinstance(data, dict):
            fields = {
                k: (v[0] if isinstance(v, (list, tuple)) and v else v)
                for k, v in data.items()
            }
        response.status_code = 422

    body = {"error": {"code": code, "message": message}}
    if fields:
        body["error"]["fields"] = fields
    response.data = body
    return response
