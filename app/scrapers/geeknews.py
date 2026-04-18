"""
GeekNewsScraper 모듈

이 모듈은 IT 뉴스 커뮤니티인 GeekNews(https://news.hada.io) 사이트의 데이터를 수집합니다.
BaseScraper를 상속받아 GeekNews 고유의 페이지 구조와 파싱 규칙을 구현합니다.

주요 특징:
1. 하이브리드 수집 전략: 상세 페이지의 댓글을 수집할 때, 구조화된 데이터인 JSON-LD를 최우선으로 
   파싱하고, 데이터가 없거나 불완전한 경우 최신 HTML 셀렉터를 활용한 Fallback 로직을 가동합니다.
2. 재귀적 댓글 추출: JSON-LD 내의 중첩된(Nested) 댓글 구조를 재귀적으로 순회하여 대댓글까지 누락 없이 확보합니다.
3. 보안 및 우회: curl-cffi의 Impersonate 기능을 사용하여 Chrome 브라우저의 실제 요청과 동일한 핑거프린트를 생성, 봇 탐지를 회피합니다.
4. 유연한 URL 처리: 날짜 기반 과거글(Past), 페이지 번호, 개별 토픽 URL 등 다양한 경로를 지원합니다.
"""
import json
import logging
import re
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
from curl_cffi import requests

from app.scrapers.base import BaseScraper
from app.models import NewsItem, CommentItem

# 로깅 설정
logger = logging.getLogger("GeekNewsScraper")

