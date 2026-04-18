"""
Crawler Data Models

This module defines the Pydantic models used throughout the crawler project.
It handles data validation, type hinting, and serialization for collected news and comments.

Main Models:
- NewsItem: Main model for news articles. Includes title, URL, source, content, publication date, and associated comments.
- CommentItem: Sub-model for individual comments. Manages author, text, unique ID, and timestamps.

Key Features:
1. Pydantic v2: Utilizes high-performance data validation and JSON transformation.
2. 3-way Storage Support: Includes raw HTML and JSON-LD fields to ensure data integrity and traceability.
3. Data Normalization: Standardizes diverse scraped formats for consistent MongoDB storage and processing.
"""

from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List

class CommentItem(BaseModel):
    """Data model for an individual comment."""
    comment_id: str = Field(..., description="Unique identifier for the comment")
    author: str = Field(..., description="Author of the comment")
    content: str = Field(..., description="Content of the comment")
    raw_html: Optional[str] = Field(None, description="Original HTML of the comment (innerhtml)")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the comment was created")

class NewsItem(BaseModel):
    """Standard data model for a news item."""
    title: str = Field(..., description="Title of the news article")
    url: str = Field(..., description="Original URL of the news article (used as PK)")
    source: str = Field(..., description="Source of the news")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    content: Optional[str] = Field(None, description="Main content or summary of the news")
    comments: Optional[List[CommentItem]] = Field(default_factory=list, description="List of collected comments")
    json_ld_raw: Optional[str] = Field(None, description="Original extracted JSON-LD data")
    html: Optional[str] = Field(None, description="Original raw HTML of the page")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Collection timestamp (UTC)")
