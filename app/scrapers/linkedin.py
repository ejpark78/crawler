"""
LinkedIn 하이브리드 피드 및 상세 댓글 스크래퍼 (LinkedIn Hybrid Feed & Deep Comment Scraper)

이 모듈은 LinkedIn의 메인 피드와 개별 게시물의 상세 댓글을 지능적으로 수집하는 프로덕션급 스크래퍼입니다.
로그인 세션의 상태에 따라 '메인 피드 수집'과 '공개 활동 수집' 모드를 자동으로 전환하며, 
단순한 텍스트 수집을 넘어 게시물의 고유 식별자(URN)를 기반으로 한 깊은 수준의 데이터 마이닝을 수행합니다.

주요 아키텍처 및 기능:
    1. 지능형 하이브리드 수집 전략:
        - 피드 수집 (Feed Discovery): 사용자의 메인 피드를 무한 스크롤하며 게시물 URN, 본문, 링크, 이미지 및 반응도(좋아요, 댓글수 등)를 수집합니다.
        - 공개 활동 수집 (Public Fallback): 세션 만료 시 followers.json에 저장된 인맥들의 공개 활동 페이지를 순회하며 수집을 지속합니다.
    
    2. 강력한 데이터 추출 엔진 (Hardened Extraction):
        - URN 식별: 단순 CSS 셀렉터가 아닌 속성(Attribute), 자식 요소, 심지어 innerHTML 정규식 검색을 통한 다중 레이어 URN 탐색을 수행합니다.
        - 반응도 파싱: LinkedIn의 빈번한 UI 변경에 대응하기 위해 aria-label 및 텍스트 시맨틱 분석을 통해 좋아요, 댓글, 공유 수를 정확히 추출합니다.
        - 콘텐츠 확장: "... more" 버튼을 자동으로 감지하고 클릭하여 잘린 텍스트 없이 전체 본문을 확보합니다.

    3. 상세 댓글 수집 (Deep Collection Pipeline):
        - 피드에서 발견된 게시물의 개별 고유 URL로 직접 이동하여 lazy-loading되는 댓글 스레드를 수집합니다.
        - 작성자 이름과 댓글 본문을 정확히 매핑하며, 중복 제거 로직이 포함되어 있습니다.

    4. 안정성 및 보안 (Resilience & Session):
        - 스무스 스크롤 (Smooth Scrolling): 마우스 휠 이벤트를 시뮬레이션하고 진행 상황을 실시간으로 로깅하여 사용자 경험과 유사한 동작을 구현합니다.
        - 세션 자동 갱신: 수집 완료 후 최신 쿠키 상태를 session.json에 다시 저장하여 세션 유지 기간을 극대화합니다.
        - 예외 처리: TargetClosedError 등 브라우저 연결 끊김 상황에 대비한 견고한 에러 핸들링과 자동 재시도 로직을 포함합니다.

    5. 환경 변수 및 설정 (Environment & Config):
        - DOCKER_MODE: 도커 환경 여부를 감지하여 브라우저 실행 옵션과 기본 헤드리스 모드를 자동으로 조정합니다.
        - HEADLESS: 환경 변수를 통해 브라우저 시각화 여부를 제어하며, 도커 모드에서는 기본적으로 활성화됩니다.
        - TOTAL_SCROLLS: 수집 깊이를 제어하며, 환경 변수 또는 실행 인자로 유연하게 설정 가능합니다.

    6. 데이터 보존 및 세션 관리 (Persistence & Session):
        - volumes/linkedin/ 하위에 실행 ID별로 HTML 스냅샷, 상세 JSON 데이터, 요약 텍스트 파일을 저장합니다.
        - 세션 자동 갱신: 모든 수집(상세 댓글 포함)이 완료된 후, 최신 쿠키와 인증 상태를 session.json에 즉시 반영하여 로그인 영속성을 유지합니다.
"""

import asyncio
import os
import json
from datetime import datetime
from linkedin_scraper import BrowserManager

from app.scrapers.base import BaseScraper


