"""Connectors package."""

from scrapesuite.connectors.custom import CustomConnector
from scrapesuite.connectors.fda import FDAConnector
from scrapesuite.connectors.generic import GenericConnector
from scrapesuite.connectors.nws import NWSConnector

__all__ = ["CustomConnector", "FDAConnector", "GenericConnector", "NWSConnector"]
