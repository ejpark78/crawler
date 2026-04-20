"""
LinkedIn 하이브리드 피드 스크래퍼 (LinkedIn Hybrid Feed Scraper)

이 모듈은 LinkedIn의 개인 메인 피드와 팔로우 목록 기반의 공개 게시물을 지능적으로 수집합니다.
로그인 세션의 유효성에 따라 '메인 피드 수집 모드' 또는 '공개 프로필 수집 모드'로 자동 전환됩니다.

주요 기능:
    1. 하이브리드 수집 모드:
        - 로그인 성공 시: 사용자의 메인 피드를 무한 스크롤하며 수집합니다.
        - 로그인 실패 시: 저장된 팔로우 목록(followers.json)의 공개 활동 페이지를 순회하며 수집합니다.
    2. 팔로우 및 인맥 관리 (Friends/Followers/Groups Tracking):
        - 로그인 확인 후 `followers.json` 파일이 없으면 자동으로 1촌(Friends), 팔로잉(Followers), 그룹(Groups) 목록을 생성/동기화합니다.
        - 수집 실패 시 구조 분석을 위한 디버그 HTML 저장 및 범용 패턴 추출 로직이 포함되어 있습니다.
    3. 데이터 보존 및 이중화:
        - 각 수집 단계별 스냅샷(Step)과 전체 누적본(Latest)을 JSON/TXT 형식으로 동시 저장합니다.
    4. 도커 및 자동화 최적화:
        - 환경 변수(DOCKER_MODE, HEADLESS)를 지원하여 서버 및 컨테이너 환경에서 무인 가동이 가능합니다.
    5. 스마트 스크롤링: 실제 사용자의 마우스 휠 동작을 모방하여 LinkedIn의 탐지 시스템을 회피합니다.
"""

import asyncio
import os
import json
from datetime import datetime
from linkedin_scraper import BrowserManager


