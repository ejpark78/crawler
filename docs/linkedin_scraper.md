# linkedin_scraper 분석 보고서

GitHub의 [joeyism/linkedin_scraper](https://github.com/joeyism/linkedin_scraper) 저장소를 분석한 내용입니다. 이 라이브러리는 LinkedIn에서 사용자 프로필, 회사 정보, 채용 공고 등을 추출하기 위한 비동기(Async) 스크래핑 도구입니다.

## 1. 주요 특징 및 기능
*   **Playwright 기반**: 이전 버전(v2.x)의 Selenium에서 Playwright로 완전히 재작성되어 성능과 안정성이 향상되었습니다.
*   **비동기 지원**: 모든 메서드가 `async/await`를 사용하는 비동기 방식으로 동작합니다.
*   **데이터 모델**: Pydantic 모델을 사용하여 데이터 구조를 정의하므로 타입 안정성을 제공합니다.
*   **세션 관리**: 인증된 세션을 파일(`session.json`)로 저장하고 재사용하여 매번 로그인할 필요가 없습니다.
*   **스크래핑 대상**:
    *   **개인 프로필**: 이름, 헤드라인, 위치, 요약, 경력, 학력, 기술 등 광범위한 정보 추출.
    *   **회사 페이지**: 개요, 산업군, 규모, 본사 위치 및 회사 게시물(Post) 데이터.
    *   **채용 공고**: 직무 상세 정보, 요구 사항, 회사 정보, 지원 링크 등.

## 2. 기술 스택 및 요구 사항
*   **언어**: Python 3.8+
*   **주요 의존성**:
    *   `playwright`: 브라우저 자동화 및 데이터 추출.
    *   `pydantic 2.0+`: 데이터 모델링 및 검증.
    *   `aiofiles`: 비동기 파일 입출력.
*   **설치 방법**:
    ```bash
    pip install linkedin-scraper
    playwright install chromium
    ```

## 3. 주요 클래스 및 구성
*   **BrowserManager**: 브라우저 인스턴스를 관리하며, 세션 로드(`load_session`) 및 저장(`save_session`) 기능을 제공합니다.
*   **Scrapers**:
    *   `PersonScraper`: 개인 프로필 정보 추출.
    *   `CompanyScraper`: 회사 정보 추출.
    *   `JobSearchScraper`: 채용 공고 검색 및 상세 정보 추출.
    *   `CompanyPostsScraper`: 회사가 작성한 게시물 정보 추출.
*   **ProgressCallback**: 스크래핑 진행 상황을 추적하기 위한 콜백 인터페이스를 제공합니다.

## 4. 사용 방법 흐름
LinkedIn은 인증이 필수적이므로 먼저 세션을 생성해야 합니다.

### 단계 1: 세션 생성 (최초 1회)
브라우저를 열어 수동 로그인하거나 자격 증명을 입력하여 세션을 저장합니다.
```python
from linkedin_scraper import BrowserManager, wait_for_manual_login
import asyncio

async def create_session():
    async with BrowserManager(headless=False) as browser:
        await browser.page.goto("https://www.linkedin.com/login")
        print("로그인 완료를 기다리는 중...")
        await wait_for_manual_login(browser.page)
        await browser.save_session("session.json")
        print("세션 저장 완료!")

asyncio.run(create_session())
```

### 단계 2: 데이터 스크래핑
저장된 세션을 사용하여 비동기로 데이터를 가져옵니다.
```python
import asyncio
from linkedin_scraper import BrowserManager, PersonScraper

async def scrape_profile():
    async with BrowserManager(headless=True) as browser:
        await browser.load_session("session.json")
        scraper = PersonScraper(browser.page)
        person = await scraper.scrape("https://linkedin.com/in/williamhgates/")
        print(f"이름: {person.name}")
        print(f"헤드라인: {person.headline}")

asyncio.run(scrape_profile())
```

## 5. 주의 사항 및 베스트 프랙티스
*   **Rate Limiting**: LinkedIn은 공격적인 스크래핑을 감지하여 차단합니다. 요청 사이에 적절한 지연(`asyncio.sleep`)을 추가하는 것이 필수적입니다.
*   **세션 재사용**: 매번 로그인하는 대신 세션 파일을 최대한 재사용하여 계정 보안 이슈를 방지해야 합니다.
*   **Headless 모드**: 개발 및 디버깅 시에는 `headless=False`를 사용하여 동작을 확인하고, 실제 운영 시에는 `True`로 설정합니다.
*   **법적 책임**: 이 도구는 교육용으로 제작되었습니다. LinkedIn의 서비스 약관(TOS)을 준수해야 하며, 오용으로 인한 책임은 사용자에게 있습니다.

## 6. 라이선스
*   **GPL-3.0 License**: 해당 프로젝트는 오픈소스 라이선스인 GPL-3.0을 따릅니다.
