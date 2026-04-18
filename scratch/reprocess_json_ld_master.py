import os
import json
import html as html_parser
import re

html_dir = "volumes/debuging/2026-04-18_1328/GeekNews_2026-03-25_1/GeekNews/geeknews_pages/htmls"
items_dir = "volumes/debuging/2026-04-18_1328/GeekNews_2026-03-25_1/GeekNews/geeknews_pages/items"

def process_comment(data):
    if not isinstance(data, dict): return []
    comments = []
    text = data.get('text')
    if text:
        url = data.get('url', '')
        author = data.get('author', {}).get('name', 'Unknown') if isinstance(data.get('author'), dict) else "Unknown"
        comments.append({
            "comment_id": url.split('id=')[-1] if 'id=' in url else f"ld_{hash(str(data))}",
            "author": author,
            "content": text
        })
    children = data.get('comment', [])
    if isinstance(children, dict): children = [children]
    for child in children:
        comments.extend(process_comment(child))
    return comments

# 1. 모든 HTML 파일에서 URL 매핑 자동 생성
mapping = {}
pattern = r'<script type="application/ld\+json">(.*?)</script>'
for hfile in os.listdir(html_dir):
    if not hfile.endswith('.html'): continue
    hpath = os.path.join(html_dir, hfile)
    with open(hpath, 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1).strip())
                # @id 또는 mainEntityOfPage 등에서 URL 추출
                url = data.get('@id') or (data.get('mainEntityOfPage', {}).get('@id') if isinstance(data.get('mainEntityOfPage'), dict) else None)
                if url:
                    # GeekNews URL 정규화 (id=...&go=comments 형태 선호)
                    if "topic?id=" in url and "go=comments" not in url:
                        url = url + "&go=comments"
                    mapping[url] = hpath
            except:
                continue

print(f"Built mapping for {len(mapping)} URLs from HTML archives.")

# 2. 모든 JSON 아이템 보정
for item_file in sorted(os.listdir(items_dir)):
    if not item_file.endswith('.json'): continue
    
    path = os.path.join(items_dir, item_file)
    with open(path, 'r', encoding='utf-8') as f:
        item = json.load(f)
    
    target_url = item.get('url', '')
    if "topic?id=" in target_url and "go=comments" not in target_url:
        target_url = target_url + "&go=comments"
    
    archive_path = mapping.get(target_url)
    if archive_path:
        with open(archive_path, 'r', encoding='utf-8') as f:
            content_html = f.read()
            match = re.search(pattern, content_html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1).strip())
                    raw_content = data.get('text') or data.get('articleBody') or data.get('description')
                    if raw_content:
                        item['content'] = html_parser.unescape(raw_content)
                    
                    item['comments'] = []
                    comment_data_list = data.get('comment', [])
                    if isinstance(comment_data_list, dict): comment_data_list = [comment_data_list]
                    for cd in comment_data_list:
                        item['comments'].extend(process_comment(cd))
                    
                    with open(path, 'w', encoding='utf-8') as out:
                        json.dump(item, out, indent=2, ensure_ascii=False)
                    print(f"Success: {item_file} -> {item['title']} ({len(item['comments'])} comments)")
                except Exception as e:
                    print(f"Fail {item_file}: {e}")
    else:
        print(f"Skipped {item_file}: No archive found for {target_url}")