class LinkedInFeedScraper:
    def __init__(self, base_dir="volumes/linkedin", headless=None):
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 도커/환경 변수 설정
        self.is_docker = os.getenv("DOCKER_MODE", "false").lower() == "true"
        if headless is None:
            default_headless = "true" if self.is_docker else "false"
            self.headless = os.getenv("HEADLESS", default_headless).lower() == "true"
        else:
            self.headless = headless

        # 경로 설정
        self.base_dir = base_dir
        self.run_dir = os.path.join(base_dir, self.run_id)
        self.html_dir = os.path.join(self.run_dir, "html")
        self.contents_dir = os.path.join(self.run_dir, "contents")
        
        self.session_file = os.path.join(base_dir, "session.json")
        self.followers_file = os.path.join(base_dir, "followers.json")
        
        # 설정
        self.config = {
            "total_scrolls": 20,
            "save_interval": 2,
            "wheel_steps": 40,
            "load_wait": 8
        }
        
        self.feed_data = []
        self.seen_texts = set()
        
        for d in [self.html_dir, self.contents_dir]:
            os.makedirs(d, exist_ok=True)

    async def run(self):
        print(f"🚀 LinkedIn Scraper 엔진 시작 (ID: {self.run_id})")
        
        async with BrowserManager(headless=self.headless) as browser:
            self.browser = browser
            self.page = browser.page
            
            await self._initialize_session()
            
            # 피드 접속 시도
            await self._navigate_to_url("https://www.linkedin.com/feed/")
            
            # 로그인 체크
            is_logged_in = await self._check_login_status()
            
            if is_logged_in:
                print("✅ 로그인 상태 확인 완료")
                
                # followers.json이 없거나 비어있으면 생성
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
                
                # 메인 피드 수집
                await self._perform_scraping_loop()
            else:
                print("⚠️ 로그인 세션 만료 또는 없음: 공개 피드 수집 모드로 전환합니다.")
                if os.path.exists(self.followers_file):
                    await self._perform_public_scrape_fallback()
                else:
                    print("❌ 오류: 팔로우 목록(followers.json)이 없어 공개 피드를 수집할 수 없습니다.")

            print(f"\n✨ 작업 완료! (수집됨: {len(self.feed_data)}개)")
            if not self.is_docker and not self.headless:
                await asyncio.to_thread(input, "\n💡 종료하려면 Enter를 누르세요...")

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
                await asyncio.to_thread(input, "로그인 완료 후 피드가 보이면 Enter를 누르세요...")
                await self.browser.save_session(self.session_file)
                return True
            return False
        return True

    async def _extract_followers(self):
        """팔로잉, 팔로워, 그룹 목록 수집 (오류 방지 강화)"""
        results = {"following": [], "followers": [], "groups": []}
        
        # 1. Following (내가 팔로우하는 사람들)
        try:
            print("\n🔔 팔로잉(Following) 목록 수집 중...")
            if await self._navigate_to_url("https://www.linkedin.com/mynetwork/network-manager/people-follow/"):
                results["following"] = await self._scrape_list_with_scrolling(name="following", link_pattern="/in/", min_scrolls=10)
        except Exception as e:
            print(f"   ❌ Following 수집 중 오류: {e}")

        # 2. Followers (나를 팔로우하는 사람들)
        try:
            print("\n👤 팔로워(Followers) 목록 수집 중...")
            if await self._navigate_to_url("https://www.linkedin.com/mynetwork/network-manager/people-follow/followers/"):
                results["followers"] = await self._scrape_list_with_scrolling(name="followers", link_pattern="/in/", min_scrolls=50)
        except Exception as e:
            print(f"   ❌ Followers 수집 중 오류: {e}")

        # 3. Groups (가입한 그룹)
        try:
            print("\n👥 가입한 그룹(Groups) 목록 수집 중...")
            if await self._navigate_to_url("https://www.linkedin.com/groups/"):
                # 그룹은 20번 스크롤 또는 변화 없을 때까지만 (행 방지)
                results["groups"] = await self._scrape_list_with_scrolling(name="groups", link_pattern="/groups/", max_scrolls=5)
        except Exception as e:
            print(f"   ❌ Groups 수집 중 오류: {e}")
        
        print(f"\n✅ 수집 완료: 팔로잉 {len(results['following'])}명, 팔로워 {len(results['followers'])}명, 그룹 {len(results['groups'])}개")
        
        # 데이터 저장
        with open(self.followers_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 메인 피드로 복귀 (페이지 상태 확인)
        try:
            if not self.page.is_closed():
                await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
                await asyncio.sleep(3)
        except: pass

    async def _scrape_list_with_scrolling(self, name, link_pattern="/in/", min_scrolls=0, max_scrolls=150):
        """스크롤 및 범용 패턴 추출 로직 (대규모 리스트 대응 및 충돌 방지)"""
        # 가능한 카드 셀렉터들
        card_selectors = [
            "li.mn-connection-card", ".mn-connection-card", ".mn-person-card",
            ".artdeco-list__item", "li[class*='group-card']", ".mn-group-card",
            ".groups-membership-list__item"
        ]
        
        collected = []
        last_link_count = 0
        no_change_count = 0
        
        print(f"   🔍 '{name}' 수집 시작 (패턴: {link_pattern}, 최소 스크롤: {min_scrolls})")
        await asyncio.sleep(5) 
        
        # 1. 셀렉터 감지 시도
        active_selector = None
        for sel in card_selectors:
            try:
                if await self.page.locator(sel).count() > 0:
                    active_selector = sel
                    print(f"   (감지된 셀렉터: {sel})")
                    break
            except: continue

        # 2. 스크롤 루프
        scroll_count = 0
        while scroll_count < max_scrolls:
            # 현재 페이지의 링크 수 확인 (추출 대상 패턴 기준)
            current_links = await self.page.locator(f"a[href*='{link_pattern}']").count()
            
            if current_links > last_link_count:
                print(f"   > {scroll_count}회 스크롤: 현재 약 {current_links}개 링크 발견됨...")
                last_link_count = current_links
                no_change_count = 0
            else:
                no_change_count += 1
            
            # 스크롤 다운 (다양한 방식 시도)
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            # 메인 컨테이너가 따로 있는 경우 대비
            await self.page.evaluate("document.querySelector('main')?.scrollTo(0, 1000000)")
            await asyncio.sleep(2)
            
            # '더 보기' 버튼 클릭 시도
            for btn_sel in ["button.scaffold-finite-scroll__load-button", "button:has-text('Show more')", "button:has-text('더 보기')"]:
                try:
                    btn = self.page.locator(btn_sel)
                    if await btn.is_visible():
                        await btn.click()
                        print("   (더 보기 버튼 클릭함)")
                        await asyncio.sleep(2)
                        no_change_count = 0
                except: pass

            # 최소 스크롤 횟수를 채우지 않았으면 계속 진행
            if no_change_count >= 6 and scroll_count >= min_scrolls:
                break
            
            scroll_count += 1

        # 3. 데이터 일괄 추출
        print(f"   📦 데이터 추출 중...")
        try:
            extract_js = f"""() => {{
                const linkPattern = '{link_pattern}';
                const allLinks = Array.from(document.querySelectorAll('a'));
                const targetLinks = allLinks.filter(a => a.href.includes(linkPattern));
                
                return targetLinks.map(a => {{
                    // 1. 가장 유망한 이름 요소 찾기 (클래스명에 name이 포함된 하위/형제 요소)
                    let name = "";
                    const parent = a.closest('li, .artdeco-list__item, [role="listitem"]') || a.parentElement;
                    
                    if (parent) {{
                        const nameEl = parent.querySelector('[class*="name"], .mn-connection-card__name, .mn-person-card__name');
                        if (nameEl) name = nameEl.innerText.trim();
                    }}
                    
                    // 2. 만약 위에서 못 찾았으면 링크 자체의 텍스트 사용
                    if (!name || name.startsWith('Status is')) {{
                        name = a.innerText.trim();
                    }}
                    
                    // 3. 줄바꿈 제거 및 첫 줄 선택
                    name = name.split('\\n')[0].trim();
                    
                    // 4. 불필요한 상태 메시지 제거
                    if (name.startsWith('Status is')) name = "";
                    
                    return {{
                        name: name,
                        url: a.href
                    }};
                }}).filter(item => 
                    item.name.length > 1 && 
                    !item.url.includes('/status/') && 
                    !item.url.includes('/manage/') &&
                    !['Show more', '더 보기', 'Follow', '팔로우'].includes(item.name)
                );
            }}"""
            
            extracted_data = await self.page.evaluate(extract_js)
            
            # 중복 제거 및 정제
            seen_urls = set()
            for item in extracted_data:
                u = item["url"].split("?")[0].rstrip("/")
                if u not in seen_urls:
                    collected.append({
                        "name": item["name"],
                        "url": u
                    })
                    seen_urls.add(u)
            
        except Exception as e:
            print(f"   ⚠️ 추출 중 오류 발생: {e}")
            await self._save_debug_html_for_analysis(f"error_{name}")

        return collected

    async def _save_debug_html_for_analysis(self, name):
        """분석을 위해 현재 페이지의 HTML을 저장"""
        debug_path = os.path.join(self.base_dir, f"debug_extract_fail_{name}.html")
        try:
            if self.page.is_closed(): return
            content = await self.page.content()
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"   📸 구조 분석용 HTML 저장됨: {debug_path}")
        except Exception as e:
            print(f"   ⚠️ HTML 저장 실패: {e}")

    async def _perform_public_scrape_fallback(self):
        try:
            with open(self.followers_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            targets = (data.get("followers", []) + data.get("friends", []))[:20]
        except: return

        print(f"🌐 총 {len(targets)}명의 프로필 방문을 시작합니다...")
        for idx, person in enumerate(targets):
            print(f"   > [{idx+1}/{len(targets)}] {person['name']} 프로필 방문 중...")
            activity_url = f"{person['url']}recent-activity/all/"
            if await self._navigate_to_url(activity_url):
                await asyncio.sleep(5)
                new_count = await self._extract_current_view()
                self._persist_data(f"public_{idx+1}")
                print(f"     ✅ {new_count}개 수집 완료")
                await asyncio.sleep(3)

    async def _perform_scraping_loop(self):
        viewport = self.page.viewport_size or {'width': 1280, 'height': 720}
        await self.page.mouse.move(viewport['width'] / 2, viewport['height'] / 2)

        for i in range(1, self.config["total_scrolls"] + 1):
            await self._smooth_scroll(i)
            if i % self.config["save_interval"] == 0:
                print(f"\n🔄 동기화 ({i}/{self.config['total_scrolls']})...")
                await self._save_debug_html(i)
                new_count = await self._extract_current_view()
                self._persist_data(i)
                print(f"📋 신규 {new_count}개 발견 (총 {len(self.feed_data)}개)")

    async def _smooth_scroll(self, step_num):
        for _ in range(self.config["wheel_steps"]):
            await self.page.mouse.wheel(0, 100)
            await asyncio.sleep(0.3)
        await asyncio.sleep(self.config["load_wait"])
        print(f"   > 스크롤 중... ({step_num}/{self.config['total_scrolls']})")

    async def _extract_current_view(self):
        extract_js = """() => {
            const containerSelectors = ["div[role='listitem']", "article", ".feed-shared-update-v2", "div[data-urn]"];
            const postEls = Array.from(document.querySelectorAll(containerSelectors.join(',')));
            
            return postEls.map(el => {
                // 1. URN 및 URL 추출
                let urn = el.getAttribute('data-urn');
                if (!urn) {
                    const urnEl = el.querySelector('[data-urn]');
                    if (urnEl) urn = urnEl.getAttribute('data-urn');
                }
                
                let postUrl = (urn && urn !== "undefined" && urn.length > 5) ? `https://www.linkedin.com/feed/update/${urn}/` : "";
                
                // 2. 타임스탬프 링크 시도
                if (!postUrl) {
                    const tsLink = el.querySelector('a[href*="/feed/update/"], .update-components-actor__sub-description a, .feed-shared-actor__sub-description a');
                    if (tsLink) postUrl = tsLink.href;
                }

                // 3. ID 추출 시도 (가장 최신 UI 대응)
                if (!postUrl || postUrl.includes('undefined')) {
                    const elementsWithKey = [el, ...Array.from(el.querySelectorAll('[componentkey], [data-urn], [data-activity-id], [id]'))];
                    for (const item of elementsWithKey) {
                        const attrs = ['componentkey', 'data-urn', 'data-activity-id', 'id'];
                        for (const attr of attrs) {
                            const val = item.getAttribute(attr);
                            if (val) {
                                // Try activity ID first (most reliable for feed posts)
                                const actMatch = val.match(/urn:li:activity:([0-9]+)/);
                                if (actMatch && actMatch[1]) {
                                    postUrl = `https://www.linkedin.com/feed/update/urn:li:activity:${actMatch[1]}/`;
                                    break;
                                }
                                // Try shareId
                                const shareMatch = val.match(/shareId=([0-9]+)/);
                                if (shareMatch && shareMatch[1]) {
                                    postUrl = `https://www.linkedin.com/feed/update/urn:li:activity:${shareMatch[1]}/`;
                                    break;
                                }
                                // Try ugcPost
                                const ugcMatch = val.match(/urn:li:ugcPost:([0-9]+)/);
                                if (ugcMatch && ugcMatch[1]) {
                                    postUrl = `https://www.linkedin.com/feed/update/urn:li:ugcPost:${ugcMatch[1]}/`;
                                    break;
                                }
                            }
                        }
                        if (postUrl && !postUrl.includes('undefined')) break;
                    }
                }

                // 4. 텍스트 추출
                const text = el.innerText.trim();
                
                // 5. 링크 및 이미지
                const links = Array.from(el.querySelectorAll('a')).map(a => a.href).filter(h => h.startsWith('http'));
                const images = Array.from(el.querySelectorAll('img')).map(img => img.src).filter(s => s.startsWith('http'));

                return {
                    content: text,
                    post_url: postUrl,
                    links: Array.from(new Set(links)),
                    image_urls: Array.from(new Set(images))
                };
            }).filter(p => p.content.length > 20);
        }"""

        try:
            results = await self.page.evaluate(extract_js)
            added = 0
            for p in results:
                if p["content"] not in self.seen_texts:
                    self.seen_texts.add(p["content"])
                    self.feed_data.append({
                        "id": len(self.feed_data) + 1,
                        "post_url": p["post_url"],
                        "content": p["content"],
                        "links": p["links"],
                        "image_urls": p["image_urls"],
                        "timestamp": datetime.now().isoformat()
                    })
                    added += 1
            return added
        except Exception as e:
            print(f"   ⚠️ 추출 중 오류 발생: {e}")
            return 0

    async def _save_debug_html(self, step_num):
        path = os.path.join(self.html_dir, f"feed_debug_step_{step_num}.html")
        try:
            content = await self.page.content()
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except: pass

    def _persist_data(self, step_info):
        s_json = os.path.join(self.contents_dir, f"feed_results_step_{step_info}.json")
        s_txt = os.path.join(self.contents_dir, f"feed_results_step_{step_info}.txt")
        l_json = os.path.join(self.contents_dir, "feed_results_latest.json")
        l_txt = os.path.join(self.contents_dir, "feed_results_latest.txt")
        
        for j, t in [(s_json, s_txt), (l_json, l_txt)]:
            self._write_files(j, t, step_info)

    def _write_files(self, j_path, t_path, info):
        try:
            with open(j_path, "w", encoding="utf-8") as f:
                json.dump(self.feed_data, f, ensure_ascii=False, indent=2)
            with open(t_path, "w", encoding="utf-8") as f:
                f.write(f"--- LinkedIn Scrape (Ref: {info}) ---\n")
                f.write(f"--- Run ID: {self.run_id} ---\n")
                f.write("="*50 + "\n")
                for item in self.feed_data:
                    f.write(f"[{item['id']}] {item['content'][:80].replace('\n',' ')}...\n")
                    f.write("-" * 30 + "\n")
        except: pass

if __name__ == "__main__":
    scraper = LinkedInFeedScraper()
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        print("\n👋 중단되었습니다.")
