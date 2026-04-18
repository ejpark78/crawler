import os
import json
import html as html_parser
from bs4 import BeautifulSoup

html_dir = "volumes/debuging/2026-04-18_1328/GeekNews_2026-03-25_1/GeekNews/geeknews_pages/htmls"
items_dir = "volumes/debuging/2026-04-18_1328/GeekNews_2026-03-25_1/GeekNews/geeknews_pages/items"
urls_file = os.path.join(html_dir, "urls.txt")

def process_comment(data):
    if not isinstance(data, dict): return []
    comments = []
    text = data.get('text')
    if text:
        url = data.get('url', '')
        author = data.get('author', {}).get('name', 'Unknown') if isinstance(data.get('author'), dict) else "Unknown"
        comments.append({
            "comment_id": url.split('id=')[-1] if 'id=' in url else f"ld_{hash(text)}",
            "author": author,
            "content": text
        })
    children = data.get('comment', [])
    if isinstance(children, dict): children = [children]
    for child in children:
        comments.extend(process_comment(child))
    return comments

# URL 매핑 로드
mapping = {}
if os.path.exists(urls_file):
    with open(urls_file, 'r') as f:
        for line in f:
            if '|' in line:
                fname, url = line.strip().split(' | ')
                mapping[fname] = url

for item_file in sorted(os.listdir(items_dir)):
    if not item_file.endswith('.json'): continue
    
    path = os.path.join(items_dir, item_file)
    with open(path, 'r') as f:
        item = json.load(f)
    
    target_url = item.get('url')
    # 상세 페이지 URL 찾기 (go=comments)
    topic_url = target_url
    if "topic?id=" in target_url and "go=comments" not in target_url:
        topic_url = target_url + "&go=comments"

    # 아카이브 파일 찾기
    archive_file = None
    for fname, url in mapping.items():
        if url == topic_url:
            archive_file = os.path.join(html_dir, fname)
            break
    
    if archive_file and os.path.exists(archive_file):
        with open(archive_file, 'r') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            script = soup.find('script', type='application/ld+json')
            if script:
                data = json.loads(script.string)
                # 본문 업데이트 및 디코딩
                raw_content = data.get('text') or data.get('articleBody') or data.get('description')
                if raw_content:
                    item['content'] = html_parser.unescape(raw_content)
                
                # 댓글 업데이트 (순수 JSON-LD)
                item['comments'] = []
                comment_data_list = data.get('comment', [])
                if isinstance(comment_data_list, dict): comment_data_list = [comment_data_list]
                for cd in comment_data_list:
                    item['comments'].extend(process_comment(cd))
                
                # 저장
                with open(path, 'w') as out:
                    json.dump(item, out, indent=2, ensure_ascii=False)
                print(f"Reprocessed {item_file}: {item['title']} (Comments: {len(item['comments'])})")
