"""
Crawler Data Models

이 모듈은 크롤러 프로젝트 전반에서 사용되는 핵심 데이터 구조를 Pydantic 모델로 정의합니다.
수집된 데이터의 유효성 검사, 타입 안전성 보장 및 JSON 직렬화(Serialization)를 전담합니다.

주요 모델:
1. NewsItem: 뉴스 기사의 메인 엔티티. 제목, URL, 본문, 수집된 댓글 리스트 및 원본 HTML을 포함합니다.
2. CommentItem: 뉴스 기사에 달린 개별 댓글 엔티티. 작성자, 내용, 고유 식별자를 관리합니다.

디자인 원칙:
- 데이터 정규화: 다양한 소스에서 수집된 데이터를 일관된 포맷으로 변환하여 분석 및 DB 처리를 용이하게 합니다.
- 유효성 강제: 필수 필드(제목, URL 등)의 누락을 수집 단계에서 차단하여 데이터 품질을 보장합니다.
- UTC 기준: 모든 시간 데이터는 UTC(ISO 8601) 기준으로 관리하여 글로벌 확장성을 확보합니다.
"""
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, List

class CommentItem(BaseModel):
    """
    개별 댓글 정보를 담는 데이터 모델.
    
    속성:
        comment_id (str): 댓글의 고유 식별자. (사이트 제공 ID 또는 생성된 해시)
        author (str): 댓글 작성자의 이름 또는 닉네임.
        content (str): 정규화된 댓글 본문 텍스트.
        raw_html (Optional[str]): 파싱 전 댓글 영역의 원문 HTML (필요 시 저장).
        created_at (Optional[datetime]): 댓글이 작성된 일시.
    """
    comment_id: str = Field(..., description="댓글 고유 식별자 (ID)")
    author: str = Field(..., description="작성자")
    content: str = Field(..., description="댓글 내용")
    raw_html: Optional[str] = Field(None, description="댓글 원문 HTML (innerhtml)")
    created_at: Optional[datetime] = Field(None, description="작성 일시")

class NewsItem(BaseModel):
    """
    수집된 뉴스 기사의 전체 정보를 담는 표준 데이터 모델.
    
    속성:
        title (str): 뉴스 기사 제목.
        url (str): 뉴스 원문 주소. MongoDB의 Primary Key(_id)로 활용됩니다.
        source (str): 뉴스 출처 소스명 (예: 'GeekNews').
        published_at (Optional[datetime]): 기사가 사이트에 게시된 일시.
        content (Optional[str]): 정규화된 기사 본문 내용.
        comments (List[CommentItem]): 해당 기사에 달린 댓글 객체들의 리스트.
        html (Optional[str]): 수집 당시의 목록 또는 상세 페이지 전체 원문 HTML.
        created_at (datetime): 데이터가 시스템에 수집된 일시 (UTC).
    """
    title: str = Field(..., description="뉴스 제목")
    url: str = Field(..., description="뉴스 원문 URL (PK로 사용)")
    source: str = Field(..., description="뉴스 출처")
    published_at: Optional[datetime] = Field(None, description="발행 일시")
    content: Optional[str] = Field(None, description="본문 내용")
    comments: Optional[List[CommentItem]] = Field(default_factory=list, description="수집된 댓글 리스트")
    html: Optional[str] = Field(None, description="페이지 원문 HTML")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        description="수집 일시 (UTC)"
    )
