from http import HTTPStatus


class DomainException(Exception):
    def __init__(self, message: str, status_code: HTTPStatus):
        self.message = message
        self.status_code = status_code
        

class ConflictingError(DomainException):
    pass


class ConflictingNameError(ConflictingError):
    pass


class ConflictingEmailError(ConflictingError):
    pass


class AuthorizationError(DomainException):
    pass


class ChefErrorNotFound(DomainException):
    pass


class AuthenticationError(DomainException):
    pass


class CredentialsError(DomainException):
    pass