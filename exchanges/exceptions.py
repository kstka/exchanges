class ExchangeException(Exception):
    """Base class for exceptions in the _exchanges module."""
    default_message = "An exchange error occurred"

    def __init__(self, message=None):
        if message is None:
            message = self.default_message
        else:
            message = f"{self.default_message}: {message}"
        super().__init__(message)


class ExchangeAPIException(ExchangeException):
    """Exception raised for errors in the API connection."""
    default_message = "API error"


class NotImplementedException(ExchangeException):
    """Exception raised for unimplemented features or methods."""
    default_message = "This feature has not been implemented yet"


class ExchangeRequestException(ExchangeException):
    """Exception raised for errors during exchange requests."""
    default_message = "Error during exchange request"


class UnknownRequestMethodException(ExchangeException):
    """Exception raised for unknown request methods."""
    default_message = "Unknown request method"