class LinkedInFeedScraper(BaseScraper):
    def __init__(self, base_dir="volumes/linkedin", headless=None, total_scrolls=30, db_connection=None):
        super().__init__(source_name="LinkedIn")
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.db_conn = db_connection
        
        # 도커/환경 변수 설정
        self.is_docker = os.getenv("DOCKER_MODE", "false").lower() == "true"
        if headless is None:
            default_headless = "true" if self.is_docker else "false"
            self.headless = os.getenv("HEADLESS", default_headless).lower() == "true"
        else:
            self.headless = headless
        
        # 설정 (환경 변수가 있으면 최우선, 없으면 매개변수 사용)
        final_total_scrolls = int(os.getenv("TOTAL_SCROLLS", str(total_scrolls)))
        self.config = {
            "total_scrolls": final_total_scrolls,
            "save_interval": 2,
            "wheel_steps": 40,
            "load_wait": 8
        }

        # 경로 설정
        self.base_dir = base_dir
        self.run_dir = os.path.join(base_dir, self.run_id)
        self.html_dir = os.path.join(self.run_dir, "html")
        self.contents_dir = os.path.join(self.run_dir, "contents")
        
        self.session_file = os.path.join(base_dir, "session.json")
        self.followers_file = os.path.join(base_dir, "followers.json")
        
        self.feed_data = []
        self.seen_texts = set()
        
        for d in [self.html_dir, self.contents_dir]:
            os.makedirs(d, exist_ok=True)

    def _do_fetch(self, url: str) -> str:
        """LinkedIn은 브라우저 세션을 사용하므로 개별 fetch 대신 run에서 처리합니다."""
        return ""

    def parse(self, html: str, db_connection=None):
        """LinkedIn은 동적 페이지이므로 _extract_current_view에서 실시간 파싱을 수행합니다."""
        return []

    async def _sync_config_with_db(self, direction="load"):
        """MongoDB와 로컬 파일(session, followers) 동기화"""
        if not self.db_conn: return
        
        db = self.db_conn["linkedin"]
        coll = db["config"]
        
        files = {
            "linkedin/config/session.json": self.session_file,
            "linkedin/config/followers.json": self.followers_file
        }
        
        for key, path in files.items():
            if direction == "load":
                # DB에서 읽어와 로컬 파일 갱신
                doc = coll.find_one({"_id": key})
                if doc and doc.get("data"):
                    print(f"🔄 DB에서 {key} 설정을 로드합니다.")
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(doc["data"], f, ensure_ascii=False, indent=2)
            else:
                # 로컬 파일 읽어서 DB 갱신
                if os.path.exists(path):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        coll.update_one(
                            {"_id": key},
                            {"$set": {"data": data, "updated_at": datetime.now()}},
                            upsert=True
                        )
                        print(f"💾 DB에 {key} 설정을 백업했습니다.")
                    except: pass

    async def run(self, db_connection=None, backfill_date=None, page=None):
        if db_connection:
            self.db_conn = db_connection
            
        print(f"🚀 LinkedIn Scraper 엔진 시작 (ID: {self.run_id})")
        
        # 시작 전 DB에서 설정 로드
        await self._sync_config_with_db(direction="load")
        
        async with BrowserManager(headless=self.headless) as browser:
            self.browser = browser
            self.page = browser.page
            self.context = browser.context
            
            await self._initialize_session()
            
            # 1. 피드 접속 및 로그인 체크
            await self._navigate_to_url("https://www.linkedin.com/feed/")
            is_logged_in = await self._check_login_status()
            
            if is_logged_in:
                print("✅ 로그인 상태 확인 완료")
                
                # followers.json 동기화 (필요시)
                await self._sync_followers_if_needed()
                
                # 2. 메인 피드 스크롤 수집
                await self._perform_scraping_loop()
                
                # 3. 상세 댓글 수집 (Deep Dive)
                await self._collect_deep_comments()
                
                # 세션 갱신 (쿠키 최신화)
                print("💾 세션 정보를 갱신합니다...")
                await self.browser.save_session(self.session_file)
                await self._sync_config_with_db(direction="save")
            else:
                print("⚠️ 로그인 세션 만료: 공개 피드 수집 모드로 전환합니다.")
                if os.path.exists(self.followers_file):
                    await self._perform_public_scrape_fallback()
                else:
                    print("❌ 오류: 팔로우 목록이 없어 공개 수집이 불가합니다.")

            print(f"\n🎉 모든 작업 완료! 총 {len(self.feed_data)}개 수집됨.")
            if not self.is_docker and not self.headless:
                print("💡 브라우저를 종료하려면 터미널에서 Enter를 누르거나 Ctrl+C를 누르세요.")

            return self.feed_data, ""

    async def _initialize_session(self):
        if os.path.exists(self.session_file):
            print(f"📦 세션 로드: {self.session_file}")
            await self.browser.load_session(self.session_file)
            self.page = self.browser.page

    async def _navigate_to_url(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                if self.page.is_closed():
                     self.page = await self.browser.context.new_page()

                print(f"🔗 이동 중: {url} (시도 {attempt+1})")
                await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)
                return True
            except Exception as e:
                print(f"⚠️ 이동 실패: {e}")
                await asyncio.sleep(5)
        return False

    async def _check_login_status(self):
        is_logged_in = "feed" in self.page.url and await self.page.locator("text=Sign in").count() == 0
        if not is_logged_in:
            if not self.is_docker and not self.headless:
                print("\n🔑 로그인이 필요합니다! 브라우저 창에서 로그인을 마쳐주세요.")
                # 터미널 입력 대기
                await asyncio.get_event_loop().run_in_executor(None, input, "로그인 완료 후 피드가 보이면 Enter를 누르세요...")
                await self.browser.save_session(self.session_file)
                await self._sync_config_with_db(direction="save")
                return True
            return False
        return True

    async def _sync_followers_if_needed(self):
        should_extract = not os.path.exists(self.followers_file)
        if not should_extract:
            try:
                with open(self.followers_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not any([data.get("following"), data.get("followers"), data.get("groups")]):
                        should_extract = True
            except: should_extract = True

        if should_extract:
            print("📝 팔로우 목록 동기화를 시작합니다.")
            await self._extract_followers()
            await self._sync_config_with_db(direction="save")

    async def _perform_scraping_loop(self):
        total = self.config["total_scrolls"]
        print(f"🔄 피드 수집 루프 시작 ({total}회 스크롤)")
        
        for i in range(1, total + 1):
            if self.page.is_closed():
                print("⚠️ 페이지가 닫혀 있어 수집을 중단합니다.")
                break
                
            success = await self._smooth_scroll(i)
            if not success: break
            
            print(f"  > 스크롤 진행 중... ({i}/{total})")
            
            if i % self.config["save_interval"] == 0 or i == total:
                try:
                    # "... more" 버튼 클릭하여 전문 펼치기
                    await self._expand_all_posts()
                    await self._save_debug_html(i)
                    new_count = await self._extract_current_view()
                    self._persist_data(i)
                    print(f"📋 스텝 {i}: 신규 {new_count}개 발견 (누적 {len(self.feed_data)}개)")
                except Exception as e:
                    print(f"⚠️ 데이터 추출 중 오류 발생: {e}")
                    if "closed" in str(e).lower(): break

    async def _smooth_scroll(self, step_num):
        try:
            # 마우스 위치 초기화 (중앙 부근으로 이동하여 피드에 포커스)
            viewport = self.page.viewport_size
            if viewport:
                await self.page.mouse.move(viewport['width'] / 2, viewport['height'] / 2)
            else:
                await self.page.mouse.move(500, 500)
                
            steps = self.config["wheel_steps"]
            for s in range(1, steps + 1):
                if self.page.is_closed(): return False
                await self.page.mouse.wheel(0, 150)
                await asyncio.sleep(0.2)
                if s % 10 == 0:
                    print(f"    ... 스크롤 중 ({s}/{steps})")
                    
            await asyncio.sleep(self.config["load_wait"])
            return True
        except Exception as e:
            print(f"⚠️ 스크롤 중 오류 발생: {e}")
            return False

    async def _expand_all_posts(self):
        if self.page.is_closed(): return
        try:
            await self.page.evaluate("""() => {
                const buttons = Array.from(document.querySelectorAll('button, span[role="button"]'));
                const moreButtons = buttons.filter(btn => {
                    const text = btn.innerText.trim().toLowerCase();
                    return text.includes('... more') || text.includes('… more') || text.includes('see more');
                });
                
                moreButtons.forEach(btn => {
                    if (btn.offsetParent !== null && !btn.hasAttribute('data-clicked-by-bot')) {
                        btn.click();
                        btn.setAttribute('data-clicked-by-bot', 'true');
                    }
                });
            }""")
            await asyncio.sleep(1.5)
        except: pass

    async def _extract_current_view(self):
        extract_js = """() => {
            const containerSelectors = [".feed-shared-update-v2", "article", "div[role='listitem']", "div[data-urn]"];
            const postEls = Array.from(document.querySelectorAll(containerSelectors.join(',')));
            const results = [];
            const seenUrns = new Set();
            
            postEls.forEach(el => {
                let urn = "";
                // 1. URN 추출 (속성 확인)
                const idAttrs = ["data-urn", "data-activity-id", "componentkey"];
                for (const attr of idAttrs) {
                    const val = el.getAttribute(attr);
                    if (val && val.includes('urn:li:')) {
                        const m = val.match(/urn:li:(activity|ugcPost|share|article):([0-9]{10,})/);
                        if (m) { urn = `urn:li:${m[1]}:${m[2]}`; break; }
                    }
                }
                
                // 2. 자식 요소 속성 확인
                if (!urn) {
                    const urnEl = el.querySelector('[data-urn], [data-activity-id], [componentkey]');
                    if (urnEl) {
                        const val = urnEl.getAttribute('data-urn') || urnEl.getAttribute('data-activity-id') || urnEl.getAttribute('componentkey');
                        if (val && val.includes('urn:li:')) {
                            const m = val.match(/urn:li:(activity|ugcPost|share|article):([0-9]{10,})/);
                            if (m) urn = `urn:li:${m[1]}:${m[2]}`;
                        }
                    }
                }

                // 3. InnerHTML 정규식 검색
                if (!urn) {
                    const m = el.innerHTML.match(/urn:li:(activity|ugcPost|share|article):([0-9]{15,})/);
                    if (m) urn = `urn:li:${m[1]}:${m[2]}`;
                }

                if (!urn || seenUrns.has(urn)) return;
                seenUrns.add(urn);

                const text = el.innerText.trim();
                const allLinks = Array.from(el.querySelectorAll('a')).map(a => a.href).filter(h => h.startsWith('http'));
                const images = Array.from(el.querySelectorAll('img')).map(img => img.src).filter(s => s.startsWith('http'));

                // Social Counts 추출
                const getCount = (labelKeywords) => {
                    const elements = Array.from(el.querySelectorAll('button, a, span, li'));
                    for (const target of elements) {
                        const label = (target.getAttribute('aria-label') || "").toLowerCase();
                        const txt = target.innerText.toLowerCase();
                        for (const kw of labelKeywords) {
                            if (label.includes(kw) || txt.includes(kw)) {
                                const m = (label + " " + txt).match(/([0-9,.]+)/);
                                if (m) {
                                    const val = parseInt(m[1].replace(/[,.]/g, ''));
                                    if (!isNaN(val)) return val;
                                }
                            }
                        }
                    }
                    return 0;
                };
                
                const likes = getCount(['reaction', 'like', '좋아요']);
                const comments = getCount(['comment', '댓글']);
                const reposts = getCount(['repost', '공유']);

                results.push({
                    urn: urn,
                    content: text,
                    links: Array.from(new Set(allLinks)),
                    image_urls: Array.from(new Set(images)),
                    engagement: { likes, comments, reposts },
                    reply: []
                });
            });
            return results;
        }"""

        try:
            results = await self.page.evaluate(extract_js)
            added = 0
            for p in results:
                is_duplicate = False
                if p["urn"]:
                    for existing in self.feed_data:
                        if existing.get("urn") == p["urn"]:
                            is_duplicate = True
                            break
                elif p["content"] in self.seen_texts:
                    is_duplicate = True

                if not is_duplicate:
                    if p["content"]: self.seen_texts.add(p["content"])
                    self.feed_data.append({
                        "urn": p["urn"],
                        "content": p["content"],
                        "links": p["links"],
                        "image_urls": p["image_urls"],
                        "engagement": p["engagement"],
                        "reply": p["reply"],
                        "timestamp": datetime.now().isoformat()
                    })
                    added += 1
            return added
        except Exception as e:
            print(f"   ⚠️ 추출 중 오류 발생: {e}")
            return 0

    async def _collect_deep_comments(self):
        """수집된 게시물들의 개별 페이지를 방문하여 댓글을 상세 수집합니다."""
        target_posts = [p for p in self.feed_data if p.get("urn") and not p.get("reply")]
        if not target_posts: return

        print(f"\n💬 {len(target_posts)}개 게시물의 댓글 상세 수집을 시작합니다...")
        
        for idx, item in enumerate(target_posts):
            urn = item["urn"]
            url = f"https://www.linkedin.com/feed/update/{urn}/"
            print(f"   > [{idx+1}/{len(target_posts)}] 댓글 수집 중: {urn}")
            
            if await self._navigate_to_url(url):
                await asyncio.sleep(4)
                # 살짝 스크롤하여 댓글 로드 유도
                await self.page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(2)

                # 디버그용 HTML 저장 및 MongoDB 저장
                try:
                    html = await self.page.content()
                    
                    # 로컬 파일 저장
                    debug_path = os.path.join(self.html_dir, f"post_debug_{idx+1}.html")
                    with open(debug_path, "w", encoding="utf-8") as f: f.write(html)
                    
                    # MongoDB 저장 (pages_html 컬렉션)
                    if self.db_conn:
                        db = self.db_conn["linkedin"]
                        html_coll = db["pages_html"]
                        html_coll.update_one(
                            {"_id": urn},
                            {"$set": {"urn": urn, "html": html, "updated_at": datetime.now()}},
                            upsert=True
                        )
                except Exception as e:
                    print(f"     ⚠️ HTML 저장 중 오류: {e}")

                # 댓글 추출 JS (매우 구체적으로)
                comments = await self.page.evaluate("""() => {
                    // 댓글 본문을 가진 span들을 찾고, 거기서부터 부모를 타고 올라가서 정보를 취합
                    const contentNodes = document.querySelectorAll('.comments-comment-item__main-content, .comments-comment-entity__content');
                    const results = [];
                    
                    contentNodes.forEach(contentEl => {
                        // 가장 가까운 댓글 컨테이너 찾기 (thread-item 또는 comment-item 등)
                        const container = contentEl.closest('.comments-thread-item, .comments-comment-item, article');
                        if (!container) return;
                        
                        // 작성자 이름 찾기
                        const authorEl = container.querySelector('.comments-comment-meta__description-title, .comments-post-meta__name-text, [data-test-comment-author-name]');
                        const author = authorEl ? authorEl.innerText.trim() : "Unknown";
                        
                        // 내용 (중복 방지를 위해 trim 및 체크)
                        const content = contentEl.innerText.trim();
                        if (content && content.length > 0) {
                            results.push({ author, content });
                        }
                    });
                    
                    // 중복 제거 (내용 기준)
                    const uniqueResults = [];
                    const seen = new Set();
                    results.forEach(r => {
                        const key = r.author + "|" + r.content;
                        if (!seen.has(key)) {
                            seen.add(key);
                            uniqueResults.push(r);
                        }
                    });
                    return uniqueResults;
                }""")
                
                print(f"     ✅ {len(comments)}개 댓글 추출됨")
                item["reply"] = comments
                self._persist_data("deep")
                await asyncio.sleep(2)

    async def _extract_followers(self):
        """팔로잉, 팔로워, 그룹 목록 수집"""
        results = {"following": [], "followers": [], "groups": []}
        try:
            print("\n🔔 팔로잉(Following) 목록 수집 중...")
            if await self._navigate_to_url("https://www.linkedin.com/mynetwork/network-manager/people-follow/"):
                results["following"] = await self._scrape_list_with_scrolling(name="following", link_pattern="/in/", min_scrolls=5)
            
            print("\n👤 팔로워(Followers) 목록 수집 중...")
            if await self._navigate_to_url("https://www.linkedin.com/mynetwork/network-manager/people-follow/followers/"):
                results["followers"] = await self._scrape_list_with_scrolling(name="followers", link_pattern="/in/", min_scrolls=10)
        except Exception as e:
            print(f"   ⚠️ 팔로우 목록 수집 중 오류: {e}")
        
        with open(self.followers_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    async def _scrape_list_with_scrolling(self, name, link_pattern, min_scrolls=0, max_scrolls=50):
        """범용 리스트 스크롤 추출"""
        collected = []
        for s in range(max_scrolls):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            if s >= min_scrolls:
                # 간단한 추출 로직
                links = await self.page.evaluate(f"""(pattern) => {{
                    return Array.from(document.querySelectorAll('a'))
                        .filter(a => a.href.includes(pattern))
                        .map(a => ({{ name: a.innerText.split('\\n')[0], url: a.href.split('?')[0] }}));
                }}""", link_pattern)
                for l in links:
                    if l['url'] not in [c['url'] for c in collected]:
                        collected.append(l)
                if s > min_scrolls + 5: break # 대략적인 중단
        return collected

    async def _perform_public_scrape_fallback(self):
        """저장된 인맥들의 공개 활동 페이지를 순회하며 수집"""
        try:
            with open(self.followers_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            targets = (data.get("followers", []) + data.get("following", []))[:10]
        except: return

        for person in targets:
            url = f"{person['url']}recent-activity/all/"
            if await self._navigate_to_url(url):
                await asyncio.sleep(5)
                await self._extract_current_view()
                self._persist_data("public")

    async def _save_debug_html(self, step_num):
        path = os.path.join(self.html_dir, f"feed_debug_step_{step_num}.html")
        try:
            content = await self.page.content()
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except: pass

    def _persist_data(self, step_info):
        l_json = os.path.join(self.contents_dir, "feed_results_latest.json")
        l_txt = os.path.join(self.contents_dir, "feed_results_latest.txt")
        try:
            with open(l_json, "w", encoding="utf-8") as f:
                json.dump(self.feed_data, f, ensure_ascii=False, indent=2)
            with open(l_txt, "w", encoding="utf-8") as f:
                f.write(f"--- LinkedIn Scrape (Step: {step_info}) ---\n")
                for item in self.feed_data:
                    f.write(f"[{item['id']}] {item['content'][:80]}...\n")
            
            # MongoDB 저장
            if self.db_conn:
                db = self.db_conn["linkedin"]
                coll = db["pages"]
                for item in self.feed_data:
                    # _id 를 urn 으로 설정하여 upsert
                    doc = item.copy()
                    if doc.get("urn"):
                        doc["_id"] = doc["urn"]
                    coll.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
                print(f"✅ MongoDB 데이터 동기화 완료 (누적 {len(self.feed_data)}개)")
        except Exception as e:
            print(f"⚠️ 데이터 저장 중 오류: {e}")

if __name__ == "__main__":
    import sys
    from pymongo import MongoClient
    # Command line argument support: python script.py [total_scrolls]
    ts = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    
    # MongoDB 연결 시도
    client = None
    try:
        client = MongoClient("mongodb://mongodb:27017/", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print("✅ MongoDB 연결 성공")
    except:
        client = None
        print("⚠️ MongoDB 연결 실패 (로컬 모드)")

    scraper = LinkedInFeedScraper(total_scrolls=ts, db_connection=client)
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        print("\n👋 중단되었습니다.")
    finally:
        if client: client.close()
