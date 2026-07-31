class ServiceError(Exception):
    """Base class for service-layer errors that API/bot handlers translate into user messages."""


class InvalidCodeError(ServiceError):
    """The supplied code does not exist."""


class CodeAlreadyConsumedError(ServiceError):
    """The supplied code has already been used."""


class CodeExpiredError(ServiceError):
    """The supplied code is past its expiry."""


class AlreadyInHouseholdError(ServiceError):
    """The user already belongs to a household and cannot join or create another."""
