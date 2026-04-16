from app.scrapers.geeknews import GeekNewsScraper

# 소스 이름과 스크래퍼 클래스의 매핑 정보
# 신규 소스 추가 시 이곳에 등록하여 DAG에서 동적으로 사용할 수 있게 함
SCRAPER_REGISTRY = {
    "GeekNews": GeekNewsScraper,
}
