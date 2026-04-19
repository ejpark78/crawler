"""
GPTERS 골든 레코드(Golden Record) 생성 스크립트

이 스크립트는 수집된 GPTERS GraphQL 응답(JSON) 샘플들을 파싱하여 기대 결과물인 JSON 파일을 생성합니다.
생성된 JSON 파일은 `tests/test_gpters.py`에서 파싱 로직의 정확성을 검증하는 
기대값(Golden Set)으로 사용됩니다.
"""
import os
import json
import logging
from app.scrapers.gpters import GPTERSScraper

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("GPTERSGoldenSetGen")

def gpters_golden_sets():
    """
    tests/site/gpters.org/samples/*.json 파일을 읽어 
    GPTERSScraper로 파싱한 후 결과를 *_expected.json 파일로 저장합니다.
    """
    scraper = GPTERSScraper()
    sample_dir = 'tests/site/gpters.org/samples'
    
    if not os.path.exists(sample_dir):
        logger.info(f"Directory not found, creating: {sample_dir}")
        os.makedirs(sample_dir, exist_ok=True)
        return

    # 원본 응답 샘플 파일들 (.json)
    # 기대 결과물과 구분하기 위해 원본은 .json, 결과는 _expected.json으로 관리하거나
    # 하위 디렉토리를 나눌 수 있으나 여기서는 .json 파일을 찾아 파싱합니다.
    json_files = [f for f in os.listdir(sample_dir) if f.endswith(".json") and not f.endswith("_expected.json")]
    logger.info(f"Found {len(json_files)} JSON sample files in {sample_dir}")
    
    generated_count = 0
    for filename in json_files:
        path = os.path.join(sample_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            json_content = f.read()
            
        try:
            # 파싱 수행
            items = scraper.parse(json_content)
            data = [item.model_dump(mode='json') for item in items]
            
            # 결과 저장 (_expected.json)
            expected_filename = filename.replace(".json", "_expected.json")
            expected_path = os.path.join(sample_dir, expected_filename)
            
            with open(expected_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Generated Golden Set: {expected_filename}")
            generated_count += 1
        except Exception as e:
            logger.error(f"Failed to parse {filename}: {e}")

    logger.info(f"Successfully generated {generated_count} golden records for GPTERS.")

if __name__ == "__main__":
    gpters_golden_sets()
