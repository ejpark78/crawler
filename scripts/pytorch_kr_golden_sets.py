"""
PyTorch KR 골든 레코드(Golden Record) 생성 스크립트

이 스크립트는 수집된 HTML 샘플들을 파싱하여 기대 결과물인 JSON 파일을 생성합니다.
생성된 JSON 파일은 `tests/test_pytorch_kr.py`에서 파싱 로직의 정확성을 검증하는 
기대값(Golden Set)으로 사용됩니다.

주요 기능:
1. `tests/site/pytorch.kr/samples/` 디렉토리 내의 모든 .html 파일을 스캔.
2. 각 HTML 파일을 `PyTorchKRScraper`를 통해 파싱.
3. 파싱 결과를 동일한 디렉토리에 .json 파일로 저장.
"""
import os
import json
import logging
from app.scrapers.pytorch_kr import PyTorchKRScraper

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("GoldenSetGen")

def pytorch_kr_golden_sets():
    """
    tests/site/pytorch.kr/samples/*.html 파일을 읽어 
    PyTorchKRScraper로 파싱한 후 결과를 *.json 파일로 저장합니다.
    이 JSON 파일들은 유닛 테스트의 기대값(Golden Record)으로 사용됩니다.
    """
    scraper = PyTorchKRScraper()
    sample_dir = 'tests/site/pytorch.kr/samples'
    
    if not os.path.exists(sample_dir):
        logger.error(f"Directory not found: {sample_dir}")
        return

    html_files = [f for f in os.listdir(sample_dir) if f.endswith(".html")]
    logger.info(f"Found {len(html_files)} HTML files in {sample_dir}")
    
    generated_count = 0
    for filename in html_files:
        path = os.path.join(sample_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # TopicID 추출하여 가상 URL 생성
        topic_id = filename.split('.')[0]
        url = f"https://discuss.pytorch.kr/t/sample/{topic_id}"
        
        try:
            # 파싱 수행
            result = scraper.parse_content(html_content, url)
            data = result.model_dump(mode='json')
            
            # JSON 파일로 저장
            json_filename = filename.replace(".html", ".json")
            json_path = os.path.join(sample_dir, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Generated: {json_filename}")
            generated_count += 1
        except Exception as e:
            logger.error(f"Failed to parse {filename}: {e}")

    logger.info(f"Successfully generated {generated_count} golden records.")

if __name__ == "__main__":
    pytorch_kr_golden_sets()
