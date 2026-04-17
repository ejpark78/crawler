from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class CommentItem(BaseModel):
    """댓글 데이터 모델"""
    comment_id: str = Field(..., description="댓글 고유 식별자 (ID)")
    author: str = Field(..., description="작성자")
    content: str = Field(..., description="댓글 내용")
    raw_html: Optional[str] = Field(None, description="댓글 원문 HTML (innerhtml)")
    created_at: Optional[datetime] = Field(None, description="작성 일시")

class NewsItem(BaseModel):
    """표준 뉴스 데이터 모델"""
    title: str = Field(..., description="뉴스 제목")
    url: str = Field(..., description="뉴스 원문 URL (PK로 사용)")
    source: str = Field(..., description="뉴스 출처")
    published_at: Optional[datetime] = Field(None, description="발행 일시")
    content: Optional[str] = Field(None, description="본문 내용")
    comments: Optional[List[CommentItem]] = Field(default_factory=list, description="수집된 댓글 리스트")
    json_ld_raw: Optional[str] = Field(None, description="추출된 JSON-LD 원본 데이터")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="수집 일시")
