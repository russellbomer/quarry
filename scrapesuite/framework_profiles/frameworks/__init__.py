"""JavaScript framework profiles."""

from .django import DjangoAdminProfile
from .nextjs import NextJSProfile
from .react import ReactComponentProfile
from .vue import VueJSProfile

__all__ = [
    "DjangoAdminProfile",
    "NextJSProfile",
    "ReactComponentProfile",
    "VueJSProfile",
]
