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
        self.root_sample_dir = 'tests/site/pytorch.kr'

    def _read_sample_file(self, filename, dir_path=None):
        """지정된 디렉토리에서 파일을 읽어 내용을 반환합니다."""
        if dir_path is None:
            dir_path = self.sample_dir
        path = os.path.join(dir_path, filename)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _read_sample_json(self, filename, dir_path=None):
        """지정된 디렉토리에서 JSON 파일을 읽어 딕셔너리로 반환합니다."""
        content = self._read_sample_file(filename, dir_path)
        return json.loads(content)

    def _verify_list_sample(self, filename, content):
        """리스트 페이지 샘플의 파싱 결과가 기대값 JSON과 일치하는지 검증합니다."""
        items = self.scraper.parse(content)
        self.assertTrue(len(items) > 0, f"{filename}에서 아이템을 추출하지 못했습니다.")
        
        actual_data = [item.model_dump(mode='json') for item in items]

        # 기대값 파일명 결정
        if filename.endswith(".html"):
            expected_filename = filename.replace(".html", ".json")
        elif filename == "list.json":
            # root의 list.json인 경우 별도의 기대값 파일이 없을 수 있으므로 기본 검증만 수행
            return
        else:
            return

        if os.path.exists(os.path.join(self.sample_dir, expected_filename)):
            expected_data = self._read_sample_json(expected_filename)
            
            # Remove dynamic fields for comparison
            for data_list in [actual_data, expected_data]:
                for item in data_list:
                    for key in ["created_at", "comments", "html"]:
                        item.pop(key, None)
            
            self.assertEqual(actual_data, expected_data, f"{filename}의 파싱 결과가 기대값과 다릅니다.")

    def _verify_item_sample(self, filename, content):
        """상세 페이지 샘플의 파싱 결과가 기대값 JSON과 일치하는지 검증합니다."""
        # 파일명을 기반으로 URL 생성 (TopicID.html -> /t/slug/ID)
        topic_id = filename.split('.')[0]
        url = f"https://discuss.pytorch.kr/t/sample/{topic_id}"
        
        item = self.scraper.parse_content(content, url)
        actual_data = item.model_dump(mode='json')

        # 기본 필드 존재 여부 확인
        self.assertTrue(len(item.title) > 0, f"{filename}: 제목이 추출되지 않았습니다.")
        self.assertTrue(len(item.content) > 0, f"{filename}: 본문이 추출되지 않았습니다.")
        self.assertIsNotNone(item.published_at, f"{filename}: 발행일이 추출되지 않았습니다.")

        # Try multiple expected filename patterns
        possible_expected = [
            filename.replace(".html", ".json"),
            filename.replace(".html", ".out.json"),
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
            
            # Remove dynamic fields and non-critical fields for comparison
            for key in ["created_at", "comments", "html"]:
                actual_data.pop(key, None)
                expected_data.pop(key, None)

            self.assertEqual(actual_data, expected_data, f"{filename}의 파싱 결과가 기대값과 다릅니다.")

    def test_parse_all_samples(self):
        """모든 수집된 샘플(HTML/JSON)에 대해 파싱 검증"""
        # 1. Root list.json 검증
        list_json_path = os.path.join(self.root_sample_dir, 'list.json')
        if os.path.exists(list_json_path):
            with self.subTest(filename="list.json"):
                content = self._read_sample_file('list.json', self.root_sample_dir)
                self._verify_list_sample("list.json", content)

        # 2. Samples 디렉토리 내의 HTML 파일들 검증
        if os.path.exists(self.sample_dir):
            html_files = [f for f in os.listdir(self.sample_dir) if f.endswith(".html")]
            for filename in html_files:
                with self.subTest(filename=f"samples/{filename}"):
                    content = self._read_sample_file(filename)
                    if filename.startswith("list_"):
                        self._verify_list_sample(filename, content)
                    else:
                        self._verify_item_sample(filename, content)

if __name__ == '__main__':
    unittest.main()
