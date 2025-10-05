from importlib import metadata as _metadata

try:
    __version__ = _metadata.version("dp-client")
except _metadata.PackageNotFoundError:
    __version__ = "0.0.0"

from .api import HealthAPI, UsersAPI  # noqa: F401
from .client import DPClient  # noqa: F401
from .clients import MetaDataServerAPIClientFactory  # noqa: F401
from .db import PGDBClient  # noqa: F401

__all__ = [
    "__version__",
    "DPClient",
    "HealthAPI",
    "UsersAPI",
    "MetaDataServerAPIClientFactory",
    "PGDBClient",
]
