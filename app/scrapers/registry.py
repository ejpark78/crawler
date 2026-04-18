"""
Scraper Registry Module

This module centrally manages all available scraper classes within the project.
When adding a new news source, the corresponding scraper class must be implemented
and registered here.

The registered scrapers are dynamically selected via the 'SOURCE' argument,
which also determines the name of the MongoDB database used for data isolation.
"""
from app.scrapers.geeknews import GeekNewsScraper

# Mapping between Source Names and Scraper Classes
# Key: Source identifier used in CLI or DAGs (Case-Sensitive)
# Value: Scraper class implementing BaseScraper
SCRAPER_REGISTRY = {
    "GeekNews": GeekNewsScraper,
}
