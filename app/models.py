"""
크롤러 데이터 모델 (Crawler Data Models)

이 모듈은 크롤러 프로젝트 전반에서 사용되는 Pydantic 모델을 정의합니다.
수집된 뉴스 및 댓글 데이터의 유효성 검사, 타입 힌팅 및 직렬화를 담당합니다.

주요 모델:
- GeekNewsList: 뉴스 기사의 메인 모델. 제목, URL, 출처, 내용, 발행일 및 관련 댓글을 포함합니다.
- GeekNewsContents: 개별 댓글을 위한 서브 모델. 작성자, 본문, 고유 ID 및 타임스탬프를 관리합니다.

핵심 기능:
1. Pydantic v2: 고성능 데이터 검증 및 JSON 변환을 활용합니다.
2. 3방향 저장소 지원: 데이터 무결성과 추적성을 보장하기 위해 원본 HTML 및 JSON-LD 필드를 포함합니다.
3. 데이터 정규화: MongoDB 저장 및 처리를 위해 다양한 스크래핑 형식을 일관된 형태로 표준화합니다.
"""

from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List

class GeekNewsContents(BaseModel):
    """개별 댓글을 위한 데이터 모델."""
    comment_id: str = Field(..., description="댓글의 고유 식별자")
    author: str = Field(..., description="댓글 작성자")
    content: str = Field(..., description="댓글 내용")
    raw_html: Optional[str] = Field(None, description="댓글의 원본 HTML (innerhtml)")
    created_at: Optional[datetime] = Field(None, description="댓글이 작성된 시점의 타임스탬프")

class GeekNewsList(BaseModel):
    """뉴스 항목을 위한 표준 데이터 모델."""
    title: str = Field(..., description="뉴스 기사 제목")
    url: str = Field(..., description="뉴스 기사의 원본 URL (PK로 사용)")
    source: str = Field(..., description="뉴스 출처")
    published_at: Optional[datetime] = Field(None, description="발행 타임스탬프")
    content: Optional[str] = Field(None, description="뉴스의 주요 내용 또는 요약")
    comments: Optional[List[GeekNewsContents]] = Field(default_factory=list, description="수집된 댓글 목록")
    json_ld_raw: Optional[str] = Field(None, description="추출된 원본 JSON-LD 데이터")
    html: Optional[str] = Field(None, description="페이지의 원본 raw HTML")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="수집 타임스탬프 (UTC)")

class PytorchKRContents(BaseModel):
    """PyTorch KR 콘텐츠를 위한 특화된 데이터 모델."""
    title: str = Field(..., description="토픽 제목")
    url: str = Field(..., description="토픽의 원본 URL")
    source: str = Field(..., description="뉴스 출처")
    published_at: Optional[str] = Field(None, description="발행 타임스탬프")
    content: Optional[str] = Field(None, description="토픽의 주요 내용")
    html: Optional[str] = Field(None, description="페이지의 원본 raw HTML")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="수집 타임스탬프 (UTC)")

class GPTERSNews(BaseModel):
    """지피터스 뉴스 항목을 위한 데이터 모델."""
    title: str = Field(..., description="뉴스 제목")
    url: str = Field(..., description="뉴스 원본 URL")
    author: Optional[str] = Field(None, description="작성자")
    short_content: Optional[str] = Field(None, description="본문 요약")
    published_at: Optional[datetime] = Field(None, description="발행일")
    reactions_count: int = Field(0, description="반응 수")
    replies_count: int = Field(0, description="댓글 수")
    html: Optional[str] = Field(None, description="원본 JSON 응답 데이터")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="수집 타임스탬프 (UTC)")