class GeekNewsScraper(BaseScraper):
    """
    GeekNews 사이트 전용 스크래퍼 클래스.
    
    속성:
        base_url (str): GeekNews의 기본 도메인
        collection_name (str): MongoDB 내 저장될 컬렉션 이름 ('geeknews_pages')
    """
    
    def __init__(self):
        """GeekNewsScraper 초기화 및 소스 정보 설정."""
        super().__init__(source_name="GeekNews")
        self.base_url = "https://news.hada.io"
        self.collection_name = "geeknews_pages"

    def _do_fetch(self, url: str) -> str:
        """
        GeekNews 전용 HTTP 요청 구현. curl-cffi를 사용하여 브라우저 환경을 모사합니다.
        
        Args:
            url (str): 수집할 대상 URL
            
        Returns:
            str: 응답 HTML 문자열. 요청 실패 시 빈 문자열 반환.
        """
        try:
            # Chrome 브라우저의 핑거프린트를 사용하여 요청
            response = requests.get(url, impersonate="chrome", timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"GeekNews network error ({url}): {e}")
            return ""

    def parse(self, html: str, db_connection=None) -> List[NewsItem]:
        """
        GeekNews 리스트 페이지를 파싱하여 뉴스 항목 리스트를 생성합니다.
        
        파싱 과정:
        1. 'div.topic_row' 단위로 개별 뉴스 항목 식별
        2. 제목, 본문 링크, 상세 페이지(댓글용) 링크 추출
        3. MongoDB 연결 시 기존 URL 존재 여부를 확인하여 중복 수집 방지
        4. 상세 페이지(fetch_comments)를 방문하여 본문 내용과 전체 댓글 확보
        
        Args:
            html (str): 리스트 페이지 HTML
            db_connection (MongoClient, optional): 중복 확인을 위한 DB 연결
            
        Returns:
            List[NewsItem]: 수집 및 상세 정보가 보완된 뉴스 항목 리스트
        """
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        # 중복 체크를 위한 컬렉션 설정
        collection = None
        if db_connection is not None:
            collection = db_connection["crawler_db"][self.collection_name]

        rows = soup.select('div.topic_row')
        for row in rows:
            try:
                # 기사 기본 정보 추출
                title_element = row.select_one('.topictitle a')
                if not title_element: continue
                
                title = title_element.get_text(strip=True)
                url = title_element.get('href', '')
                if not (title and url): continue

                # 상대 경로를 절대 경로로 변환
                if url and not url.startswith('http'):
                    url = f"https://news.hada.io/{url.lstrip('/')}"
                
                # 상세 페이지(댓글/본문) 수집을 위한 토픽 URL 추출 (topic?id=... 패턴 매칭)
                topic_element = row.select_one('.topicinfo a[href*="topic?id="]')
                topic_url = None
                if topic_element:
                    href = topic_element.get('href', '')
                    topic_url = href if href.startswith('http') else f"https://news.hada.io/{href.lstrip('/')}"
                
                # DB 중복 체크 로직
                existing_item = collection.find_one({"_id": url}) if collection is not None else None
                
                content = None
                comments = []

                if not existing_item:
                    # 신규 데이터인 경우 상세 페이지 정보 수집
                    if topic_url:
                        logger.info(f"Processing new item: {title}")
                        content, comments = self.fetch_comments(topic_url)
                        
                        # 디버그 모드일 때만 데이터 샘플 출력
                        logger.debug(f"Content snippet: {content[:100] if content else 'None'}...")
                        logger.debug(f"Comments count: {len(comments)}")
                    else:
                        logger.warning(f"No topic link found for item: {title}")
                else:
                    logger.debug(f"Skipping duplicate: {title}")
                    continue

                items.append(NewsItem(
                    title=title,
                    url=url,
                    source=self.source_name,
                    content=content,
                    comments=comments
                ))
            except Exception as e:
                logger.error(f"Error parsing news row: {e}")
                continue
                
        return items

    def fetch_comments(self, url: str) -> Tuple[Optional[str], List[CommentItem]]:
        """
        개별 뉴스 상세 페이지에서 본문과 댓글 리스트를 추출합니다.
        
        추출 전략:
        1. 본문: '.topic_contents' 클래스 내에서 텍스트 추출 (불필요한 광고/관련글 제거)
        2. 댓글(우선): JSON-LD 스크립트를 찾아 재귀적으로 전체 댓글 트리 파싱
        3. 댓글(Fallback): JSON-LD 부재 시 '.comment_thread' HTML 구조를 직접 파싱
        
        Args:
            url (str): 상세 페이지 URL
            
        Returns:
            Tuple[Optional[str], List[CommentItem]]: 기사 본문과 댓글 객체 리스트
        """
        try:
            html = self.fetch(url)
            if not html: return None, []
            
            soup = BeautifulSoup(html, "html.parser")
            content = None
            comments = []

            # 0. 기사 본문(Content) 추출
            content_el = soup.select_one('.topic_contents')
            if content_el:
                # 관련글 링크, 광고성 요소 제거
                for unwanted in content_el.select('.related-topics, .adsense'):
                    unwanted.decompose()
                content = content_el.get_text(separator="\n", strip=True)

            # 1. JSON-LD 시도 (데이터 정합성이 가장 높음)
            json_ld_script = soup.find('script', type='application/ld+json')
            if json_ld_script:
                try:
                    data = json.loads(json_ld_script.string)
                    comment_data_list = data.get('comment', [])
                    if isinstance(comment_data_list, dict): 
                        comment_data_list = [comment_data_list]
                    
                    for comment_data in comment_data_list:
                        self._process_json_ld_comment(comment_data, comments)
                    
                    if comments:
                        logger.debug(f"Collected {len(comments)} comments via JSON-LD from {url}")
                except Exception as je:
                    logger.warning(f"JSON-LD parsing failed for {url}: {je}")

            # 2. HTML Fallback (JSON-LD가 없거나 댓글이 비어있는 경우)
            if not comments:
                comment_threads = soup.select('.comment_thread')
                for thread in comment_threads:
                    row = thread.select_one('.comment_row')
                    if not row: continue

                    # 작성자 정보 추출 (.commentinfo 하위의 사용자 링크)
                    author_el = row.select_one('.commentinfo a[href^="/@"]')
                    author = author_el.get_text(strip=True) if author_el else "Unknown"

                    # 댓글 내용 추출 (.comment_contents)
                    text_el = row.select_one('.comment_contents')
                    text = text_el.get_text(separator="\n", strip=True) if text_el else ""

                    if text:
                        comments.append(CommentItem(
                            comment_id=f"{author}_{hash(text)}",
                            author=author,
                            content=text
                        ))
                if comments:
                    logger.debug(f"Collected {len(comments)} comments via HTML Fallback from {url}")
            
            return content, comments
        except Exception as e:
            logger.error(f"Critical error fetching/parsing detail page ({url}): {e}")
            return None, []

    def _process_json_ld_comment(self, comment_data: dict, comments: List[CommentItem]):
        """
        JSON-LD 형식의 댓글 데이터를 재귀적으로 처리하여 CommentItem 리스트에 추가합니다.
        
        Args:
            comment_data (dict): JSON-LD 내의 단일 댓글 데이터 객체
            comments (List[CommentItem]): 결과를 누적할 댓글 리스트
        """
        if not isinstance(comment_data, dict): return
        
        text = comment_data.get('text')
        if text:
            url = comment_data.get('url', '')
            author_data = comment_data.get('author', {})
            author = author_data.get('name') if isinstance(author_data, dict) else "Unknown"
            
            comments.append(CommentItem(
                comment_id=url.split('id=')[-1] if 'id=' in url else f"ld_{hash(text)}",
                author=author or "Unknown",
                content=text
            ))
            
        # 하위 댓글(대댓글) 재귀 처리
        children = comment_data.get('comment', [])
        if isinstance(children, dict): 
            children = [children]
        
        for child in children:
            self._process_json_ld_comment(child, comments)

    def _get_backfill_url(self, base_url: str, date_str: str, page: Optional[int] = None) -> str:
        """
        GeekNews 전용 백필 URL을 생성합니다.
        
        날짜(YYYY-MM-DD), 댓글 모아보기(comments), 페이지 번호 등 
        다양한 백필 시나리오에 맞는 엔드포인트를 반환합니다.
        
        Args:
            base_url (str): 베이스 URL
            date_str (str): 백필 타겟 식별자 (날짜 또는 특수 명령)
            page (int, optional): 타겟 페이지 번호
            
        Returns:
            str: 구성된 백필 타겟 URL
        """
        base = base_url.rstrip('/')
        # 1. 댓글 모아보기 수집
        if date_str == 'comments':
            return f"{base}/comments?page={page}" if page else f"{base}/comments"
        
        # 2. 특정 날짜(과거글) 수집 (YYYY-MM-DD 패턴)
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            url = f"{base}/past?day={date_str}"
            return f"{url}&page={page}" if page else url
        
        # 3. 단순 페이지 번호 기반 수집
        if date_str.isdigit():
            p = int(date_str)
            # 메인 페이지는 5페이지까지만 지원, 그 이상은 과거글(past) 섹션에서 조회
            return f"{base}/?page={p}" if p <= 5 else f"{base}/past?page={p}"
            
        return f"{base}/"
