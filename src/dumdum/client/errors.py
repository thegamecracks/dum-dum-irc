class ClientCannotUpgradeSSLError(Exception):
    """Raised when the server requires SSL and the client cannot upgrade."""


class ServerCannotUpgradeSSLError(Exception):
    """Raised when the server does not use SSL and the client requires it."""


class AuthenticationFailedError(Exception):
    """Raised when authentication with the dumdum server fails."""
