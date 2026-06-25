class IdentityDomainError(Exception):
    """Base identity domain error."""


class DisabledUserError(IdentityDomainError):
    """Raised when a disabled user attempts to authenticate."""
