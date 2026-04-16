import pytest
import os
import random
from typing import List
from app.scrapers.geeknews import GeekNewsScraper
from app.models import NewsItem

class SampleCollector:
    """
    GeekNews의 랜덤한 페이지를 수집하고 검증하는 헬퍼 클래스
    """
    def __init__(self, scraper: GeekNewsScraper):
        self.scraper = scraper
        self.sample_dir = "tests/site/geeknews/samples"
        os.makedirs(self.sample_dir, exist_ok=True)

    def collect_random_sample(self, page: int) -> bool:
        """
        특정 페이지를 수집하고, 파싱이 가능할 때만 저장합니다.
        """
        url = self.scraper._get_backfill_url("https://news.hada.io/", str(page))
        file_path = os.path.join(self.sample_dir, f"sample_{page}.html")
        json_path = os.path.join(self.sample_dir, f"sample_{page}.json")

        print(f"\nCollecting sample from page {page}: {url}")

        try:
            # 1. HTML 수집
            html = self.scraper.fetch(url)

            # 2. 즉시 파싱 검증 (데이터가 실제로 존재하는지 확인)
            items = self.scraper.parse(html)
            if not items:
                print(f"Warning: No news items found in page {page}. Skipping save.")
                return False

            print(f"Verified: {len(items)} items found. Saving sample and JSON...")

            # 3. HTML 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)

            # 4. 파싱 결과 JSON 저장 (TDD 기대 결과값으로 활용)
            self.scraper.save_to_json(items, json_path)

            os.chmod(file_path, 0o666)
            if os.path.exists(json_path):
                os.chmod(json_path, 0o666)
            return True
        except Exception as e:
            print(f"Failed to collect sample from page {page}: {e}")
            return False

@pytest.fixture
def scraper():
    return GeekNewsScraper()

@pytest.fixture
def collector(scraper):
    return SampleCollector(scraper)

def test_collect_and_verify_random_pages(collector):
    """
    랜덤한 페이지들을 수집하여 봇 차단을 피하고 정상적인 HTML을 확보하는 테스트
    """
    # 1~1000 페이지 중 5개를 랜덤하게 선택하여 시도
    pages = random.sample(range(1, 1001), 5)
    success_count = 0

    for page in pages:
        if collector.collect_random_sample(page):
            success_count += 1

    # 최소 한 개 이상의 페이지라도 성공적으로 수집되었는지 확인
    # (완전 차단 상태라면 0이 될 것이며, 이는 테스트 실패로 이어짐)
    assert success_count > 0, "Failed to collect any valid samples from random pages. Possible bot-block."

def test_parse_existing_samples(scraper):
    """
    저장된 모든 샘플 파일들을 사용하여 파싱 로직의 회귀 테스트를 수행합니다.
    """
    sample_dir = "tests/site/geeknews/samples"
    if not os.path.exists(sample_dir):
        pytest.skip("Sample directory does not exist.")

    sample_files = [f for f in os.listdir(sample_dir) if f.endswith(".html")]
    if not sample_files:
        pytest.skip("No sample HTML files found.")

    for file_name in sample_files:
        if file_name == "comment_sample.html":
            continue
        file_path = os.path.join(sample_dir, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        items = scraper.parse(html_content)

        # 저장된 샘플은 이미 검증된 것이어야 하므로, 파싱 결과가 반드시 있어야 함
        assert len(items) > 0, f"Failed to parse items from existing sample: {file_name}"

        for item in items:
            assert item.title, f"Title missing in {file_name}"
            assert item.url, f"URL missing in {file_name}"
            assert item.url.startswith("http"), f"Invalid URL in {file_name}: {item.url}"
            assert item.source == "GeekNews"

if __name__ == "__main__":
    # 직접 실행 시 pytest를 통해 테스트 수행
    import pytest
    pytest.main([__file__])
