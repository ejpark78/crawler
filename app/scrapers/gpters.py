import json
import logging
import requests
from typing import List, Optional, Tuple
from datetime import datetime
from app.scrapers.base import BaseScraper
from app.models import GPTERSNews

logger = logging.getLogger("GPTERSScraper")

class GPTERSScraper(BaseScraper):
    """지피터스 뉴스 스크래퍼 (GraphQL 기반)"""

    def __init__(self):
        super().__init__(source_name="GPTERS")
        self.base_url = "https://www.gpters.org/news"
        self.graphql_url = "https://api.bettermode.com/graphql"
        self.space_slug = "news"

    def _do_fetch(self, url: str) -> str:
        """GraphQL API를 호출하여 데이터를 가져옵니다."""
        # Note: 실제 운영 시에는 유효한 Access Token이 필요할 수 있습니다.
        # 현재는 분석된 쿼리 구조를 바탕으로 요청을 구성합니다.
        
        query = """
        query getNewsFeed($spaceSlug: String!, $limit: Int!, $after: String) { 
          posts(spaceSlug: $spaceSlug, limit: $limit, after: $after) { 
            nodes {
              id 
              title 
              slug 
              createdAt 
              author { 
                name 
              } 
              reactionsCount 
              repliesCount 
              shortContent
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          } 
        }
        """
        variables = {
            "spaceSlug": self.space_slug,
            "limit": 20,
            "after": None
        }
        
        payload = {
            "operationName": "getNewsFeed",
            "query": query,
            "variables": variables
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            # "Authorization": "Bearer <TOKEN>" # 실제 토큰 필요시 추가
        }

        try:
            # StealthyFetcher 대신 직접 requests 사용 (GraphQL 특성상)
            response = requests.post(self.graphql_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"GraphQL request failed: {e}")
            return json.dumps({"data": {"posts": {"nodes": []}}})

    def parse(self, json_data: str, db_connection=None) -> List[GPTERSNews]:
        """GraphQL 응답 JSON을 파싱하여 모델 객체 리스트로 변환합니다."""
        try:
            data = json.loads(json_data)
            posts = data.get("data", {}).get("posts", {}).get("nodes", [])
            
            results = []
            for post in posts:
                slug = post.get("slug")
                post_id = post.get("id")
                url = f"https://www.gpters.org/news/post/{slug}-{post_id}"
                
                # 날짜 변환
                published_at = None
                if post.get("createdAt"):
                    try:
                        published_at = datetime.fromisoformat(post.get("createdAt").replace("Z", "+00:00"))
                    except Exception:
                        pass

                item = GPTERSNews(
                    title=post.get("title", "No Title"),
                    url=url,
                    author=post.get("author", {}).get("name") if post.get("author") else None,
                    short_content=post.get("shortContent"),
                    published_at=published_at,
                    reactions_count=post.get("reactionsCount", 0),
                    replies_count=post.get("repliesCount", 0),
                    html=json_data # 원본 JSON을 html 필드에 저장
                )
                results.append(item)
            return results
        except Exception as e:
            logger.error(f"Failed to parse GPTERS JSON: {e}")
            return []

    def run(self, db_connection, backfill_date: Optional[str] = None, page: Optional[int] = None) -> Tuple[List[GPTERSNews], str]:
        """실행 및 데이터 수집"""
        json_response = self._do_fetch(self.base_url)
        items = self.parse(json_response, db_connection=db_connection)
        return items, json_response
