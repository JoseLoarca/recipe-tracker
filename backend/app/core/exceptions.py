"""Service-layer exceptions, kept independent of HTTP status codes and Telegram copy.

API routes and bot handlers each catch these and translate them into
whatever's appropriate for their surface — an HTTP 400 response, or a
human-readable Telegram message.
"""


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


class NotAuthorizedError(ServiceError):
    """The user isn't allowed to perform this action on this resource."""


class NoHouseholdError(ServiceError):
    """The action requires a household the user doesn't have."""
