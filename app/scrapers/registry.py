"""
Scraper Registry 모듈

이 모듈은 프로젝트 내에서 사용 가능한 모든 스크래퍼 클래스를 중앙 관리합니다.
새로운 뉴스 소스를 추가할 때, 해당 스크래퍼 클래스를 구현한 후 이 레지스트리에 등록해야 합니다.

등록된 스크래퍼는 'SOURCE' 인자를 통해 동적으로 선택되며, 이는 수집 데이터의 MongoDB 데이터베이스 이름을 결정하는 기준이 됩니다.
"""
from app.scrapers.geeknews import GeekNewsScraper

# 소스 이름(Source Name)과 스크래퍼 클래스(Class)의 매핑 정보
# Key: CLI 또는 DAG에서 사용될 소스 식별자 (Case-Sensitive)
# Value: BaseScraper를 상속받아 구현된 스크래퍼 클래스
SCRAPER_REGISTRY = {
    "GeekNews": GeekNewsScraper,
}
