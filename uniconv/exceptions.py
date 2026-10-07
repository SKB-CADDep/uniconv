"""Public errors raised by UniConv."""


class UnknownParameterError(ValueError):
    """The exact string parameter ID is not registered."""


class UnknownUnitError(ValueError):
    """The unit code is not registered for the requested parameter."""


class DataLoadError(ValueError):
    """A packaged JSON resource is missing, malformed or invalid."""
