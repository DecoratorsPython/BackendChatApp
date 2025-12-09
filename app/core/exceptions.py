class InvalidRefreshTokenError(Exception):
    """Raised when a refresh token is unknown / malformed / not found in DB."""

    pass


class ExpiredRefreshTokenError(Exception):
    """Raised when a refresh token is past its expiry."""

    pass


class RevokedRefreshTokenError(Exception):
    """Raised when a refresh token has been revoked or already rotated."""

    pass


class InvalidTokenError(Exception):
    """Raised when a token is invalid or cannot be decoded."""

    pass


class ExpiredTokenError(Exception):
    """Raised when a token is valid but expired."""

    pass
