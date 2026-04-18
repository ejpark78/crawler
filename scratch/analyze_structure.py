from curl_cffi import requests
from bs4 import BeautifulSoup
import json

url = "https://news.hada.io/topic?id=27829"
print(f"Fetching {url} using curl-cffi...")

try:
    response = requests.get(url, impersonate="chrome")
    if response.status_code == 200:
        html = response.text
        print(f"Success! HTML Length: {len(html)}")
        
        soup = BeautifulSoup(html, "html.parser")
        
        # 기사 본문 영역 탐색
        print("\n--- Body Content Search ---")
        # common class names in GeekNews
        for cls in ['topic_contents', 'topic_content', 'topic_row', 'topictitle', 'topicinfo']:
            elements = soup.select(f".{cls}")
            print(f"Selector '.{cls}' found {len(elements)} elements.")
            for i, el in enumerate(elements[:2]):
                print(f"  {cls} {i}: {el.get_text()[:100]}...")
            
        # 댓글 영역 탐색
        print("\n--- Comment Section Search ---")
        # common comment selectors
        for cls in ['comment_thread', 'comment', 'comment_row', 'comment_content', 'comment_list']:
            elements = soup.select(f".{cls}")
            print(f"Selector '.{cls}' found {len(elements)} elements.")
            for i, el in enumerate(elements[:3]):
                print(f"  {cls} {i} Class: {el.get('class')}")

        # 댓글 작성자 및 텍스트 패턴 찾기
        user_links = soup.select("a[href^='/@']")
        print(f"Found {len(user_links)} user links (potential authors).")
        for i, link in enumerate(user_links[:10]):
            p = link.parent
            gp = p.parent
            ggp = gp.parent
            print(f"Author {i}: {link.get_text()}, Link Parent: {p.name}.{'.'.join(p.get('class', []))}, Link GP: {gp.name}.{'.'.join(gp.get('class', []))}, Link GGP: {ggp.name}.{'.'.join(ggp.get('class', []))}")
            
        # 실제 댓글 텍스트가 있을법한 영역 출력
        # 긱뉴스는 보통 작성자 정보 다음에 텍스트가 오거나 특정 클래스 내에 있음
        for cls in ['content', 'comment_contents', 'comment_content']:
            els = soup.select(f".{cls}")
            print(f"Selector '.{cls}' found {len(els)} elements.")

    else:
        print(f"Failed to fetch. Status code: {response.status_code}")
except Exception as e:
    print(f"Error occurred: {e}")
