import pytest
import os
import random
from typing import List
from app.scrapers.geeknews import GeekNewsScraper
from app.models import NewsItem

def test_get_backfill_url_combinations():
    """
    다양한 입력 조합에 대해 올바른 백필 URL이 생성되는지 테스트합니다.
    """
    scraper = GeekNewsScraper()
    base = "https://news.hada.io"

    # 1. 기본 페이지 (1~5)
    assert scraper._get_backfill_url(base, "1") == f"{base}/?page=1"
    assert scraper._get_backfill_url(base, "5") == f"{base}/?page=5"

    # 2. 과거 페이지 (6+)
    assert scraper._get_backfill_url(base, "6") == f"{base}/past?page=6"
    assert scraper._get_backfill_url(base, "100") == f"{base}/past?page=100"

    # 3. 특정 날짜
    assert scraper._get_backfill_url(base, "2026-04-15") == f"{base}/past?day=2026-04-15"

    # 4. 특정 날짜 + 페이지
    assert scraper._get_backfill_url(base, "2026-04-15", page=2) == f"{base}/past?day=2026-04-15&page=2"

    # 5. 최신 댓글 리스트
    assert scraper._get_backfill_url(base, "comments", page=22) == f"{base}/comments?page=22"

    # 6. 댓글 리스트 호출 시 페이지 누락 시 에러 확인
    with pytest.raises(ValueError, match="Page number is required"):
        scraper._get_backfill_url(base, "comments")

def test_fetch_comments_with_mock(scraper, mocker):
    """
    fetch_comments의 파싱 로직을 검증합니다.
    JSON-LD와 HTML 요소가 결합되어 댓글이 정상적으로 추출되는지 확인합니다.
    """
    mock_html = """
    <html>
        <script type="application/ld+json">
        {
            "@context": "http://schema.org",
            "@type": "DiscussionForumPosting",
            "comment": [
                {
                    "url": "https://news.hada.io/topic?id=123&cid=100",
                    "author": {"name": "User1"},
                    "text": "First comment",
                    "comment": [
                        {
                            "url": "https://news.hada.io/topic?id=123&cid=101",
                            "author": {"name": "User2"},
                            "text": "Reply to first"
                        }
                    ]
                },
                {
                    "url": "https://news.hada.io/topic?id=123&cid=102",
                    "author": {"name": "User3"},
                    "text": "Second comment"
                }
            ]
        }
        </script>
        <body>
            <div id="cid100" class="comment">
                <span class="comment_contents">First comment <b>Bold</b></span>
            </div>
            <div id="cid101" class="comment">
                <span class="comment_contents">Reply to first <i>Italic</i></span>
            </div>
            <div id="cid102" class="comment">
                <span class="comment_contents">Second comment <a href="#">Link</a></span>
            </div>
        </body>
    </html>
    """
    scraper.fetch = mocker.Mock(return_value=mock_html)

    comments = scraper.fetch_comments("https://news.hada.io/topic?id=123")

    assert len(comments) == 3

    # User1 (Root)
    c1 = next(c for c in comments if c.comment_id == "100")
    assert c1.author == "User1"
    assert c1.content == "First comment"
    assert "<b>Bold</b>" in c1.raw_html

    # User2 (Child)
    c2 = next(c for c in comments if c.comment_id == "101")
    assert c2.author == "User2"
    assert c2.content == "Reply to first"
    assert "<i>Italic</i>" in c2.raw_html

    # User3 (Root)
    c3 = next(c for c in comments if c.comment_id == "102")
    assert c3.author == "User3"
    assert c3.content == "Second comment"
    assert "<a href=\"#\">Link</a>" in c3.raw_html

def test_fetch_comments_no_json_ld(scraper, mocker):
    """JSON-LD가 없는 경우 빈 리스트를 반환하는지 확인합니다."""
    scraper.fetch = mocker.Mock(return_value="<html><body>No JSON here</body></html>")
    comments = scraper.fetch_comments("https://news.hada.io/topic?id=123")
    assert comments == []

def test_fetch_comments_invalid_json(scraper, mocker):
    """JSON-LD 형식이 잘못된 경우 빈 리스트를 반환하는지 확인합니다."""
    mock_html = "<html><script type='application/ld+json'>{ invalid json }</script></html>"
    scraper.fetch = mocker.Mock(return_value=mock_html)
    comments = scraper.fetch_comments("https://news.hada.io/topic?id=123")
    assert comments == []

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
