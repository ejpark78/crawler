"""
GeekNews 골든 레코드(Golden Record) 생성 스크립트

이 스크립트는 수집된 GeekNews HTML 샘플들을 파싱하여 기대 결과물인 JSON 파일을 생성합니다.
생성된 JSON 파일은 `tests/test_geeknews.py`에서 파싱 로직의 정확성을 검증하는 
기대값(Golden Set)으로 사용됩니다.

주요 기능:
1. `tests/site/geeknews/samples/` 디렉토리 내의 모든 .html 파일을 스캔.
2. 각 HTML 파일을 `GeekNewsScraper`를 통해 파싱 (리스트 또는 상세 페이지 구분).
3. 파싱 결과를 동일한 디렉토리에 .json 파일로 저장.
"""
import os
import json
import logging
from unittest.mock import patch
from app.scrapers.geeknews import GeekNewsScraper

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("GeekNewsGoldenSetGen")

def identify_page_type(html):
    """HTML 내용에 따라 페이지 타입을 판별합니다."""
    if "topic_row" in html:
        return "list"
    if "comment_row" in html or "application/ld+json" in html:
        return "detail"
    return "unknown"

def geeknews_golden_sets():
    """
    tests/site/geeknews/samples/*.html 파일을 읽어 파싱 후 *.json 파일로 저장합니다.
    """
    scraper = GeekNewsScraper()
    sample_dir = 'tests/site/geeknews/samples'
    
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
            
        page_type = identify_page_type(html_content)
        
        try:
            if page_type == "list":
                # 리스트 페이지 파싱 (상세 요청 방지)
                with patch.object(scraper, 'fetch_comments', return_value=([], None, None)):
                    items = scraper.parse(html_content)
                    data = [item.model_dump(mode='json') for item in items]
                    
            elif page_type == "detail":
                # 상세 페이지 파싱 (fetch를 mock)
                with patch.object(scraper, '_do_fetch', return_value=html_content):
                    with patch('time.sleep', return_value=None):
                        url = f"https://news.hada.io/topic?id={filename.split('_')[-1].split('.')[0]}"
                        comments, json_ld_raw, detail_html = scraper.fetch_comments(url)
                        
                        # 상세 페이지 결과는 단일 아이템으로 구성 (가상 메타데이터 포함)
                        from app.models import GeekNewsList
                        item = GeekNewsList(
                            title="Mock Title",
                            url=url,
                            content="Mock Content",
                            source="GeekNews",
                            comments=comments,
                            json_ld_raw=json_ld_raw,
                            html=detail_html
                        )
                        data = item.model_dump(mode='json')
            else:
                logger.warning(f"Unknown page type for {filename}, skipping.")
                continue
            
            # JSON 파일로 저장
            json_filename = filename.replace(".html", ".json")
            json_path = os.path.join(sample_dir, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Generated: {json_filename} ({page_type})")
            generated_count += 1
            
        except Exception as e:
            logger.error(f"Failed to parse {filename}: {e}")

    logger.info(f"Successfully generated {generated_count} golden records for GeekNews.")

if __name__ == "__main__":
    geeknews_golden_sets()
