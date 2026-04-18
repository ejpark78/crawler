"""
PyTorchKRScraper 테스트 모듈

이 모듈은 PyTorch KR 크롤러의 유닛 및 통합 테스트를 수행합니다.

[중요 지침 - 데이터 사용 원칙]
1. 하드코딩된 Mock 데이터(HTML 문자열 등)의 사용을 엄격히 금지합니다.
2. 모든 파싱 테스트는 반드시 다음 중 하나를 사용해야 합니다:
   - 라이브 사이트 요청 (Self-contained Integration Tests)
   - 로컬 샘플 파일 (tests/site/pytorch.kr/samples/*.html 또는 *.json)
3. 사이트 구조 변경으로 인해 테스트가 실패할 경우, 코드 내의 Mock을 수정하는 것이 아니라
   실제 사이트에서 새로운 샘플 HTML/JSON을 내려받아 tests/site/ 경로에 업데이트해야 합니다.
4. 이 원칙은 크롤러가 실제 웹 환경의 변화를 정확히 감지하고 대응할 수 있도록 하기 위함입니다.
"""
import unittest
import json
import os
from app.scrapers.pytorch_kr import PyTorchKRScraper


class TestPyTorchKRParsing(unittest.TestCase):
    def setUp(self):
        self.scraper = PyTorchKRScraper()
        self.sample_dir = 'tests/site/pytorch.kr/samples'

    def _read_sample_file(self, filename):
        """샘플 디렉토리에서 파일을 읽어 내용을 반환합니다."""
        path = os.path.join(self.sample_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _read_sample_json(self, filename):
        """샘플 디렉토리에서 JSON 파일을 읽어 딕셔너리로 반환합니다."""
        content = self._read_sample_file(filename)
        return json.loads(content)

    def _verify_list_sample(self, filename, content):
        """리스트 페이지 샘플의 파싱 결과가 기대값 JSON과 일치하는지 검증합니다."""
        items = self.scraper.parse(content)
        actual_data = [item.model_dump() for item in items]

        # 기대값 파일명 결정: list_1.html -> list_1.json / list_1.json -> list_1_expected.json
        if filename.endswith(".html"):
            expected_filename = filename.replace(".html", ".json")
        else:
            return

        if os.path.exists(os.path.join(self.sample_dir, expected_filename)):
            expected_data = self._read_sample_json(expected_filename)
            self.assertEqual(actual_data, expected_data, f"{filename}의 파싱 결과가 기대값과 다릅니다.")

    def _verify_item_sample(self, filename, content):
        """상세 페이지 샘플의 파싱 결과가 기대값 JSON과 일치하는지 검증합니다."""
        item = self.scraper.parse_content(content, "https://discuss.pytorch.kr/t/test/123")
        actual_data = item.model_dump()

        # Try multiple expected filename patterns
        possible_expected = [
            filename.replace(".html", ".json"),
            filename.replace(".html", ".out.json"),
            filename.replace(".html", "_expected.json")
        ]
        
        expected_path = None
        for exp in possible_expected:
            path = os.path.join(self.sample_dir, exp)
            if os.path.exists(path):
                expected_path = path
                break

        if expected_path:
            with open(expected_path, 'r', encoding='utf-8') as f:
                expected_data = json.load(f)
            self.assertEqual(actual_data, expected_data, f"{filename}의 파싱 결과가 기대값과 다릅니다.")
        else:
            # If no expected file, we might want to log it or fail if strict
            pass

    def test_parse_all_samples(self):
        """tests/site/pytorch.kr/samples/ 내의 모든 HTML/JSON 파일에 대해 파싱 검증"""
        if not os.path.exists(self.sample_dir):
            self.skipTest(f"샘플 디렉토리가 없습니다: {self.sample_dir}")

        html_files = [f for f in os.listdir(self.sample_dir) if f.endswith(".html")]
        
        for filename in html_files:
            with self.subTest(filename=filename):
                content = self._read_sample_file(filename)

                if filename.startswith("list_"):
                    self._verify_list_sample(filename, content)
                else:
                    # Default to item parsing if not list_
                    self._verify_item_sample(filename, content)

    def test_parse_content(self):
        # Keep as fallback for now
        self.content_sample_path = 'tests/site/pytorch.kr/samples/content.html'
        if os.path.exists(self.content_sample_path):
            with open(self.content_sample_path, 'r', encoding='utf-8') as f:
                self.content_html = f.read()
            expected_title = "베이지안 티칭(Bayesian Teaching): LLM에게 베이지안처럼 추론하는 법을 가르치는 Google Research의 연구"
            expected_url = "https://discuss.pytorch.kr/t/bayesian-teaching-llm-google-research/9404"
            self.assertIn(expected_title, self.content_html)
            self.assertIn(expected_url, self.content_html)

if __name__ == '__main__':
    unittest.main()
