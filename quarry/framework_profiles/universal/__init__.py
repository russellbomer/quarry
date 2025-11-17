"""Universal/meta framework profiles (Schema.org, social meta tags, etc.)."""

from .opengraph import OpenGraphProfile
from .schema_org import SchemaOrgProfile
from .twitter_cards import TwitterCardsProfile

__all__ = ["OpenGraphProfile", "SchemaOrgProfile", "TwitterCardsProfile"]
