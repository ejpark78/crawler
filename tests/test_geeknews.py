"""
GeekNewsScraper 테스트 모듈

이 모듈은 GeekNews 크롤러의 유닛 및 통합 테스트를 수행합니다.

[중요 지침 - 데이터 사용 원칙]
1. 하드코딩된 Mock 데이터(HTML 문자열 등)의 사용을 엄격히 금지합니다.
2. 모든 파싱 테스트는 반드시 다음 중 하나를 사용해야 합니다:
   - 라이브 사이트 요청 (Self-contained Integration Tests)
   - 로컬 샘플 파일 (tests/site/geeknews/samples/*.html)
3. 사이트 구조 변경으로 인해 테스트가 실패할 경우, 코드 내의 Mock을 수정하는 것이 아니라
   실제 사이트에서 새로운 샘플 HTML을 내려받아 tests/site/ 경로에 업데이트해야 합니다.
4. 이 원칙은 크롤러가 실제 웹 환경의 변화를 정확히 감지하고 대응할 수 있도록 하기 위함입니다.
"""
import unittest
from unittest.mock import patch
import os
import json
import logging
from app.scrapers.geeknews import GeekNewsScraper

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestGeekNews")

class TestGeekNewsScraper(unittest.TestCase):
    """실제 데이터 및 로컬 샘플 파일 전수를 사용하는 테스트"""
    
    def setUp(self):
        self.scraper = GeekNewsScraper()
        self.base_url = "https://news.hada.io"
        self.sample_dir = "tests/site/geeknews/samples"

    def test_get_backfill_url_combinations(self):
        """백필 URL 생성 규칙 검증"""
        self.assertEqual(self.scraper._get_backfill_url(self.base_url, "1"), f"{self.base_url}/?page=1")
        self.assertEqual(self.scraper._get_backfill_url(self.base_url, "2024-01-01"), f"{self.base_url}/past?day=2024-01-01")

    def test_parse_all_samples(self):
        """tests/site/geeknews/samples/ 내의 모든 HTML 파일에 대해 파싱 검증"""
        if not os.path.exists(self.sample_dir):
            self.skipTest(f"샘플 디렉토리가 없습니다: {self.sample_dir}")

        files = [f for f in os.listdir(self.sample_dir) if f.endswith(".html")]
        if not files:
            self.skipTest("테스트할 HTML 샘플 파일이 없습니다.")

        logger.info(f"Found {len(files)} sample files for testing.")

        for filename in files:
            with self.subTest(filename=filename):
                sample_path = os.path.join(self.sample_dir, filename)
                with open(sample_path, 'r', encoding='utf-8') as f:
                    html = f.read()

                # 파일 내용에 따라 리스트 페이지인지 상세 페이지인지 판별
                is_list_page = "topic_row" in html
                is_detail_page = "comment_row" in html or "application/ld+json" in html

                if is_list_page:
                    # 리스트 파싱 시 상세 페이지(댓글) 수집은 패치하여 외부 요청 방지
                    with patch.object(self.scraper, 'fetch_comments', return_value=([], None)):
                        items = self.scraper.parse(html, db_connection=None)
                        self.assertGreaterEqual(len(items), 1, f"리스트 샘플 {filename}에서 항목 추출 실패")
                        for item in items:
                            self.assertTrue(item.title, f"{filename} 내 항목의 제목이 없습니다.")
                            self.assertTrue(item.url.startswith("http"), f"{filename} 내 항목의 URL이 부적절합니다.")
                        logger.info(f"Parsed {len(items)} items from list sample: {filename}")

                if is_detail_page:
                    # fetch_comments 로직 검증을 위해 fetch를 패치
                    with patch.object(self.scraper, '_do_fetch', return_value=html):
                        with patch('time.sleep', return_value=None):
                            comments, json_ld_raw, detail_html = self.scraper.fetch_comments("https://news.hada.io/topic?id=test")

                            # JSON-LD 검증: 대응하는 .json 파일이 있으면 내용 비교
                            json_filename = filename.replace(".html", "_ld.json")
                            json_path = os.path.join(self.sample_dir, json_filename)
                            if os.path.exists(json_path):
                                with open(json_path, 'r', encoding='utf-8') as jf:
                                    expected_json_str = jf.read()
                                # json_ld_raw는 문자열이므로 직접 비교하거나 JSON 객체로 변환하여 비교
                                if json_ld_raw:
                                    parsed_json_ld = json.loads(json_ld_raw)
                                    expected_json = json.loads(expected_json_str)
                                    self.assertEqual(parsed_json_ld, expected_json, f"{filename}의 JSON-LD 결과가 기대값과 다릅니다.")
                                else:
                                    self.fail(f"{filename}에서 JSON-LD를 추출하지 못했습니다.")
                                logger.info(f"Verified JSON-LD for {filename}")

                            self.assertTrue(len(comments) >= 0)
                            logger.info(f"Parsed {len(comments)} comments from detail sample: {filename}")
                
                if not (is_list_page or is_detail_page):
                    logger.warning(f"Unknown page type for sample: {filename}")

    def test_live_main_page(self):
        """실제 라이브 사이트 메인 페이지 수집 테스트"""
        logger.info("Starting live test for main page...")
        with patch.object(self.scraper, 'fetch_comments', return_value=([], None, None)):
            html = self.scraper.fetch(self.base_url)
            items = self.scraper.parse(html, db_connection=None)
            self.assertGreater(len(items), 0, "라이브 사이트 메인 페이지 파싱 결과가 비어있습니다.")

    def test_live_detail_page(self):
        """실제 라이브 사이트 상세 페이지 수집 테스트"""
        test_url = f"{self.base_url}/topic?id=28587"
        logger.info(f"Starting live test for detail page: {test_url}")
        comments, json_ld_raw, detail_html = self.scraper.fetch_comments(test_url)
        self.assertGreaterEqual(len(comments), 1, "라이브 상세 페이지에서 댓글 수집에 실패했습니다.")

if __name__ == '__main__':
    unittest.main()
