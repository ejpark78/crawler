"""
Crawler Data Models

이 모듈은 크롤러 프로젝트 전반에서 사용되는 데이터 구조를 Pydantic 모델로 정의합니다.
수집된 데이터의 유효성 검사, 타입 힌팅 및 직렬화(Serialization)를 담당합니다.

주요 모델:
- NewsItem: 뉴스 기사 정보를 담는 메인 모델. 제목, URL, 출처, 원문 내용, 수집 시간, 그리고 관련 댓글 리스트를 포함합니다.
- CommentItem: 개별 댓글 정보를 담는 하위 모델. 작성자, 본문, 고유 ID 등을 관리합니다.

특징:
1. Pydantic v2 사용: 고성능 데이터 검증 및 JSON 변환을 지원합니다.
2. 데이터 정규화: 스크래핑된 다양한 형태의 데이터를 일관된 형식으로 변환하여 DB 저장 및 처리를 용이하게 합니다.
"""

from pydantic import BaseModel, Field
from datetime import datetime, timezone
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="수집 일시 (UTC)")
