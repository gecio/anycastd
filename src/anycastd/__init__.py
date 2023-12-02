from importlib import metadata as __metadata

from anycastd.core import Service

__version__ = __metadata.version(__name__)
